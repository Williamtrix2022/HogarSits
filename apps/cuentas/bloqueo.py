"""Límite de intentos fallidos de inicio de sesión: bloqueo temporal por usuario + IP."""

from datetime import timedelta

from django.utils import timezone

from .models import IntentoAcceso

MAX_FALLOS = 5
MINUTOS_BLOQUEO = 15


def _clave(request, username):
    usuario = (username or "").strip().lower()[:150]
    return {"usuario": usuario, "ip": request.META.get("REMOTE_ADDR") or None}


def minutos_restantes(request, username):
    """Minutos que faltan para poder reintentar, o 0 si no hay bloqueo vigente."""
    intento = IntentoAcceso.objects.filter(**_clave(request, username)).first()
    if intento is None or not intento.bloqueado:
        return 0
    return max(1, -(-int((intento.bloqueado_hasta - timezone.now()).total_seconds()) // 60))


def registrar_fallo(request, username):
    intento, _ = IntentoAcceso.objects.get_or_create(**_clave(request, username))
    if intento.bloqueado_hasta and intento.bloqueado_hasta <= timezone.now():
        intento.fallos = 0  # el bloqueo anterior ya venció: se empieza de cero
        intento.bloqueado_hasta = None
    intento.fallos += 1
    if intento.fallos >= MAX_FALLOS:
        intento.bloqueado_hasta = timezone.now() + timedelta(minutes=MINUTOS_BLOQUEO)
    intento.save()


def limpiar_usuario(username):
    """Levanta el bloqueo de un usuario desde cualquier IP (lo usa el restablecimiento)."""
    IntentoAcceso.objects.filter(usuario=(username or "").strip().lower()).delete()


def limpiar(request, username):
    IntentoAcceso.objects.filter(**_clave(request, username)).delete()
