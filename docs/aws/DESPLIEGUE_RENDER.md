# Despliegue de demostración en Render

Para la sustentación: la aplicación y su base PostgreSQL funcionando en internet, sin tocar AWS. Es **un despliegue de demostración**, no el de producción de #46 (App Runner + RDS), que sigue pendiente.

## Qué se despliega
`render.yaml` (en la raíz) describe dos recursos:
- **`hogarsits`**: servicio web que construye la imagen de producción (`Dockerfile.prod`) desde este repositorio y se actualiza solo con cada cambio en `main`.
- **`hogarsits-db`**: PostgreSQL 17 (plan gratuito).

Al arrancar, el contenedor aplica las migraciones y ejecuta `python manage.py preparar_demo` (variable `PREPARAR_DEMO=1`), que **solo crea lo que falta**: el usuario `administradora`, el usuario `asesor_demo` y 120 días de **datos simulados** (la aplicación los marca como simulados). No cambia contraseñas ni duplica datos si se reinicia.

## Contraseñas
No están en el repositorio. Se escriben en el panel de Render como `DEMO_ADMIN_PASSWORD` y `DEMO_ASESOR_PASSWORD` (Environment del servicio). Para cambiarlas después: cambie el valor **y** el usuario ya creado conservará la clave anterior (el comando no modifica usuarios existentes); use «Restablecer clave» en Administración → Usuarios.

## Qué esperar (capa gratuita)
- **El servicio se duerme** tras ~15 minutos sin visitas; la primera petición tarda ~1 minuto en despertarlo. **Abra la URL unos minutos antes de la sustentación.**
- **La base gratuita caduca a los 30 días** de crearse (24-dic-2026) y se borra: si hace falta, cree otra o pase a un plan de pago.
- Memoria limitada (512 MB): un solo *worker* (`WEB_CONCURRENCY=1`). Suficiente para una demostración, no para carga real.
- HTTPS lo pone Render; la aplicación ya lo exige en producción.

## Comprobar que funciona
1. `https://<url>/salud/` → «ok» y `https://<url>/salud/db/` → «ok» (la segunda toca la base).
2. Entrar con `administradora` → inicio, inmuebles, agenda, **Análisis** (con el aviso de datos simulados).
3. Entrar con `asesor_demo` → no ve Análisis ni Administración.

## Limitaciones (no se oculta nada)
- Es una demostración con datos simulados; no se ha usado con una inmobiliaria real.
- Las fotos de inmuebles no usan S3 aquí: sin bucket configurado se guardan en el disco del contenedor, que **se borra en cada despliegue**.
- Esto **no** reemplaza el despliegue en AWS (#45, #46, #47), que sigue pendiente.
