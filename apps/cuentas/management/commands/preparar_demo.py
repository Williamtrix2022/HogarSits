"""Prepara un despliegue de demostración: un administrador, un asesor y datos simulados.

Es **idempotente**: se puede ejecutar en cada arranque. Solo crea lo que falta y nunca toca ni
reinicia lo que ya existe (no cambia contraseñas ni duplica datos).

    DEMO_ADMIN_PASSWORD   contraseña del administrador (si falta, no se crea el usuario)
    DEMO_ASESOR_PASSWORD  contraseña del asesor de demostración (si falta, no se crea)

Las contraseñas llegan por variables de entorno y **no se escriben en la salida ni en el
repositorio**.
Los datos de ejemplo son simulados y la aplicación los marca como tales en el análisis.
"""

import os

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.core.management.base import BaseCommand
from django.db import transaction

from apps.cuentas.roles import ROL_ADMIN, ROL_ASESOR, asignar_rol
from apps.seguimiento.models import SolicitudAtencion

USUARIO_ADMIN = "administradora"
USUARIO_ASESOR = "asesor_demo"


class Command(BaseCommand):
    help = "Crea el administrador, un asesor y datos simulados de demostración (idempotente)."

    def add_arguments(self, parser):
        parser.add_argument("--dias", type=int, default=120, help="Días de datos simulados.")
        parser.add_argument("--semilla", type=int, default=7)
        parser.add_argument("--asesores", type=int, default=3)

    def _crear_usuario(self, username, clave_env, rol, nombre, apellido):
        User = get_user_model()
        clave = os.environ.get(clave_env, "")
        if not clave:
            self.stdout.write(f"Sin {clave_env}: no se crea el usuario {username}.")
            return
        if User.objects.filter(username=username).exists():
            self.stdout.write(f"El usuario {username} ya existe: no se modifica.")
            return
        with transaction.atomic():
            usuario = User.objects.create_user(
                username, password=clave, first_name=nombre, last_name=apellido
            )
            asignar_rol(usuario, rol)
        self.stdout.write(f"Usuario {username} creado con el rol {rol}.")

    def handle(self, *args, **o):
        self._crear_usuario(
            USUARIO_ADMIN, "DEMO_ADMIN_PASSWORD", ROL_ADMIN, "Administradora", "Demo"
        )
        self._crear_usuario(
            USUARIO_ASESOR, "DEMO_ASESOR_PASSWORD", ROL_ASESOR, "Asesor", "Demo"
        )
        if SolicitudAtencion.objects.exists():
            self.stdout.write("Ya hay solicitudes: no se generan datos simulados.")
            return
        self.stdout.write("Generando datos simulados...")
        call_command(
            "seed_datos_simulados",
            "--dias", str(o["dias"]),
            "--semilla", str(o["semilla"]),
            "--asesores", str(o["asesores"]),
            stdout=self.stdout,
        )
        self.stdout.write(self.style.SUCCESS("Demostración lista."))
