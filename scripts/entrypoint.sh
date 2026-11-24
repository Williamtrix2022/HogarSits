#!/bin/sh
# Arranque del contenedor de producción.
set -e

# Aplicar migraciones solo si se pide (RUN_MIGRATIONS=1). Con varias instancias arrancando a la
# vez conviene hacerlo en un paso de despliegue aparte, no aquí.
if [ "${RUN_MIGRATIONS:-0}" = "1" ]; then
    echo "[entrypoint] aplicando migraciones..."
    python manage.py migrate --noinput
fi

exec "$@"
