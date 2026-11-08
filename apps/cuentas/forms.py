from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm

from .roles import ROL_ADMIN, ROL_ASESOR, administradores_activos, asignar_rol, rol_de

User = get_user_model()

OPCIONES_ROL = [(ROL_ASESOR, "Asesor"), (ROL_ADMIN, "Administrador")]


class AccesibleFormMixin:
    """Tras validar, enlaza cada campo con su error para los lectores de pantalla."""

    def full_clean(self):
        super().full_clean()
        for nombre in self.errors:
            if nombre in self.fields:  # los errores generales no pertenecen a un campo
                atributos = self.fields[nombre].widget.attrs
                atributos["aria-invalid"] = "true"
                atributos["aria-describedby"] = f"error-{nombre}"


class LoginForm(AuthenticationForm):
    """El mensaje no revela si falló el usuario, la contraseña o si la cuenta está inactiva."""

    error_messages = {
        "invalid_login": "Usuario o contraseña incorrectos. Revise e intente de nuevo.",
        "inactive": "Usuario o contraseña incorrectos. Revise e intente de nuevo.",
    }


class UsuarioCrearForm(AccesibleFormMixin, UserCreationForm):
    rol = forms.ChoiceField(choices=OPCIONES_ROL, initial=ROL_ASESOR, label="Rol")

    class Meta:
        model = User
        fields = ("username", "first_name", "last_name", "email")
        labels = {
            "username": "Usuario",
            "first_name": "Nombre",
            "last_name": "Apellido",
            "email": "Correo",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for campo in ("first_name", "email"):
            self.fields[campo].required = True
        self.fields["password1"].label = "Contraseña"
        self.fields["password2"].label = "Repita la contraseña"

    def save(self, commit=True):
        usuario = super().save(commit=commit)
        if commit:
            asignar_rol(usuario, self.cleaned_data["rol"])
        return usuario


class UsuarioEditarForm(AccesibleFormMixin, forms.ModelForm):
    rol = forms.ChoiceField(choices=OPCIONES_ROL, label="Rol")

    class Meta:
        model = User
        fields = ("first_name", "last_name", "email", "is_active")
        labels = {
            "first_name": "Nombre",
            "last_name": "Apellido",
            "email": "Correo",
            "is_active": "Activo",
        }

    def __init__(self, *args, editor=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.editor = editor
        self.fields["first_name"].required = True
        self.fields["email"].required = True
        self.fields["rol"].initial = rol_de(self.instance) or ROL_ASESOR

    def clean(self):
        datos = super().clean()
        usuario = self.instance
        sigue_activo = datos.get("is_active", usuario.is_active)
        sigue_admin = datos.get("rol") == ROL_ADMIN or usuario.is_superuser
        if self.editor is not None and usuario.pk == self.editor.pk:
            if not sigue_activo:
                raise forms.ValidationError("No puede desactivar su propia cuenta.")
            if not sigue_admin:
                raise forms.ValidationError("No puede quitarse a sí mismo el rol de Administrador.")
        pierde_admin = usuario.is_active and rol_de(usuario) == ROL_ADMIN and not (
            sigue_activo and sigue_admin
        )
        if pierde_admin and not administradores_activos().exclude(pk=usuario.pk).exists():
            raise forms.ValidationError("Debe quedar al menos un administrador activo.")
        return datos

    def save(self, commit=True):
        usuario = super().save(commit=commit)
        if commit:
            asignar_rol(usuario, self.cleaned_data["rol"])
        return usuario
