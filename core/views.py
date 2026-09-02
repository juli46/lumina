
from datetime import date, datetime, timedelta
import hashlib
import json
import logging
import uuid

import requests
from decimal import Decimal, InvalidOperation, ROUND_CEILING

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.db import transaction
from django.db.models import Avg, Count, Exists, OuterRef, Q, Sum
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.utils.text import slugify
from django.views.decorators.http import require_POST

from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side

from .decorators import admin_required
from .forms import CambiarPasswordForm, DireccionForm, EditarPerfilForm, RegistroForm
from .gmail import enviar_correo, obtener_encabezado, obtener_hilo, obtener_texto
from .models import (
    BlogPost, BlogSeccion, Carrito, CarritoItem, CarritoItemKitSeleccion,
    Categoria, Coleccion, Contacto, Direccion, Etiqueta, EventoCalendario,
    Galeria, IdeaContenido, Kit, KitProducto, Marca, NotaAdmin, Opcion, Pago,
    Pedido, PedidoItem, PedidoItemKitSeleccion, PostIt, Pregunta, Producto,
    ProductoImagen, ProductoVideo, Recordatorio, RecomendacionEmprendimiento,
    ReporteEmprendimiento, Resultado, ResultadoUsuario, Test, Usuario, Variante,
)

from django.contrib.auth.views import (
    PasswordResetView,
    PasswordResetDoneView,
    PasswordResetConfirmView,
    PasswordResetCompleteView,
)

logger = logging.getLogger(__name__)


# =========================================================================
# HELPERS Y CONSTANTES DE PRECIOS / MÁRGENES / ENVÍO / STOCK
# (usados por productos, checkout, kits, estadísticas y recomendaciones)
# =========================================================================

MARGENES_RENTABILIDAD = (
    {
        "desde": Decimal("0"),
        "margen": Decimal("0.30"),
        "etiqueta": "Al detalle",
    },
    {
        "desde": Decimal("1200000"),
        "margen": Decimal("0.10"),
        "etiqueta": "Más de $1.200.000",
    },
    {
        "desde": Decimal("500000"),
        "margen": Decimal("0.15"),
        "etiqueta": "Más de $500.000",
    },
    {
        "desde": Decimal("100000"),
        "margen": Decimal("0.20"),
        "etiqueta": "Más de $100.000",
    },
)

UMBRAL_STOCK_BAJO = 5


def normalizar_precio(valor):
    """Convierte '150.500' o '150500,25' (formato colombiano) a Decimal
    de forma segura. Devuelve None si el valor está vacío o no es válido."""

    valor = (valor or "").strip()

    if not valor:
        return None

    # Si tiene coma, se asume que la coma es el separador decimal
    # y el punto (si existe) es separador de miles.
    if "," in valor:
        valor = valor.replace(".", "").replace(",", ".")

    try:
        return Decimal(valor)
    except InvalidOperation:
        return None


def calcular_precio_con_margen(costo):

    precio = costo / (Decimal("1") - Decimal("0.30"))

    return aproximar_precio(precio), Decimal("0.30")


def aproximar_precio(precio):

    return (precio / Decimal("100")).to_integral_value(
        rounding=ROUND_CEILING
    ) * Decimal("100")


def calcular_precios_por_margen(costo):

    return [
        {
            "etiqueta": regla["etiqueta"],
            "margen": regla["margen"] * Decimal("100"),
            "precio": aproximar_precio(
                costo / (Decimal("1") - regla["margen"])
            ),
        }
        for regla in sorted(
            MARGENES_RENTABILIDAD,
            key=lambda item: item["margen"],
            reverse=True
        )
    ]


def obtener_margen_por_monto(total):
    """
    Determina el margen de rentabilidad según
    el valor total de la compra al detal.
    """

    reglas = sorted(
        MARGENES_RENTABILIDAD,
        key=lambda x: x["desde"],
        reverse=True
    )

    for regla in reglas:

        if total >= regla["desde"]:
            return regla

    return reglas[-1]


def calcular_precio_segun_monto(producto, monto):
    """
    Calcula el precio de venta del producto según
    el monto total de la compra.
    """

    regla = obtener_margen_por_monto(monto)

    margen = regla["margen"]

    precio = producto.costo_base / (
        Decimal("1") - margen
    )

    return aproximar_precio(precio)


def calcular_carrito_con_margen(items):

    subtotal_detalle = Decimal("0")

    # ==========================================
    # PRIMERO: calcular subtotal al detal
    # ==========================================

    for item in items:

        precio_detalle = (
            item.variante.producto.precio_base
        )

        subtotal_detalle += (
            precio_detalle * item.cantidad
        )

    # ==========================================
    # DETERMINAR MARGEN
    # ==========================================

    regla = obtener_margen_por_monto(
        subtotal_detalle
    )

    margen = regla["margen"]

    # ==========================================
    # CALCULAR CADA PRODUCTO
    # ==========================================

    subtotal_final = Decimal("0")
    descuento_total = Decimal("0")

    productos = []

    for item in items:

        producto = item.variante.producto

        precio_detalle = producto.precio_base

        # Precio según margen
        precio_mayorista = (
            producto.costo_base /
            (Decimal("1") - margen)
        )

        # Redondear a centenas
        precio_mayorista = aproximar_precio(
            precio_mayorista
        )

        # Descuento de ESTE producto
        descuento_unitario = (
            precio_detalle -
            precio_mayorista
        )

        subtotal_producto = (
            precio_mayorista *
            item.cantidad
        )

        descuento_producto = (
            descuento_unitario *
            item.cantidad
        )

        subtotal_final += subtotal_producto

        descuento_total += descuento_producto

        productos.append({
            "item": item,
            "precio_detalle": precio_detalle,
            "precio_mayorista": precio_mayorista,
            "descuento_unitario": descuento_unitario,
            "subtotal": subtotal_producto,
            "descuento": descuento_producto,
        })

    return {
        "subtotal_detalle": subtotal_detalle,
        "subtotal_final": subtotal_final,
        "descuento_total": descuento_total,
        "margen": margen,
        "etiqueta": regla["etiqueta"],
        "productos": productos,
    }


def calcular_costo_envio(direccion):
    ciudad = direccion.ciudad.strip().lower()

    if ciudad in ("medellín", "medellin"):
        return Decimal("10000")

    return Decimal("12000")


# =========================
# PÁGINAS
# =========================

def home(request):
    return render(request, "core/inicio.html")


def nosotros(request):
    return render(request, "core/nosotros.html")


def contacto(request):

    if request.method == "POST":

        nombre = request.POST.get("nombre")
        correo = request.POST.get("correo")
        asunto = request.POST.get("asunto")
        mensaje = request.POST.get("mensaje")

        contacto = Contacto.objects.create(
            nombre=nombre,
            correo=correo,
            asunto=asunto,
            mensaje=mensaje
        )

        resultado = enviar_correo(
            correo,
            "✨ Hemos recibido tu mensaje | Lúmina",
            f"""
Hola {nombre},

Gracias por comunicarte con Lúmina 💖

Hemos recibido tu mensaje:

{mensaje}

Nuestro equipo responderá pronto.

Equipo Lúmina
"""
        )

        contacto.gmail_message_id = resultado["message_id"]
        contacto.gmail_thread_id = resultado["thread_id"]
        contacto.save()

        messages.success(
            request,
            "✨ Tu mensaje fue enviado correctamente."
        )

        return redirect("contacto")

    return render(
        request,
        "core/contacto.html"
    )


def emprender(request):

    recomendaciones = (
        RecomendacionEmprendimiento.objects
        .filter(activa=True)
        .prefetch_related("productos", "kits")
        .order_by("presupuesto_min")
    )

    return render(
        request,
        "core/emprender.html",
        {
            "recomendaciones": recomendaciones,
        }
    )


def tips(request):
    blogs = BlogPost.objects.filter(publicado=True).order_by("-fecha_creacion")
    galeria = Galeria.objects.all().order_by("-fecha_creacion")
    tests = Test.objects.filter(activo=True)

    return render(request, "core/tips.html", {
        "blogs": blogs,
        "galeria": galeria,
        "tests": tests,
    })


@login_required
def mi_cuenta(request):
    form = DireccionForm()

    pedidos = Pedido.objects.filter(
        usuario=request.user
    ).order_by("-id")[:4]

    resultados_usuario = ResultadoUsuario.objects.filter(
        usuario=request.user
    ).select_related(
        "test",
        "resultado"
    )

    reportes_emprendimiento = request.user.reportes_emprendimiento.all()

    return render(request, "core/cuenta.html", {
        "form": form,
        "pedidos": pedidos,
        "resultados_usuario": resultados_usuario,
        "reportes_emprendimiento": reportes_emprendimiento,
    })


# =========================
# REGISTRO
# =========================

def registro(request):
    if request.method == "POST":
        form = RegistroForm(request.POST)

        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data["password"])
            user.rol = "usuario"
            user.save()

            login(request, user)
            return redirect("home")
    else:
        form = RegistroForm()

    return render(request, "core/registro.html", {"form": form})


# =========================
# LOGIN / LOGOUT
# =========================

def login_view(request):
    if request.method == "POST":
        email = request.POST.get("email")
        password = request.POST.get("password")

        try:
            user_obj = Usuario.objects.get(email=email)

            if not user_obj.is_active:
                messages.error(request, "Tu cuenta está inactiva, contacta al administrador")
                return redirect("login")

            user = authenticate(
                request,
                username=user_obj.username,
                password=password,
            )

            if user is None:
                messages.error(request, "Correo o contraseña incorrectos")
                return redirect("login")

            login(request, user)

            if getattr(user, "rol", None) == "admin":
                return redirect("admin_dashboard")

            return redirect("home")

        except Usuario.DoesNotExist:
            messages.error(request, "Correo o contraseña incorrectos")
            return redirect("login")

    return render(request, "core/login.html")


def logout_view(request):
    logout(request)
    return redirect("login")


# =========================
# PERFIL Y CUENTA
# =========================

@login_required
def editar_perfil(request):
    if request.method == "POST":
        form = EditarPerfilForm(
            request.POST,
            request.FILES,
            instance=request.user,
        )

        if form.is_valid():
            form.save()
            return redirect("mi_cuenta")
    else:
        form = EditarPerfilForm(instance=request.user)

    return render(request, "core/editar_perfil.html", {"form": form})


def validar_email(request):
    email = request.GET.get("email")
    existe = Usuario.objects.filter(email=email).exists()

    return JsonResponse({"existe": existe})


@login_required
def configuracion(request):
    perfil_form = EditarPerfilForm(instance=request.user)
    password_form = CambiarPasswordForm()

    if request.method == "POST":

        # Cambiar contraseña
        if "password_actual" in request.POST:
            password_form = CambiarPasswordForm(request.POST)

            if password_form.is_valid():
                user = request.user

                actual = password_form.cleaned_data["password_actual"]
                nueva = password_form.cleaned_data["password_nueva"]
                confirmar = password_form.cleaned_data["password_confirmar"]

                if not user.check_password(actual):
                    messages.error(request, "La contraseña actual no es correcta")

                elif nueva != confirmar:
                    messages.error(request, "Las contraseñas no coinciden")

                else:
                    user.set_password(nueva)
                    user.save()

                    update_session_auth_hash(request, user)
                    messages.success(request, "Contraseña actualizada")

                return redirect("configuracion")

        # Editar perfil
        perfil_form = EditarPerfilForm(
            request.POST,
            request.FILES,
            instance=request.user,
        )

        if perfil_form.is_valid():
            perfil_form.save()
            messages.success(request, "Perfil actualizado")
            return redirect("configuracion")

    return render(request, "core/configuracion.html", {
        "form_perfil": perfil_form,
        "form_password": password_form,
    })


# =========================
# ADMINISTRACIÓN DE USUARIOS
# =========================

@login_required
@admin_required
def usuario_d(request):
    usuarios_list = Usuario.objects.all().order_by("-id")

    paginator = Paginator(usuarios_list, 10)
    page_number = request.GET.get("page")
    usuarios = paginator.get_page(page_number)

    return render(request, "core/usuarios_d.html", {
        "usuarios": usuarios,
    })


@login_required
@admin_required
def editar_usuario(request, id):
    usuario = get_object_or_404(Usuario, id=id)

    if request.method == "POST":
        usuario.username = request.POST.get("username")
        usuario.email = request.POST.get("email")
        usuario.telefono = request.POST.get("telefono")
        usuario.rol = request.POST.get("rol")
        usuario.is_active = request.POST.get("is_active") == "True"

        usuario.save()
        return redirect("usuario_d")

    return render(request, "core/editar_usuario.html", {
        "usuario": usuario,
    })

@login_required
@admin_required
@require_POST
def eliminar_usuario(request, user_id):
    usuario = get_object_or_404(Usuario, id=user_id)

    # Evitar que el administrador se elimine a sí mismo
    if request.user.id == usuario.id:
        messages.warning(
            request,
            "No puedes eliminar tu propia cuenta."
        )
        return redirect("usuario_d")

    # Si tiene pedidos, se desactiva en lugar de eliminarse
    if usuario.pedidos.exists():
        usuario.estado = "inactivo"
        usuario.is_active = False
        usuario.save(update_fields=["estado", "is_active"])

        messages.warning(
            request,
            f"El usuario {usuario.username} tiene pedidos asociados. "
            "La cuenta fue desactivada para conservar su historial de pedidos."
        )
    else:
        # Si no tiene pedidos, se elimina normalmente
        usuario.delete()

        messages.success(
            request,
            f"El usuario {usuario.username} fue eliminado correctamente."
        )

    return redirect("usuario_d")

@login_required
@admin_required
def exportar_usuarios_excel(request):
    wb = Workbook()
    ws = wb.active
    ws.title = "Usuarios"

    # Título
    ws.merge_cells("A1:E1")
    titulo = ws["A1"]
    titulo.value = "Reporte de Usuarios - Lúmina"
    titulo.font = Font(size=16, bold=True, color="FFFFFF")
    titulo.fill = PatternFill("solid", fgColor="DF6D77")
    titulo.alignment = Alignment(horizontal="center")

    # Fecha
    ws["A2"] = f"Generado: {datetime.now().strftime('%d/%m/%Y %H:%M')}"

    # Encabezados
    encabezados = [
        "Usuario",
        "Correo",
        "Teléfono",
        "Rol",
        "Estado",
    ]

    fila_header = 4

    for col_num, header in enumerate(encabezados, 1):
        cell = ws.cell(row=fila_header, column=col_num)
        cell.value = header
        cell.font = Font(bold=True, color="FFFFFF")
        cell.fill = PatternFill("solid", fgColor="DF6D77")
        cell.alignment = Alignment(horizontal="center")

    # Datos
    fila = 5

    for usuario in Usuario.objects.all():
        ws.cell(fila, 1, usuario.username)
        ws.cell(fila, 2, usuario.email)
        ws.cell(fila, 3, usuario.telefono or "")
        ws.cell(fila, 4, usuario.rol)
        ws.cell(fila, 5, "Activo" if usuario.is_active else "Inactivo")

        fila += 1

    # Bordes
    borde = Border(
        left=Side(style="thin"),
        right=Side(style="thin"),
        top=Side(style="thin"),
        bottom=Side(style="thin"),
    )

    for row in ws.iter_rows(
        min_row=4,
        max_row=ws.max_row,
        min_col=1,
        max_col=5,
    ):
        for cell in row:
            cell.border = borde

    # Ancho de columnas
    columnas = {
        "A": 25,
        "B": 35,
        "C": 20,
        "D": 15,
        "E": 18,
    }

    for col, ancho in columnas.items():
        ws.column_dimensions[col].width = ancho

    ws.auto_filter.ref = f"A4:E{ws.max_row}"

    response = HttpResponse(
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

    response["Content-Disposition"] = 'attachment; filename="usuarios_lumina.xlsx"'

    wb.save(response)

    return response


# =========================
# GESTIÓN DE DIRECCIONES
# =========================

@login_required
def agregar_direccion(request):
    if request.method == "POST":
        form = DireccionForm(request.POST)

        if form.is_valid():
            direccion = form.save(commit=False)
            direccion.usuario = request.user

            if direccion.principal:
                Direccion.objects.filter(
                    usuario=request.user,
                    principal=True,
                ).update(principal=False)

            direccion.save()
            return redirect("mi_cuenta")

    return redirect("mi_cuenta")


@login_required
@require_POST
def eliminar_direccion(request, id):
    direccion = get_object_or_404(
        Direccion,
        id=id,
        usuario=request.user,
    )

    direccion.delete()
    return redirect("mi_cuenta")


# =========================
# BLOG
# =========================

@login_required
@admin_required
def blog(request):
    blogs_borrador = BlogPost.objects.filter(publicado=False)
    blogs_publicados = BlogPost.objects.filter(publicado=True)

    if request.method == "POST":
        blog_post = BlogPost.objects.create(
            titulo=request.POST.get("titulo"),
            resumen=request.POST.get("resumen"),
            portada=request.FILES.get("portada"),
            publicado=request.POST.get("publicado") == "True",
        )

        index = 0

        while True:
            subtitulo = request.POST.get(f"seccion-{index}-subtitulo")
            contenido = request.POST.get(f"seccion-{index}-contenido")
            imagen = request.FILES.get(f"seccion-{index}-imagen")

            if not subtitulo and not contenido and not imagen:
                break

            BlogSeccion.objects.create(
                blog=blog_post,
                subtitulo=subtitulo or "",
                contenido=contenido or "",
                imagen=imagen,
                orden=index,
            )

            index += 1

        return redirect("blog")

    return render(request, "core/blog.html", {
        "blogs_borrador": blogs_borrador,
        "blogs_publicados": blogs_publicados,
    })


def blog_modal(request, id):
    blog_post = get_object_or_404(BlogPost, id=id)
    secciones = blog_post.secciones.all().order_by("orden")

    return JsonResponse({
        "titulo": blog_post.titulo,
        "resumen": blog_post.resumen,
        "portada": blog_post.portada.url if blog_post.portada else "",
        "secciones": [
            {
                "subtitulo": seccion.subtitulo,
                "contenido": seccion.contenido,
                "imagen": seccion.imagen.url if seccion.imagen else "",
            }
            for seccion in secciones
        ],
    })


@login_required
@admin_required
def editar_blog(request, id):
    blog_post = get_object_or_404(BlogPost, id=id)

    blogs_borrador = BlogPost.objects.filter(publicado=False)
    blogs_publicados = BlogPost.objects.filter(publicado=True)
    secciones = blog_post.secciones.all().order_by("orden")

    if request.method == "POST":
        blog_post.titulo = request.POST.get("titulo")
        blog_post.resumen = request.POST.get("resumen")
        blog_post.publicado = request.POST.get("publicado") == "True"

        if request.FILES.get("portada"):
            blog_post.portada = request.FILES.get("portada")

        blog_post.save()

        existentes = {str(seccion.id): seccion for seccion in blog_post.secciones.all()}

        index = 0

        while True:
            seccion_id = request.POST.get(f"seccion-{index}-id")
            subtitulo = request.POST.get(f"seccion-{index}-subtitulo")
            contenido = request.POST.get(f"seccion-{index}-contenido")
            imagen = request.FILES.get(f"seccion-{index}-imagen")

            if not subtitulo and not contenido and not imagen and not seccion_id:
                break

            if seccion_id and seccion_id in existentes:
                seccion = existentes[seccion_id]
                seccion.subtitulo = subtitulo or seccion.subtitulo
                seccion.contenido = contenido or seccion.contenido

                if imagen:
                    seccion.imagen = imagen

                seccion.orden = index
                seccion.save()

            else:
                BlogSeccion.objects.create(
                    blog=blog_post,
                    subtitulo=subtitulo or "",
                    contenido=contenido or "",
                    imagen=imagen,
                    orden=index,
                )

            index += 1

        return redirect("blog")

    return render(request, "core/blog.html", {
        "blog_edit": blog_post,
        "blogs_borrador": blogs_borrador,
        "blogs_publicados": blogs_publicados,
        "secciones": secciones,
    })


@login_required
@admin_required
@require_POST
def publicar_blog(request, id):
    blog_post = get_object_or_404(BlogPost, id=id)
    blog_post.publicado = True
    blog_post.save()

    return redirect("blog")


@login_required
@admin_required
@require_POST
def eliminar_blog(request, id):
    blog_post = get_object_or_404(BlogPost, id=id)
    blog_post.delete()

    return redirect("blog")


# =========================
# GALERÍA
# =========================

@login_required
@admin_required
def galeria(request):
    galeria_items = Galeria.objects.all().order_by("-fecha_creacion")

    if request.method == "POST":
        Galeria.objects.create(
            titulo=request.POST.get("titulo"),
            categoria=request.POST.get("categoria"),
            descripcion=request.POST.get("descripcion"),
            tags=request.POST.get("tags", ""),
            imagen=request.FILES.get("imagen"),
        )

        messages.success(request, "Imagen agregada correctamente.")
        return redirect("galeria")

    return render(request, "core/galeria.html", {
        "galeria_items": galeria_items,
    })


@login_required
@admin_required
def editar_galeria(request, id):
    item = get_object_or_404(Galeria, id=id)
    galeria_items = Galeria.objects.all().order_by("-fecha_creacion")

    if request.method == "POST":
        item.titulo = request.POST.get("titulo")
        item.categoria = request.POST.get("categoria")
        item.descripcion = request.POST.get("descripcion")
        item.tags = request.POST.get("tags", "")

        if request.FILES.get("imagen"):
            item.imagen = request.FILES["imagen"]

        item.save()

        messages.success(request, "Imagen actualizada correctamente.")
        return redirect("galeria")

    return render(request, "core/galeria.html", {
        "galeria_edit": item,
        "galeria_items": galeria_items,
    })


@login_required
@admin_required
@require_POST
def eliminar_galeria(request, id):
    item = get_object_or_404(Galeria, id=id)
    item.delete()

    messages.success(request, "Imagen eliminada correctamente.")
    return redirect("galeria")


def galeria_modal(request, id):
    item = get_object_or_404(Galeria, id=id)

    return JsonResponse({
        "id": item.id,
        "titulo": item.titulo,
        "categoria": item.categoria,
        "descripcion": item.descripcion,
        "tags": item.tags,
        "imagen": item.imagen.url if item.imagen else "",
    })


# =========================
# TESTS
# =========================
@login_required
@admin_required
def test(request, test_id=None):

    editar = None

    if test_id:
        editar = get_object_or_404(Test, id=test_id)

    if request.method == "POST":

        with transaction.atomic():

            titulo = request.POST.get("titulo")
            categoria = request.POST.get("categoria")
            descripcion = request.POST.get("descripcion")

            # =====================
            # TEST
            # =====================

            if editar:

                editar.titulo = titulo
                editar.categoria = categoria
                editar.descripcion = descripcion

                if request.FILES.get("imagen"):
                    editar.imagen = request.FILES.get("imagen")

                editar.save()
                test_obj = editar

            else:

                test_obj = Test.objects.create(
                    titulo=titulo,
                    categoria=categoria,
                    descripcion=descripcion,
                    imagen=request.FILES.get("imagen")
                )

            # =====================
            # RESULTADOS
            # =====================

            nombres_resultado = request.POST.getlist("resultado_nombre[]")
            descripciones_resultado = request.POST.getlist("resultado_descripcion[]")
            resultado_ids = request.POST.getlist("resultado_id[]")

            resultados_guardados = []
            ids_resultados_enviados = []

            for i, nombre_resultado in enumerate(nombres_resultado):

                descripcion_resultado = (
                    descripciones_resultado[i]
                    if i < len(descripciones_resultado)
                    else ""
                )

                resultado_id = resultado_ids[i] if i < len(resultado_ids) else ""
                imagen_nueva = request.FILES.get(f"resultado_imagen_{i}")

                if editar and resultado_id:

                    resultado = Resultado.objects.get(
                        id=resultado_id,
                        test=test_obj
                    )

                    resultado.nombre = nombre_resultado
                    resultado.descripcion = descripcion_resultado

                    if imagen_nueva:
                        resultado.imagen = imagen_nueva

                    resultado.save()

                else:

                    resultado = Resultado.objects.create(
                        test=test_obj,
                        nombre=nombre_resultado,
                        descripcion=descripcion_resultado,
                        imagen=imagen_nueva
                    )

                resultados_guardados.append(resultado)
                ids_resultados_enviados.append(resultado.id)

            if editar:
                Resultado.objects.filter(test=test_obj).exclude(
                    id__in=ids_resultados_enviados
                ).delete()

            # =====================
            # PREGUNTAS Y OPCIONES
            # =====================

            if editar:
                test_obj.preguntas.all().delete()

            preguntas = request.POST.getlist("pregunta[]")

            for indice_pregunta, texto_pregunta in enumerate(preguntas, start=1):

                pregunta = Pregunta.objects.create(
                    test=test_obj,
                    texto=texto_pregunta
                )

                opciones = request.POST.getlist(f"opcion_{indice_pregunta}[]")
                resultados_opcion = request.POST.getlist(f"resultado_{indice_pregunta}[]")

                for j, texto_opcion in enumerate(opciones):

                    valor_resultado = (
                        resultados_opcion[j]
                        if j < len(resultados_opcion)
                        else ""
                    )

                    if not valor_resultado:
                        continue

                    try:
                        posicion = int(valor_resultado) - 1
                    except ValueError:
                        continue

                    if posicion < 0 or posicion >= len(resultados_guardados):
                        continue

                    resultado = resultados_guardados[posicion]

                    Opcion.objects.create(
                        pregunta=pregunta,
                        texto=texto_opcion,
                        resultado=resultado
                    )

            if editar:
                messages.success(request, "Test actualizado correctamente")
            else:
                messages.success(request, "Test guardado correctamente")

        return redirect("test")

    tests = Test.objects.all().order_by("-id")

    return render(
        request,
        "core/test.html",
        {
            "tests": tests,
            "editar": editar
        }
    )


def obtener_test(request, test_id):

    test = get_object_or_404(Test, id=test_id)

    if not test.activo:
        return JsonResponse({
            "ok": False,
            "inactivo": True,
            "mensaje": "Este test no está disponible. Estamos preparando una nueva versión para ti."
        }, status=403)

    preguntas = []

    for pregunta in test.preguntas.all():

        opciones = []

        for opcion in pregunta.opciones.all():

            opciones.append({
                "id": opcion.id,
                "texto": opcion.texto,
                "resultado": {
                    "id": opcion.resultado.id,
                    "nombre": opcion.resultado.nombre,
                    "descripcion": opcion.resultado.descripcion,
                    "imagen": opcion.resultado.imagen.url if opcion.resultado.imagen else ""
                }
            })

        preguntas.append({
            "id": pregunta.id,
            "texto": pregunta.texto,
            "opciones": opciones
        })

    return JsonResponse({
        "id": test.id,
        "titulo": test.titulo,
        "preguntas": preguntas
    })


@login_required
@admin_required
@require_POST
def eliminar_test(request, test_id):

    test = get_object_or_404(Test, id=test_id)

    test.delete()

    messages.success(request, "Test eliminado correctamente")

    return redirect("test")


@login_required
def guardar_resultado_usuario(request):
    if request.method != "POST":
        return JsonResponse({
            "ok": False,
            "error": "Método no permitido"
        }, status=405)

    test_id = request.POST.get("test_id")
    resultado_id = request.POST.get("resultado_id")

    if not test_id or not resultado_id:
        return JsonResponse({
            "ok": False,
            "error": "Faltan datos"
        }, status=400)

    try:
        test = Test.objects.get(id=test_id)
        resultado = Resultado.objects.get(id=resultado_id, test=test)
    except (Test.DoesNotExist, Resultado.DoesNotExist):
        return JsonResponse({
            "ok": False,
            "error": "Test o resultado no encontrado"
        }, status=404)

    resultado_usuario, creado = ResultadoUsuario.objects.update_or_create(
        usuario=request.user,
        test=test,
        defaults={
            "resultado": resultado
        }
    )

    return JsonResponse({
        "ok": True,
        "creado": creado,
        "resultado": {
            "id": resultado.id,
            "nombre": resultado.nombre,
            "descripcion": resultado.descripcion,
            "imagen": resultado.imagen.url if resultado.imagen else "",
            "fecha": resultado_usuario.actualizado.strftime("%d/%m/%Y")
        }
    })


@login_required
@admin_required
@require_POST
def activar_test(request, test_id):

    test = get_object_or_404(Test, id=test_id)

    test.activo = True
    test.save()

    messages.success(request, "Test activado correctamente.")

    return redirect("test")


@login_required
@admin_required
@require_POST
def desactivar_test(request, test_id):

    test = get_object_or_404(Test, id=test_id)

    test.activo = False
    test.save()

    messages.success(request, "Test desactivado correctamente.")

    return redirect("test")


@login_required
@require_POST
def eliminar_resultado_usuario(request, resultado_id):

    resultado = get_object_or_404(
        ResultadoUsuario,
        id=resultado_id,
        usuario=request.user
    )

    resultado.delete()

    messages.success(
        request,
        "Resultado eliminado correctamente."
    )

    return redirect("mi_cuenta")


# =========================
# PRODUCTOS
# =========================

@login_required
@admin_required
def dashboard_productos(request):

    producto_editar = None

    # =========================
    # DETECTAR EDICIÓN
    # =========================

    editar_id = request.GET.get("editar")

    if editar_id:

        producto_editar = Producto.objects.prefetch_related(
            "variantes",
            "imagenes",
            "videos",
            "etiquetas"
        ).get(id=editar_id)

    if request.method == "POST":

        producto_id = request.POST.get("producto_id")

        # =========================
        # DATOS PRODUCTO
        # =========================

        nombre = request.POST.get("nombre")
        descripcion = request.POST.get("descripcion")
        info_extra = request.POST.get("info_extra", "").strip()

        categoria_id = request.POST.get("categoria")
        marca_id = request.POST.get("marca")
        coleccion_id = request.POST.get("coleccion")

        costo_texto = request.POST.get("costo_base", "").strip()

        etiquetas_ids = request.POST.getlist("etiquetas[]")

        costo_base = normalizar_precio(costo_texto)

        if costo_base is None:

            messages.error(
                request,
                "Debes ingresar un costo válido."
            )

            return redirect("dashboard_productos")

        precio_base, margen_aplicado = calcular_precio_con_margen(costo_base)

        # =========================
        # SI EXISTE ID ACTUALIZA
        # =========================

        if producto_id:

            producto = Producto.objects.get(
                id=producto_id
            )

            producto.nombre = nombre
            producto.descripcion = descripcion
            producto.info_extra = info_extra
            producto.categoria_id = categoria_id
            producto.marca_id = marca_id
            producto.coleccion_id = coleccion_id or None
            producto.precio_base = precio_base

            if hasattr(producto, "costo_base"):
                producto.costo_base = costo_base

            producto.save()

            # Actualizar etiquetas

            producto.etiquetas.set(
                etiquetas_ids
            )

            # =========================
            # ELIMINAR IMÁGENES MARCADAS
            # =========================

            ids_imagenes_eliminar = request.POST.getlist(
                "eliminar_imagenes[]"
            )

            if ids_imagenes_eliminar:

                imagenes_a_borrar = producto.imagenes.filter(
                    id__in=ids_imagenes_eliminar
                )

                for imagen in imagenes_a_borrar:

                    # Borra el archivo físico del storage
                    imagen.imagen.delete(save=False)
                    imagen.delete()

            # =========================
            # ELIMINAR VIDEOS MARCADOS
            # =========================

            ids_videos_eliminar = request.POST.getlist(
                "eliminar_videos[]"
            )

            if ids_videos_eliminar:

                videos_a_borrar = producto.videos.filter(
                    id__in=ids_videos_eliminar
                )

                for video in videos_a_borrar:

                    video.video.delete(save=False)
                    video.delete()

            # =========================
            # AGREGAR NUEVAS IMAGENES
            # =========================

            for imagen in request.FILES.getlist(
                "imagenes"
            ):

                ProductoImagen.objects.create(
                    producto=producto,
                    imagen=imagen
                )

            # =========================
            # AGREGAR NUEVOS VIDEOS
            # =========================

            for video in request.FILES.getlist(
                "videos"
            ):

                ProductoVideo.objects.create(
                    producto=producto,
                    video=video
                )

            # =========================
            # ACTUALIZAR VARIANTES
            # =========================

            producto.variantes.all().delete()

        else:

            # =========================
            # CREAR SLUG
            # =========================

            slug = slugify(nombre)

            slug_original = slug

            contador = 1

            while Producto.objects.filter(
                slug=slug
            ).exists():

                slug = f"{slug_original}-{contador}"

                contador += 1

            # =========================
            # CREAR PRODUCTO
            # =========================
            producto = Producto.objects.create(

                nombre=nombre,

                slug=slug,

                descripcion=descripcion,

                info_extra=info_extra,

                categoria_id=categoria_id,

                marca_id=marca_id,

                coleccion_id=coleccion_id or None,

                precio_base=precio_base

            )

            if hasattr(producto, "costo_base"):
                producto.costo_base = costo_base
                producto.save(update_fields=["costo_base"])

            producto.etiquetas.set(
                etiquetas_ids
            )

            # =========================
            # GUARDAR IMÁGENES
            # =========================
            for imagen in request.FILES.getlist("imagenes"):

                ProductoImagen.objects.create(
                    producto=producto,
                    imagen=imagen
                )

            # =========================
            # GUARDAR VIDEOS
            # =========================
            for video in request.FILES.getlist("videos"):

                ProductoVideo.objects.create(
                    producto=producto,
                    video=video
                )

        # =========================
        # CREAR VARIANTES
        # =========================

        skus = request.POST.getlist(
            "sku[]"
        )

        nombres_tono = request.POST.getlist(
            "nombre_tono[]"
        )

        codigos_tono = request.POST.getlist(
            "codigo_tono[]"
        )

        stocks = request.POST.getlist(
            "stock[]"
        )

        for i in range(len(nombres_tono)):

            Variante.objects.create(

                producto=producto,

                sku=skus[i],

                nombre_tono=nombres_tono[i],

                codigo_tono=(

                    codigos_tono[i]

                    if i < len(codigos_tono)

                    else ""

                ),

                stock=int(

                    stocks[i]

                    if i < len(stocks)

                    else 0

                )

            )

        return redirect(
            "dashboard_productos"
        )

    # =========================
    # LISTAR PRODUCTOS (con búsqueda)
    # =========================

    query = request.GET.get("q", "").strip()

    productos_qs = Producto.objects.prefetch_related(

        "imagenes",

        "videos",

        "variantes",

        "etiquetas"

    ).select_related(

        "categoria",

        "marca",

        "coleccion"

    ).order_by(
        "-fecha_creacion"
    )

    if query:

        productos_qs = productos_qs.filter(
            Q(nombre__icontains=query) |
            Q(marca__nombre__icontains=query) |
            Q(categoria__nombre__icontains=query) |
            Q(coleccion__nombre__icontains=query) |
            Q(variantes__sku__icontains=query)
        ).distinct()

    # =========================
    # STOCK BAJO
    # =========================
    # Se calcula sobre productos_qs (respeta la búsqueda activa) y ANTES
    # de paginar, para que el contador refleje el total real, no solo
    # lo que se ve en la página actual.

    variantes_stock_bajo_qs = Variante.objects.filter(
        producto__in=productos_qs,
        stock__lte=UMBRAL_STOCK_BAJO
    )

    productos_stock_bajo_ids = set(
        variantes_stock_bajo_qs.values_list("producto_id", flat=True)
    )

    total_stock_bajo_productos = len(productos_stock_bajo_ids)

    # =========================
    # PAGINACIÓN
    # =========================

    paginator = Paginator(productos_qs, 10)

    numero_pagina = request.GET.get("page")

    productos = paginator.get_page(numero_pagina)

    for producto in productos:

        costo_referencia = getattr(
            producto,
            "costo_base",
            producto.precio_base
        )

        producto.costo_referencia = costo_referencia
        producto.precios_rentabilidad = calcular_precios_por_margen(costo_referencia)

    contexto = {

        "productos": productos,

        "query": query,

        "producto_editar": producto_editar,

        "categorias": Categoria.objects.all(),

        "marcas": Marca.objects.filter(
            activa=True
        ),

        "colecciones": Coleccion.objects.filter(
            activa=True
        ),

        "etiquetas": Etiqueta.objects.all(),

        # Stock bajo
        "total_stock_bajo_productos": total_stock_bajo_productos,
        "productos_stock_bajo_ids": productos_stock_bajo_ids,
        "umbral_stock_bajo": UMBRAL_STOCK_BAJO,

    }

    return render(

        request,

        "core/productos.html",

        contexto

    )


@login_required
@admin_required
def editar_producto(request, producto_id):
    producto = get_object_or_404(Producto, id=producto_id)
    if request.method == 'POST':
        # actualizar campos según tu formulario
        producto.nombre = request.POST.get('nombre', producto.nombre)
        producto.descripcion = request.POST.get('descripcion', producto.descripcion)
        # ... resto de campos ...
        producto.save()
        messages.success(request, 'Producto actualizado correctamente.')
        return redirect('dashboard_productos')
    return render(request, 'core/editar_producto.html', {'producto': producto})


@login_required
@admin_required
@require_POST
def eliminar_producto(request, producto_id):
    producto = get_object_or_404(Producto, id=producto_id)
    producto.delete()
    messages.success(request, 'Producto eliminado correctamente.')
    return redirect('dashboard_productos')


# =========================
# CATÁLOGO (MARCAS / CATEGORIAS / COLECCIONES / ETIQUETAS)
# =========================

@login_required
@admin_required
def dashboard_catalogo(request):

    if request.method == "POST":

        tipo = request.POST.get("tipo")
        registro_id = request.POST.get("id")
        nombre = request.POST.get("nombre")

        # ==========================
        # CATEGORIAS
        # ==========================

        if tipo == "categoria":

            if registro_id:

                categoria = Categoria.objects.get(
                    id=registro_id
                )

                categoria.nombre = nombre
                categoria.save()

                messages.success(
                    request,
                    "Categoría actualizada correctamente."
                )

            else:

                Categoria.objects.create(
                    nombre=nombre
                )

                messages.success(
                    request,
                    "Categoría creada correctamente."
                )

        # ==========================
        # MARCAS
        # ==========================

        elif tipo == "marca":

            if registro_id:

                marca = Marca.objects.get(
                    id=registro_id
                )

                marca.nombre = nombre
                marca.save()

                messages.success(
                    request,
                    "Marca actualizada correctamente."
                )

            else:

                Marca.objects.create(
                    nombre=nombre
                )

                messages.success(
                    request,
                    "Marca creada correctamente."
                )

        # ==========================
        # COLECCIONES
        # ==========================

        elif tipo == "coleccion":

            marca_id = request.POST.get("marca")

            if registro_id:

                coleccion = Coleccion.objects.get(
                    id=registro_id
                )

                coleccion.nombre = nombre
                coleccion.marca_id = marca_id
                coleccion.save()

                messages.success(
                    request,
                    "Colección actualizada correctamente."
                )

            else:

                Coleccion.objects.create(
                    nombre=nombre,
                    marca_id=marca_id
                )

                messages.success(
                    request,
                    "Colección creada correctamente."
                )

        # ==========================
        # ETIQUETAS
        # ==========================

        elif tipo == "etiqueta":

            if registro_id:

                etiqueta = Etiqueta.objects.get(
                    id=registro_id
                )

                etiqueta.nombre = nombre
                etiqueta.save()

                messages.success(
                    request,
                    "Etiqueta actualizada correctamente."
                )

            else:

                Etiqueta.objects.create(
                    nombre=nombre
                )

                messages.success(
                    request,
                    "Etiqueta creada correctamente."
                )

        return redirect(
            "dashboard_catalogo"
        )

    # ======================================
    # CONSULTAS
    # ======================================

    categorias_lista = Categoria.objects.order_by(
        "nombre"
    )

    marcas_lista = Marca.objects.order_by(
        "nombre"
    )

    colecciones_lista = (
        Coleccion.objects
        .select_related("marca")
        .order_by(
            "marca__nombre",
            "nombre"
        )
    )

    etiquetas_lista = Etiqueta.objects.order_by(
        "nombre"
    )

    # ======================================
    # PAGINADORES
    # ======================================

    categorias_paginator = Paginator(
        categorias_lista,
        10
    )

    marcas_paginator = Paginator(
        marcas_lista,
        10
    )

    colecciones_paginator = Paginator(
        colecciones_lista,
        10
    )

    etiquetas_paginator = Paginator(
        etiquetas_lista,
        10
    )

    categorias_page = request.GET.get(
        "categorias_page"
    )

    marcas_page = request.GET.get(
        "marcas_page"
    )

    colecciones_page = request.GET.get(
        "colecciones_page"
    )

    etiquetas_page = request.GET.get(
        "etiquetas_page"
    )

    contexto = {

        "categorias": categorias_paginator.get_page(
            categorias_page
        ),

        "marcas": marcas_paginator.get_page(
            marcas_page
        ),

        "colecciones": colecciones_paginator.get_page(
            colecciones_page
        ),

        "etiquetas": etiquetas_paginator.get_page(
            etiquetas_page
        ),

    }

    return render(
        request,
        "core/variantes.html",
        contexto
    )


def obtener_colecciones(request):

    marca_id = request.GET.get("marca")

    colecciones = Coleccion.objects.filter(
        marca_id=marca_id,
        activa=True
    ).values(
        "id",
        "nombre"
    )

    return JsonResponse(
        list(colecciones),
        safe=False
    )


@login_required
@admin_required
@require_POST
def eliminar_categoria(request, id):

    Categoria.objects.filter(id=id).delete()

    messages.success(
        request,
        "Categoría eliminada correctamente."
    )

    return redirect("dashboard_catalogo")


@login_required
@admin_required
@require_POST
def eliminar_marca(request, id):

    Marca.objects.filter(id=id).delete()

    messages.success(
        request,
        "Marca eliminada correctamente."
    )

    return redirect("dashboard_catalogo")


@login_required
@admin_required
@require_POST
def eliminar_coleccion(request, id):

    Coleccion.objects.filter(id=id).delete()

    messages.success(
        request,
        "Colección eliminada correctamente."
    )

    return redirect("dashboard_catalogo")


@login_required
@admin_required
@require_POST
def eliminar_etiqueta(request, etiqueta_id):

    etiqueta = get_object_or_404(
        Etiqueta,
        id=etiqueta_id
    )

    etiqueta.delete()

    return redirect(
        "dashboard_catalogo"
    )


# =========================
# CONTACTO (ADMIN)
# =========================

@login_required
@admin_required
def responder_contacto(request, id):

    contacto = get_object_or_404(
        Contacto,
        id=id
    )

    respuesta = request.POST["respuesta"]

    resultado = enviar_correo(
        contacto.correo,
        contacto.asunto,
        respuesta
    )

    respuesta_limpia = respuesta.split("El ")[0].strip()

    contacto.respuesta = respuesta_limpia

    contacto.gmail_message_id = resultado["message_id"]

    contacto.gmail_thread_id = resultado["thread_id"]

    contacto.respondido = True

    contacto.fecha_respuesta = timezone.now()

    contacto.save()

    return redirect(
        "dashboard_contacto"
    )


@login_required
@admin_required
def dashboard_contacto(request):

    # Filtro principal (botones Bandeja / Archivados)
    vista = request.GET.get("vista", "entrada")

    # Filtros secundarios si existen
    filtro = request.GET.get("estado", "")

    mensajes = Contacto.objects.all()

    # ================================
    # VISTA ARCHIVADOS
    # ================================

    if vista == "archivados":

        mensajes = mensajes.filter(
            archivado=True
        )

    # ================================
    # VISTA BANDEJA
    # ================================

    else:

        mensajes = mensajes.filter(
            archivado=False
        )

        # ================================
        # FILTROS DE ESTADO
        # ================================

        if filtro == "nuevo":

            mensajes = mensajes.filter(
                leido=False
            )

        elif filtro == "leido":

            mensajes = mensajes.filter(
                leido=True,
                respondido=False
            )

        elif filtro == "respondido":

            mensajes = mensajes.filter(
                respondido=True
            )

        elif filtro == "cliente":

            mensajes = mensajes.exclude(
                respuesta_cliente=""
            )

        elif filtro == "pendiente":

            mensajes = mensajes.filter(
                respondido=False
            )

    mensajes = mensajes.order_by("-fecha")

    contexto = {

        "mensajes": mensajes,

        "vista": vista,

        "filtro": filtro,

        # ================================
        # ESTADÍSTICAS
        # ================================

        "total": Contacto.objects.filter(
            archivado=False
        ).count(),

        "sin_leer": Contacto.objects.filter(
            leido=False,
            archivado=False
        ).count(),

        "respondidos": Contacto.objects.filter(
            respondido=True,
            archivado=False
        ).count(),

        "cliente_respondio": Contacto.objects.exclude(
            respuesta_cliente=""
        ).filter(
            archivado=False
        ).count(),

        "pendientes": Contacto.objects.filter(
            respondido=False,
            archivado=False
        ).count(),

        "archivados": Contacto.objects.filter(
            archivado=True
        ).count(),

    }

    return render(
        request,
        "core/contacto_d.html",
        contexto
    )


@login_required
@admin_required
def sincronizar_respuestas_gmail(request):

    contactos = Contacto.objects.exclude(
        gmail_thread_id=None
    )

    for contacto in contactos:

        hilo = obtener_hilo(
            contacto.gmail_thread_id
        )

        mensajes = hilo.get(
            "messages",
            []
        )

        if not mensajes:
            continue

        # Recorrer desde el más reciente
        for mensaje in reversed(mensajes):

            remitente = obtener_encabezado(
                mensaje,
                "From"
            )

            # Solo correos enviados por el cliente
            if contacto.correo.lower() not in remitente.lower():
                continue

            texto = obtener_texto(
                mensaje
            )

            if not texto:
                continue

            # Evitar guardar la misma respuesta
            if texto == contacto.respuesta_cliente:
                break

            contacto.respuesta_cliente = texto
            contacto.fecha_cliente = timezone.now()
            contacto.respuesta_cliente_leida = False
            contacto.leido = True
            contacto.save()

            break

    messages.success(
        request,
        "Respuestas sincronizadas correctamente."
    )

    return redirect("dashboard_contacto")


@login_required
@admin_required
def archivar_contacto(request, id):

    contacto = get_object_or_404(Contacto, id=id)

    contacto.archivado = True
    contacto.save()

    messages.success(request, "La conversación fue archivada.")

    return redirect("dashboard_contacto")


@login_required
@admin_required
def restaurar_contacto(request, id):

    contacto = get_object_or_404(Contacto, id=id)

    contacto.archivado = False
    contacto.save()

    messages.success(request, "La conversación fue restaurada.")

    return redirect("dashboard_contacto")


@login_required
@admin_required
@require_POST
def eliminar_mensaje(request, id):

    mensaje = get_object_or_404(
        Contacto,
        id=id
    )

    mensaje.delete()

    messages.success(
        request,
        "Conversación eliminada correctamente."
    )

    return redirect("dashboard_contacto")


@login_required
@admin_required
def marcar_leido(request, id):

    contacto = get_object_or_404(
        Contacto,
        id=id
    )

    contacto.leido = True

    if contacto.respuesta_cliente:
        contacto.respuesta_cliente_leida = True

    contacto.save()

    return JsonResponse({
        "ok": True
    })


# =========================
# DASHBOARD ADMIN
# =========================

FRASES_DIA = [

    "✨ Crea, inspira y transforma tu pasión en un negocio.",

    "🌸 Cada pequeño paso construye grandes resultados.",

    "💄 Tu creatividad es la esencia de tu marca.",

    "🚀 Los grandes proyectos empiezan con una pequeña idea.",

    "🌱 Aprende, mejora y sigue creciendo cada día.",

    "💡 Las ideas se convierten en realidad cuando actúas.",

    "✨ Hazlo con amor, hazlo con propósito.",

    "🌷 La constancia supera al talento cuando el talento no se esfuerza.",

    "🔥 Tu esfuerzo de hoy será tu éxito de mañana.",

    "🌈 Confía en tu proceso y disfruta el camino."

]


@login_required
@admin_required
def admin_dashboard(request):

    usuario = request.user

    # =========================
    # CREACIONES
    # =========================

    if request.method == "POST":

        accion = request.POST.get("accion")

        if accion == "crear_nota":

            NotaAdmin.objects.create(
                usuario=usuario,
                texto=request.POST.get("texto")
            )

        elif accion == "crear_postit":

            PostIt.objects.create(
                usuario=usuario,
                contenido=request.POST.get("contenido"),
                color=request.POST.get(
                    "color",
                    "rosa"
                )
            )

        elif accion == "crear_recordatorio":

            Recordatorio.objects.create(
                usuario=usuario,
                titulo=request.POST.get("titulo"),
                fecha=request.POST.get("fecha"),
                prioridad=request.POST.get(
                    "prioridad",
                    "media"
                )
            )

        elif accion == "crear_evento":

            EventoCalendario.objects.create(
                usuario=usuario,
                titulo=request.POST.get("titulo"),
                descripcion=request.POST.get("descripcion"),
                fecha=request.POST.get("fecha"),
                hora=request.POST.get("hora") or None,
                tipo=request.POST.get("tipo")
            )

        elif accion == "crear_idea":

            IdeaContenido.objects.create(
                usuario=usuario,
                titulo=request.POST.get("titulo"),
                descripcion=request.POST.get("descripcion"),
                categoria=request.POST.get("categoria")
            )

        return redirect(
            "admin_dashboard"
        )

    # =========================
    # CONSULTAS
    # =========================

    notas = NotaAdmin.objects.filter(
        usuario=usuario
    ).order_by("-fecha_creacion")

    postits = PostIt.objects.filter(
        usuario=usuario
    ).order_by("-fecha_creacion")

    recordatorios = Recordatorio.objects.filter(
        usuario=usuario
    ).order_by("fecha")

    eventos = EventoCalendario.objects.filter(
        usuario=usuario
    ).order_by("fecha")

    ideas = IdeaContenido.objects.filter(
        usuario=usuario
    ).order_by("-creada")

    # =========================
    # CALENDARIO EVENTOS + RECORDATORIOS
    # =========================

    calendario_items = []

    # EVENTOS

    for evento in eventos:

        calendario_items.append({

            "id": f"evento-{evento.id}",

            "title": "📅 " + evento.titulo,

            "start": str(evento.fecha),

            "color": evento.color,

            "tipo": "evento"

        })

    # RECORDATORIOS

    colores = {

        "alta": "#ef4444",

        "media": "#f59e0b",

        "baja": "#22c55e"

    }

    for recordatorio in recordatorios:

        calendario_items.append({

            "id": f"recordatorio-{recordatorio.id}",

            "title": "⏰ " + recordatorio.titulo,

            "start": str(recordatorio.fecha),

            "color": colores.get(
                recordatorio.prioridad,
                "#df6d86"
            ),

            "tipo": "recordatorio"

        })

    eventos_json = json.dumps(
        calendario_items
    )

    # =========================
    # CONTEXTO
    # =========================

    contexto = {

        "frase_dia":
            FRASES_DIA[
                date.today().toordinal() % len(FRASES_DIA)
            ],

        "notas":
        notas,

        "postits":
        postits,

        "recordatorios":
        recordatorios,

        "eventos":
        eventos,

        "ideas":
        ideas[:6],

        "eventos_json":
        eventos_json,

        "total_notas":
        notas.count(),

        "total_ideas":
        ideas.count(),

        "total_eventos":
        eventos.count(),

        "total_recordatorios":
        recordatorios.count(),

        "recordatorios_pendientes":
        recordatorios.filter(
            completado=False
        ).count(),

        "ideas_publicadas":
        ideas.filter(
            estado="publicada"
        ).count(),

    }

    return render(

        request,

        "core/inicio_dashboard.html",

        contexto

    )


# =========================
# NOTAS
# =========================

@login_required
@require_POST
def eliminar_nota(request, id):

    nota = get_object_or_404(
        NotaAdmin,
        id=id,
        usuario=request.user
    )

    nota.delete()

    return redirect(
        "admin_dashboard"
    )


@login_required
def toggle_nota(request, id):

    nota = get_object_or_404(
        NotaAdmin,
        id=id,
        usuario=request.user
    )

    nota.completada = not nota.completada

    nota.save()

    return redirect(
        "admin_dashboard"
    )


@login_required
def editar_nota(request, id):

    nota = get_object_or_404(
        NotaAdmin,
        id=id,
        usuario=request.user
    )

    if request.method == "POST":

        nota.texto = request.POST.get(
            "texto"
        )

        nota.save()

        return redirect(
            "admin_dashboard"
        )

    return redirect(
        "admin_dashboard"
    )


# =========================
# POST ITS
# =========================

@login_required
@require_POST
def eliminar_postit(request, id):

    postit = get_object_or_404(
        PostIt,
        id=id,
        usuario=request.user
    )

    postit.delete()

    return redirect(
        "admin_dashboard"
    )


@login_required
def editar_postit(request, id):

    postit = get_object_or_404(
        PostIt,
        id=id,
        usuario=request.user
    )

    if request.method == "POST":

        postit.contenido = request.POST.get(
            "contenido"
        )

        postit.color = request.POST.get(
            "color",
            postit.color
        )

        postit.save()

        return redirect(
            "admin_dashboard"
        )

    return redirect(
        "admin_dashboard"
    )


# =========================
# IDEAS DE CONTENIDO
# =========================

@login_required
@require_POST
def eliminar_idea(request, id):

    idea = get_object_or_404(
        IdeaContenido,
        id=id,
        usuario=request.user
    )

    idea.delete()

    return redirect(
        "admin_dashboard"
    )


@login_required
def editar_idea(request, id):

    idea = get_object_or_404(
        IdeaContenido,
        id=id,
        usuario=request.user
    )

    if request.method == "POST":

        idea.titulo = request.POST.get(
            "titulo"
        )

        idea.descripcion = request.POST.get(
            "descripcion"
        )

        idea.categoria = request.POST.get(
            "categoria"
        )

        idea.save()

        return redirect(
            "admin_dashboard"
        )

    return redirect(
        "admin_dashboard"
    )


@login_required
def cambiar_estado_idea(request, id):

    idea = get_object_or_404(
        IdeaContenido,
        id=id,
        usuario=request.user
    )

    estado_actual = idea.estado

    estados = [
        "pendiente",
        "proceso",
        "publicada"
    ]

    posicion = estados.index(
        estado_actual
    )

    siguiente = (
        posicion + 1
    ) % len(estados)

    idea.estado = estados[siguiente]

    idea.save()

    return redirect(
        "admin_dashboard"
    )


# =========================
# EVENTOS CALENDARIO
# =========================

@login_required
@require_POST
def eliminar_evento(request, id):

    evento = get_object_or_404(
        EventoCalendario,
        id=id,
        usuario=request.user
    )

    evento.delete()

    return redirect(
        "admin_dashboard"
    )


@login_required
def editar_evento(request, id):

    evento = get_object_or_404(
        EventoCalendario,
        id=id,
        usuario=request.user
    )

    if request.method == "POST":

        evento.titulo = request.POST.get(
            "titulo"
        )

        evento.descripcion = request.POST.get(
            "descripcion"
        )

        evento.fecha = request.POST.get(
            "fecha"
        )

        evento.hora = request.POST.get(
            "hora"
        ) or None

        evento.tipo = request.POST.get(
            "tipo"
        )

        evento.save()

        return redirect(
            "admin_dashboard"
        )

    return redirect(
        "admin_dashboard"
    )


# =========================
# RECORDATORIOS
# =========================

@login_required
@require_POST
def eliminar_recordatorio(request, id):

    recordatorio = get_object_or_404(
        Recordatorio,
        id=id,
        usuario=request.user
    )

    recordatorio.delete()

    return redirect(
        "admin_dashboard"
    )


@login_required
def toggle_recordatorio(request, id):

    recordatorio = get_object_or_404(
        Recordatorio,
        id=id,
        usuario=request.user
    )

    recordatorio.completado = not recordatorio.completado

    recordatorio.save()

    return redirect(
        "admin_dashboard"
    )


@login_required
def editar_recordatorio(request, id):

    recordatorio = get_object_or_404(
        Recordatorio,
        id=id,
        usuario=request.user
    )

    if request.method == "POST":

        recordatorio.titulo = request.POST.get(
            "titulo"
        )

        recordatorio.fecha = request.POST.get(
            "fecha"
        )

        recordatorio.prioridad = request.POST.get(
            "prioridad"
        )

        recordatorio.save()

        return redirect(
            "admin_dashboard"
        )

    return redirect(
        "admin_dashboard"
    )


# =========================
# ESTADÍSTICAS
# =========================

@login_required
@admin_required
def estadisticas(request):

    # =====================================
    # KPIS GENERALES
    # =====================================

    total_usuarios = Usuario.objects.count()
    usuarios_activos = Usuario.objects.filter(estado="activo").count()

    total_productos = Producto.objects.count()
    total_categorias = Categoria.objects.count()
    total_marcas = Marca.objects.count()

    total_pedidos = Pedido.objects.count()
    total_blogs = BlogPost.objects.count()
    total_galeria = Galeria.objects.count()

    total_tests = Test.objects.count()
    total_contactos = Contacto.objects.count()
    resultados_tests = ResultadoUsuario.objects.count()

    # =====================================
    # KITS
    # =====================================

    kits_qs = Kit.objects.select_related("categoria").prefetch_related(
        "items__producto"
    )

    total_kits = kits_qs.count()
    kits_activos = kits_qs.filter(activo=True).count()
    kits_destacados = kits_qs.filter(destacado=True).count()
    stock_kits = kits_qs.aggregate(total=Sum("stock"))["total"] or 0

    kits_list = list(kits_qs)

    if kits_list:
        ahorro_promedio = sum(k.ahorro for k in kits_list) / len(kits_list)
    else:
        ahorro_promedio = 0

    top_kits_ahorro = sorted(
        kits_list, key=lambda k: k.ahorro, reverse=True
    )[:5]

    kits_labels = [k.nombre for k in top_kits_ahorro]
    kits_data = [float(k.ahorro) for k in top_kits_ahorro]

    kits_recientes = kits_qs.order_by("-fecha_creacion")[:6]

    # =====================================
    # ALERTAS DE STOCK BAJO
    # =====================================

    variantes_stock_bajo_qs = Variante.objects.filter(
        stock__lte=UMBRAL_STOCK_BAJO
    ).select_related("producto").order_by("stock")

    productos_stock_bajo_count = variantes_stock_bajo_qs.values("producto").distinct().count()
    variantes_stock_bajo = variantes_stock_bajo_qs[:8]

    kits_stock_bajo_qs = kits_qs.filter(stock__lte=UMBRAL_STOCK_BAJO).order_by("stock")
    kits_stock_bajo_count = kits_stock_bajo_qs.count()
    kits_stock_bajo = kits_stock_bajo_qs[:8]

    alertas_stock_total = productos_stock_bajo_count + kits_stock_bajo_count

    # =====================================
    # VENTAS
    # =====================================

    ventas = Pedido.objects.filter(
        estado__in=["PAGADO"]
    ).aggregate(
        total=Sum("total")
    )["total"] or 0

    # =====================================
    # PEDIDOS POR ESTADO
    # =====================================

    pedidos_estado = Pedido.objects.values("estado").annotate(
        cantidad=Count("id")
    )

    estados_labels = []
    estados_data = []

    for estado in pedidos_estado:
        estados_labels.append(estado["estado"].capitalize())
        estados_data.append(estado["cantidad"])

    pedidos_pagados = Pedido.objects.filter(estado="PAGADO").count()
    pedidos_pendientes = Pedido.objects.filter(estado="PENDIENTE").count()

    # =====================================
    # PRODUCTOS POR CATEGORIA
    # =====================================

    categorias = Categoria.objects.annotate(
        cantidad=Count("producto")
    )

    categorias_labels = []
    categorias_data = []

    for categoria in categorias:
        categorias_labels.append(categoria.nombre)
        categorias_data.append(categoria.cantidad)

    # =====================================
    # USUARIOS POR MES
    # =====================================

    meses = []
    usuarios_mes = []

    for i in range(5, -1, -1):
        fecha = timezone.now() - timedelta(days=30 * i)
        inicio = fecha.replace(day=1)

        if inicio.month == 12:
            fin = inicio.replace(year=inicio.year + 1, month=1)
        else:
            fin = inicio.replace(month=inicio.month + 1)

        cantidad = Usuario.objects.filter(
            date_joined__gte=inicio,
            date_joined__lt=fin
        ).count()

        meses.append(inicio.strftime("%b"))
        usuarios_mes.append(cantidad)

    # =====================================
    # TESTS MÁS REALIZADOS
    # =====================================

    top_tests = ResultadoUsuario.objects.values(
        "test__titulo"
    ).annotate(
        total=Count("id")
    ).order_by("-total")[:5]

    tests_labels = [t["test__titulo"] for t in top_tests]
    tests_data = [t["total"] for t in top_tests]

    # =====================================
    # CONTACTOS
    # =====================================

    contactos_respondidos = Contacto.objects.filter(respondido=True).count()
    contactos_pendientes = Contacto.objects.filter(respondido=False).count()

    # =====================================
    # PRODUCTOS MÁS VENDIDOS
    # =====================================

    top_productos = PedidoItem.objects.values(
        "producto_nombre"
    ).annotate(
        vendidos=Sum("cantidad")
    ).order_by("-vendidos")[:5]

    productos_labels = [p["producto_nombre"] for p in top_productos]
    productos_data = [p["vendidos"] or 0 for p in top_productos]

    # =====================================
    # USUARIOS RECIENTES
    # =====================================

    usuarios_recientes = Usuario.objects.order_by("-date_joined")[:10]

    # =====================================
    # CONTEXTO
    # =====================================

    context = {

        "total_usuarios": total_usuarios,
        "usuarios_activos": usuarios_activos,

        "total_productos": total_productos,
        "total_categorias": total_categorias,
        "total_marcas": total_marcas,

        "total_pedidos": total_pedidos,
        "total_blogs": total_blogs,
        "total_galeria": total_galeria,

        "total_tests": total_tests,
        "resultados_tests": resultados_tests,

        "total_contactos": total_contactos,

        "ventas": ventas,

        # Kits (catálogo)
        "total_kits": total_kits,
        "kits_activos": kits_activos,
        "kits_destacados": kits_destacados,
        "stock_kits": stock_kits,
        "ahorro_promedio": round(ahorro_promedio, 0),
        "kits_recientes": kits_recientes,
        "kits_labels": json.dumps(kits_labels),
        "kits_data": json.dumps(kits_data),

        # Alertas de stock bajo
        "productos_stock_bajo_count": productos_stock_bajo_count,
        "variantes_stock_bajo": variantes_stock_bajo,
        "kits_stock_bajo_count": kits_stock_bajo_count,
        "kits_stock_bajo": kits_stock_bajo,
        "alertas_stock_total": alertas_stock_total,
        "umbral_stock_bajo": UMBRAL_STOCK_BAJO,

        # Pedidos por estado
        "pedidos_pagados": pedidos_pagados,
        "pedidos_pendientes": pedidos_pendientes,

        # Usuarios recientes
        "usuarios_recientes": usuarios_recientes,

        # Usuarios por mes
        "meses": json.dumps(meses),
        "usuarios_mes": json.dumps(usuarios_mes),

        # Categorías
        "categorias_labels": json.dumps(categorias_labels),
        "categorias_data": json.dumps(categorias_data),

        # Pedidos estado
        "estados_labels": json.dumps(estados_labels),
        "estados_data": json.dumps(estados_data),

        # Tests
        "tests_labels": json.dumps(tests_labels),
        "tests_data": json.dumps(tests_data),

        # Productos vendidos
        "productos_labels": json.dumps(productos_labels),
        "productos_data": json.dumps(productos_data),

        # Contactos
        "contactos_respondidos": contactos_respondidos,
        "contactos_pendientes": contactos_pendientes,
    }

    return render(request, "core/estadisticas.html", context)


# =========================
# KITS
# =========================

@login_required
@admin_required
def dashboard_kits(request):

    kit_editar = None

    editar_id = request.GET.get("editar")

    if editar_id:
        kit_editar = get_object_or_404(
            Kit,
            id=editar_id
        )

    if request.method == "POST":

        kit_id = request.POST.get("kit_id")

        nombre = request.POST.get("nombre")

        descripcion = request.POST.get("descripcion")

        categoria_id = request.POST.get("categoria")

        sku = (
            request.POST.get("sku") or ""
        ).strip()

        stock = (
            request.POST.get("stock") or ""
        ).strip()

        descuento = normalizar_precio(
            request.POST.get(
                "descuento_personalizado"
            )
        ) or 0

        if descuento < 0:
            descuento = 0

        if descuento > 100:
            descuento = 100

        activo = (
            request.POST.get("activo") == "on"
        )

        destacado = (
            request.POST.get("destacado") == "on"
        )

        # =====================================================
        # RECOMENDACIONES DEL TEST
        # =====================================================

        recomendar_test = (
            request.POST.get("recomendar_test") == "on"
        )

        inversion_minima = normalizar_precio(
            request.POST.get("inversion_minima")
        ) or 0

        inversion_maxima = normalizar_precio(
            request.POST.get("inversion_maxima")
        ) or 0

        nivel_recomendado = (
            request.POST.get(
                "nivel_recomendado"
            ) or ""
        ).strip()

        plataforma_recomendada = (
            request.POST.get(
                "plataforma_recomendada"
            ) or ""
        ).strip()

        tipo_negocio = (
            request.POST.get(
                "tipo_negocio"
            ) or ""
        ).strip()

        recomendacion_texto = (
            request.POST.get(
                "recomendacion_texto"
            ) or ""
        ).strip()

        # =====================================================
        # VALIDAR INVERSIÓN
        # =====================================================

        if inversion_maxima < inversion_minima:

            messages.error(
                request,
                "La inversión máxima no puede ser menor que la inversión mínima."
            )

            return redirect(
                request.META.get(
                    "HTTP_REFERER",
                    "dashboard_kits"
                )
            )

        # =====================================================
        # EDITAR KIT
        # =====================================================

        if kit_id:

            kit = get_object_or_404(
                Kit,
                id=kit_id
            )

            kit.nombre = nombre

            kit.descripcion = descripcion

            kit.categoria_id = (
                categoria_id
                or None
            )

            kit.sku = (
                sku
                or None
            )

            kit.stock = (
                int(stock)
                if stock
                else 0
            )

            kit.activo = activo

            kit.destacado = destacado

            kit.descuento_personalizado = (
                descuento
            )

            # =================================================
            # RECOMENDACIONES
            # =================================================

            kit.recomendar_test = (
                recomendar_test
            )

            kit.inversion_minima = (
                inversion_minima
            )

            kit.inversion_maxima = (
                inversion_maxima
            )

            kit.nivel_recomendado = (
                nivel_recomendado
            )

            kit.plataforma_recomendada = (
                plataforma_recomendada
            )

            kit.tipo_negocio = (
                tipo_negocio
            )

            kit.recomendacion_texto = (
                recomendacion_texto
            )

            # =================================================
            # IMAGEN
            # =================================================

            if request.FILES.get("imagen"):

                kit.imagen = request.FILES[
                    "imagen"
                ]

            kit.save()

            messages.success(
                request,
                "Kit actualizado correctamente."
            )

            return redirect(
                "dashboard_kits"
            )

        # =====================================================
        # CREAR KIT
        # =====================================================

        else:

            slug = slugify(nombre)

            slug_original = slug

            contador = 1

            while Kit.objects.filter(
                slug=slug
            ).exists():

                slug = (
                    f"{slug_original}-{contador}"
                )

                contador += 1

            Kit.objects.create(

                nombre=nombre,

                slug=slug,

                descripcion=descripcion,

                categoria_id=(
                    categoria_id
                    or None
                ),

                sku=(
                    sku
                    or None
                ),

                stock=(
                    int(stock)
                    if stock
                    else 0
                ),

                descuento_personalizado=(
                    descuento
                ),

                activo=activo,

                destacado=destacado,

                imagen=request.FILES.get(
                    "imagen"
                ),

                # =============================================
                # RECOMENDACIONES
                # =============================================

                recomendar_test=(
                    recomendar_test
                ),

                inversion_minima=(
                    inversion_minima
                ),

                inversion_maxima=(
                    inversion_maxima
                ),

                nivel_recomendado=(
                    nivel_recomendado
                ),

                plataforma_recomendada=(
                    plataforma_recomendada
                ),

                tipo_negocio=(
                    tipo_negocio
                ),

                recomendacion_texto=(
                    recomendacion_texto
                ),
            )

            messages.success(
                request,
                "Kit creado correctamente."
            )

        return redirect(
            "dashboard_kits"
        )

    # =====================================================
    # LISTADO DE KITS
    # =====================================================

    kits = (
        Kit.objects
        .prefetch_related(
            "items__producto",
            "items__variante"
        )
        .order_by(
            "-fecha_creacion"
        )
    )

    # =====================================================
    # ALERTAS DE STOCK BAJO
    # =====================================================

    kits_stock_bajo = kits.filter(
        stock__lte=UMBRAL_STOCK_BAJO
    ).count()

    # =====================================================
    # CONTEXTO
    # =====================================================

    contexto = {

        "kits": kits,

        "kit_editar": kit_editar,

        "categorias": Categoria.objects.all(),

        "productos": (
            Producto.objects
            .filter(activo=True)
            .prefetch_related(
                "imagenes",
                "variantes"
            )
        ),

        # Alertas
        "kits_stock_bajo": kits_stock_bajo,

        "umbral_stock_bajo": UMBRAL_STOCK_BAJO,

    }

    return render(
        request,
        "core/kits.html",
        contexto
    )


@login_required
@admin_required
@require_POST
def eliminar_kit(request, kit_id):

    kit = get_object_or_404(
        Kit,
        id=kit_id
    )

    kit.delete()

    messages.success(
        request,
        "Kit eliminado correctamente."
    )

    return redirect(
        "dashboard_kits"
    )


@login_required
@admin_required
@require_POST
def eliminar_producto_kit(request, item_id):

    item = get_object_or_404(
        KitProducto,
        id=item_id
    )

    kit_id = item.kit.id

    item.delete()

    messages.success(
        request,
        "Producto eliminado del kit."
    )

    return redirect(
        f"/dashboard/kits/?editar={kit_id}"
    )


@login_required
@admin_required
def agregar_producto_kit(request, kit_id):

    kit = get_object_or_404(
        Kit,
        id=kit_id
    )

    if request.method == "POST":

        producto_id = request.POST.get("producto")

        variante_id = request.POST.get("variante")

        cantidad = int(
            request.POST.get("cantidad", 1)
        )

        producto = get_object_or_404(
            Producto,
            id=producto_id
        )

        variante = None

        if variante_id:
            variante = get_object_or_404(
                Variante,
                id=variante_id
            )

        item, creado = KitProducto.objects.get_or_create(

            kit=kit,

            producto=producto,

            variante=variante,

            defaults={
                "cantidad": cantidad
            }

        )

        if not creado:

            item.cantidad += cantidad

            item.save()

        messages.success(
            request,
            "Producto agregado al kit."
        )

    return redirect(
        f"/dashboard/kits/?editar={kit.id}"
    )


@login_required
@admin_required
@require_POST
def toggle_kit_activo(request, kit_id):

    kit = get_object_or_404(Kit, id=kit_id)

    kit.activo = not kit.activo

    kit.save(update_fields=["activo"])

    messages.success(
        request,
        f"Kit '{kit.nombre}' {'activado' if kit.activo else 'desactivado'} correctamente."
    )

    return redirect(request.META.get("HTTP_REFERER", "dashboard_kits"))


# =====================================================
# CATÁLOGO PÚBLICO
# =====================================================

def catalogo(request):

    variante_con_stock = Variante.objects.filter(
        producto=OuterRef("pk"),
        stock__gt=0
    )

    productos = (
        Producto.objects
        .filter(activo=True)
        .annotate(
            tiene_stock=Exists(variante_con_stock)
        )
        .select_related(
            "categoria",
            "marca",
            "coleccion"
        )
        .prefetch_related(
            "imagenes",
            "videos",
            "variantes",
            "etiquetas"
        )
        .order_by("-fecha_creacion")
    )

    kits = (
        Kit.objects
        .filter(activo=True)
        .select_related("categoria")
        .prefetch_related("items__producto__imagenes")
        .order_by("-fecha_creacion")
    )

    categorias = Categoria.objects.order_by("nombre")

    marcas = (
        Marca.objects
        .filter(activa=True)
        .order_by("nombre")
    )

    colecciones = (
        Coleccion.objects
        .filter(activa=True)
        .select_related("marca")
        .order_by("nombre")
    )

    return render(
        request,
        "core/catalogo.html",
        {
            "productos": productos,
            "kits": kits,
            "categorias": categorias,
            "marcas": marcas,
            "colecciones": colecciones,
        }
    )


# =====================================================
# DETALLE DEL PRODUCTO
# =====================================================

def detalle_producto(request, slug):

    producto = get_object_or_404(
        Producto.objects
        .filter(activo=True)
        .select_related(
            "categoria",
            "marca",
            "coleccion"
        )
        .prefetch_related(
            "imagenes",
            "videos",
            "variantes",
            "etiquetas"
        ),
        slug=slug
    )

    otros_productos = (
        Producto.objects
        .filter(activo=True)
        .exclude(id=producto.id)
        .select_related(
            "categoria",
            "marca",
            "coleccion"
        )
        .prefetch_related("imagenes")
        .order_by("-fecha_creacion")[:8]
    )

    return render(
        request,
        "core/detalle_producto.html",
        {
            "producto": producto,
            "otros_productos": otros_productos,
        }
    )


# =====================================================
# DETALLE DEL KIT
# =====================================================

def detalle_kit(request, slug):

    kit = get_object_or_404(
        Kit.objects
        .filter(activo=True)
        .select_related("categoria")
        .prefetch_related(
            "items__producto__imagenes",
            "items__variante"
        ),
        slug=slug
    )

    otros_kits = (
        Kit.objects
        .filter(activo=True)
        .exclude(id=kit.id)
        .select_related("categoria")
        .order_by("?")[:4]
    )

    return render(
        request,
        "core/detalle_kit.html",
        {
            "kit": kit,
            "otros_kits": otros_kits,
        }
    )


# =====================================================
# CARRITO
# =====================================================
@login_required
def carrito(request):
    """
    Muestra el carrito del usuario.
    """

    carrito, creado = Carrito.objects.get_or_create(
        usuario=request.user
    )

    items = (
        carrito.items
        .select_related(
            "variante",
            "variante__producto",
            "variante__producto__marca",
            "kit",
        )
        .prefetch_related(
            "variante__producto__imagenes"
        )
    )

    subtotal = Decimal("0")

    for item in items:
        subtotal += item.subtotal

    contexto = {
        "carrito": carrito,
        "items": items,
        "subtotal": subtotal,
        "cantidad_total": carrito.cantidad_total,
    }

    return render(
        request,
        "core/carrito.html",
        contexto
    )


# ==========================================================
# AGREGAR AL CARRITO
# ==========================================================
@login_required
@require_POST
def agregar_al_carrito(request, variante_id):

    variante = get_object_or_404(
        Variante.objects.select_related("producto"),
        id=variante_id
    )

    # ==========================================
    # PRODUCTO ACTIVO
    # ==========================================

    if not variante.producto.activo:
        return JsonResponse({
            "ok": False,
            "mensaje": "Este producto no está disponible."
        }, status=400)

    # ==========================================
    # STOCK
    # ==========================================

    if variante.stock <= 0:
        return JsonResponse({
            "ok": False,
            "mensaje": "Esta variante está agotada."
        }, status=400)

    # ==========================================
    # CANTIDAD
    # ==========================================

    try:
        cantidad = int(
            request.POST.get("cantidad", 1)
        )
    except (TypeError, ValueError):

        return JsonResponse({
            "ok": False,
            "mensaje": "La cantidad no es válida."
        }, status=400)

    if cantidad < 1:

        return JsonResponse({
            "ok": False,
            "mensaje": "La cantidad no es válida."
        }, status=400)

    # ==========================================
    # STOCK DISPONIBLE
    # ==========================================

    if cantidad > variante.stock:

        return JsonResponse({
            "ok": False,
            "mensaje": (
                f"Solo hay {variante.stock} "
                f"unidades disponibles."
            )
        }, status=400)

    # ==========================================
    # CARRITO
    # ==========================================

    carrito, creado = Carrito.objects.get_or_create(
        usuario=request.user
    )

    # ==========================================
    # ITEM
    # ==========================================

    item, creado = CarritoItem.objects.get_or_create(
        carrito=carrito,
        variante=variante,
        defaults={
            "cantidad": cantidad
        }
    )

    # ==========================================
    # SI YA EXISTÍA
    # ==========================================

    if not creado:

        nueva_cantidad = (
            item.cantidad + cantidad
        )

        if nueva_cantidad > variante.stock:

            return JsonResponse({
                "ok": False,
                "mensaje": (
                    f"No puedes agregar más de "
                    f"{variante.stock} unidades."
                )
            }, status=400)

        item.cantidad = nueva_cantidad
        item.save()

    # ==========================================
    # RESPUESTA
    # ==========================================

    return JsonResponse({
        "ok": True,
        "mensaje": "Producto agregado al carrito.",
        "cantidad_item": item.cantidad,
        "cantidad_carrito": carrito.cantidad_total,
        "subtotal_item": str(item.subtotal),
    })


# ==========================================================
# AUMENTAR CANTIDAD
# ==========================================================
@login_required
@require_POST
def aumentar_carrito(request, item_id):

    item = get_object_or_404(
        CarritoItem.objects.select_related(
            "variante",
            "variante__producto",
            "kit",
            "carrito"
        ),
        id=item_id,
        carrito__usuario=request.user
    )

    # ==========================================
    # STOCK
    # ==========================================

    if item.cantidad >= item.stock_disponible:

        return JsonResponse({
            "ok": False,
            "mensaje": (
                f"Solo hay {item.stock_disponible} "
                f"unidades disponibles."
            )
        }, status=400)

    # ==========================================
    # AUMENTAR
    # ==========================================

    item.cantidad += 1
    item.save()

    return JsonResponse({
        "ok": True,
        "cantidad": item.cantidad,
        "subtotal": str(item.subtotal),
        "cantidad_carrito": item.carrito.cantidad_total,
        "stock": item.stock_disponible,
    })


# ==========================================================
# DISMINUIR CANTIDAD
# ==========================================================

@login_required
@require_POST
def disminuir_carrito(request, item_id):

    item = get_object_or_404(
        CarritoItem.objects.select_related(
            "variante",
            "variante__producto",
            "kit",
            "carrito"
        ),
        id=item_id,
        carrito__usuario=request.user
    )

    carrito = item.carrito

    if item.cantidad > 1:

        item.cantidad -= 1
        item.save()

        return JsonResponse({
            "ok": True,
            "eliminado": False,
            "cantidad": item.cantidad,
            "subtotal": str(item.subtotal),
            "cantidad_carrito": carrito.cantidad_total,
        })

    item.delete()

    return JsonResponse({
        "ok": True,
        "eliminado": True,
        "cantidad": 0,
        "cantidad_carrito": carrito.cantidad_total,
    })


# ==========================================================
# ELIMINAR DEL CARRITO
# ==========================================================

@login_required
@require_POST
def eliminar_carrito(request, item_id):

    item = get_object_or_404(
        CarritoItem,
        id=item_id,
        carrito__usuario=request.user
    )

    carrito = item.carrito

    item.delete()

    return JsonResponse({
        "ok": True,
        "mensaje": "Producto eliminado del carrito.",
        "cantidad_carrito": carrito.cantidad_total,
    })


@login_required
@require_POST
def agregar_kit_al_carrito(request, kit_id):

    kit = get_object_or_404(Kit, id=kit_id)

    # ==========================================
    # KIT ACTIVO / STOCK
    # ==========================================

    if not kit.activo:
        return JsonResponse({
            "ok": False,
            "mensaje": "Este kit no está disponible."
        }, status=400)

    if kit.stock <= 0:
        return JsonResponse({
            "ok": False,
            "mensaje": "Este kit está agotado."
        }, status=400)

    # ==========================================
    # CANTIDAD
    # ==========================================

    try:
        cantidad = int(request.POST.get("cantidad", 1))
    except (TypeError, ValueError):
        return JsonResponse({
            "ok": False,
            "mensaje": "La cantidad no es válida."
        }, status=400)

    if cantidad < 1:
        return JsonResponse({
            "ok": False,
            "mensaje": "La cantidad no es válida."
        }, status=400)

    if cantidad > kit.stock:
        return JsonResponse({
            "ok": False,
            "mensaje": f"Solo hay {kit.stock} unidades disponibles."
        }, status=400)

    # ==========================================
    # TONOS ELEGIDOS POR EL CLIENTE
    # ==========================================
    # Para cada producto del kit que NO tenga un tono fijo asignado
    # por el admin (item.variante is null) y que tenga variantes,
    # el cliente debe elegir un tono desde el formulario.

    selecciones_variante = {}

    for item in kit.items.select_related("producto").all():

        if item.variante_id:
            # El admin ya fijó el tono para este producto del kit.
            continue

        if not item.producto.variantes.exists():
            # El producto no maneja tonos/variantes.
            continue

        variante_id = request.POST.get(f"tono_{item.id}")

        if not variante_id:
            return JsonResponse({
                "ok": False,
                "mensaje": f'Debes elegir un tono para "{item.producto.nombre}".'
            }, status=400)

        variante = Variante.objects.filter(
            id=variante_id,
            producto_id=item.producto_id
        ).first()

        if not variante:
            return JsonResponse({
                "ok": False,
                "mensaje": f'El tono elegido para "{item.producto.nombre}" no es válido.'
            }, status=400)

        stock_necesario = item.cantidad * cantidad

        if variante.stock < stock_necesario:
            return JsonResponse({
                "ok": False,
                "mensaje": (
                    f'No hay stock suficiente del tono "{variante.nombre_tono}" '
                    f'para "{item.producto.nombre}".'
                )
            }, status=400)

        selecciones_variante[item.id] = variante

    # ==========================================
    # CARRITO
    # ==========================================

    carrito, _ = Carrito.objects.get_or_create(usuario=request.user)

    item_carrito, creado = CarritoItem.objects.get_or_create(
        carrito=carrito,
        kit=kit,
        defaults={"cantidad": cantidad}
    )

    if not creado:

        nueva_cantidad = item_carrito.cantidad + cantidad

        if nueva_cantidad > kit.stock:
            return JsonResponse({
                "ok": False,
                "mensaje": f"No puedes agregar más de {kit.stock} unidades."
            }, status=400)

        item_carrito.cantidad = nueva_cantidad
        item_carrito.save()

    # Guardamos (o actualizamos, si ya existían) los tonos elegidos.
    for kit_producto_id, variante in selecciones_variante.items():
        CarritoItemKitSeleccion.objects.update_or_create(
            carrito_item=item_carrito,
            kit_producto_id=kit_producto_id,
            defaults={"variante": variante}
        )

    return JsonResponse({
        "ok": True,
        "mensaje": "Kit agregado al carrito.",
        "cantidad_item": item_carrito.cantidad,
        "cantidad_carrito": carrito.cantidad_total,
        "subtotal_item": str(item_carrito.subtotal),
    })


# ==========================================================
# CHECKOUT
# ==========================================================
@login_required
def checkout(request):

    carrito = Carrito.objects.filter(usuario=request.user).first()

    if not carrito:
        return redirect("carrito")

    items = list(
        carrito.items.select_related("variante", "variante__producto", "kit")
    )

    if not items:
        return redirect("carrito")

    items_productos = [item for item in items if not item.es_kit]
    items_kits = [item for item in items if item.es_kit]

    direcciones = Direccion.objects.filter(
        usuario=request.user
    ).order_by("-principal", "-id")

    # ======================================================
    # 1. SUBTOTAL AL DETAL (SOLO PRODUCTOS, define el nivel)
    # ======================================================

    subtotal_detalle = Decimal("0")

    for item in items_productos:

        producto = item.variante.producto
        precio_detalle = Decimal(str(producto.precio_base))
        subtotal_item_detalle = precio_detalle * item.cantidad

        item.checkout_precio_detalle = precio_detalle
        item.checkout_subtotal_detalle = subtotal_item_detalle

        subtotal_detalle += subtotal_item_detalle

    # ======================================================
    # 2. NIVEL DE PRECIO
    # ======================================================

    if subtotal_detalle >= Decimal("1200000"):
        margen = Decimal("0.10")
        nivel_precio = "Más de $1.200.000"
    elif subtotal_detalle >= Decimal("500000"):
        margen = Decimal("0.15")
        nivel_precio = "Más de $500.000"
    elif subtotal_detalle >= Decimal("100000"):
        margen = Decimal("0.20")
        nivel_precio = "Más de $100.000"
    else:
        margen = Decimal("0.30")
        nivel_precio = "Al detalle"

    # ======================================================
    # 3. PRECIO FINAL POR PRODUCTO (con margen)
    # ======================================================

    subtotal_productos = Decimal("0")
    descuento_total = Decimal("0")

    for item in items_productos:

        producto = item.variante.producto
        costo = Decimal(str(producto.costo_base))

        precio_final = aproximar_precio(costo / (Decimal("1") - margen))
        subtotal_producto = precio_final * item.cantidad
        subtotal_producto_detalle = item.checkout_subtotal_detalle

        descuento_producto = subtotal_producto_detalle - subtotal_producto
        if descuento_producto < 0:
            descuento_producto = Decimal("0")

        item.checkout_precio = precio_final
        item.checkout_subtotal = subtotal_producto
        item.checkout_descuento = descuento_producto

        subtotal_productos += subtotal_producto
        descuento_total += descuento_producto

    # ======================================================
    # 3b. KITS: precio propio, SIN descuento por monto
    # ======================================================

    subtotal_kits = Decimal("0")

    for item in items_kits:

        precio_kit = item.kit.precio_final
        subtotal_item_kit = precio_kit * item.cantidad

        item.checkout_precio = precio_kit
        item.checkout_subtotal = subtotal_item_kit
        item.checkout_descuento = Decimal("0")

        subtotal_kits += subtotal_item_kit

    subtotal = subtotal_productos + subtotal_kits

    # ======================================================
    # 4. ENVÍO (según dirección principal / primera disponible)
    # ======================================================

    direccion_seleccionada = direcciones.first()

    if direccion_seleccionada:
        costo_envio = calcular_costo_envio(direccion_seleccionada)
    else:
        costo_envio = Decimal("0")

    total = subtotal + costo_envio

    porcentaje_descuento = margen * Decimal("100")

    # ======================================================
    # CONTEXTO
    # ======================================================

    contexto = {
        "carrito": carrito,
        "items": items,
        "items_productos": items_productos,
        "items_kits": items_kits,
        "direcciones": direcciones,
        "subtotal_detalle": subtotal_detalle,
        "subtotal": subtotal,
        "descuento": descuento_total,
        "total": total,
        "margen": margen,
        "porcentaje_descuento": porcentaje_descuento,
        "nivel_precio": nivel_precio,
        "envio": costo_envio,
        "direccion_seleccionada_id": (
            direccion_seleccionada.id if direccion_seleccionada else None
        ),
    }

    return render(request, "core/checkout.html", contexto)


# ==========================================================
# INICIAR PAGO CON WOMPI
# ==========================================================
@login_required
@require_POST
def pago_checkout(request):

    try:
        datos = json.loads(request.body)
    except (json.JSONDecodeError, TypeError):
        datos = {}

    direccion_id = datos.get("direccion_id")

    if not direccion_id:
        return JsonResponse({
            "ok": False,
            "mensaje": "Debes seleccionar una dirección de entrega."
        }, status=400)

    try:
        direccion = Direccion.objects.get(id=direccion_id, usuario=request.user)
    except Direccion.DoesNotExist:
        return JsonResponse({
            "ok": False,
            "mensaje": "La dirección seleccionada no es válida."
        }, status=400)

    carrito = Carrito.objects.filter(usuario=request.user).first()

    if not carrito:
        return JsonResponse({
            "ok": False,
            "mensaje": "No tienes un carrito activo."
        }, status=400)

    items = list(
        carrito.items.select_related("variante", "variante__producto", "kit")
    )

    if not items:
        return JsonResponse({
            "ok": False,
            "mensaje": "Tu carrito está vacío."
        }, status=400)

    items_productos = [item for item in items if not item.es_kit]
    items_kits = [item for item in items if item.es_kit]

    # ======================================================
    # STOCK
    # ======================================================

    for item in items:

        if item.cantidad <= 0:
            return JsonResponse({
                "ok": False,
                "mensaje": f"La cantidad de {item.nombre} no es válida."
            }, status=400)

        if item.cantidad > item.stock_disponible:
            return JsonResponse({
                "ok": False,
                "mensaje": f"No hay suficiente stock de {item.nombre}."
            }, status=400)

    # ======================================================
    # SUBTOTAL AL DETAL (SOLO PRODUCTOS)
    # ======================================================

    subtotal_detalle = Decimal("0")

    for item in items_productos:
        producto = item.variante.producto
        precio_detalle = Decimal(str(producto.precio_base))
        subtotal_detalle += precio_detalle * item.cantidad

    # ======================================================
    # NIVEL
    # ======================================================

    if subtotal_detalle >= Decimal("1200000"):
        margen = Decimal("0.10")
        nivel_precio = "Más de $1.200.000"
    elif subtotal_detalle >= Decimal("500000"):
        margen = Decimal("0.15")
        nivel_precio = "Más de $500.000"
    elif subtotal_detalle >= Decimal("100000"):
        margen = Decimal("0.20")
        nivel_precio = "Más de $100.000"
    else:
        margen = Decimal("0.30")
        nivel_precio = "Al detalle"

    # ======================================================
    # SUBTOTAL CON DESCUENTO (PRODUCTOS)
    # ======================================================

    subtotal_productos = Decimal("0")
    descuento_total = Decimal("0")

    for item in items_productos:
        producto = item.variante.producto
        costo = Decimal(str(producto.costo_base))

        precio_final = aproximar_precio(costo / (Decimal("1") - margen))
        subtotal_item = precio_final * item.cantidad

        subtotal_item_detalle = Decimal(str(producto.precio_base)) * item.cantidad

        subtotal_productos += subtotal_item
        descuento_total += (subtotal_item_detalle - subtotal_item)

    # ======================================================
    # SUBTOTAL KITS (precio propio, sin descuento por monto)
    # ======================================================

    subtotal_kits = Decimal("0")

    for item in items_kits:
        precio_kit = item.kit.precio_final
        subtotal_kits += precio_kit * item.cantidad

    subtotal = subtotal_productos + subtotal_kits

    # ======================================================
    # ENVÍO + TOTAL
    # ======================================================

    costo_envio = calcular_costo_envio(direccion)
    total = subtotal + costo_envio

    if total <= 0:
        return JsonResponse({
            "ok": False,
            "mensaje": "El total del pedido no es válido."
        }, status=400)

    # ======================================================
    # WOMPI
    # ======================================================

    monto_en_centavos = int(total * Decimal("100"))

    referencia = f"LUMINA-{uuid.uuid4().hex[:12].upper()}"

    cadena_integridad = (
        f"{referencia}{monto_en_centavos}COP{settings.WOMPI_INTEGRITY_SECRET}"
    )

    firma_integridad = hashlib.sha256(
        cadena_integridad.encode("utf-8")
    ).hexdigest()

    return JsonResponse({
        "ok": True,
        "referencia": referencia,
        "monto": monto_en_centavos,
        "moneda": "COP",
        "public_key": settings.WOMPI_PUBLIC_KEY,
        "firma_integridad": firma_integridad,
        "subtotal_detalle": str(subtotal_detalle),
        "descuento": str(descuento_total),
        "subtotal": str(subtotal),
        "costo_envio": str(costo_envio),
        "total": str(total),
        "nivel_precio": nivel_precio,
        "direccion_id": direccion.id,
    })


# ==========================================================
# CONFIRMAR PEDIDO DESPUÉS DEL PAGO
# ==========================================================
@login_required
@require_POST
def confirmar_pedido(request):

    try:
        datos = json.loads(request.body)
    except (json.JSONDecodeError, TypeError):
        return JsonResponse({"ok": False, "mensaje": "Datos de pago inválidos."}, status=400)

    transaction_id = datos.get("transaction_id")
    referencia = datos.get("reference")
    direccion_id = datos.get("direccion_id")

    if not transaction_id or not referencia:
        return JsonResponse({"ok": False, "mensaje": "Faltan datos de la transacción."}, status=400)

    if not direccion_id:
        return JsonResponse({"ok": False, "mensaje": "Falta la dirección de entrega."}, status=400)

    try:
        direccion = Direccion.objects.get(id=direccion_id, usuario=request.user)
    except Direccion.DoesNotExist:
        return JsonResponse({"ok": False, "mensaje": "La dirección seleccionada no es válida."}, status=400)

    # ======================================================
    # WOMPI
    # ======================================================

    if settings.WOMPI_ENVIRONMENT == "sandbox":
        wompi_url = f"https://sandbox.wompi.co/v1/transactions/{transaction_id}"
    else:
        wompi_url = f"https://production.wompi.co/v1/transactions/{transaction_id}"

    try:
        respuesta = requests.get(
            wompi_url,
            headers={"Authorization": f"Bearer {settings.WOMPI_PRIVATE_KEY}"},
            timeout=15
        )
    except requests.RequestException:
        return JsonResponse({"ok": False, "mensaje": "No fue posible verificar el pago con Wompi."}, status=500)

    if not respuesta.ok:
        return JsonResponse({"ok": False, "mensaje": "Wompi no pudo verificar la transacción."}, status=400)

    try:
        respuesta_wompi = respuesta.json()
    except ValueError:
        return JsonResponse({"ok": False, "mensaje": "Respuesta inválida de Wompi."}, status=500)

    transaccion = respuesta_wompi.get("data")

    if not transaccion:
        return JsonResponse({"ok": False, "mensaje": "No se encontró la transacción."}, status=400)

    if transaccion.get("reference") != referencia:
        return JsonResponse({"ok": False, "mensaje": "La referencia del pago no coincide con el pedido."}, status=400)

    if transaccion.get("currency") != "COP":
        return JsonResponse({"ok": False, "mensaje": "La moneda de la transacción no es válida."}, status=400)

    if transaccion.get("status") != "APPROVED":
        return JsonResponse({
            "ok": False,
            "estado": transaccion.get("status"),
            "mensaje": "El pago todavía no ha sido aprobado."
        }, status=400)

    # ======================================================
    # CARRITO
    # ======================================================

    carrito = Carrito.objects.filter(usuario=request.user).first()
    if not carrito:
        return JsonResponse({"ok": False, "mensaje": "No se encontró tu carrito."}, status=400)

    items = list(
        carrito.items.select_related("variante", "variante__producto", "kit")
    )
    if not items:
        return JsonResponse({"ok": False, "mensaje": "El carrito está vacío."}, status=400)

    items_productos = [item for item in items if not item.es_kit]
    items_kits = [item for item in items if item.es_kit]

    # ======================================================
    # SUBTOTAL AL DETAL (SOLO PRODUCTOS)
    # ======================================================

    subtotal_detalle = Decimal("0")

    for item in items_productos:
        producto = item.variante.producto
        precio_detalle = Decimal(str(producto.precio_base))
        subtotal_detalle += precio_detalle * item.cantidad

    # ======================================================
    # NIVEL
    # ======================================================

    if subtotal_detalle >= Decimal("1200000"):
        margen = Decimal("0.10")
        etiqueta = "Más de $1.200.000"
    elif subtotal_detalle >= Decimal("500000"):
        margen = Decimal("0.15")
        etiqueta = "Más de $500.000"
    elif subtotal_detalle >= Decimal("100000"):
        margen = Decimal("0.20")
        etiqueta = "Más de $100.000"
    else:
        margen = Decimal("0.30")
        etiqueta = "Al detalle"

    # ======================================================
    # TOTAL FINAL + DESCUENTO POR ITEM (PRODUCTOS)
    # ======================================================

    subtotal = Decimal("0")
    descuento_total = Decimal("0")
    precios_items = []

    for item in items_productos:
        producto = item.variante.producto
        costo = Decimal(str(producto.costo_base))

        precio_unitario = aproximar_precio(costo / (Decimal("1") - margen))
        subtotal_item = precio_unitario * item.cantidad

        precio_detalle_item = Decimal(str(producto.precio_base))
        subtotal_detalle_item = precio_detalle_item * item.cantidad

        descuento_item = subtotal_detalle_item - subtotal_item
        if descuento_item < 0:
            descuento_item = Decimal("0")

        subtotal += subtotal_item
        descuento_total += descuento_item

        precios_items.append({
            "item": item,
            "es_kit": False,
            "precio_unitario": precio_unitario,
            "precio_original": precio_detalle_item,
            "descuento": descuento_item,
            "subtotal": subtotal_item,
        })

    # ======================================================
    # KITS: precio propio, SIN descuento por monto
    # ======================================================

    for item in items_kits:
        precio_kit = item.kit.precio_final
        subtotal_item = precio_kit * item.cantidad

        subtotal += subtotal_item

        precios_items.append({
            "item": item,
            "es_kit": True,
            "precio_unitario": precio_kit,
            "precio_original": precio_kit,
            "descuento": Decimal("0"),
            "subtotal": subtotal_item,
        })

    porcentaje_descuento = margen * Decimal("100")

    # ======================================================
    # ENVÍO + TOTAL FINAL (recalculado, no confiamos en el front)
    # ======================================================

    costo_envio = calcular_costo_envio(direccion)
    total = subtotal + costo_envio

    # ======================================================
    # VALIDAR MONTO WOMPI
    # ======================================================

    monto_wompi = transaccion.get("amount_in_cents")
    monto_esperado = int(total * Decimal("100"))

    if monto_wompi != monto_esperado:
        return JsonResponse({
            "ok": False,
            "mensaje": "El monto pagado no coincide con el total del pedido.",
            "monto_wompi": monto_wompi,
            "monto_esperado": monto_esperado,
        }, status=400)

    # ======================================================
    # EVITAR DUPLICADOS
    # ======================================================

    if Pedido.objects.filter(referencia=referencia).exists():
        return JsonResponse({"ok": False, "mensaje": "Este pedido ya fue registrado."}, status=400)

    # ======================================================
    # STOCK
    # ======================================================

    for item in items:
        if item.cantidad > item.stock_disponible:
            return JsonResponse({
                "ok": False,
                "mensaje": f"No hay suficiente stock de {item.nombre}."
            }, status=400)

    # ======================================================
    # CREAR PEDIDO
    # ======================================================

    with transaction.atomic():

        pedido = Pedido.objects.create(
            usuario=request.user,
            referencia=referencia,
            subtotal_detalle=subtotal_detalle,
            subtotal=subtotal,
            descuento=descuento_total,
            porcentaje_descuento=porcentaje_descuento,
            costo_envio=costo_envio,
            total=total,
            nivel_precio=etiqueta,
            estado="PAGADO",
            direccion_nombre_receptor=direccion.nombre_receptor,
            direccion_telefono=direccion.telefono,
            direccion_texto=direccion.direccion,
            direccion_ciudad=direccion.ciudad,
            direccion_departamento=direccion.departamento,
            direccion_codigo_postal=direccion.codigo_postal or "",
        )

        for datos_item in precios_items:
            item = datos_item["item"]
            es_kit = datos_item["es_kit"]

            pedido_item = PedidoItem.objects.create(
                pedido=pedido,
                variante=None if es_kit else item.variante,
                kit=item.kit if es_kit else None,
                producto_nombre=item.kit.nombre if es_kit else item.variante.producto.nombre,
                variante_nombre=(
                    None if es_kit else
                    (item.variante.nombre_tono if item.variante.nombre_tono else None)
                ),
                precio_unitario=datos_item["precio_unitario"],
                precio_original=datos_item["precio_original"],
                descuento=datos_item["descuento"],
                cantidad=item.cantidad,
                subtotal=datos_item["subtotal"]
            )

            # ==========================================
            # COPIAR TONOS ELEGIDOS DEL KIT (si aplica)
            # ==========================================
            if es_kit:

                selecciones = item.selecciones_kit.select_related(
                    "kit_producto__producto", "variante"
                )

                for seleccion in selecciones:
                    PedidoItemKitSeleccion.objects.create(
                        pedido_item=pedido_item,
                        kit_producto=seleccion.kit_producto,
                        variante=seleccion.variante,
                        producto_nombre=seleccion.kit_producto.producto.nombre,
                        variante_nombre=seleccion.variante.nombre_tono or "Único",
                    )

                item.kit.stock -= item.cantidad
                item.kit.save(update_fields=["stock"])
            else:
                item.variante.stock -= item.cantidad
                item.variante.save(update_fields=["stock"])

        Pago.objects.create(
            pedido=pedido,
            referencia_wompi=referencia,
            monto=total,
            estado="APROBADO",
            metodo_pago=transaccion.get("payment_method_type"),
            transaccion_id=transaction_id
        )

        carrito.items.all().delete()

    return JsonResponse({
        "ok": True,
        "mensaje": "Tu pedido fue confirmado correctamente.",
        "pedido_id": pedido.id,
        "referencia": pedido.referencia,
        "subtotal_detalle": str(subtotal_detalle),
        "subtotal": str(subtotal),
        "descuento": str(descuento_total),
        "porcentaje_descuento": str(porcentaje_descuento),
        "costo_envio": str(costo_envio),
        "total": str(total),
        "margen": str(margen * Decimal("100")),
        "nivel": etiqueta,
    })


# ==========================================================
# CALCULAR CHECKOUT
# ==========================================================

@login_required
@require_POST
def calcular_checkout(request):

    # ======================================================
    # LEER JSON
    # ======================================================

    try:
        datos = json.loads(request.body)
    except (json.JSONDecodeError, TypeError):
        return JsonResponse({
            "ok": False,
            "mensaje": "Datos inválidos."
        }, status=400)

    # ======================================================
    # DIRECCIÓN
    # ======================================================

    direccion_id = datos.get("direccion_id")

    if not direccion_id:
        return JsonResponse({
            "ok": False,
            "mensaje": "Debes seleccionar una dirección."
        }, status=400)

    try:
        direccion = Direccion.objects.get(
            id=direccion_id,
            usuario=request.user
        )
    except Direccion.DoesNotExist:
        return JsonResponse({
            "ok": False,
            "mensaje": "La dirección seleccionada no es válida."
        }, status=400)

    # ======================================================
    # CARRITO
    # ======================================================

    carrito = Carrito.objects.filter(usuario=request.user).first()

    if not carrito:
        return JsonResponse({
            "ok": False,
            "mensaje": "No tienes un carrito activo."
        }, status=400)

    items = list(
        carrito.items.select_related("variante", "variante__producto", "kit")
    )

    if not items:
        return JsonResponse({
            "ok": False,
            "mensaje": "Tu carrito está vacío."
        }, status=400)

    items_productos = [item for item in items if not item.es_kit]
    items_kits = [item for item in items if item.es_kit]

    # ======================================================
    # SUBTOTAL AL DETAL (SOLO PRODUCTOS)
    # ======================================================

    subtotal_detalle = Decimal("0")

    for item in items_productos:

        producto = item.variante.producto
        precio_detalle = Decimal(str(producto.precio_base))

        subtotal_detalle += precio_detalle * item.cantidad

    # ======================================================
    # NIVEL
    # ======================================================

    if subtotal_detalle >= Decimal("1200000"):
        margen = Decimal("0.10")
        etiqueta = "Más de $1.200.000"

    elif subtotal_detalle >= Decimal("500000"):
        margen = Decimal("0.15")
        etiqueta = "Más de $500.000"

    elif subtotal_detalle >= Decimal("100000"):
        margen = Decimal("0.20")
        etiqueta = "Más de $100.000"

    else:
        margen = Decimal("0.30")
        etiqueta = "Al detalle"

    # ======================================================
    # TOTAL PRODUCTOS (con margen)
    # ======================================================

    subtotal_productos = Decimal("0")
    descuento = Decimal("0")

    for item in items_productos:

        producto = item.variante.producto
        costo = Decimal(str(producto.costo_base))

        precio_final = aproximar_precio(
            costo / (Decimal("1") - margen)
        )

        subtotal_item = precio_final * item.cantidad

        subtotal_detalle_item = (
            Decimal(str(producto.precio_base)) * item.cantidad
        )

        subtotal_productos += subtotal_item
        descuento += (subtotal_detalle_item - subtotal_item)

    # ======================================================
    # TOTAL KITS (precio propio, sin descuento por monto)
    # ======================================================

    subtotal_kits = Decimal("0")

    for item in items_kits:
        precio_kit = item.kit.precio_final
        subtotal_kits += precio_kit * item.cantidad

    subtotal = subtotal_productos + subtotal_kits

    # ======================================================
    # ENVÍO
    # ======================================================

    costo_envio = calcular_costo_envio(direccion)

    # ======================================================
    # TOTAL CON ENVÍO
    # ======================================================

    total = subtotal + costo_envio

    # ======================================================
    # RESPUESTA
    # ======================================================

    return JsonResponse({

        "ok": True,
        "direccion_id": direccion.id,
        "subtotal_detalle": float(subtotal_detalle),
        "subtotal": float(subtotal),
        "descuento": float(descuento),
        "margen": float(margen * Decimal("100")),
        "nivel": etiqueta,
        "costo_envio": float(costo_envio),
        "total": float(total),

    })


# =========================
# PEDIDOS
# =========================

@login_required
def factura_pedido(request, pedido_id):

    pedido = get_object_or_404(
        Pedido.objects.select_related("pago"),
        id=pedido_id,
        usuario=request.user
    )

    items = pedido.items.select_related(
        "variante",
        "variante__producto"
    )

    contexto = {
        "pedido": pedido,
        "items": items,
        "pago": getattr(pedido, "pago", None),
    }

    return render(
        request,
        "core/factura.html",
        contexto
    )


@login_required
def dashboard_pedidos(request):

    if request.user.rol != "admin":
        return redirect("home")

    # ---- Orden ----
    orden = request.GET.get("orden", "recientes")

    ORDENES = {
        "recientes": "-creado",
        "antiguos": "creado",
        "mayor_total": "-total",
        "menor_total": "total",
    }
    orden_campo = ORDENES.get(orden, "-creado")

    pedidos_qs = (
        Pedido.objects
        .select_related("usuario")
        .prefetch_related(
            "items",
            "pago"
        )
        .order_by(orden_campo)
    )

    # ---- Paginación ----
    paginator = Paginator(pedidos_qs, 10)
    page_number = request.GET.get("page")

    try:
        pedidos = paginator.page(page_number)
    except PageNotAnInteger:
        pedidos = paginator.page(1)
    except EmptyPage:
        pedidos = paginator.page(paginator.num_pages)

    return render(
        request,
        "core/pedidos.html",
        {
            "pedidos": pedidos,  # ahora es un objeto Page, sigue siendo iterable
            "total_pedidos": paginator.count,
            "pedidos_pendientes_envio": pedidos_qs.filter(
                estado_envio__in=["PREPARANDO", "EN_PROCESO"]
            ).count(),
            "pedidos_enviados": pedidos_qs.filter(
                estado_envio__in=["ENVIADO", "ENTREGADO", "FINALIZADO"]
            ).count(),
            "orden_actual": orden,
        }
    )


@login_required
def dashboard_pedido_detalle(request, pedido_id):

    pedido = get_object_or_404(
        Pedido.objects.select_related(
            "usuario"
        ).prefetch_related(
            "items",
            "items__variante",
            "items__variante__producto",
            "items__selecciones_kit",
            "items__selecciones_kit__variante",
        ),
        id=pedido_id
    )

    return render(
        request,
        "core/pedido_detalle.html",
        {
            "pedido": pedido,
        }
    )


# NOTA: en el original esta vista estaba definida DOS VECES con lógica
# distinta. La primera versión validaba `request.user.rol != "admin"` y
# actualizaba `pedido.estado` (estado de pago) a partir de "estado" en el
# POST. Como la segunda definición pisa a la primera en Python, esa primera
# versión era código muerto: nunca se ejecutaba. Se conserva únicamente la
# versión que realmente corre (más abajo), que actualiza el estado de
# ENVÍO y NO valida que el usuario sea admin — vale la pena revisar si eso
# fue intencional.
def dashboard_pedido_estado(request, pedido_id):
    pedido = get_object_or_404(Pedido, id=pedido_id)

    if request.method == 'POST':
        nuevo_estado_envio = request.POST.get('estado_envio')
        numero_guia = request.POST.get('numero_guia', '').strip()
        transportadora = request.POST.get('transportadora', '').strip()

        if nuevo_estado_envio not in dict(Pedido.ESTADOS_ENVIO):
            messages.error(request, 'Estado de envío inválido.')
            return redirect('dashboard_pedido_detalle', pedido_id=pedido.id)

        if nuevo_estado_envio == 'ENVIADO':
            if pedido.estado != 'PAGADO':
                messages.error(request, 'No puedes marcar el pedido como enviado si el pago no está aprobado.')
                return redirect('dashboard_pedido_detalle', pedido_id=pedido.id)

            if not numero_guia or not transportadora:
                messages.error(request, 'Debes ingresar el número de guía y la transportadora para marcar el pedido como enviado.')
                return redirect('dashboard_pedido_detalle', pedido_id=pedido.id)

            pedido.numero_guia = numero_guia
            pedido.transportadora = transportadora

            if not pedido.fecha_envio:
                pedido.fecha_envio = timezone.now()

        pedido.estado_envio = nuevo_estado_envio
        pedido.save()

        messages.success(request, 'Estado del pedido actualizado correctamente.')
        return redirect('dashboard_pedido_detalle', pedido_id=pedido.id)

    return redirect('dashboard_pedidos')


# =========================================================================
# RECOMENDACIONES DE EMPRENDIMIENTO
# =========================================================================

def _nivel_desde_presupuesto(presupuesto):
    if presupuesto <= 100000:
        return "Principiante"
    if presupuesto <= 300000:
        return "Intermedio"
    return "Avanzado"


# atributo_precio (precio_base / precio_500 / precio_1200) es lo que LE
# CUESTA AL EMPRENDEDOR comprarle a Lúmina, según el tramo de volumen de su
# compra — NO es un precio de reventa. precio_base es "el mismo que ve
# cualquier cliente" (sin descuento por volumen, para compras chicas);
# precio_500 y precio_1200 son precios con descuento por volumen para
# compras mayores. costo_base es el costo INTERNO de Lúmina y no participa
# en este cálculo: es contabilidad nuestra, no del emprendedor.
#
# El primer tramo es "hasta $99.999" (no $100.000), para que un presupuesto
# de exactamente $100.000 caiga en el segundo tramo.
#
# `divisor` es la base del margen sugerido de reventa para ese tramo:
# margen = 1 − divisor, y el precio de venta al cliente final sale de
# precio_venta = costo_emprendedor ÷ divisor (ver FORMULA_PRECIO_VENTA).
TRAMOS_MARGEN = [
    (Decimal("99999"), Decimal("0.75"), "precio_base", "hasta $99.999"),
    (Decimal("500000"), Decimal("0.85"), "precio_500", "entre $100.000 y $500.000"),
    (None, Decimal("0.90"), "precio_1200", "más de $500.000"),
]

# Fórmula de precio de venta sugerido al cliente final, expuesta tal cual
# al frontend para que la explicación al usuario no dependa de texto
# hardcodeado en el JS. costo = lo que el emprendedor le paga a Lúmina
# (atributo_precio del tramo), margen = el margen sugerido de ese tramo.
FORMULA_PRECIO_VENTA = "precio_venta = costo ÷ (1 − margen)"

MAX_UNIDADES_POR_PRODUCTO = 3  # evita recomendar "8x lo mismo" cuando hay poca variedad


def _tramo_margen_por_presupuesto(presupuesto):
    for limite, divisor, atributo_precio, etiqueta in TRAMOS_MARGEN:
        if limite is None or presupuesto <= limite:
            return divisor, atributo_precio, etiqueta
    ultimo = TRAMOS_MARGEN[-1]
    return ultimo[1], ultimo[2], ultimo[3]


def _ganancia_y_roi_generico(presupuesto, divisor):
    """
    Fallback SOLO para cuando no hay productos con precio configurado para
    este tramo (atributo_precio) y por tanto no se puede armar una lista de
    compra real. Es un promedio del tramo, no un cálculo trazable.
    """
    factor = (Decimal("1") / divisor) - Decimal("1")
    ganancia = (presupuesto * factor).quantize(Decimal("1"))
    roi = (factor * 100).quantize(Decimal("0.01"))
    return ganancia, roi, factor


def _productos_activos(recomendacion):
    """
    Filtra sobre la caché ya traída por prefetch_related("productos") en vez
    de volver a golpear la base con .filter(activo=True), que invalida el
    prefetch y dispara una query nueva cada vez que se llama.
    """
    return [p for p in recomendacion.productos.all() if p.activo]


def _kits_activos(recomendacion):
    """
    Igual que _productos_activos pero para kits: usa la caché del
    prefetch_related("kits") en vez de volver a consultar la base.
    """
    return [k for k in recomendacion.kits.all() if k.activo]


def _construir_lista_compra(productos_activos, presupuesto, atributo_precio, divisor):
    """
    Arma una lista de compra concreta repartiendo el presupuesto entre los
    productos activos ya filtrados (ver _productos_activos), del más barato
    al más caro, usando lo que REALMENTE le cuesta al emprendedor comprarle
    a Lúmina en este tramo (atributo_precio: precio_base / precio_500 /
    precio_1200, según el volumen de la compra). costo_base NO se usa acá:
    es el costo interno de Lúmina, no el del emprendedor.

    El precio de venta sugerido al cliente final sale de aplicar el margen
    del tramo sobre ese costo: precio_venta = costo ÷ divisor (ver
    FORMULA_PRECIO_VENTA, donde margen = 1 − divisor).

    Pone un tope de MAX_UNIDADES_POR_PRODUCTO por producto: si con eso no
    se agota el presupuesto, es señal de que a esta recomendación le faltan
    productos asociados (se deja advertencia en logs) en vez de comprar
    cantidades absurdas de un solo producto.

    Devuelve None si ningún producto activo tiene precio > 0 para este
    tramo (el caller debe usar el fallback genérico del tramo en ese caso).
    """
    productos = [
        p for p in productos_activos
        if getattr(p, atributo_precio) and getattr(p, atributo_precio) > 0
    ]
    if not productos:
        return None

    productos = sorted(productos, key=lambda p: getattr(p, atributo_precio))

    restante = presupuesto
    cantidades = {p.id: 0 for p in productos}

    compro_algo = True
    while compro_algo:
        compro_algo = False
        for p in productos:
            if cantidades[p.id] >= MAX_UNIDADES_POR_PRODUCTO:
                continue
            costo_unit = getattr(p, atributo_precio)
            if costo_unit <= restante:
                cantidades[p.id] += 1
                restante -= costo_unit
                compro_algo = True

    margen_tramo = ((1 - divisor) * 100).quantize(Decimal("0.1"))

    lineas = []
    total_costo = Decimal("0")
    total_venta = Decimal("0")

    for p in productos:
        cantidad = cantidades[p.id]
        if cantidad == 0:
            continue

        costo_unit = getattr(p, atributo_precio)
        precio_venta_unit = (costo_unit / divisor).quantize(Decimal("1"))

        subtotal_costo = (costo_unit * cantidad).quantize(Decimal("1"))
        subtotal_venta = (precio_venta_unit * cantidad).quantize(Decimal("1"))

        total_costo += subtotal_costo
        total_venta += subtotal_venta

        lineas.append(
            {
                "nombre": p.nombre,
                "cantidad": cantidad,
                "costo_unitario": float(costo_unit),
                "precio_venta_unitario": float(precio_venta_unit),
                "margen_porcentaje": float(margen_tramo),
                "subtotal_costo": float(subtotal_costo),
                "subtotal_venta": float(subtotal_venta),
            }
        )

    if not lineas:
        return None

    limite_alcanzado_en_todos = all(
        cantidades[p.id] >= MAX_UNIDADES_POR_PRODUCTO for p in productos
    )
    if limite_alcanzado_en_todos and restante > (presupuesto * Decimal("0.15")):
        logger.warning(
            "recomendación: solo tiene %d producto(s) configurado(s) y "
            "queda %.0f sin usar del presupuesto tras topar %d unidades por "
            "producto — considera asociar más productos a esta regla.",
            len(productos), restante, MAX_UNIDADES_POR_PRODUCTO,
        )

    return {
        "lineas": lineas,
        "total_costo": total_costo,
        "total_venta": total_venta,
        "sobrante": restante,
    }


def _composicion_kit(kit):
    """
    Detalle de qué trae un kit: cada producto (agrupado, sumando
    cantidades entre variantes distintas del mismo producto — un mismo
    producto puede aparecer en varias filas de KitProducto si el kit
    ofrece distintos tonos de ese producto), y el ahorro real del kit
    (kit.ahorro / kit.ahorro_porcentaje ya calculan precio_normal vs
    precio_final en el modelo) vs comprar todo suelto al precio de
    catálogo.
    """
    items = list(kit.items.all())

    por_producto = {}
    orden_productos = []
    for item in items:
        pid = item.producto_id
        if pid not in por_producto:
            por_producto[pid] = {"nombre": item.producto.nombre, "cantidad": 0}
            orden_productos.append(pid)
        por_producto[pid]["cantidad"] += item.cantidad

    productos_agrupados = [por_producto[pid] for pid in orden_productos]

    return {
        "num_productos_distintos": len(productos_agrupados),
        "unidades_totales": sum(item.cantidad for item in items),
        "productos": productos_agrupados,
        "precio_normal": float(kit.precio_normal),
        "precio_final": float(kit.precio_final),
        "ahorro": float(kit.ahorro),
        "ahorro_porcentaje": float(kit.ahorro_porcentaje),
    }


def _reventa_individual_kit(kit, atributo_precio, divisor):
    """
    Para quien compra el kit y prefiere revender los productos por
    separado: aplica la MISMA fórmula de precio de venta que se usa para
    productos sueltos (FORMULA_PRECIO_VENTA) a cada producto del kit
    (agrupado por producto, sumando cantidades entre variantes distintas
    del mismo producto), con su costo en el tramo actual (atributo_precio).
    Esto es independiente del descuento del kit: el descuento del kit es
    lo que el emprendedor AHORRA al comprar el combo; esto es a cuánto
    podría venderlos luego, uno por uno.

    Devuelve None si ningún producto del kit tiene precio configurado para
    este tramo.
    """
    por_producto = {}
    orden_productos = []
    for item in kit.items.all():
        pid = item.producto_id
        if pid not in por_producto:
            por_producto[pid] = {"producto": item.producto, "cantidad": 0}
            orden_productos.append(pid)
        por_producto[pid]["cantidad"] += item.cantidad

    lineas = []
    total_venta = Decimal("0")

    for pid in orden_productos:
        producto = por_producto[pid]["producto"]
        cantidad = por_producto[pid]["cantidad"]

        costo_unit = getattr(producto, atributo_precio)
        if not costo_unit or costo_unit <= 0:
            continue

        precio_venta_unit = (costo_unit / divisor).quantize(Decimal("1"))
        subtotal_venta = (precio_venta_unit * cantidad).quantize(Decimal("1"))
        total_venta += subtotal_venta

        lineas.append(
            {
                "nombre": producto.nombre,
                "cantidad": cantidad,
                "precio_venta_unitario": float(precio_venta_unit),
                "subtotal_venta": float(subtotal_venta),
            }
        )

    if not lineas:
        return None

    return {"lineas": lineas, "total_venta": float(total_venta)}


def _sugerir_uso_sobrante(sobrante, productos_activos, atributo_precio):
    """
    Qué hacer con lo que sobra del presupuesto (venga de la lista de compra
    de productos sueltos o de la estimación de kits): si alcanza para sumar
    una unidad más del producto más barato de la selección, se sugiere eso
    (así queda TODO el presupuesto invertido en mercancía); si no alcanza
    para nada, la única opción realista es dejarlo para cubrir el envío.
    """
    if sobrante is None or sobrante <= 0:
        return None

    candidatos = [
        p for p in productos_activos
        if getattr(p, atributo_precio) and 0 < getattr(p, atributo_precio) <= sobrante
    ]

    if not candidatos:
        return {"monto": float(sobrante), "producto_sugerido": None}

    mas_barato = min(candidatos, key=lambda p: getattr(p, atributo_precio))

    return {
        "monto": float(sobrante),
        "producto_sugerido": {
            "nombre": mas_barato.nombre,
            "costo": float(getattr(mas_barato, atributo_precio)),
        },
    }


def _kits_estimados(kits_activos, presupuesto):
    """
    Cuántos kits completos alcanza a comprar el presupuesto, usando
    precio_final (lo que el emprendedor paga por adquirir el kit), y
    cuánto sobra tras esa compra.
    Recibe los kits ya filtrados (ver _kits_activos) para no volver a
    consultar la base.
    """
    kits_con_precio = [k for k in kits_activos if k.precio_final and k.precio_final > 0]
    if not kits_con_precio:
        return None

    costo_kit_promedio = sum(k.precio_final for k in kits_con_precio) / len(kits_con_precio)
    if costo_kit_promedio <= 0:
        return None

    cantidad = int(presupuesto // costo_kit_promedio)
    sobrante = (presupuesto - (cantidad * costo_kit_promedio)).quantize(Decimal("1"))

    return {"cantidad": cantidad, "sobrante": sobrante}


def _mejor_match(candidatas, presupuesto, producto, plataforma):
    """
    Elige la regla MÁS ESPECÍFICA (la que coincide en más criterios
    explícitos) entre las que matchean, en vez de la primera. Si ninguna
    matchea, devuelve None para que el caller use el fallback genérico.
    """
    mejor = None
    mejor_score = -1
    for r in candidatas:
        if not r.coincide_con(presupuesto, producto, plataforma):
            continue
        score = 0
        if r.producto_interes and r.producto_interes == producto:
            score += 1
        if r.plataforma and r.plataforma == plataforma:
            score += 1
        if score > mejor_score:
            mejor_score = score
            mejor = r
    return mejor


@require_POST
def recomendar_emprendimiento(request):
    try:
        presupuesto = Decimal(str(request.POST.get("presupuesto", "")))
    except (InvalidOperation, TypeError):
        return JsonResponse(
            {"encontrada": False, "mensaje": "Selecciona un presupuesto válido."},
            status=400,
        )

    if presupuesto <= 0:
        return JsonResponse(
            {"encontrada": False, "mensaje": "Ingresa un presupuesto mayor a $0."},
            status=400,
        )

    producto = request.POST.get("producto") or None
    plataforma = request.POST.get("plataforma") or None

    candidatas = RecomendacionEmprendimiento.objects.filter(
        activa=True
    ).prefetch_related("kits__items__producto", "productos")

    recomendacion = _mejor_match(candidatas, presupuesto, producto, plataforma)

    divisor, atributo_precio, tramo_etiqueta = _tramo_margen_por_presupuesto(presupuesto)

    if recomendacion is None:
        logger.warning(
            "recomendar_emprendimiento: sin regla específica para "
            "presupuesto=%s producto=%s plataforma=%s — usando fallback genérico",
            presupuesto, producto, plataforma,
        )
        ganancia_estimada, roi, _ = _ganancia_y_roi_generico(presupuesto, divisor)
        margen_porcentaje = ((1 - divisor) * 100).quantize(Decimal("0.1"))

        return JsonResponse(
            {
                "encontrada": True,
                "generica": True,
                "nombre": "Recomendación general",
                "producto_interes_display": "Cualquiera",
                "plataforma_display": "Cualquiera",
                "nivel": _nivel_desde_presupuesto(presupuesto),
                "inversion_estimada": float(presupuesto),
                "ganancia_estimada": float(ganancia_estimada),
                "roi": float(roi),
                "margen_porcentaje": float(margen_porcentaje),
                "formula_precio_venta": FORMULA_PRECIO_VENTA,
                "tramo_etiqueta": tramo_etiqueta,
                "lista_compra": [],
                "compra_total_costo": None,
                "compra_total_venta": None,
                "presupuesto_sobrante": None,
                "presupuesto_sobrante_sugerencia": None,
                "kits_estimados": None,
                "kits_sobrante_sugerencia": None,
                "recomendacion": (
                    "Todavía no tenemos una recomendación específica para esta "
                    "combinación exacta, pero con este presupuesto puedes "
                    "empezar comprando al por mayor en Lúmina y revendiendo "
                    "con el margen típico de este tramo."
                ),
                "productos": [],
                "kits": [],
            }
        )

    # Se filtran una sola vez sobre la caché del prefetch_related y se
    # reutilizan en todo lo que sigue (lista de compra, kits estimados,
    # productos_data, kits_data) para no volver a consultar la base.
    productos_activos = _productos_activos(recomendacion)
    kits_activos = _kits_activos(recomendacion)

    lista_compra = _construir_lista_compra(productos_activos, presupuesto, atributo_precio, divisor)

    # El margen mostrado es siempre el del tramo (1 − divisor): es el mismo
    # margen sugerido para todos los productos de esa recomendación, porque
    # el precio de venta de cada uno se DERIVA de aplicar ese margen a lo
    # que le cuesta al emprendedor (ver _construir_lista_compra).
    margen_porcentaje = ((1 - divisor) * 100).quantize(Decimal("0.1"))

    if lista_compra:
        total_costo = lista_compra["total_costo"]
        total_venta = lista_compra["total_venta"]
        ganancia_estimada = (total_venta - total_costo).quantize(Decimal("1"))
        roi = (
            ((total_venta / total_costo - 1) * 100).quantize(Decimal("0.01"))
            if total_costo > 0 else Decimal("0")
        )

        lista_compra_json = lista_compra["lineas"]
        compra_total_costo = float(total_costo)
        compra_total_venta = float(total_venta)
        presupuesto_sobrante = float(lista_compra["sobrante"])
        presupuesto_sobrante_sugerencia = _sugerir_uso_sobrante(
            lista_compra["sobrante"], productos_activos, atributo_precio
        )
    else:
        logger.warning(
            "recomendar_emprendimiento: recomendación '%s' sin productos con "
            "precio configurado para este tramo (%s) — usando fallback "
            "genérico del tramo",
            recomendacion.nombre, atributo_precio,
        )
        ganancia_estimada, roi, _ = _ganancia_y_roi_generico(presupuesto, divisor)
        lista_compra_json = []
        compra_total_costo = None
        compra_total_venta = None
        presupuesto_sobrante = None
        presupuesto_sobrante_sugerencia = None

    kits_estimados_info = _kits_estimados(kits_activos, presupuesto)
    kits_estimados = kits_estimados_info["cantidad"] if kits_estimados_info else None
    kits_sobrante_sugerencia = (
        _sugerir_uso_sobrante(
            kits_estimados_info["sobrante"], productos_activos, atributo_precio
        )
        if kits_estimados_info else None
    )

    kits_data = [
        {
            "id": k.id,
            "nombre": k.nombre,
            "precio": float(k.precio_final),
            "url": reverse("detalle_kit", args=[k.slug]),
            "composicion": _composicion_kit(k),
            "reventa_individual": _reventa_individual_kit(k, atributo_precio, divisor),
        }
        for k in kits_activos
    ]

    productos_data = []
    for p in productos_activos:
        costo_unit = getattr(p, atributo_precio)
        if costo_unit and costo_unit > 0:
            precio_venta_unit = (costo_unit / divisor).quantize(Decimal("1"))
            margen_unit = float(((1 - divisor) * 100).quantize(Decimal("0.1")))
        else:
            precio_venta_unit = None
            margen_unit = None

        productos_data.append(
            {
                "id": p.id,
                "nombre": p.nombre,
                # Lo que le cuesta al emprendedor comprarle a Lúmina en este
                # tramo (NO es costo_base, que es el costo interno de Lúmina).
                "costo": float(costo_unit) if costo_unit else None,
                "precio_sugerido": float(precio_venta_unit) if precio_venta_unit is not None else None,
                "precio_catalogo": float(p.precio_base),
                "margen_porcentaje": margen_unit,
                "url": reverse("detalle_producto", args=[p.slug]),
            }
        )

    return JsonResponse(
        {
            "encontrada": True,
            "generica": False,
            "margen_real": bool(lista_compra),
            "nombre": recomendacion.nombre,
            "producto_interes_display": (
                recomendacion.get_producto_interes_display()
                if recomendacion.producto_interes
                else "Cualquiera"
            ),
            "plataforma_display": (
                recomendacion.get_plataforma_display()
                if recomendacion.plataforma
                else "Cualquiera"
            ),
            "nivel": _nivel_desde_presupuesto(presupuesto),
            "inversion_estimada": float(presupuesto),
            "ganancia_estimada": float(ganancia_estimada),
            "roi": float(roi),
            "margen_porcentaje": float(margen_porcentaje),
            "formula_precio_venta": FORMULA_PRECIO_VENTA,
            "tramo_etiqueta": tramo_etiqueta,
            "lista_compra": lista_compra_json,
            "compra_total_costo": compra_total_costo,
            "compra_total_venta": compra_total_venta,
            "presupuesto_sobrante": presupuesto_sobrante,
            "presupuesto_sobrante_sugerencia": presupuesto_sobrante_sugerencia,
            "kits_estimados": kits_estimados,
            "kits_sobrante_sugerencia": kits_sobrante_sugerencia,
            "recomendacion": recomendacion.recomendacion,
            "productos": productos_data,
            "kits": kits_data,
        }
    )


@login_required
def dashboard_recomendaciones(request):
    if request.method == "POST":
        recomendacion_id = request.POST.get("recomendacion_id")

        nombre = request.POST.get("nombre", "").strip()
        producto_interes = request.POST.get("producto_interes") or None
        plataforma = request.POST.get("plataforma") or None
        recomendacion_texto = request.POST.get("recomendacion", "").strip()
        activa = request.POST.get("activa") == "on"
        kits_ids = request.POST.getlist("kits")
        productos_ids = request.POST.getlist("productos")

        if not nombre:
            messages.error(request, "El nombre de la recomendación es obligatorio.")
            return redirect("dashboard_recomendaciones")

        try:
            presupuesto_min = Decimal(str(request.POST.get("presupuesto_min", "0")))
            presupuesto_max = Decimal(str(request.POST.get("presupuesto_max", "0")))
        except InvalidOperation:
            messages.error(request, "El rango de inversión no es válido.")
            return redirect("dashboard_recomendaciones")

        if presupuesto_max < presupuesto_min:
            messages.error(
                request,
                "El presupuesto máximo no puede ser menor que el presupuesto mínimo.",
            )
            return redirect("dashboard_recomendaciones")

        if recomendacion_id:
            recomendacion = get_object_or_404(
                RecomendacionEmprendimiento, id=recomendacion_id
            )
            accion = "actualizada"
        else:
            recomendacion = RecomendacionEmprendimiento()
            accion = "creada"

        recomendacion.nombre = nombre
        recomendacion.presupuesto_min = presupuesto_min
        recomendacion.presupuesto_max = presupuesto_max
        recomendacion.producto_interes = producto_interes
        recomendacion.plataforma = plataforma
        recomendacion.recomendacion = recomendacion_texto
        recomendacion.activa = activa
        recomendacion.save()

        recomendacion.kits.set(kits_ids)
        recomendacion.productos.set(productos_ids)

        messages.success(request, f"Recomendación «{nombre}» {accion} correctamente.")
        return redirect("dashboard_recomendaciones")

    recomendaciones = RecomendacionEmprendimiento.objects.prefetch_related(
        "kits", "productos"
    ).all()
    kits = Kit.objects.filter(activo=True)
    productos = Producto.objects.filter(activo=True)

    return render(
        request,
        "core/recomendaciones.html",
        {
            "recomendaciones": recomendaciones,
            "kits": kits,
            "productos": productos,
        },
    )


@login_required
def eliminar_recomendacion(request, id):
    recomendacion = get_object_or_404(RecomendacionEmprendimiento, id=id)
    nombre = recomendacion.nombre
    recomendacion.delete()
    messages.success(request, f"Recomendación «{nombre}» eliminada.")
    return redirect("dashboard_recomendaciones")


# =====================================================================
# REPORTES GUARDADOS (Mi cuenta)
# =====================================================================

@login_required
@require_POST
def guardar_reporte_emprendimiento(request):
    """
    Guarda una copia del resultado que ya se le mostró al usuario en el
    test de /emprender/. Recibe por POST (JSON en el body) el mismo dict
    que devolvió /api/recomendar-emprendimiento/, más los filtros usados.
    """
    try:
        payload = json.loads(request.body.decode("utf-8"))
    except (ValueError, UnicodeDecodeError):
        return JsonResponse({"ok": False, "mensaje": "Datos inválidos."}, status=400)

    data = payload.get("data")
    if not isinstance(data, dict) or not data.get("encontrada"):
        return JsonResponse(
            {"ok": False, "mensaje": "No hay un resultado válido para guardar."},
            status=400,
        )

    try:
        presupuesto = Decimal(str(payload.get("presupuesto", "0")))
    except InvalidOperation:
        presupuesto = Decimal("0")

    reporte = ReporteEmprendimiento.objects.create(
        usuario=request.user,
        nombre_recomendacion=(data.get("nombre") or "")[:200],
        presupuesto=presupuesto,
        producto=payload.get("producto") or "",
        plataforma=payload.get("plataforma") or "",
        ganancia_estimada=Decimal(str(data.get("ganancia_estimada", 0))),
        roi=Decimal(str(data.get("roi", 0))),
        datos=data,
    )

    return JsonResponse({"ok": True, "id": reporte.id})


@login_required
def reporte_emprendimiento_detalle(request, id):
    reporte = get_object_or_404(ReporteEmprendimiento, id=id, usuario=request.user)
    return render(request, "core/reporte_emprendimiento_detalle.html", {"reporte": reporte})


@login_required
def eliminar_reporte_emprendimiento(request, id):
    reporte = get_object_or_404(ReporteEmprendimiento, id=id, usuario=request.user)
    reporte.delete()
    messages.success(request, "Reporte eliminado.")
    return redirect("mi_cuenta")