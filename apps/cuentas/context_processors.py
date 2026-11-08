from .navegacion import construir_menu
from .roles import es_admin, rol_de


def rol(request):
    """Rol del usuario y menú principal para las plantillas."""
    user = request.user
    if not user.is_authenticated:
        return {"rol_usuario": "", "es_admin": False, "menu": []}
    admin = es_admin(user)
    return {
        "rol_usuario": rol_de(user),
        "es_admin": admin,
        "menu": construir_menu(request.path, admin),
    }
