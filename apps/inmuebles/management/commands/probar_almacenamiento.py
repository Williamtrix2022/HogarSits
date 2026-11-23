"""Comprueba de punta a punta el almacenamiento de fotos (disco local o S3).

    python manage.py probar_almacenamiento

Guarda un archivo de prueba, comprueba que existe, imprime su enlace, lo lee de vuelta y lo
borra. Si algo falla (bucket inexistente, credenciales o permisos mal), dice cuál es el paso.
"""

import uuid

from django.conf import settings
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = "Guarda, lee y borra un archivo de prueba en el almacenamiento de fotos."

    def handle(self, *args, **opciones):
        bucket = settings.AWS_STORAGE_BUCKET_NAME
        destino = f"S3, bucket «{bucket}»" if bucket else "disco local (carpeta media/)"
        self.stdout.write(f"Almacenamiento configurado: {destino}")

        contenido = f"prueba hogarsits {uuid.uuid4()}".encode()
        nombre = f"pruebas/{uuid.uuid4().hex}.txt"
        guardado = self._paso(
            "Guardar el archivo", lambda: default_storage.save(nombre, ContentFile(contenido))
        )
        self._paso("Comprobar que existe", lambda: self._exigir(default_storage.exists(guardado)))
        enlace = self._paso("Generar el enlace", lambda: default_storage.url(guardado))
        self.stdout.write(f"    {enlace}")

        def leer():
            with default_storage.open(guardado) as f:
                self._exigir(f.read() == contenido, "el contenido leído no coincide")

        self._paso("Leer el archivo de vuelta", leer)
        self._paso("Borrar el archivo de prueba", lambda: default_storage.delete(guardado))
        self.stdout.write(self.style.SUCCESS("Todo correcto: el almacenamiento funciona."))

    def _exigir(self, condicion, mensaje="la comprobación falló"):
        if not condicion:
            raise RuntimeError(mensaje)

    def _paso(self, etiqueta, accion):
        try:
            resultado = accion()
        except Exception as error:
            raise CommandError(
                f"Falló «{etiqueta}»: {type(error).__name__}: {error}\n"
                "Revise el nombre del bucket, las credenciales (AWS_ACCESS_KEY_ID y "
                "AWS_SECRET_ACCESS_KEY en .env) y que la política IAM permita "
                "s3:PutObject, s3:GetObject y s3:DeleteObject sobre el bucket."
            ) from error
        self.stdout.write(self.style.SUCCESS(f"  [OK] {etiqueta}"))
        return resultado
