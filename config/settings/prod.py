"""Configuración para producción (AWS).

Todo lo que cambia entre entornos llega por variables de entorno; nada de secretos aquí:
  SECRET_KEY            (obligatoria, la pide base.py)
  DATABASE_URL          (obligatoria: RDS)
  ALLOWED_HOSTS         lista separada por comas con el dominio público (obligatoria)
  CSRF_TRUSTED_ORIGINS  lista separada por comas con el origen https://… (necesaria para los
                        formularios detrás de un balanceador)
  AWS_STORAGE_BUCKET_NAME / AWS_S3_REGION_NAME   fotos en S3 (ver docs/aws/FOTOS_S3.md)
"""

from django.core.exceptions import ImproperlyConfigured

from .base import *  # noqa: F403

DEBUG = False

ALLOWED_HOSTS = env.list("ALLOWED_HOSTS", default=[])  # noqa: F405
if not ALLOWED_HOSTS:
    raise ImproperlyConfigured(
        "Defina ALLOWED_HOSTS con el dominio público (p. ej. ALLOWED_HOSTS=hogarsits.example.com); "
        "sin él Django rechaza todas las peticiones y el error es confuso."
    )
CSRF_TRUSTED_ORIGINS = env.list("CSRF_TRUSTED_ORIGINS", default=[])  # noqa: F405

# HTTPS: detrás de App Runner/ALB el TLS termina en el balanceador y llega este encabezado.
SECURE_SSL_REDIRECT = env.bool("SECURE_SSL_REDIRECT", default=True)  # noqa: F405
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
# El balanceador consulta la salud por HTTP: sin esta excepción recibiría una redirección 301
# y daría la instancia por caída.
SECURE_REDIRECT_EXEMPT = [r"^salud/"]
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 31536000
SECURE_CONTENT_TYPE_NOSNIFF = True

# Archivos estáticos: WhiteNoise los sirve desde la propia imagen (no hay runserver en producción).
# Va ANTES de LoginRequiredMiddleware: el CSS de la pantalla de acceso se pide sin sesión.
MIDDLEWARE = [  # noqa: F405
    MIDDLEWARE[0],  # noqa: F405  SecurityMiddleware
    "whitenoise.middleware.WhiteNoiseMiddleware",
    *MIDDLEWARE[1:],  # noqa: F405
]
STORAGES = {  # noqa: F405
    **STORAGES,  # noqa: F405  conserva el almacenamiento de fotos (disco o S3)
    "staticfiles": {"BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage"},
}

# Registros a la salida estándar: CloudWatch recoge lo que el contenedor imprime.
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {"simple": {"format": "%(asctime)s %(levelname)s %(name)s %(message)s"}},
    "handlers": {"consola": {"class": "logging.StreamHandler", "formatter": "simple"}},
    "root": {"handlers": ["consola"], "level": env("LOG_LEVEL", default="INFO")},  # noqa: F405
}
