"""Dónde se guardan las fotos (#27, RF-13).

Sin bucket definido, las fotos van al disco local (`MEDIA_ROOT`): así el proyecto corre sin AWS.
Con `AWS_STORAGE_BUCKET_NAME` van a S3. Las credenciales **no** se escriben aquí ni en el
código: boto3 las toma de las variables de entorno (en local, del `.env`) o del rol IAM del
servicio en AWS.
"""

ESTATICOS = {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"}


def construir_storages(bucket: str = "", region: str = "us-east-1") -> dict:
    if not bucket:
        return {
            "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
            "staticfiles": ESTATICOS,
        }
    return {
        "default": {
            "BACKEND": "storages.backends.s3.S3Storage",
            "OPTIONS": {
                "bucket_name": bucket,
                "region_name": region,
                "signature_version": "s3v4",
                # El bucket es privado: cada foto se sirve con un enlace firmado que caduca.
                "querystring_auth": True,
                "querystring_expire": 3600,
                "default_acl": None,
                # Dos fotos con el mismo nombre no se pisan.
                "file_overwrite": False,
            },
        },
        "staticfiles": ESTATICOS,
    }
