#!/bin/sh
# Arranque del contenedor de producción.
set -e

# Aplicar migraciones solo si se pide (RUN_MIGRATIONS=1). Con varias instancias arrancando a la
# vez conviene hacerlo en un paso de despliegue aparte, no aquí.
if [ "${RUN_MIGRATIONS:-0}" = "1" ]; then
    echo "[entrypoint] aplicando migraciones..."
    python manage.py migrate --noinput
fi

# Despliegue de demostración (PREPARAR_DEMO=1): crea administrador, asesor y datos simulados si
# faltan. Es idempotente y las contraseñas llegan por variables de entorno.
if [ "${PREPARAR_DEMO:-0}" = "1" ]; then
    echo "[entrypoint] preparando la demostración..."
    python manage.py preparar_demo
fi

exec "$@"
