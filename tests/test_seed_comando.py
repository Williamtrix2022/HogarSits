"""El comando persiste la simulación respetando todas las restricciones de la BD."""

import pytest
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.core.management.base import CommandError

from apps.agenda.models import HorarioAsesor, Visita
from apps.clientes.models import Cliente
from apps.inmuebles.models import Inmueble
from apps.seguimiento.models import SeguimientoEtapa, SolicitudAtencion

pytestmark = pytest.mark.django_db

ARGS = dict(dias=12, fecha_inicio="2026-02-02", asesores=3, inmuebles=15, semilla=11)


def test_genera_datos_coherentes(capsys):
    call_command("seed_datos_simulados", **ARGS)
    assert get_user_model().objects.filter(username__startswith="sim_asesor").count() == 3
    assert HorarioAsesor.objects.count() == 3 * 6
    assert Inmueble.objects.filter(titulo__startswith="[SIM]").count() == 15
    n = SolicitudAtencion.objects.count()
    assert n > 50
    assert SolicitudAtencion.objects.filter(estado="FINALIZADO").count() == n
    assert SeguimientoEtapa.objects.exists() and Visita.objects.exists()
    salida = capsys.readouterr().out
    assert "solicitudes" in salida and "espera media" in salida


def test_etapa_actual_coincide_con_la_ultima_transicion():
    call_command("seed_datos_simulados", **ARGS)
    for s in SolicitudAtencion.objects.prefetch_related("seguimientos")[:200]:
        pasos = sorted(s.seguimientos.all(), key=lambda e: e.fecha_transicion)
        esperada = pasos[-1].estado_destino if pasos else 1
        assert s.etapa_actual == esperada


def test_las_visitas_no_se_cruzan_en_la_bd():
    call_command("seed_datos_simulados", **ARGS)  # un cruce lanzaría IntegrityError
    assert Visita.objects.count() > 0


def test_rechaza_regenerar_sin_reemplazar():
    call_command("seed_datos_simulados", **ARGS)
    with pytest.raises(CommandError, match="--reemplazar"):
        call_command("seed_datos_simulados", **ARGS)


def test_reemplazar_regenera_sin_duplicar():
    call_command("seed_datos_simulados", **ARGS)
    antes = SolicitudAtencion.objects.count()
    call_command("seed_datos_simulados", reemplazar=True, **ARGS)
    assert SolicitudAtencion.objects.count() == antes  # misma semilla, mismos datos


def test_limpiar_no_toca_datos_reales(cliente, inmueble, solicitud):
    call_command("seed_datos_simulados", **ARGS)
    call_command("seed_datos_simulados", limpiar=True)
    assert not Cliente.objects.filter(correo__endswith="@sim.hogarsits.test").exists()
    assert not Inmueble.objects.filter(titulo__startswith="[SIM]").exists()
    assert Cliente.objects.filter(pk=cliente.pk).exists()
    assert Inmueble.objects.filter(pk=inmueble.pk).exists()
    assert SolicitudAtencion.objects.filter(pk=solicitud.pk).exists()


def test_matriz_invalida_da_error_claro():
    with pytest.raises(CommandError, match="suma 1"):
        call_command(
            "seed_datos_simulados",
            matriz="[[0.5,0.5,0,0,0.1],[0,0.15,0.45,0,0.4],[0,0,0.2,0.55,0.25],"
            "[0,0,0,1,0],[0,0,0,0,1]]",
            **ARGS,
        )
