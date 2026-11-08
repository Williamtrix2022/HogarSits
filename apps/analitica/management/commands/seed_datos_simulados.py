"""Genera datos simulados de operación (RF-60, HU-10).

Ejemplos:
    python manage.py seed_datos_simulados                       # 30 días, parámetros de la ronda 1
    python manage.py seed_datos_simulados --dias 90 --asesores 4 --clientes-por-dia 15
    python manage.py seed_datos_simulados --reemplazar          # borra lo simulado y regenera
    python manage.py seed_datos_simulados --limpiar             # solo borra lo simulado

Todo lo simulado se marca para no confundirlo con datos reales: usuarios `sim_asesorN`, correos
`@sim.hogarsits.test` e inmuebles con título `[SIM] ...`. Nunca se tocan datos sin esas marcas.
"""

import json
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from apps.agenda.models import HorarioAsesor, Visita
from apps.analitica.services import simulacion as sim
from apps.clientes.models import Cliente
from apps.inmuebles.models import Inmueble
from apps.seguimiento.models import SeguimientoEtapa, SolicitudAtencion

DOMINIO = "@sim.hogarsits.test"
PREFIJO_USUARIO = "sim_asesor"
PREFIJO_INMUEBLE = "[SIM] "


def _simulados():
    User = get_user_model()
    return {
        "usuarios": User.objects.filter(username__startswith=PREFIJO_USUARIO),
        "clientes": Cliente.objects.filter(correo__endswith=DOMINIO),
        "inmuebles": Inmueble.objects.filter(titulo__startswith=PREFIJO_INMUEBLE),
    }


def borrar_simulados() -> dict:
    """Borra solo datos simulados, en el orden que respeta los PROTECT. Devuelve conteos."""
    s = _simulados()
    cuentas = {k: v.count() for k, v in s.items()}
    Visita.objects.filter(asesor__in=s["usuarios"]).delete()
    SolicitudAtencion.objects.filter(cliente__in=s["clientes"]).delete()  # cascada a etapas
    s["clientes"].delete()
    s["inmuebles"].delete()
    s["usuarios"].delete()  # cascada a horarios
    return cuentas


class Command(BaseCommand):
    help = "Genera datos simulados (llegadas Poisson con picos, atención M/M/c, visitas y Markov)."

    def add_arguments(self, parser):
        defecto = sim.Parametros(fecha_inicio=timezone.localdate())
        parser.add_argument("--dias", type=int, default=defecto.dias)
        parser.add_argument("--fecha-inicio", help="AAAA-MM-DD (por defecto: hoy menos --dias)")
        parser.add_argument("--clientes-por-dia", type=float, default=defecto.clientes_por_dia)
        parser.add_argument("--asesores", type=int, default=defecto.n_asesores)
        parser.add_argument("--servicio-min", type=float, default=defecto.servicio_medio_min)
        parser.add_argument("--visita-min", type=int, default=defecto.visita_min)
        parser.add_argument("--visita-max", type=int, default=defecto.visita_max)
        parser.add_argument("--apertura", type=int, default=defecto.hora_apertura)
        parser.add_argument("--cierre", type=int, default=defecto.hora_cierre)
        parser.add_argument("--inmuebles", type=int, default=defecto.n_inmuebles)
        parser.add_argument("--dias-entre-etapas", type=float, default=defecto.dias_entre_etapas)
        parser.add_argument(
            "--matriz", help="JSON con la matriz P de 5x5 (por defecto, la del README)"
        )
        parser.add_argument("--semilla", type=int, default=defecto.semilla)
        parser.add_argument("--reemplazar", action="store_true", help="borra lo simulado antes")
        parser.add_argument("--limpiar", action="store_true", help="solo borra lo simulado")

    def handle(self, *args, **o):
        if o["limpiar"]:
            with transaction.atomic():
                self._informar_borrado(borrar_simulados())
            return

        existentes = _simulados()["clientes"].exists() or _simulados()["usuarios"].exists()
        if existentes and not o["reemplazar"]:
            raise CommandError(
                "Ya hay datos simulados. Use --reemplazar para regenerarlos "
                "o --limpiar para borrarlos."
            )

        tz = ZoneInfo(sim.Parametros(fecha_inicio=timezone.localdate()).zona)
        hoy = datetime.now(tz).date()
        inicio = (
            datetime.strptime(o["fecha_inicio"], "%Y-%m-%d").date()
            if o["fecha_inicio"]
            else hoy - timedelta(days=o["dias"])
        )
        matriz = sim.MATRIZ_README
        if o["matriz"]:
            matriz = tuple(tuple(fila) for fila in json.loads(o["matriz"]))
        params = sim.Parametros(
            fecha_inicio=inicio,
            dias=o["dias"],
            clientes_por_dia=o["clientes_por_dia"],
            n_asesores=o["asesores"],
            servicio_medio_min=o["servicio_min"],
            visita_min=o["visita_min"],
            visita_max=o["visita_max"],
            hora_apertura=o["apertura"],
            hora_cierre=o["cierre"],
            n_inmuebles=o["inmuebles"],
            dias_entre_etapas=o["dias_entre_etapas"],
            matriz=matriz,
            semilla=o["semilla"],
        )
        try:
            resultado = sim.simular(params)
        except ValueError as e:
            raise CommandError(str(e)) from e

        with transaction.atomic():
            if o["reemplazar"]:
                self._informar_borrado(borrar_simulados())
            resumen = self._persistir(resultado)

        self.stdout.write(self.style.SUCCESS("Datos simulados generados:"))
        for clave, valor in resumen.items():
            self.stdout.write(f"  {clave}: {valor}")

    def _informar_borrado(self, cuentas):
        self.stdout.write(
            "Borrado simulado: "
            + ", ".join(f"{v} {k}" for k, v in cuentas.items())
        )

    def _persistir(self, r: sim.Resultado) -> dict:
        p = r.parametros
        User = get_user_model()

        asesores = []
        for i in range(p.n_asesores):
            u = User(username=f"{PREFIJO_USUARIO}{i + 1}", first_name=f"Asesor {i + 1}")
            u.set_unusable_password()
            asesores.append(u)
        asesores = User.objects.bulk_create(asesores)
        HorarioAsesor.objects.bulk_create(
            HorarioAsesor(
                asesor=u,
                dia_semana=dia,
                hora_inicio=datetime(2000, 1, 1, p.hora_apertura).time(),
                hora_fin=datetime(2000, 1, 1, p.hora_cierre % 24).time()
                if p.hora_cierre < 24
                else datetime(2000, 1, 1, 23, 59).time(),
            )
            for u in asesores
            for dia in p.dias_laborales
        )

        inmuebles = Inmueble.objects.bulk_create(
            Inmueble(
                titulo=f"{PREFIJO_INMUEBLE}{s.tipo_inmueble.title()} {i + 1:03d}",
                tipo_inmueble=s.tipo_inmueble,
                operacion=s.operacion,
                direccion=f"Calle {i + 1} # {i % 40 + 1}-{i % 90 + 10}",
                barrio=s.barrio,
                precio=s.precio,
                area_m2=s.area_m2,
                habitaciones=s.habitaciones,
            )
            for i, s in enumerate(r.inmuebles)
        )

        clientes = Cliente.objects.bulk_create(
            Cliente(
                nombre=f"Cliente Simulado {i + 1:04d}",
                correo=f"cliente{i + 1:04d}{DOMINIO}",
                telefono=f"300{i + 1:07d}",
            )
            for i in range(r.n_clientes)
        )

        solicitudes = SolicitudAtencion.objects.bulk_create(
            SolicitudAtencion(
                cliente=clientes[s.cliente],
                inmueble=inmuebles[s.inmueble] if s.inmueble is not None else None,
                asesor=asesores[s.asesor],
                tipo_interes=s.tipo_interes,
                presupuesto=s.presupuesto,
                timestamp_llegada=s.llegada,
                timestamp_inicio_atencion=s.inicio,
                timestamp_fin_atencion=s.fin,
                estado=SolicitudAtencion.Estado.FINALIZADO,
                etapa_actual=s.etapa_actual,
            )
            for s in r.solicitudes
        )

        etapas, visitas = [], []
        ahora = timezone.now()
        for modelo, s in zip(solicitudes, r.solicitudes, strict=True):
            etapas.extend(
                SeguimientoEtapa(
                    solicitud=modelo,
                    estado_origen=e.origen,
                    estado_destino=e.destino,
                    fecha_transicion=e.fecha,
                    registrado_por=asesores[s.asesor],
                    nota=e.nota,
                )
                for e in s.etapas
            )
            visitas.extend(
                Visita(
                    solicitud=modelo,
                    inmueble=inmuebles[v.inmueble],
                    asesor=asesores[v.asesor],
                    inicio=v.inicio,
                    fin=v.fin,
                    estado=Visita.Estado.REALIZADA if v.fin <= ahora else Visita.Estado.PROGRAMADA,
                )
                for v in s.visitas
            )
        SeguimientoEtapa.objects.bulk_create(etapas)
        Visita.objects.bulk_create(visitas)

        cierres = sum(1 for s in r.solicitudes if s.etapa_actual == sim.CIERRE)
        abandonos = sum(1 for s in r.solicitudes if s.etapa_actual == sim.ABANDONO)
        esperas = [(s.inicio - s.llegada).total_seconds() / 60 for s in r.solicitudes]
        return {
            "asesores": len(asesores),
            "inmuebles": len(inmuebles),
            "clientes": len(clientes),
            "solicitudes": len(solicitudes),
            "transiciones de etapa": len(etapas),
            "visitas": len(visitas),
            "cierres / abandonos / en curso": (
                f"{cierres} / {abandonos} / {len(solicitudes) - cierres - abandonos}"
            ),
            "espera media (min)": round(sum(esperas) / len(esperas), 1) if esperas else 0,
        }
