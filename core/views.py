from datetime import datetime
import uuid
import hashlib
import requests
from django.conf import settings
from django.views.decorators.http import require_POST
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.core.paginator import EmptyPage, PageNotAnInteger
from django.core.paginator import Paginator
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from .gmail import enviar_correo
from django.db.models import Count, Sum
from datetime import timedelta
from openpyxl import Workbook
from decimal import Decimal, InvalidOperation, ROUND_CEILING
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from django.utils import timezone
from django.utils.text import slugify
from django.db.models import Q, Exists, OuterRef
import json
from datetime import date

from .gmail import (
    enviar_correo,
    obtener_hilo,
    obtener_encabezado,
    obtener_texto
)
from .decorators import admin_required
from .forms import CambiarPasswordForm, DireccionForm, EditarPerfilForm, RegistroForm
from .models import (
    BlogPost, BlogSeccion, Direccion, Galeria, Pedido, Usuario, Test, Resultado,
    Pregunta, Opcion, ResultadoUsuario, NotaAdmin, Recordatorio, PedidoItem, Etiqueta,
    Producto, Categoria, Marca, Coleccion, ProductoImagen, ProductoVideo, Kit,
    KitProducto, Carrito, CarritoItem, Variante, Contacto, EventoCalendario,
    IdeaContenido, PostIt, Pago, Pedido, CarritoItemKitSeleccion, PedidoItemKitSeleccion, RecomendacionEmprendimiento,
)
from django.db import transaction


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


from django.shortcuts import render
from .models import RecomendacionEmprendimiento


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

    return render(request, "core/cuenta.html", {
        "form": form,
        "pedidos": pedidos,
        "resultados_usuario": resultados_usuario,
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

    if request.user.id == usuario.id:
        return redirect("usuario_d")

    usuario.delete()
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
# PRODUCTOS - MÁRGENES DE PRECIO
# =========================

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
def obtener_margen_por_monto(monto):
    """
    Determina el margen de rentabilidad según el valor
    total de la compra.
    """

    monto = Decimal(monto or 0)

    regla_aplicable = MARGENES_RENTABILIDAD[0]

    for regla in MARGENES_RENTABILIDAD:
        if monto >= regla["desde"]:
            regla_aplicable = regla

    return regla_aplicable
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
UMBRAL_STOCK_BAJO = 5


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
from django.db.models import Sum, Count, Avg
from datetime import timedelta
import json

UMBRAL_STOCK_BAJO = 5  # si ya la definiste en dashboard_productos, no la repitas — solo va una vez en el módulo


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
@login_required
def dashboard_pedido_estado(request, pedido_id):

    if request.user.rol != "admin":
        return redirect("home")

    pedido = get_object_or_404(
        Pedido,
        id=pedido_id
    )

    if request.method == "POST":

        nuevo_estado = request.POST.get("estado")

        estados_validos = [
            estado[0]
            for estado in Pedido.ESTADOS
        ]

        if nuevo_estado in estados_validos:

            pedido.estado = nuevo_estado
            pedido.save(
                update_fields=[
                    "estado",
                    "actualizado"
                ]
            )

        return redirect(
            "dashboard_pedido_detalle",
            pedido_id=pedido.id
        )

    return redirect(
        "dashboard_pedido_detalle",
        pedido_id=pedido.id
    )
def calcular_costo_envio(direccion):
    ciudad = direccion.ciudad.strip().lower()

    if ciudad in ("medellín", "medellin"):
        return Decimal("10000")

    return Decimal("12000")

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
# =========================
# RECOMENDACIONES
# =========================
@login_required
@admin_required
def dashboard_recomendaciones(request):

    # =====================================
    # CREAR RECOMENDACIÓN
    # =====================================

    if request.method == "POST":

        nombre = (
            request.POST.get("nombre") or ""
        ).strip()

        presupuesto_min = (
            request.POST.get("presupuesto_min") or "0"
        ).strip()

        presupuesto_max = (
            request.POST.get("presupuesto_max") or "0"
        ).strip()

        producto_interes = (
            request.POST.get("producto_interes") or ""
        ).strip()

        plataforma = (
            request.POST.get("plataforma") or ""
        ).strip()

        inversion_estimada = (
            request.POST.get("inversion_estimada") or "0"
        ).strip()

        ganancia_estimada = (
            request.POST.get("ganancia_estimada") or "0"
        ).strip()

        recomendacion = (
            request.POST.get("recomendacion") or ""
        ).strip()

        activa = request.POST.get("activa") == "on"

        # =====================================
        # CREAR
        # =====================================

        nueva_recomendacion = RecomendacionEmprendimiento.objects.create(

            nombre=nombre,

            presupuesto_min=presupuesto_min,

            presupuesto_max=presupuesto_max,

            producto_interes=producto_interes,

            plataforma=plataforma,

            inversion_estimada=inversion_estimada,

            ganancia_estimada=ganancia_estimada,

            recomendacion=recomendacion,

            activa=activa,

        )

        # =====================================
        # KITS
        # =====================================

        kits_ids = request.POST.getlist("kits")

        if kits_ids:

            nueva_recomendacion.kits.set(
                Kit.objects.filter(
                    id__in=kits_ids,
                    activo=True
                )
            )

        # =====================================
        # PRODUCTOS
        # =====================================

        productos_ids = request.POST.getlist("productos")

        if productos_ids:

            nueva_recomendacion.productos.set(
                Producto.objects.filter(
                    id__in=productos_ids,
                    activo=True
                )
            )

        messages.success(
            request,
            "Recomendación creada correctamente."
        )

        return redirect(
            "dashboard_recomendaciones"
        )

    # =====================================
    # LISTADO
    # =====================================

    recomendaciones = (
        RecomendacionEmprendimiento.objects
        .prefetch_related(
            "kits",
            "productos"
        )
        .order_by("-fecha_creacion")
    )

    contexto = {

        "recomendaciones": recomendaciones,

        "kits": (
            Kit.objects
            .filter(activo=True)
            .order_by("nombre")
        ),

        "productos": (
            Producto.objects
            .filter(activo=True)
            .order_by("nombre")
        ),

    }

    return render(
        request,
        "core/recomendaciones.html",
        contexto
    )
# =========================
# EDITAR RECOMENDACIÓN
# =========================

@login_required
@admin_required
def editar_recomendacion(request, recomendacion_id):

    recomendacion = get_object_or_404(
        RecomendacionEmprendimiento,
        id=recomendacion_id
    )

    if request.method == "POST":

        recomendacion.nombre = (
            request.POST.get("nombre") or ""
        ).strip()

        recomendacion.presupuesto_min = (
            request.POST.get("presupuesto_min") or 0
        )

        recomendacion.presupuesto_max = (
            request.POST.get("presupuesto_max") or 0
        )

        recomendacion.producto_interes = (
            request.POST.get("producto_interes") or ""
        ).strip()

        recomendacion.plataforma = (
            request.POST.get("plataforma") or ""
        ).strip()

        recomendacion.inversion_estimada = (
            request.POST.get("inversion_estimada") or 0
        )

        recomendacion.ganancia_estimada = (
            request.POST.get("ganancia_estimada") or 0
        )

        recomendacion.recomendacion = (
            request.POST.get("recomendacion") or ""
        ).strip()

        recomendacion.activa = (
            request.POST.get("activa") == "on"
        )

        recomendacion.save()

        # Actualizar kits
        kits_ids = request.POST.getlist("kits")

        recomendacion.kits.set(
            Kit.objects.filter(
                id__in=kits_ids,
                activo=True
            )
        )

        # Actualizar productos
        productos_ids = request.POST.getlist("productos")

        recomendacion.productos.set(
            Producto.objects.filter(
                id__in=productos_ids,
                activo=True
            )
        )

        messages.success(
            request,
            "Recomendación actualizada correctamente."
        )

        return redirect(
            "dashboard_recomendaciones"
        )

    contexto = {

        "recomendacion": recomendacion,

        "kits": (
            Kit.objects
            .filter(activo=True)
            .order_by("nombre")
        ),

        "productos": (
            Producto.objects
            .filter(activo=True)
            .order_by("nombre")
        ),

    }

    return render(
        request,
        "core/editar_recomendacion.html",
        contexto
    )


# =========================
# ELIMINAR RECOMENDACIÓN
# =========================

@login_required
@admin_required
@require_POST
def eliminar_recomendacion(request, recomendacion_id):

    recomendacion = get_object_or_404(
        RecomendacionEmprendimiento,
        id=recomendacion_id
    )

    recomendacion.delete()

    messages.success(
        request,
        "Recomendación eliminada correctamente."
    )

    return redirect(
        "dashboard_recomendaciones"
    )
# =========================
# RECOMENDACIONES CLIENTE
# =========================

def recomendaciones_emprendimiento_api(request):

    presupuesto = request.GET.get("presupuesto")
    producto = request.GET.get("producto")
    plataforma = request.GET.get("plataforma")

    if not presupuesto or not producto or not plataforma:
        return JsonResponse(
            {
                "ok": False,
                "mensaje": "Debes completar todas las preguntas."
            },
            status=400
        )

    try:
        presupuesto = float(presupuesto)
    except (ValueError, TypeError):

        return JsonResponse(
            {
                "ok": False,
                "mensaje": "El presupuesto no es válido."
            },
            status=400
        )

    # --------------------------------------------------
    # 1. BUSCAR RECOMENDACIONES QUE COINCIDAN
    # --------------------------------------------------

    recomendaciones = RecomendacionEmprendimiento.objects.filter(
        activa=True,
        producto_interes=producto,
        plataforma=plataforma,
        presupuesto_min__lte=presupuesto,
        presupuesto_max__gte=presupuesto
    ).prefetch_related(
        "kits",
        "productos"
    )

    # --------------------------------------------------
    # 2. SI NO HAY UNA EXACTA, BUSCAR UNA PARECIDA
    # --------------------------------------------------

    if not recomendaciones.exists():

        recomendaciones = RecomendacionEmprendimiento.objects.filter(
            activa=True,
            producto_interes=producto,
            plataforma=plataforma
        ).prefetch_related(
            "kits",
            "productos"
        )

    # --------------------------------------------------
    # 3. SI TODAVÍA NO HAY, BUSCAR SOLO POR PRODUCTO
    # --------------------------------------------------

    if not recomendaciones.exists():

        recomendaciones = RecomendacionEmprendimiento.objects.filter(
            activa=True,
            producto_interes=producto
        ).prefetch_related(
            "kits",
            "productos"
        )

    # --------------------------------------------------
    # 4. SI NO EXISTE NADA
    # --------------------------------------------------

    if not recomendaciones.exists():

        return JsonResponse(
            {
                "ok": False,
                "mensaje": (
                    "Todavía no tenemos una recomendación "
                    "para esta combinación. Prueba con otra opción."
                )
            },
            status=404
        )

    # Tomamos la primera recomendación encontrada
    recomendacion = recomendaciones.first()

    # --------------------------------------------------
    # NIVEL SEGÚN PRESUPUESTO
    # --------------------------------------------------

    if presupuesto <= 100000:
        nivel = "🌱 Principiante"

    elif presupuesto <= 300000:
        nivel = "✨ En crecimiento"

    else:
        nivel = "💎 Emprendedor avanzado"

    # --------------------------------------------------
    # PRODUCTOS RELACIONADOS
    # --------------------------------------------------

    productos = []

    for producto_relacionado in recomendacion.productos.all():

        productos.append({
            "nombre": producto_relacionado.nombre
        })

    # --------------------------------------------------
    # KITS RELACIONADOS
    # --------------------------------------------------

    kits = []

    for kit in recomendacion.kits.all():

        kits.append({
            "nombre": str(kit)
        })

    # --------------------------------------------------
    # RESPUESTA
    # --------------------------------------------------

    return JsonResponse(
        {
            "ok": True,

            "recomendacion": {
                "id": recomendacion.id,
                "nombre": recomendacion.nombre,

                "producto": dict(
                    RecomendacionEmprendimiento.PRODUCTOS_INTERES
                ).get(
                    recomendacion.producto_interes,
                    recomendacion.producto_interes
                ),

                "plataforma": dict(
                    RecomendacionEmprendimiento.PLATAFORMAS
                ).get(
                    recomendacion.plataforma,
                    recomendacion.plataforma
                ),

                "presupuesto_min": float(
                    recomendacion.presupuesto_min
                ),

                "presupuesto_max": float(
                    recomendacion.presupuesto_max
                ),

                "inversion": float(
                    recomendacion.inversion_estimada
                ),

                "ganancia": float(
                    recomendacion.ganancia_estimada
                ),

                "roi": float(
                    recomendacion.roi
                ),

                "nivel": nivel,

                "texto": recomendacion.recomendacion,

                "productos": productos,

                "kits": kits
            }
        }
    )