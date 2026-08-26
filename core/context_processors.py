from django.db.models import Q
from .models import Contacto
from .models import Carrito

def notificaciones_dashboard(request):

    mensajes_nuevos = Contacto.objects.filter(
        Q(leido=False, archivado=False) |
        Q(
            respuesta_cliente_leida=False,
            respuesta_cliente__gt=""
        )
    ).count()

    return {
        "mensajes_nuevos": mensajes_nuevos
    }



def carrito_context(request):

    cantidad_carrito = 0

    if request.user.is_authenticated:

        carrito = (
            Carrito.objects
            .filter(usuario=request.user)
            .first()
        )

        if carrito:
            cantidad_carrito = carrito.cantidad_total

    return {
        "cantidad_carrito": cantidad_carrito
    }