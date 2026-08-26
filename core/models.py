from django.db import models
from django.contrib.auth.models import AbstractUser
from ckeditor_uploader.fields import RichTextUploadingField
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from decimal import Decimal, ROUND_CEILING


# =========================
# USUARIO
# =========================
class Usuario(AbstractUser):
    ROL_CHOICES = [
        ("usuario", "Usuario"),
        ("admin", "Admin"),
    ]

    rol = models.CharField(max_length=20, choices=ROL_CHOICES, default="usuario")
    telefono = models.CharField(max_length=20, blank=True, null=True)
    foto = models.ImageField(upload_to="usuarios/", blank=True, null=True)

    estado = models.CharField(
        max_length=20,
        choices=[
            ('activo', 'Activo'),
            ('inactivo', 'Inactivo')
        ],
        default='activo'
    )

    def es_admin(self):
        return self.rol == "admin"


# =========================
# DIRECCIONES
# =========================
class Direccion(models.Model):
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name="direcciones")

    nombre_receptor = models.CharField(max_length=100)
    telefono = models.CharField(max_length=20)

    direccion = models.TextField()
    ciudad = models.CharField(max_length=100)
    departamento = models.CharField(max_length=100)
    codigo_postal = models.CharField(max_length=20, blank=True, null=True)

    principal = models.BooleanField(default=False)


# =========================
# CATEGORIAS
# =========================

class Categoria(models.Model):

    nombre = models.CharField(
        max_length=100
    )

    def __str__(self):
        return self.nombre

# =========================
# MARCAS
# =========================

class Marca(models.Model):

    nombre = models.CharField(
        max_length=100
    )

    activa = models.BooleanField(
        default=True
    )

    def __str__(self):
        return self.nombre


# =========================
# COLECCIONES
# =========================

class Coleccion(models.Model):

    marca = models.ForeignKey(
        Marca,
        on_delete=models.CASCADE,
        related_name="colecciones"
    )

    nombre = models.CharField(
        max_length=100
    )

    activa = models.BooleanField(
        default=True
    )

    class Meta:
        unique_together = (
            "marca",
            "nombre"
        )

    def __str__(self):
        return f"{self.marca.nombre} - {self.nombre}"

# =========================
# PRODUCTOS
# =========================

class Producto(models.Model):

    categoria = models.ForeignKey(
        Categoria,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    marca = models.ForeignKey(
        Marca,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    coleccion = models.ForeignKey(
        Coleccion,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    nombre = models.CharField(
        max_length=200
    )

    slug = models.SlugField(
        unique=True
    )

    descripcion = models.TextField()

    info_extra = models.TextField(
        blank=True,
        null=True,
        help_text="Información adicional del producto (composición, modo de uso, cuidados, etc.)"
    )

    activo = models.BooleanField(
        default=True
    )

    precio_base = models.DecimalField(
        max_digits=12,
        decimal_places=2
    )

    costo_base = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        help_text="Costo real del producto antes de aplicar margen de rentabilidad."
    )

    etiquetas = models.ManyToManyField(
        "Etiqueta",
        blank=True,
        related_name="productos"
    )

    fecha_creacion = models.DateTimeField(
        auto_now_add=True
    )

    def calcular_precio_con_margen(self):

        return self.costo_base / Decimal("0.70")

    def aproximar_precio(self, precio):

        return (precio / Decimal("100")).to_integral_value(
            rounding=ROUND_CEILING
        ) * Decimal("100")

    @property
    def margen_rentabilidad(self):

        return Decimal("30")

    def save(self, *args, **kwargs):

        if self.costo_base and self.costo_base > 0:
            self.precio_base = self.aproximar_precio(
                self.calcular_precio_con_margen(),
            )

            update_fields = kwargs.get("update_fields")

            if update_fields and "costo_base" in update_fields:
                kwargs["update_fields"] = set(update_fields) | {"precio_base"}

        super().save(*args, **kwargs)

    @property
    def precio_100(self):
        return self.aproximar_precio(
            self.costo_base / Decimal("0.80"),
        )

    @property
    def precio_500(self):
        return self.aproximar_precio(
            self.costo_base / Decimal("0.85"),
        )

    @property
    def precio_1200(self):
        return self.aproximar_precio(
            self.costo_base / Decimal("0.90"),
        )

    def __str__(self):
        return self.nombre

# =========================
# VARIANTES
# =========================

class Variante(models.Model):

    producto = models.ForeignKey(
        Producto,
        on_delete=models.CASCADE,
        related_name="variantes"
    )

    nombre_tono = models.CharField(
        max_length=100,
        verbose_name="Nombre del tono",
        blank=True,
        null=True
    )

    codigo_tono = models.CharField(
        max_length=50,
        blank=True,
        null=True
    )

    sku = models.CharField(
        max_length=50
    )

    stock = models.PositiveIntegerField(
        default=0
    )

    def __str__(self):
        return f"{self.producto.nombre} - {self.nombre_tono}"


class NivelPrecio(models.Model):

    nombre = models.CharField(
        max_length=100
    )

    monto_minimo = models.DecimalField(
        max_digits=12,
        decimal_places=2
    )

    descuento = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        help_text="Porcentaje de descuento"
    )

    activo = models.BooleanField(
        default=True
    )

    class Meta:
        ordering = ["monto_minimo"]

    def __str__(self):
        return (
            f"{self.nombre} "
            f"({self.descuento}%)"
        )

# =========================
# IMAGENES PRODUCTO
# =========================

class ProductoImagen(models.Model):

    producto = models.ForeignKey(
        Producto,
        on_delete=models.CASCADE,
        related_name="imagenes"
    )

    imagen = models.ImageField(
        upload_to="productos/"
    )

    principal = models.BooleanField(
        default=False
    )

    def __str__(self):
        return self.producto.nombre


# =========================
# VIDEOS PRODUCTO
# =========================

class ProductoVideo(models.Model):

    producto = models.ForeignKey(
        Producto,
        on_delete=models.CASCADE,
        related_name="videos"
    )

    video = models.FileField(
        upload_to="productos/videos/"
    )

    titulo = models.CharField(
        max_length=150,
        blank=True
    )

    def __str__(self):
        return self.producto.nombre

# =========================
# RESEÑAS
# =========================
class Resena(models.Model):
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE)
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE)

    rating = models.IntegerField()
    comentario = models.TextField()


# =========================
# BLOG
# =========================
class BlogPost(models.Model):
    titulo = models.CharField(max_length=200)
    resumen = models.CharField(max_length=250)

    portada = models.ImageField(
        upload_to='blog/portadas/',
        blank=True,
        null=True
    )

    publicado = models.BooleanField(default=False)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.titulo


class BlogSeccion(models.Model):

    blog = models.ForeignKey(
        BlogPost,
        on_delete=models.CASCADE,
        related_name='secciones'
    )

    subtitulo = models.CharField(
        max_length=200,
        blank=True
    )

    contenido = models.TextField()

    imagen = models.ImageField(
        upload_to='blog/contenido/',
        blank=True,
        null=True
    )

    orden = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"{self.blog.titulo} - Sección {self.orden}"

# =========================
# GALERIA
# =========================

class Galeria(models.Model):

    titulo = models.CharField(max_length=150)

    categoria = models.CharField(max_length=100)

    descripcion = models.TextField()

    tags = models.CharField(
        max_length=255,
        blank=True,
        default=""
    )

    imagen = models.ImageField(
        upload_to="galeria/"
    )

    fecha_creacion = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return self.titulo

# =========================
# TEST
# =========================

class Test(models.Model):
    titulo = models.CharField(max_length=100)
    activo = models.BooleanField(default=True)
    categoria = models.CharField(max_length=100)
    descripcion = models.TextField()
    imagen = models.ImageField(upload_to='tests/')
    fecha = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.titulo


class Resultado(models.Model):
    test = models.ForeignKey(
        Test,
        on_delete=models.CASCADE,
        related_name='resultados'
    )

    nombre = models.CharField(max_length=100)
    descripcion = models.TextField()

    imagen = models.ImageField(
        upload_to='resultados/'
    )

    def __str__(self):
        return self.nombre


class Pregunta(models.Model):
    test = models.ForeignKey(
        Test,
        on_delete=models.CASCADE,
        related_name='preguntas'
    )

    texto = models.CharField(
        max_length=255
    )

    def __str__(self):
        return self.texto


class Opcion(models.Model):
    pregunta = models.ForeignKey(
        Pregunta,
        on_delete=models.CASCADE,
        related_name='opciones'
    )

    texto = models.CharField(
        max_length=255
    )

    resultado = models.ForeignKey(
        Resultado,
        on_delete=models.CASCADE
    )

    def __str__(self):
        return self.texto


class ResultadoUsuario(models.Model):
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="resultados_test"
    )

    test = models.ForeignKey(
        Test,
        on_delete=models.CASCADE,
        related_name="resultados_usuario"
    )

    resultado = models.ForeignKey(
        Resultado,
        on_delete=models.CASCADE,
        related_name="usuarios_resultado"
    )

    fecha = models.DateTimeField(auto_now_add=True)
    actualizado = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["usuario", "test"],
                name="resultado_unico_por_usuario_test"
            )
        ]
        ordering = ["-actualizado"]

    def __str__(self):
        return f"{self.usuario.username} - {self.test.titulo}: {self.resultado.nombre}"


# =========================
# CONTACTO
# =========================

class Contacto(models.Model):

    nombre = models.CharField(max_length=150)

    correo = models.EmailField()

    asunto = models.CharField(max_length=200)

    mensaje = models.TextField()

    respuesta = models.TextField(
        blank=True
    )

    leido = models.BooleanField(default=False)

    respondido = models.BooleanField(default=False)

    fecha = models.DateTimeField(auto_now_add=True)

    fecha_respuesta = models.DateTimeField(
        null=True,
        blank=True
    )

    # =========================
    # GMAIL API
    # =========================

    gmail_message_id = models.CharField(
        max_length=300,
        blank=True,
        null=True
    )

    gmail_thread_id = models.CharField(
        max_length=255,
        blank=True,
        null=True
    )

    respuesta_cliente = models.TextField(
        blank=True
    )

    fecha_cliente = models.DateTimeField(
        null=True,
        blank=True
    )

    archivado = models.BooleanField(default=False)

    respuesta_cliente_leida = models.BooleanField(
        default=False
    )

    def __str__(self):
        return self.asunto


# ================================
# NOTAS
# ================================

class NotaAdmin(models.Model):

    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notas"
    )

    texto = models.CharField(
        max_length=255
    )

    completada = models.BooleanField(
        default=False
    )

    fecha_limite = models.DateField(
        null=True,
        blank=True
    )

    fecha_creacion = models.DateTimeField(
        auto_now_add=True
    )

    fecha_actualizacion = models.DateTimeField(
        auto_now=True
    )

    class Meta:
        ordering = ["completada", "-fecha_creacion"]
        verbose_name = "Nota"
        verbose_name_plural = "Notas"

    def __str__(self):
        return self.texto


# ================================
# RECORDATORIOS
# ================================

class Recordatorio(models.Model):

    PRIORIDADES = [
        ("baja", "Baja"),
        ("media", "Media"),
        ("alta", "Alta"),
    ]

    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="recordatorios"
    )

    titulo = models.CharField(
        max_length=150
    )

    descripcion = models.TextField(
        blank=True
    )

    fecha = models.DateField()

    prioridad = models.CharField(
        max_length=10,
        choices=PRIORIDADES,
        default="media"
    )

    completado = models.BooleanField(
        default=False
    )

    fecha_creacion = models.DateTimeField(
        auto_now_add=True
    )

    fecha_actualizacion = models.DateTimeField(
        auto_now=True
    )

    class Meta:
        ordering = ["fecha"]
        verbose_name = "Recordatorio"
        verbose_name_plural = "Recordatorios"

    def __str__(self):
        return self.titulo


# ================================
# CALENDARIO LÚMINA
# ================================

class EventoCalendario(models.Model):

    TIPOS = [
        ("contenido", "Contenido"),
        ("pedido", "Pedido"),
        ("reunion", "Reunión"),
        ("otro", "Otro"),
    ]

    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="eventos"
    )

    titulo = models.CharField(
        max_length=150
    )

    descripcion = models.TextField(
        blank=True,
        null=True
    )

    fecha = models.DateField()

    hora = models.TimeField(
        blank=True,
        null=True
    )

    tipo = models.CharField(
        max_length=30,
        choices=TIPOS,
        default="otro"
    )

    completado = models.BooleanField(
        default=False
    )

    creado = models.DateTimeField(
        auto_now_add=True
    )

    actualizado = models.DateTimeField(
        auto_now=True
    )

    class Meta:
        ordering = ["fecha", "hora"]
        verbose_name = "Evento"
        verbose_name_plural = "Eventos"

    def __str__(self):
        return self.titulo

    @property
    def color(self):

        colores = {
            "contenido": "#df6d86",
            "pedido": "#35c76e",
            "reunion": "#4b88ff",
            "otro": "#f4a62a",
        }

        return colores.get(self.tipo, "#df6d86")


# ================================
# IDEAS DE CONTENIDO
# ================================

class IdeaContenido(models.Model):

    CATEGORIAS = [
        ("galeria", "Galeria"),
        ("post", "Post"),
        ("historia", "Historia"),
        ("blog", "Blog"),
        ("otro", "Otro"),
    ]

    ESTADOS = [
        ("pendiente", "Pendiente"),
        ("proceso", "En proceso"),
        ("publicada", "Publicada"),
    ]

    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="ideas"
    )

    titulo = models.CharField(
        max_length=150
    )

    descripcion = models.TextField(
        blank=True
    )

    categoria = models.CharField(
        max_length=30,
        choices=CATEGORIAS,
        default="post"
    )

    estado = models.CharField(
        max_length=20,
        choices=ESTADOS,
        default="pendiente"
    )

    fecha_publicacion = models.DateField(
        null=True,
        blank=True
    )

    creada = models.DateTimeField(
        auto_now_add=True
    )

    actualizada = models.DateTimeField(
        auto_now=True
    )

    class Meta:
        ordering = ["estado", "-creada"]
        verbose_name = "Idea de contenido"
        verbose_name_plural = "Ideas de contenido"

    def __str__(self):
        return self.titulo


class PostIt(models.Model):

    COLOR_CHOICES = [
        ("rosa", "Rosa"),
        ("amarillo", "Amarillo"),
        ("lila", "Lila"),
        ("azul", "Azul"),
    ]

    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="postits",
        null=True,
        blank=True
    )

    contenido = models.TextField()

    color = models.CharField(
        max_length=20,
        choices=COLOR_CHOICES,
        default="rosa"
    )

    fecha_creacion = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return self.contenido[:40]


class Etiqueta(models.Model):

    nombre = models.CharField(
        max_length=100,
        unique=True
    )

    def __str__(self):
        return self.nombre

# =========================
# KITS
# =========================

# =========================
# KITS
# =========================

class Kit(models.Model):

    nombre = models.CharField(
        max_length=200
    )

    slug = models.SlugField(
        unique=True
    )

    sku = models.CharField(
        max_length=50,
        unique=True,
        blank=True,
        null=True,
        help_text="Código interno del kit. Si se deja vacío, se genera automáticamente."
    )

    stock = models.PositiveIntegerField(
        default=0,
        help_text="Unidades disponibles de este kit."
    )

    descripcion = models.TextField()

    imagen = models.ImageField(
        upload_to="kits/",
        blank=True,
        null=True
    )

    categoria = models.ForeignKey(
        Categoria,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="kits"
    )

    activo = models.BooleanField(
        default=True
    )

    destacado = models.BooleanField(
        default=False
    )

    precio_personalizado = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        blank=True,
        null=True,
        help_text="Campo legado. Usa descuento_personalizado para calcular el precio final."
    )

    descuento_personalizado = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        validators=[
            MinValueValidator(Decimal("0")),
            MaxValueValidator(Decimal("100")),
        ],
        help_text="Porcentaje de descuento aplicado al precio normal del kit."
    )

    fecha_creacion = models.DateTimeField(
        auto_now_add=True
    )

    # =====================================================
    # RECOMENDACIONES DEL TEST DE EMPRENDIMIENTO
    # =====================================================

    recomendar_test = models.BooleanField(
        default=False,
        help_text=(
            "Si está activo, este kit podrá aparecer "
            "en las recomendaciones del test de emprendimiento."
        )
    )

    inversion_minima = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        help_text="Inversión mínima recomendada para este kit."
    )

    inversion_maxima = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        help_text="Inversión máxima recomendada para este kit."
    )

    NIVEL_CHOICES = [
        ("principiante", "Principiante"),
        ("intermedio", "Intermedio"),
        ("avanzado", "Avanzado"),
    ]

    nivel_recomendado = models.CharField(
        max_length=20,
        choices=NIVEL_CHOICES,
        blank=True,
        default="",
        help_text="Nivel de emprendedor para el que se recomienda este kit."
    )

    PLATAFORMA_CHOICES = [
        ("tiktok", "TikTok"),
        ("instagram", "Instagram"),
        ("whatsapp", "WhatsApp"),
        ("todas", "Todas"),
    ]

    plataforma_recomendada = models.CharField(
        max_length=20,
        choices=PLATAFORMA_CHOICES,
        blank=True,
        default="",
        help_text="Plataforma donde se recomienda vender este kit."
    )

    tipo_negocio = models.CharField(
        max_length=100,
        blank=True,
        default="",
        help_text=(
            "Tipo de negocio o productos. "
            "Ej: Gloss, Skincare, Pestañas, Kits beauty."
        )
    )

    recomendacion_texto = models.TextField(
        blank=True,
        default="",
        help_text=(
            "Mensaje que verá el usuario cuando este kit "
            "sea recomendado por el test."
        )
    )

    # =====================================================
    # PRODUCTOS DEL KIT
    # =====================================================

    productos = models.ManyToManyField(
        Producto,
        through="KitProducto",
        related_name="kits"
    )

    # =====================================================
    # PRECIOS
    # =====================================================

    @property
    def precio_normal(self):
        """
        Suma de los precios de cada producto agregado,
        teniendo en cuenta la cantidad.
        """

        return sum(
            (
                item.subtotal
                for item in self.items.all()
            ),
            Decimal("0")
        )

    @property
    def precio_final(self):
        """
        Precio que realmente paga el cliente.
        """

        if (
            self.descuento_personalizado
            and self.descuento_personalizado > 0
        ):

            descuento = (
                self.descuento_personalizado
                / Decimal("100")
            )

            return (
                self.precio_normal
                * (Decimal("1") - descuento)
            ).quantize(
                Decimal("0.01")
            )

        if self.precio_personalizado:

            return self.precio_personalizado

        return self.precio_normal

    @property
    def ahorro(self):
        """
        Cuánto dinero ahorra el cliente.
        """

        ahorro = (
            self.precio_normal
            - self.precio_final
        )

        return (
            ahorro
            if ahorro > 0
            else Decimal("0")
        )

    @property
    def ahorro_porcentaje(self):
        """
        Porcentaje de ahorro del kit.
        """

        if self.precio_normal > 0:

            return round(
                (
                    self.ahorro
                    / self.precio_normal
                ) * 100,
                1
            )

        return 0

    # =====================================================
    # REGLAS PARA EL TEST
    # =====================================================

    @property
    def tiene_rango_inversion(self):
        """
        Indica si el kit tiene configurado
        un rango válido de inversión.
        """

        return (
            self.inversion_minima is not None
            and self.inversion_maxima is not None
            and self.inversion_maxima >= self.inversion_minima
        )

    def coincide_inversion(self, inversion):
        """
        Comprueba si una inversión está dentro
        del rango configurado para el kit.
        """

        if not self.recomendar_test:
            return False

        if not self.tiene_rango_inversion:
            return False

        return (
            self.inversion_minima
            <= Decimal(str(inversion))
            <= self.inversion_maxima
        )

    def coincide_producto(self, producto):
        """
        Comprueba si el tipo de producto seleccionado
        coincide con el tipo de negocio configurado.
        """

        if not self.tipo_negocio:
            return True

        if not producto:
            return True

        return (
            self.tipo_negocio.lower()
            == str(producto).lower()
        )

    def coincide_plataforma(self, plataforma):
        """
        Comprueba si la plataforma seleccionada
        coincide con la recomendada.
        """

        if not self.plataforma_recomendada:
            return True

        if self.plataforma_recomendada == "todas":
            return True

        if not plataforma:
            return True

        return (
            self.plataforma_recomendada.lower()
            == str(plataforma).lower()
        )

    # =====================================================
    # REPRESENTACIÓN
    # =====================================================

    def __str__(self):
        return self.nombre

# =========================
# PRODUCTOS DEL KIT
# =========================

class KitProducto(models.Model):

    kit = models.ForeignKey(
        Kit,
        on_delete=models.CASCADE,
        related_name="items"
    )

    producto = models.ForeignKey(
        Producto,
        on_delete=models.CASCADE
    )

    variante = models.ForeignKey(
        Variante,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    cantidad = models.PositiveIntegerField(
        default=1
    )

    class Meta:
        unique_together = ("kit", "producto", "variante")

    @property
    def subtotal(self):
        return self.producto.precio_base * self.cantidad

    def __str__(self):
        if self.variante:
            return f"{self.kit.nombre} - {self.producto.nombre} ({self.variante.nombre_tono})"
        return f"{self.kit.nombre} - {self.producto.nombre}"

# =========================
# CARRITO
# =========================

class Carrito(models.Model):

    usuario = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="carrito"
    )

    creado = models.DateTimeField(
        auto_now_add=True
    )

    actualizado = models.DateTimeField(
        auto_now=True
    )

    @property
    def cantidad_total(self):
        return sum(
            item.cantidad
            for item in self.items.all()
        )

    @property
    def subtotal(self):
        return sum(
            (
                item.subtotal
                for item in self.items.all()
            ),
            Decimal("0")
        )

    def __str__(self):
        return f"Carrito de {self.usuario.username}"

class CarritoItem(models.Model):

    carrito = models.ForeignKey(
        Carrito,
        on_delete=models.CASCADE,
        related_name="items"
    )

    variante = models.ForeignKey(
        Variante,
        on_delete=models.CASCADE,
        related_name="items_carrito",
        null=True,
        blank=True
    )

    kit = models.ForeignKey(
        Kit,
        on_delete=models.CASCADE,
        related_name="items_carrito",
        null=True,
        blank=True
    )

    cantidad = models.PositiveIntegerField(
        default=1
    )

    agregado = models.DateTimeField(
        auto_now_add=True,
        null=True,
        blank=True
    )

    actualizado = models.DateTimeField(
        auto_now=True
    )

    class Meta:
            constraints = [
                models.UniqueConstraint(
                    fields=["carrito", "variante"],
                    condition=models.Q(variante__isnull=False),
                    name="carrito_variante_unica"
                ),
                models.UniqueConstraint(
                    fields=["carrito", "kit"],
                    condition=models.Q(kit__isnull=False),
                    name="carrito_kit_unica"
                ),
                models.CheckConstraint(
                    condition=(
                        models.Q(variante__isnull=False, kit__isnull=True) |
                        models.Q(variante__isnull=True, kit__isnull=False)
                    ),
                    name="carrito_item_variante_xor_kit"
                ),
            ]

    @property
    def es_kit(self):
        return self.kit_id is not None

    @property
    def nombre(self):
        return self.kit.nombre if self.es_kit else self.variante.producto.nombre

    @property
    def precio_unitario(self):
        # El kit ya trae su propio descuento; se usa tal cual, sin
        # aplicar el descuento por monto de compra.
        return self.kit.precio_final if self.es_kit else self.variante.producto.precio_base

    @property
    def stock_disponible(self):
        return self.kit.stock if self.es_kit else self.variante.stock

    @property
    def subtotal(self):
        return self.precio_unitario * self.cantidad

    def __str__(self):
        if self.es_kit:
            return f"Kit: {self.kit.nombre} x{self.cantidad}"
        return (
            f"{self.variante.producto.nombre} "
            f"- {self.variante.nombre_tono} "
            f"x{self.cantidad}"
        )


# =========================
# PEDIDOS
# =========================
class Pedido(models.Model):

    ESTADOS = [
        ("PENDIENTE", "Pendiente"),
        ("PAGADO", "Pagado"),
        ("RECHAZADO", "Rechazado"),
        ("CANCELADO", "Cancelado"),
    ]

    ESTADOS_ENVIO = [
        ("PREPARANDO", "Preparando pedido"),
        ("EN_PROCESO", "En proceso"),
        ("ENVIADO", "Enviado"),
        ("ENTREGADO", "Entregado"),
        ("FINALIZADO", "Finalizado"),
    ]

    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="pedidos"
    )

    referencia = models.CharField(
        max_length=100,
        unique=True
    )

    # Estado del PAGO
    estado = models.CharField(
        max_length=20,
        choices=ESTADOS,
        default="PENDIENTE"
    )

    # Estado del ENVÍO / logística
    estado_envio = models.CharField(
        max_length=20,
        choices=ESTADOS_ENVIO,
        default="PREPARANDO"
    )

    # ======================================================
    # PRECIOS
    # ======================================================

    subtotal_detalle = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0
    )

    subtotal = models.DecimalField(
        max_digits=12,
        decimal_places=2
    )

    descuento = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0
    )

    porcentaje_descuento = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0
    )

    nivel_precio = models.CharField(
        max_length=100,
        blank=True,
        default=""
    )

    # ======================================================
    # ENVÍO - COSTO
    # ======================================================

    costo_envio = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0
    )

    # ======================================================
    # ENVÍO - GUÍA
    # ======================================================

    transportadora = models.CharField(
        max_length=100,
        blank=True,
        default=""
    )

    numero_guia = models.CharField(
        max_length=100,
        blank=True,
        default=""
    )

    fecha_envio = models.DateTimeField(
        null=True,
        blank=True
    )

    # ======================================================
    # DIRECCIÓN DE ENTREGA (snapshot)
    # ======================================================

    direccion_nombre_receptor = models.CharField(
        max_length=100,
        blank=True,
        default=""
    )

    direccion_telefono = models.CharField(
        max_length=20,
        blank=True,
        default=""
    )

    direccion_texto = models.TextField(
        blank=True,
        default=""
    )

    direccion_ciudad = models.CharField(
        max_length=100,
        blank=True,
        default=""
    )

    direccion_departamento = models.CharField(
        max_length=100,
        blank=True,
        default=""
    )

    direccion_codigo_postal = models.CharField(
        max_length=20,
        blank=True,
        default=""
    )

    # ======================================================
    # TOTAL
    # ======================================================

    total = models.DecimalField(
        max_digits=12,
        decimal_places=2
    )

    creado = models.DateTimeField(
        auto_now_add=True
    )

    actualizado = models.DateTimeField(
        auto_now=True
    )

    def __str__(self):
        return f"Pedido {self.referencia}"


class PedidoItem(models.Model):

    pedido = models.ForeignKey(
        Pedido,
        on_delete=models.CASCADE,
        related_name="items"
    )

    variante = models.ForeignKey(
        Variante,
        on_delete=models.PROTECT,
        null=True,
        blank=True
    )

    kit = models.ForeignKey(
        Kit,
        on_delete=models.PROTECT,
        null=True,
        blank=True
    )

    producto_nombre = models.CharField(
        max_length=255
    )

    variante_nombre = models.CharField(
        max_length=255,
        blank=True,
        null=True
    )

    precio_unitario = models.DecimalField(
        max_digits=12,
        decimal_places=2
    )

    precio_original = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0
    )

    descuento = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0
    )

    cantidad = models.PositiveIntegerField()

    subtotal = models.DecimalField(
        max_digits=12,
        decimal_places=2
    )

    def __str__(self):
        return f"{self.producto_nombre} x{self.cantidad}"


class Pago(models.Model):

    ESTADOS = [
        ("PENDIENTE", "Pendiente"),
        ("APROBADO", "Aprobado"),
        ("RECHAZADO", "Rechazado"),
        ("ERROR", "Error"),
    ]

    pedido = models.OneToOneField(
        Pedido,
        on_delete=models.CASCADE,
        related_name="pago"
    )

    referencia_wompi = models.CharField(
        max_length=255,
        blank=True,
        null=True
    )

    monto = models.DecimalField(
        max_digits=12,
        decimal_places=2
    )

    estado = models.CharField(
        max_length=20,
        choices=ESTADOS,
        default="PENDIENTE"
    )

    metodo_pago = models.CharField(
        max_length=100,
        blank=True,
        null=True
    )

    transaccion_id = models.CharField(
        max_length=255,
        blank=True,
        null=True
    )

    creado = models.DateTimeField(
        auto_now_add=True
    )

    actualizado = models.DateTimeField(
        auto_now=True
    )

    def __str__(self):
        return f"Pago {self.pedido.referencia} - {self.estado}"
# =========================
# TONOS ELEGIDOS EN EL KIT
# =========================

class CarritoItemKitSeleccion(models.Model):
    """
    Guarda qué variante (tono) eligió el cliente para cada producto
    del kit, solo para los productos donde el admin NO fijó un tono
    (KitProducto.variante es null) y el producto tiene variantes.
    """

    carrito_item = models.ForeignKey(
        CarritoItem,
        on_delete=models.CASCADE,
        related_name="selecciones_kit"
    )

    kit_producto = models.ForeignKey(
        KitProducto,
        on_delete=models.CASCADE,
        related_name="selecciones_carrito"
    )

    variante = models.ForeignKey(
        Variante,
        on_delete=models.PROTECT
    )

    class Meta:
        unique_together = ("carrito_item", "kit_producto")

    def __str__(self):
        return (
            f"{self.carrito_item} - "
            f"{self.kit_producto.producto.nombre}: "
            f"{self.variante.nombre_tono}"
        )
# =========================
# TONOS ELEGIDOS EN EL KIT (PEDIDO)
# =========================

class PedidoItemKitSeleccion(models.Model):

    pedido_item = models.ForeignKey(
        PedidoItem,
        on_delete=models.CASCADE,
        related_name="selecciones_kit"
    )

    kit_producto = models.ForeignKey(
        KitProducto,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    variante = models.ForeignKey(
        Variante,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    producto_nombre = models.CharField(
        max_length=255
    )

    variante_nombre = models.CharField(
        max_length=255
    )

    def __str__(self):
        return (
            f"{self.pedido_item} - "
            f"{self.producto_nombre}: {self.variante_nombre}"
        )
# =========================
# RECOMENDACIONES DE EMPRENDIMIENTO
# =========================

class RecomendacionEmprendimiento(models.Model):

    PRODUCTOS_INTERES = [
        ("gloss", "Gloss"),
        ("skincare", "Skincare"),
        ("pestanas", "Pestañas"),
        ("kits", "Kits beauty"),
    ]

    PLATAFORMAS = [
        ("tiktok", "TikTok"),
        ("instagram", "Instagram"),
        ("whatsapp", "WhatsApp"),
    ]

    nombre = models.CharField(
        max_length=200
    )

    presupuesto_min = models.DecimalField(
        max_digits=12,
        decimal_places=2
    )

    presupuesto_max = models.DecimalField(
        max_digits=12,
        decimal_places=2
    )

    producto_interes = models.CharField(
        max_length=30,
        choices=PRODUCTOS_INTERES
    )

    plataforma = models.CharField(
        max_length=30,
        choices=PLATAFORMAS
    )

    kits = models.ManyToManyField(
        Kit,
        blank=True,
        related_name="recomendaciones_emprendimiento"
    )

    productos = models.ManyToManyField(
        Producto,
        blank=True,
        related_name="recomendaciones_emprendimiento"
    )

    inversion_estimada = models.DecimalField(
        max_digits=12,
        decimal_places=2
    )

    ganancia_estimada = models.DecimalField(
        max_digits=12,
        decimal_places=2
    )

    recomendacion = models.TextField()

    activa = models.BooleanField(
        default=True
    )

    fecha_creacion = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return self.nombre

    @property
    def roi(self):

        if self.inversion_estimada > 0:

            return round(
                (
                    self.ganancia_estimada /
                    self.inversion_estimada
                ) * 100,
                2
            )

        return 0