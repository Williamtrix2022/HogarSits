"""Comprobaciones de salud para el balanceador de AWS (App Runner, ALB, EC2).

Son **públicas** (`@login_not_required`): el balanceador no tiene sesión. No devuelven nada
sensible, solo el estado.

  * `/salud/`     → la aplicación está viva (no toca la base de datos). Es la comprobación de
                    «liveness»: si falla, hay que reiniciar el contenedor.
  * `/salud/db/`  → además comprueba que la base de datos responde («readiness»). Si la BD cae,
                    responde 503 sin reiniciar a nadie en vano: se deja de enviarle tráfico.
"""

from django.contrib.auth.decorators import login_not_required
from django.db import DatabaseError, connection
from django.http import JsonResponse
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_safe


@login_not_required
@require_safe
@never_cache
def salud(request):
    return JsonResponse({"estado": "ok"})


@login_not_required
@require_safe
@never_cache
def salud_db(request):
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
    except DatabaseError:
        # Sin detalles del error: no se filtra información de la infraestructura.
        return JsonResponse({"estado": "sin_base_de_datos"}, status=503)
    return JsonResponse({"estado": "ok"})
