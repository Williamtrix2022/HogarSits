from .roles import es_admin, rol_de


def rol(request):
    """Expone el rol del usuario a las plantillas (menú y permisos visuales)."""
    user = request.user
    if not user.is_authenticated:
        return {"rol_usuario": "", "es_admin": False}
    return {"rol_usuario": rol_de(user), "es_admin": es_admin(user)}
