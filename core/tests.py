
from decimal import Decimal
from pathlib import Path

from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from django.test import SimpleTestCase, TestCase

from .models import (
    Categoria,
    Producto,
    Variante,
    Kit,
    KitProducto,
    Pedido,
    PedidoItem,
    Resena,
    recalcular_rating,
    usuario_compro_producto,
)


Usuario = get_user_model()


# =========================================================
# 1. PRUEBAS DEL JAVASCRIPT DE LOS TEST
# =========================================================

class TestFormJavaScriptTests(SimpleTestCase):

    def test_archivo_javascript_existe(self):
        ruta = (
            Path(__file__).resolve().parent
            / "static"
            / "js"
            / "test.js"
        )

        self.assertTrue(
            ruta.is_file(),
            f"No se encontró el archivo: {ruta}",
        )

    def test_script_contiene_selectores_de_resultado(self):
        ruta = (
            Path(__file__).resolve().parent
            / "static"
            / "js"
            / "test.js"
        )

        if not ruta.is_file():
            self.fail(f"No se encontró el archivo: {ruta}")

        contenido = ruta.read_text(encoding="utf-8")

        self.assertIn(
            'class="form-control resultado-select"',
            contenido,
        )

        self.assertIn(
            'name="resultado_${idPregunta}[]"',
            contenido,
        )


# =========================================================
# 2. PRUEBAS DE PRECIOS DE LOS PRODUCTOS
# =========================================================

class ProductoTests(TestCase):

    def crear_producto(self, nombre="Producto de prueba",
                       costo="6000.00", slug="producto-prueba"):

        return Producto.objects.create(
            nombre=nombre,
            slug=slug,
            descripcion="Producto creado para pruebas automatizadas.",
            costo_base=Decimal(costo),
            precio_base=Decimal("0.00"),
        )

    def test_calcula_precio_base_con_margen(self):
        producto = self.crear_producto()

        # 6.000 / 0,60 = 10.000
        self.assertEqual(
            producto.precio_base,
            Decimal("10000.00"),
        )

    def test_redondea_precio_hacia_arriba(self):
        producto = self.crear_producto(
            costo="6100.00",
            slug="producto-redondeo",
        )

        # 6.100 / 0,60 = 10.166,66...
        # Se aproxima al siguiente múltiplo de 100.
        self.assertEqual(
            producto.precio_base,
            Decimal("10200"),
        )

    def test_calcula_precios_por_nivel(self):
        producto = self.crear_producto()

        self.assertEqual(
            producto.precio_100,
            Decimal("8600"),
        )

        self.assertEqual(
            producto.precio_500,
            Decimal("8000"),
        )

        self.assertEqual(
            producto.precio_1200,
            Decimal("7500"),
        )

    def test_margen_de_rentabilidad(self):
        producto = self.crear_producto()

        self.assertEqual(
            producto.margen_rentabilidad,
            Decimal("40"),
        )

    def test_actualiza_precio_al_cambiar_costo(self):
        producto = self.crear_producto()

        producto.costo_base = Decimal("12000")
        producto.save()

        producto.refresh_from_db()

        self.assertEqual(
            producto.precio_base,
            Decimal("20000"),
        )


# =========================================================
# 3. PRUEBAS DE RESEÑAS Y CALIFICACIONES
# =========================================================

class ResenaTests(TestCase):

    def setUp(self):
        self.usuario1 = Usuario.objects.create_user(
            username="cliente_uno",
            password="ClavePrueba123!",
        )

        self.usuario2 = Usuario.objects.create_user(
            username="cliente_dos",
            password="ClavePrueba123!",
        )

        self.producto = Producto.objects.create(
            nombre="Crema de prueba",
            slug="crema-prueba",
            descripcion="Crema para probar las reseñas.",
            precio_base=Decimal("15000"),
            costo_base=Decimal("0"),
        )

    def crear_resena(
        self,
        usuario,
        calificacion,
        estado="aprobada",
        comentario="Buena experiencia",
    ):
        return Resena.objects.create(
            producto=self.producto,
            usuario=usuario,
            calificacion=calificacion,
            comentario=comentario,
            estado=estado,
        )

    def test_crea_resena_correctamente(self):
        resena = self.crear_resena(
            self.usuario1,
            5,
        )

        self.assertEqual(
            Resena.objects.filter(producto=self.producto).count(),
            1,
        )

        self.assertEqual(resena.calificacion, 5)
        self.assertEqual(resena.estado, "aprobada")

    def test_calificacion_debe_estar_entre_uno_y_cinco(self):
        # full_clean ejecuta también los validadores del modelo.
        resena = Resena(
            producto=self.producto,
            usuario=self.usuario1,
            calificacion=6,
        )

        from django.core.exceptions import ValidationError

        with self.assertRaises(ValidationError):
            resena.full_clean()

    def test_no_permite_dos_resenas_del_mismo_usuario_y_producto(self):
        self.crear_resena(self.usuario1, 5)

        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                self.crear_resena(self.usuario1, 4)

    def test_recalcula_promedio_solo_con_resenas_aprobadas(self):
        self.crear_resena(self.usuario1, 5)
        self.crear_resena(self.usuario2, 4)

        # Esta reseña no debe contar en el promedio.
        otro_usuario = Usuario.objects.create_user(
            username="cliente_tres",
            password="ClavePrueba123!",
        )

        self.crear_resena(
            otro_usuario,
            1,
            estado="rechazada",
        )

        recalcular_rating(self.producto.id)
        self.producto.refresh_from_db()

        self.assertEqual(
            self.producto.rating_promedio,
            Decimal("4.50"),
        )

        self.assertEqual(
            self.producto.rating_cantidad,
            2,
        )

    def test_recalcula_promedio_sin_resenas_aprobadas(self):
        self.crear_resena(
            self.usuario1,
            5,
            estado="rechazada",
        )

        recalcular_rating(self.producto.id)
        self.producto.refresh_from_db()

        self.assertEqual(
            self.producto.rating_promedio,
            Decimal("0.00"),
        )

        self.assertEqual(
            self.producto.rating_cantidad,
            0,
        )

    def test_eliminar_resena_permite_recalcular_promedio(self):
        resena = self.crear_resena(self.usuario1, 5)
        resena.delete()

        recalcular_rating(self.producto.id)
        self.producto.refresh_from_db()

        self.assertEqual(
            self.producto.rating_cantidad,
            0,
        )


# =========================================================
# 4. PRUEBAS DE COMPRAS VERIFICADAS
# =========================================================

class CompraVerificadaTests(TestCase):

    def setUp(self):
        self.usuario = Usuario.objects.create_user(
            username="comprador",
            password="ClavePrueba123!",
        )

        self.producto = Producto.objects.create(
            nombre="Labial de prueba",
            slug="labial-prueba",
            descripcion="Producto para comprobar compras.",
            precio_base=Decimal("12000"),
            costo_base=Decimal("0"),
        )

        self.variante = Variante.objects.create(
            producto=self.producto,
            nombre_tono="Rosa",
            codigo_tono="ROS01",
            sku="LAB-ROS-01",
            stock=10,
        )

    def crear_pedido(self, estado):
        pedido = Pedido.objects.create(
            usuario=self.usuario,
            referencia=f"PED-{estado}",
            estado=estado,
            subtotal=Decimal("12000"),
            total=Decimal("12000"),
        )

        PedidoItem.objects.create(
            pedido=pedido,
            variante=self.variante,
            producto_nombre=self.producto.nombre,
            variante_nombre="Rosa",
            precio_unitario=Decimal("12000"),
            precio_original=Decimal("12000"),
            descuento=Decimal("0"),
            cantidad=1,
            subtotal=Decimal("12000"),
        )

        return pedido

    def test_compra_pagada_habilita_resena(self):
        self.crear_pedido("PAGADO")

        self.assertTrue(
            usuario_compro_producto(
                self.usuario,
                self.producto,
            )
        )

    def test_pedido_pendiente_no_habilita_resena(self):
        self.crear_pedido("PENDIENTE")

        self.assertFalse(
            usuario_compro_producto(
                self.usuario,
                self.producto,
            )
        )

    def test_pedido_cancelado_no_habilita_resena(self):
        self.crear_pedido("CANCELADO")

        self.assertFalse(
            usuario_compro_producto(
                self.usuario,
                self.producto,
            )
        )

    def test_otro_usuario_no_puede_usar_compra_ajena(self):
        self.crear_pedido("PAGADO")

        otro_usuario = Usuario.objects.create_user(
            username="otra_persona",
            password="ClavePrueba123!",
        )

        self.assertFalse(
            usuario_compro_producto(
                otro_usuario,
                self.producto,
            )
        )


# =========================================================
# 5. PRUEBAS DE KITS Y RECOMENDACIONES
# =========================================================

class KitTests(TestCase):

    def setUp(self):
        self.producto = Producto.objects.create(
            nombre="Brillo de prueba",
            slug="brillo-prueba",
            descripcion="Producto de prueba para un kit.",
            precio_base=Decimal("10000"),
            costo_base=Decimal("0"),
        )

        self.kit = Kit.objects.create(
            nombre="Kit principiante",
            slug="kit-principiante-prueba",
            sku="KIT-TEST-001",
            descripcion="Kit creado para pruebas.",
            stock=5,
            descuento_personalizado=Decimal("10"),
            recomendar_test=True,
            inversion_minima=Decimal("100000"),
            inversion_maxima=Decimal("500000"),
            nivel_recomendado="principiante",
            plataforma_recomendada="instagram",
            tipo_negocio="Gloss",
        )

        KitProducto.objects.create(
            kit=self.kit,
            producto=self.producto,
            cantidad=2,
        )

    def test_calcula_precio_normal_del_kit(self):
        self.assertEqual(
            self.kit.precio_normal,
            Decimal("20000"),
        )

    def test_aplica_descuento_al_precio_final(self):
        self.assertEqual(
            self.kit.precio_final,
            Decimal("18000"),
        )

    def test_calcula_ahorro_del_kit(self):
        self.assertEqual(
            self.kit.ahorro,
            Decimal("2000"),
        )

        self.assertEqual(
            self.kit.ahorro_porcentaje,
            10.0,
        )

    def test_recomienda_kit_si_la_inversion_coincide(self):
        self.assertTrue(
            self.kit.coincide_inversion(Decimal("250000"))
        )

    def test_no_recomienda_kit_fuera_del_presupuesto(self):
        self.assertFalse(
            self.kit.coincide_inversion(Decimal("600000"))
        )

    def test_no_recomienda_kit_si_esta_desactivado(self):
        self.kit.recomendar_test = False

        self.assertFalse(
            self.kit.coincide_inversion(Decimal("250000"))
        )

    def test_coincide_tipo_de_producto(self):
        self.assertTrue(
            self.kit.coincide_producto("Gloss")
        )

        self.assertTrue(
            self.kit.coincide_producto("gloss")
        )

        self.assertFalse(
            self.kit.coincide_producto("Skincare")
        )

    def test_coincide_plataforma(self):
        self.assertTrue(
            self.kit.coincide_plataforma("instagram")
        )

        self.assertFalse(
            self.kit.coincide_plataforma("tiktok")
        )

    def test_plataforma_todas_acepta_cualquier_plataforma(self):
        self.kit.plataforma_recomendada = "todas"

        self.assertTrue(
            self.kit.coincide_plataforma("tiktok")
        )

import json
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase, RequestFactory
from django.db import IntegrityError, transaction

from core.models import (
    Producto,
    Variante,
    Pedido,
    PedidoItem,
    Resena,
)
from core import views


class PruebasAmpliadasResenas(TestCase):
    """
    Pruebas adicionales para las reseñas de Lúmina.
    No reemplaza las pruebas que ya existen en tests.py.
    """

    @classmethod
    def setUpTestData(cls):
        Usuario = get_user_model()

        cls.usuario = Usuario.objects.create_user(
            username="cliente_pruebas",
            email="cliente@pruebas.com",
            password="PruebaSegura123!",
            first_name="María",
            last_name="Pérez",
        )

        cls.otro_usuario = Usuario.objects.create_user(
            username="otro_cliente",
            email="otro@pruebas.com",
            password="PruebaSegura123!",
        )

        cls.admin = Usuario.objects.create_user(
            username="admin_pruebas",
            email="admin@pruebas.com",
            password="PruebaSegura123!",
            rol="admin",
        )

        # Ajusta estos campos si tu modelo Producto exige otros
        # campos obligatorios en tu versión del proyecto.
        cls.producto = Producto.objects.create(
            nombre="Labial de prueba",
            slug="labial-de-prueba",
            costo_base=Decimal("6000"),
            activo=True,
        )

        cls.variante = Variante.objects.create(
            producto=cls.producto,
            nombre_tono="Rosa",
            codigo_tono="ROS-01",
            sku="ROS-01-TEST",
            stock=10,
        )

    def setUp(self):
        self.factory = RequestFactory()

    def crear_pedido(self, usuario, estado="PAGADO"):
        pedido = Pedido.objects.create(
            usuario=usuario,
            referencia=f"REF-{usuario.pk}-{Pedido.objects.count()}",
            estado=estado,
            subtotal=Decimal("10000"),
            total=Decimal("10000"),
        )

        PedidoItem.objects.create(
            pedido=pedido,
            variante=self.variante,
            kit=None,
            producto_nombre=self.producto.nombre,
            variante_nombre="Rosa",
            precio_unitario=Decimal("10000"),
            precio_original=Decimal("10000"),
            descuento=Decimal("0"),
            cantidad=1,
            subtotal=Decimal("10000"),
        )

        return pedido

    def post_json(self, vista, usuario, *args, datos=None):
        request = self.factory.post(
            "/pruebas/",
            data=json.dumps(datos or {}),
            content_type="application/json",
        )
        request.user = usuario
        return vista(request, *args)

    # -------------------------------------------------
    # CREAR RESEÑAS
    # -------------------------------------------------

    def test_cliente_con_compra_pagada_puede_resenar(self):
        self.crear_pedido(self.usuario)

        response = self.post_json(
            views.crear_resena,
            self.usuario,
            self.producto.slug,
            datos={
                "calificacion": 5,
                "titulo": "Me encantó",
                "comentario": "Muy buen producto.",
            },
        )

        self.assertEqual(response.status_code, 201)

        resena = Resena.objects.get(
            producto=self.producto,
            usuario=self.usuario,
        )

        self.assertEqual(resena.calificacion, 5)
        self.assertEqual(resena.estado, "aprobada")
        self.assertTrue(resena.compra_verificada)
        self.assertEqual(resena.titulo, "Me encantó")

    def test_cliente_sin_compra_no_puede_resenar(self):
        response = self.post_json(
            views.crear_resena,
            self.usuario,
            self.producto.slug,
            datos={"calificacion": 5},
        )

        self.assertEqual(response.status_code, 403)
        self.assertFalse(
            Resena.objects.filter(usuario=self.usuario).exists()
        )

    def test_pedido_pendiente_no_permite_resenar(self):
        self.crear_pedido(self.usuario, estado="PENDIENTE")

        response = self.post_json(
            views.crear_resena,
            self.usuario,
            self.producto.slug,
            datos={"calificacion": 4},
        )

        self.assertEqual(response.status_code, 403)

    def test_calificacion_menor_que_uno_es_rechazada(self):
        self.crear_pedido(self.usuario)

        response = self.post_json(
            views.crear_resena,
            self.usuario,
            self.producto.slug,
            datos={"calificacion": 0},
        )

        self.assertEqual(response.status_code, 400)

    def test_calificacion_mayor_que_cinco_es_rechazada(self):
        self.crear_pedido(self.usuario)

        response = self.post_json(
            views.crear_resena,
            self.usuario,
            self.producto.slug,
            datos={"calificacion": 6},
        )

        self.assertEqual(response.status_code, 400)

    def test_calificacion_no_numerica_es_rechazada(self):
        self.crear_pedido(self.usuario)

        response = self.post_json(
            views.crear_resena,
            self.usuario,
            self.producto.slug,
            datos={"calificacion": "excelente"},
        )

        self.assertEqual(response.status_code, 400)

    def test_json_invalido_es_rechazado(self):
        self.crear_pedido(self.usuario)

        request = self.factory.post(
            "/pruebas/",
            data="{json incorrecto",
            content_type="application/json",
        )
        request.user = self.usuario

        response = views.crear_resena(
            request,
            self.producto.slug,
        )

        self.assertEqual(response.status_code, 400)

    def test_titulo_y_comentario_se_recortan(self):
        self.crear_pedido(self.usuario)

        response = self.post_json(
            views.crear_resena,
            self.usuario,
            self.producto.slug,
            datos={
                "calificacion": 4,
                # Los espacios van en los extremos para comprobar que se eliminan
                # antes de aplicar el límite máximo de caracteres.
                "titulo": "   " + ("T" * 130) + "   ",
                "comentario": "   " + ("C" * 2100) + "   ",
            },
        )

        self.assertEqual(response.status_code, 201)

        resena = Resena.objects.get(usuario=self.usuario)

        self.assertLessEqual(len(resena.titulo), 120)
        self.assertLessEqual(len(resena.comentario), 2000)
        self.assertEqual(resena.titulo, resena.titulo.strip())
        self.assertEqual(resena.comentario, resena.comentario.strip())
        self.assertEqual(resena.titulo, "T" * 120)
        self.assertEqual(resena.comentario, "C" * 2000)

    def test_editar_resena_actualiza_la_existente(self):
        self.crear_pedido(self.usuario)

        Resena.objects.create(
            producto=self.producto,
            usuario=self.usuario,
            calificacion=3,
            titulo="Título anterior",
            comentario="Comentario anterior",
            estado="aprobada",
            compra_verificada=True,
        )

        response = self.post_json(
            views.crear_resena,
            self.usuario,
            self.producto.slug,
            datos={
                "calificacion": 5,
                "titulo": "Nuevo título",
                "comentario": "Nuevo comentario",
            },
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(
            Resena.objects.filter(
                producto=self.producto,
                usuario=self.usuario,
            ).count(),
            1,
        )

        resena = Resena.objects.get(usuario=self.usuario)
        self.assertEqual(resena.calificacion, 5)
        self.assertEqual(resena.titulo, "Nuevo título")

    def test_editar_resena_rechazada_no_la_publica(self):
        self.crear_pedido(self.usuario)

        Resena.objects.create(
            producto=self.producto,
            usuario=self.usuario,
            calificacion=2,
            titulo="Reseña oculta",
            estado="rechazada",
            compra_verificada=True,
        )

        response = self.post_json(
            views.crear_resena,
            self.usuario,
            self.producto.slug,
            datos={
                "calificacion": 5,
                "titulo": "Intento de actualización",
            },
        )

        self.assertEqual(response.status_code, 201)

        resena = Resena.objects.get(usuario=self.usuario)
        self.assertEqual(resena.estado, "rechazada")
        self.assertEqual(resena.calificacion, 5)

    # -------------------------------------------------
    # VISUALIZACIÓN PÚBLICA
    # -------------------------------------------------

    def test_listado_publico_muestra_solo_aprobadas(self):
        Resena.objects.create(
            producto=self.producto,
            usuario=self.usuario,
            calificacion=5,
            titulo="Visible",
            estado="aprobada",
        )

        Resena.objects.create(
            producto=self.producto,
            usuario=self.otro_usuario,
            calificacion=1,
            titulo="Oculta",
            estado="rechazada",
        )

        request = self.factory.get("/pruebas/resenas/")
        response = views.resenas_producto(
            request,
            self.producto.slug,
        )

        self.assertEqual(response.status_code, 200)

        datos = json.loads(response.content)
        titulos = [r["titulo"] for r in datos["resenas"]]

        self.assertIn("Visible", titulos)
        self.assertNotIn("Oculta", titulos)

    def test_producto_inactivo_no_muestra_resenas(self):
        self.producto.activo = False
        self.producto.save()

        request = self.factory.get("/pruebas/resenas/")

        with self.assertRaises(Exception):
            views.resenas_producto(
                request,
                self.producto.slug,
            )

    def test_consulta_mi_resena_sin_iniciar_sesion(self):
        from django.contrib.auth.models import AnonymousUser

        request = self.factory.get("/pruebas/mi-resena/")
        request.user = AnonymousUser()

        response = views.mi_resena(
            request,
            self.producto.slug,
        )

        self.assertEqual(response.status_code, 200)

        datos = json.loads(response.content)
        self.assertFalse(datos["autenticado"])
        self.assertFalse(datos["puede_resenar"])
        self.assertIsNone(datos["resena"])

    # -------------------------------------------------
    # ELIMINACIÓN Y PERMISOS
    # -------------------------------------------------

    def test_usuario_puede_eliminar_su_resena(self):
        resena = Resena.objects.create(
            producto=self.producto,
            usuario=self.usuario,
            calificacion=4,
            estado="aprobada",
        )

        response = self.post_json(
            views.eliminar_resena,
            self.usuario,
            resena.pk,
        )

        self.assertEqual(response.status_code, 200)
        self.assertFalse(
            Resena.objects.filter(pk=resena.pk).exists()
        )

    def test_usuario_no_puede_eliminar_resena_ajena(self):
        resena = Resena.objects.create(
            producto=self.producto,
            usuario=self.otro_usuario,
            calificacion=4,
            estado="aprobada",
        )

        request = self.factory.post("/pruebas/eliminar/")
        request.user = self.usuario

        with self.assertRaises(Exception):
            views.eliminar_resena(request, resena.pk)

        self.assertTrue(
            Resena.objects.filter(pk=resena.pk).exists()
        )

    # -------------------------------------------------
    # MODERACIÓN ADMINISTRATIVA
    # -------------------------------------------------

    def test_admin_puede_listar_resenas_pendientes(self):
        Resena.objects.create(
            producto=self.producto,
            usuario=self.usuario,
            calificacion=4,
            estado="pendiente",
        )

        request = self.factory.get("/pruebas/admin-resenas/")
        request.user = self.admin

        response = views.admin_resenas(request)

        self.assertEqual(response.status_code, 200)

        datos = json.loads(response.content)
        self.assertEqual(len(datos["resenas"]), 1)
        self.assertEqual(datos["resenas"][0]["estado"], "pendiente")

    def test_admin_puede_aprobar_resena(self):
        resena = Resena.objects.create(
            producto=self.producto,
            usuario=self.usuario,
            calificacion=5,
            estado="rechazada",
        )

        response = self.post_json(
            views.moderar_resena,
            self.admin,
            resena.pk,
            datos={
                "estado": "aprobada",
                "respuesta_admin": "Gracias por tu opinión.",
            },
        )

        self.assertEqual(response.status_code, 200)

        resena.refresh_from_db()
        self.assertEqual(resena.estado, "aprobada")

    def test_estado_de_moderacion_invalido_es_rechazado(self):
        resena = Resena.objects.create(
            producto=self.producto,
            usuario=self.usuario,
            calificacion=4,
            estado="pendiente",
        )

        response = self.post_json(
            views.moderar_resena,
            self.admin,
            resena.pk,
            datos={"estado": "eliminada"},
        )

        self.assertEqual(response.status_code, 400)

        resena.refresh_from_db()
        self.assertEqual(resena.estado, "pendiente")

    def test_usuario_normal_no_puede_moderar(self):
        resena = Resena.objects.create(
            producto=self.producto,
            usuario=self.otro_usuario,
            calificacion=4,
            estado="pendiente",
        )

        request = self.factory.post(
            "/pruebas/admin/",
            data=json.dumps({"estado": "aprobada"}),
            content_type="application/json",
        )
        request.user = self.usuario

        response = views.moderar_resena(request, resena.pk)

        # La vista puede denegar el acceso con 403 o redirigir al usuario.
        # Un 200 indicaría que un usuario normal pudo acceder a la moderación.
        self.assertNotEqual(response.status_code, 200)

        resena.refresh_from_db()
        self.assertEqual(resena.estado, "pendiente")
