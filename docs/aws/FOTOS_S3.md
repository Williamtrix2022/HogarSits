# Fotos de inmuebles en S3 — guía paso a paso (#27)

Sin configuración, las fotos se guardan en la carpeta `media/` (disco local) y todo funciona. Para usar **S3** hay que crear un bucket privado y un usuario IAM con permisos mínimos, y definir tres variables en `.env`. **Antes de empezar, el Budget de AWS (#14) ya está creado.** S3 entra en el nivel gratuito (5 GB); un puñado de fotos de prueba cuesta cero.

## 1. Crear el bucket (privado)
1. Consola de AWS → **S3** → **Crear bucket** (*Create bucket*).
2. **Nombre:** único en todo AWS, p. ej. `hogarsits-fotos-dev-<tus-iniciales>`. **Región:** `us-east-1` (o la que uses; debe coincidir con `AWS_S3_REGION_NAME`).
3. **Bloquear todo el acceso público:** déjalo **activado** (marcado «Bloquear *todo* el acceso público»). Las fotos se sirven con enlaces firmados que caducan; el bucket **no** debe ser público.
4. **Cifrado por defecto:** deja SSE-S3 (viene activo). Versionado: no hace falta.
5. **Crear bucket.**

## 2. Crear un usuario IAM solo para las fotos
No uses `WilliamAwsAdmin` en la aplicación: si la clave se filtra, solo debe poder tocar este bucket.
1. **IAM → Usuarios → Crear usuario**, nombre `hogarsits-fotos-dev`, **sin** acceso a la consola.
2. **Adjuntar políticas directamente → Crear política → JSON** y pega esto (cambia el nombre del bucket por el tuyo):

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "FotosHogarSits",
      "Effect": "Allow",
      "Action": ["s3:PutObject", "s3:GetObject", "s3:DeleteObject"],
      "Resource": "arn:aws:s3:::hogarsits-fotos-dev-XXXX/*"
    },
    {
      "Sid": "ListarBucket",
      "Effect": "Allow",
      "Action": "s3:ListBucket",
      "Resource": "arn:aws:s3:::hogarsits-fotos-dev-XXXX"
    }
  ]
}
```
3. Nómbrala `HogarSitsFotosDev`, adjúntala al usuario.
4. En el usuario → **Credenciales de seguridad → Crear clave de acceso** → caso de uso «Aplicación que se ejecuta fuera de AWS». **Copia el ID y la clave secreta ahora**: la clave secreta no se vuelve a mostrar.

## 3. Configurar `.env` (nunca se sube a git)
```
AWS_STORAGE_BUCKET_NAME=hogarsits-fotos-dev-XXXX
AWS_S3_REGION_NAME=us-east-1
AWS_ACCESS_KEY_ID=AKIA...
AWS_SECRET_ACCESS_KEY=...
```

## 4. Verificar
```
python manage.py probar_almacenamiento
```
Debe imprimir cinco pasos con `[OK]` y «Todo correcto». Si falla, el mensaje dice en qué paso y qué revisar. Después, en la aplicación: **Inmuebles → abrir uno → Fotos → Subir fotos**; la foto debe verse en la ficha, y aparecer en el bucket bajo `inmuebles/AAAA/MM/`. **Quitar** la borra también de S3.

## 5. En producción (Sprint 6)
No se usan claves: el servicio de AWS (App Runner o EC2) lleva un **rol IAM** con la misma política, y solo se define `AWS_STORAGE_BUCKET_NAME` y `AWS_S3_REGION_NAME`. Bucket aparte del de desarrollo.

## Cómo está construido
- `config/storage.py` elige el almacenamiento según `AWS_STORAGE_BUCKET_NAME`: sin él, disco local; con él, `S3Storage` privado con enlaces firmados de 1 hora y sin sobrescribir archivos.
- Las credenciales **no** están en el código ni en `settings`: boto3 las toma del entorno o del rol.
- Cada foto se valida antes de guardarse: JPG, PNG o WebP **de verdad** (se comprueba con Pillow, no solo la extensión), hasta 5 MB, máximo 10 por inmueble; si una falla, no se guarda ninguna.
