# Imagen Docker de producción y repositorio ECR (#45)

La imagen de producción está en [`Dockerfile.prod`](../../Dockerfile.prod). El `Dockerfile` de la raíz es el de **desarrollo** (`runserver`, con pytest y ruff) y no debe usarse en AWS.

## 1. Qué hace la imagen
| | |
|---|---|
| Base | `python:3.14-slim` |
| Servidor | **gunicorn** (2 *workers* por defecto, `WEB_CONCURRENCY`) con registros a la salida estándar (CloudWatch los recoge) |
| Estáticos | recogidos **dentro de la imagen** con `collectstatic` y servidos por **WhiteNoise**, comprimidos y con nombre con hash. Se sirven **sin sesión** (el login necesita su CSS) |
| Usuario | `app` (uid 10001, **sin privilegios**, sin shell) |
| Dependencias | solo `requirements/base.txt`: **sin** pytest, ruff, coverage, **ni pandas ni matplotlib** (estaban en los requisitos y nada las importaba) |
| Dentro de la imagen | solo el código y los estáticos: **sin** `.env`, `tests/`, `docs/`, `db.sqlite3`, `media/` ni `.git` (`.dockerignore`) |
| Salud | `/salud/` (la app está viva, no toca la BD) y `/salud/db/` (además comprueba la BD; **503** si cae). Públicas y sin filtrar detalles. Excluidas de la redirección a HTTPS para que el balanceador pueda consultarlas |
| Migraciones | solo si se define `RUN_MIGRATIONS=1` (con **una** instancia; con varias, aplicarlas en un paso de despliegue aparte) |

### Variables de entorno (en tiempo de ejecución; nada de secretos dentro de la imagen)
| Variable | Obligatoria | Para qué |
|---|---|---|
| `SECRET_KEY` | sí | clave de Django (larga y aleatoria; en AWS, desde Secrets Manager o Parameter Store) |
| `DATABASE_URL` | sí | `postgres://usuario:clave@host:5432/base` (RDS) |
| `ALLOWED_HOSTS` | **sí** (si falta, **no arranca** y dice por qué) | dominio público, separado por comas |
| `CSRF_TRUSTED_ORIGINS` | sí detrás de un balanceador | `https://tu-dominio` |
| `AWS_STORAGE_BUCKET_NAME`, `AWS_S3_REGION_NAME` | para las fotos | ver [`FOTOS_S3.md`](FOTOS_S3.md); en AWS sin claves, con el rol IAM del servicio |
| `RUN_MIGRATIONS`, `PORT`, `WEB_CONCURRENCY`, `LOG_LEVEL`, `SECURE_SSL_REDIRECT` | no | ver `Dockerfile.prod` |

## 2. Construir y probar en local
```
docker compose up -d db
docker build -f Dockerfile.prod -t hogarsits:prod .
docker run -d --name hs --network hogarsits_default -p 8010:8000 ^
  -e SECRET_KEY=prueba-local -e ALLOWED_HOSTS=localhost -e RUN_MIGRATIONS=1 ^
  -e DATABASE_URL=postgres://hogarsits:hogarsits@db:5432/hogarsits hogarsits:prod
curl -H "X-Forwarded-Proto: https" http://localhost:8010/salud/db/
```
(En PowerShell, `^` se reemplaza por el acento grave `` ` ``.) El encabezado `X-Forwarded-Proto: https` simula al balanceador; sin él, la app redirige a HTTPS.

## 3. Lo que se verificó (sobre la imagen real, 24-nov-2026)
- **Tamaño:** 655 MB descomprimida, **145 MB comprimida** (lo que ocuparía en ECR; la capa gratuita es de 500 MB). El código del proyecto son 2 MB: la mayor parte es el software científico (`scipy` ≈ 140 MB y `numpy` ≈ 70 MB; `scipy` solo se usa para el valor-p del χ²).
- **Arranque:** aplica las migraciones y levanta gunicorn; el contenedor queda `healthy`.
- **HTTPS:** la salud por HTTP responde 200 sin redirigir; el resto redirige (301) a HTTPS; con el encabezado del balanceador responde 200; cookies `Secure` y `HSTS` presentes.
- **Acceso:** el CSS del login, los estáticos y Chart.js se sirven sin sesión (con nombre con hash y comprimidos: 205 851 → 69 688 bytes); toda pantalla de gestión sin sesión redirige al login; un `Host` no permitido da 400.
- **Base de datos caída:** `/salud/` sigue en 200 (no hace falta reiniciar la app), `/salud/db/` responde 503 **sin filtrar detalles**, y al volver la base se recupera sola.
- **Seguridad de la imagen:** corre como `app` (no root); no contiene `.env`, tests, docs ni la base SQLite; no hay `ENV` con secretos (solo una clave de relleno desechable en el `RUN` de `collectstatic`, visible en `docker history`, que no es un secreto); sin `ALLOWED_HOSTS` falla de inmediato con un mensaje claro.
- **CI:** el job `imagen` construye la imagen y repite las comprobaciones de salud, estáticos y acceso en cada PR.

### Un error que solo apareció al construir de verdad
El primer `docker build` **falló** en `collectstatic`: `chart.umd.min.js` termina con una referencia a un mapa de depuración (`chart.umd.js.map`) que no se copió, y el almacenamiento con manifiesto de producción se niega a recoger un archivo con referencias inexistentes. En desarrollo no se nota (`runserver` no hace ese paso). Se corrigió quitando esa línea del archivo copiado (documentado, con las dos huellas SHA-256, en `static/js/vendor/README.md`) y se añadieron pruebas que lo detectan sin Docker. De paso se descubrió que Git de Windows (`autocrlf`) alteraba los saltos de línea del archivo de terceros, invalidando su huella: `.gitattributes` ahora lo excluye de la conversión.

## 4. Subir a ECR (**lo ejecuta usted**: necesita su cuenta de AWS)
El script [`scripts/subir_a_ecr.sh`](../../scripts/subir_a_ecr.sh) crea el repositorio (una sola vez), construye, inicia sesión y sube, etiquetando con el SHA del commit.

**Antes:** el *Budget* de AWS (#14) ya existe. Cree un usuario IAM **solo para subir imágenes** (no use el administrador) con esta política, cambiando la cuenta y la región:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    { "Sid": "Token", "Effect": "Allow", "Action": "ecr:GetAuthorizationToken", "Resource": "*" },
    { "Sid": "Subir", "Effect": "Allow",
      "Action": ["ecr:BatchCheckLayerAvailability", "ecr:InitiateLayerUpload", "ecr:UploadLayerPart",
                 "ecr:CompleteLayerUpload", "ecr:PutImage", "ecr:DescribeRepositories",
                 "ecr:CreateRepository", "ecr:PutLifecyclePolicy"],
      "Resource": "arn:aws:ecr:us-east-1:CUENTA:repository/hogarsits" }
  ]
}
```
```
aws configure                       # con las claves de ese usuario
scripts/subir_a_ecr.sh              # en Git Bash o WSL
```
El repositorio se crea con **análisis de vulnerabilidades al subir**, **etiquetas inmutables** (cada versión es identificable por su commit; no se pisa `latest`) y una regla que **conserva solo las 10 imágenes más recientes** (ECR cobra por GB).

> ⚠️ **No verificado:** el script se escribió sin credenciales y **nunca se ejecutó contra AWS** (solo se comprobó su sintaxis con `bash -n`). Léalo antes de correrlo; si algo falla, dígame el mensaje exacto. Tampoco se ha ejecutado la imagen en App Runner, ECS o EC2, ni con RDS ni con un dominio y certificado reales: eso es el issue #46.
