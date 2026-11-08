"""Roles del sistema (RF-03). Se implementan con los grupos de Django.

- **Administrador**: gestiona usuarios y ve toda la analítica. Un superusuario también lo es.
- **Asesor**: trabaja con sus solicitudes, visitas e inmuebles.

Un usuario tiene como máximo un rol. Los usuarios sin rol (p. ej. los asesores simulados)
pueden existir pero no pasan ninguna comprobación de rol.
"""

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.db.models import Q

ROL_ADMIN = "Administrador"
ROL_ASESOR = "Asesor"
ROLES = (ROL_ASESOR, ROL_ADMIN)


def es_admin(user) -> bool:
    return bool(
        user.is_authenticated
        and user.is_active
        and (user.is_superuser or user.groups.filter(name=ROL_ADMIN).exists())
    )


def es_asesor(user) -> bool:
    return bool(
        user.is_authenticated and user.is_active and user.groups.filter(name=ROL_ASESOR).exists()
    )


def rol_de(user) -> str:
    """Nombre del rol del usuario, o cadena vacía si no tiene."""
    if user.is_superuser or user.groups.filter(name=ROL_ADMIN).exists():
        return ROL_ADMIN
    if user.groups.filter(name=ROL_ASESOR).exists():
        return ROL_ASESOR
    return ""


def asignar_rol(user, rol: str) -> None:
    """Deja al usuario con exactamente un rol."""
    if rol not in ROLES:
        raise ValueError(f"Rol desconocido: {rol!r}")
    user.groups.remove(*Group.objects.filter(name__in=ROLES))
    user.groups.add(Group.objects.get(name=rol))


def administradores_activos():
    """Usuarios activos con rol de administrador (incluye superusuarios)."""
    return (
        get_user_model()
        .objects.filter(is_active=True)
        .filter(Q(is_superuser=True) | Q(groups__name=ROL_ADMIN))
        .distinct()
    )
