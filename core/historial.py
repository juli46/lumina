import threading

from django.apps import apps
from django.contrib.auth.signals import user_logged_in
from django.db.models.signals import post_delete, post_save

_local = threading.local()


class HistorialMiddleware:
    """Guarda la petición actual para saber qué admin hizo el cambio."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        _local.request = request
        try:
            return self.get_response(request)
        finally:
            _local.request = None


def _admin_actual():
    request = getattr(_local, "request", None)
    user = getattr(request, "user", None)
    if (
        user is not None
        and user.is_authenticated
        and getattr(user, "rol", None) == "admin"
    ):
        return user
    return None


def registrar(accion, entidad, descripcion, user=None):
    """Crea un registro en el historial. Nunca rompe la petición."""
    try:
        from .models import HistorialActividad

        user = user or _admin_actual()
        if not user:
            return

        HistorialActividad.objects.create(
            admin=user,
            admin_nombre=user.username,
            accion=accion,
            entidad=entidad,
            descripcion=descripcion[:255],
        )
    except Exception:
        pass


# Modelo -> nombre que se muestra en el historial
MODELOS_REGISTRADOS = {
    "Producto": "Producto",
    "Kit": "Kit",
    "Marca": "Marca",
    "Categoria": "Categoría",
    "Coleccion": "Colección",
    "Etiqueta": "Etiqueta",
    "BlogPost": "Blog",
    "Galeria": "Galería",
    "Test": "Test",
    "Proveedor": "Proveedor",
    "Pedido": "Pedido",
    "Usuario": "Usuario",
    "RecomendacionEmprendimiento": "Recomendación",
}


def _nombre(instance):
    try:
        return str(instance)
    except Exception:
        return f"#{instance.pk}"


def _on_save(sender, instance, created, **kwargs):
    update_fields = kwargs.get("update_fields")
    if update_fields and set(update_fields) == {"last_login"}:
        return

    etiqueta = MODELOS_REGISTRADOS[sender.__name__]
    if created:
        registrar("crear", etiqueta, f"Creó {etiqueta.lower()}: {_nombre(instance)}")
    else:
        registrar("editar", etiqueta, f"Editó {etiqueta.lower()}: {_nombre(instance)}")


def _on_delete(sender, instance, **kwargs):
    etiqueta = MODELOS_REGISTRADOS[sender.__name__]
    registrar("eliminar", etiqueta, f"Eliminó {etiqueta.lower()}: {_nombre(instance)}")


def _on_login(sender, request, user, **kwargs):
    if getattr(user, "rol", None) == "admin":
        registrar("otro", "Sesión", "Inició sesión", user=user)


def conectar_senales():
    for nombre in MODELOS_REGISTRADOS:
        modelo = apps.get_model("core", nombre)
        post_save.connect(_on_save, sender=modelo, dispatch_uid=f"hist_save_{nombre}")
        post_delete.connect(_on_delete, sender=modelo, dispatch_uid=f"hist_del_{nombre}")

    user_logged_in.connect(_on_login, dispatch_uid="hist_login")