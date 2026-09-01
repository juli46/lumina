
import requests

from django.core.files.base import ContentFile
from django.db import transaction

from allauth.socialaccount.adapter import DefaultSocialAccountAdapter

from .models import Usuario


class LuminaSocialAccountAdapter(DefaultSocialAccountAdapter):

    def pre_social_login(self, request, sociallogin):
        """
        Evita usuarios duplicados.

        Si el correo de Google ya existe en Lúmina:
        - reutiliza ese Usuario
        - conecta la cuenta de Google
        - intenta guardar la foto si todavía no tiene una.
        """

        if sociallogin.is_existing:
            return

        extra_data = sociallogin.account.extra_data or {}

        email = extra_data.get("email")

        if not email:
            return

        email = email.strip().lower()

        try:
            usuario = Usuario.objects.get(
                email__iexact=email
            )
        except Usuario.DoesNotExist:
            return

        # Conecta Google con el usuario existente.
        sociallogin.connect(
            request,
            usuario
        )

        # Guardamos datos que falten.
        self._actualizar_datos_google(
            usuario,
            extra_data
        )

    def save_user(self, request, sociallogin, form=None):
        """
        Crea un usuario nuevo desde Google y guarda
        sus datos y foto.
        """

        user = super().save_user(
            request,
            sociallogin,
            form
        )

        extra_data = sociallogin.account.extra_data or {}

        self._actualizar_datos_google(
            user,
            extra_data
        )

        return user

    @transaction.atomic
    def _actualizar_datos_google(self, user, extra_data):
        """
        Guarda información proveniente de Google.

        No reemplaza información que el usuario
        ya haya completado en Lúmina.
        """

        email = extra_data.get("email")
        nombre = extra_data.get("given_name")
        apellido = extra_data.get("family_name")
        foto_url = extra_data.get("picture")

        cambio = False

        # ==========================================
        # EMAIL
        # ==========================================

        if email and not user.email:
            user.email = email.strip().lower()
            cambio = True

        # ==========================================
        # NOMBRE
        # ==========================================

        if nombre and not user.first_name:
            user.first_name = nombre
            cambio = True

        # ==========================================
        # APELLIDO
        # ==========================================

        if apellido and not user.last_name:
            user.last_name = apellido
            cambio = True

        if cambio:
            user.save(
                update_fields=[
                    "email",
                    "first_name",
                    "last_name"
                ]
            )

        # ==========================================
        # FOTO
        # ==========================================

        if foto_url and not user.foto:

            try:

                respuesta = requests.get(
                    foto_url,
                    timeout=15,
                    headers={
                        "User-Agent": "Mozilla/5.0"
                    }
                )

                if respuesta.status_code == 200:

                    user.foto.save(
                        f"google_{user.pk}.jpg",
                        ContentFile(respuesta.content),
                        save=True
                    )

            except requests.RequestException:
                pass
