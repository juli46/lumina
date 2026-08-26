from django import forms
from .models import Usuario
from .models import Direccion
from .models import Producto, Variante, ProductoImagen, ProductoVideo


# =========================
# REGISTRO
# =========================
class RegistroForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput)
    password2 = forms.CharField(widget=forms.PasswordInput)

    class Meta:
        model = Usuario
        fields = ['username', 'email', 'password']

    def clean(self):
        cleaned_data = super().clean()
        return cleaned_data

    def clean_email(self):
        email = self.cleaned_data.get("email")

        if email and Usuario.objects.filter(email=email).exists():
            raise forms.ValidationError("Este correo ya está registrado.")

        return email


# =========================
# EDITAR PERFIL
# =========================
class EditarPerfilForm(forms.ModelForm):

    class Meta:
        model = Usuario
        fields = [
            'username',
            'email',
            'telefono',
            'foto'
        ]

 #========================
# DIRECCION
 #========================
class DireccionForm(forms.ModelForm):

    class Meta:
        model = Direccion
        exclude = ["usuario"]

        widgets = {
            "nombre_receptor": forms.TextInput(attrs={"class": "input"}),
            "telefono": forms.TextInput(attrs={"class": "input"}),
            "direccion": forms.TextInput(attrs={"class": "input"}),
            "codigo_postal": forms.TextInput(attrs={"class": "input"}),
        }

#========================
# Cambiar contraseña
#========================
class CambiarPasswordForm(forms.Form):
    password_actual = forms.CharField(widget=forms.PasswordInput)
    password_nueva = forms.CharField(widget=forms.PasswordInput)
    password_confirmar = forms.CharField(widget=forms.PasswordInput)
    
    
class ProductoForm(forms.ModelForm):

    class Meta:
        model = Producto

        fields = [
                "nombre",
                "categoria",
                "marca",
                "coleccion",
                "descripcion",
                "precio_base",
                "activo",
            ]

        widgets = {
            "descripcion": forms.Textarea(
                attrs={
                    "rows":5,
                    "placeholder":"Descripción del producto"
                }
            )
        }


class VarianteForm(forms.ModelForm):

    class Meta:
        model = Variante

        fields = [
            "nombre_tono",
            "codigo_tono",
            "sku",
            "stock",
        ]

class ProductoImagenForm(forms.ModelForm):

    class Meta:
        model = ProductoImagen
        fields = [
            "imagen",
            "principal"
        ]


class ProductoVideoForm(forms.ModelForm):

    class Meta:
        model = ProductoVideo
        fields = [
            "video",
            "titulo"
        ]
from .models import Kit

class KitForm(forms.ModelForm):

    class Meta:

        model = Kit

        fields = [
            "nombre",
            "slug",
            "descripcion",
            "imagen",
            "categoria",
            "precio_personalizado",
            "activo",
            "destacado"
        ]
