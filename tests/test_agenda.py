"""Agenda sin cruces (RN-01, RN-02, RN-04): la regla vive en PostgreSQL (ExclusionConstraint)."""

import datetime as dt

import pytest
from django.db import IntegrityError, transaction

from apps.agenda.models import HorarioAsesor, Visita

from .conftest import hora

pytestmark = pytest.mark.django_db


def visita(solicitud, inmueble, asesor, ini, fin, estado="PROGRAMADA"):
    return Visita.objects.create(
        solicitud=solicitud,
        inmueble=inmueble,
        asesor=asesor,
        inicio=hora(ini),
        fin=hora(fin),
        estado=estado,
    )


def test_rechaza_cruce_del_mismo_asesor(solicitud, inmueble, otro_inmueble, asesor):
    visita(solicitud, inmueble, asesor, 0, 60)
    with pytest.raises(IntegrityError), transaction.atomic():
        visita(solicitud, otro_inmueble, asesor, 30, 90)  # otro inmueble, mismo asesor


def test_rechaza_cruce_del_mismo_inmueble(solicitud, inmueble, asesor, otro_asesor):
    visita(solicitud, inmueble, asesor, 0, 60)
    with pytest.raises(IntegrityError), transaction.atomic():
        visita(solicitud, inmueble, otro_asesor, 59, 120)  # otro asesor, mismo inmueble


def test_visitas_contiguas_no_se_cruzan(solicitud, inmueble, asesor):
    visita(solicitud, inmueble, asesor, 0, 60)
    visita(solicitud, inmueble, asesor, 60, 120)  # empieza justo cuando termina la otra
    assert Visita.objects.count() == 2


def test_asesor_e_inmueble_distintos_pueden_coincidir(
    solicitud, inmueble, otro_inmueble, asesor, otro_asesor
):
    visita(solicitud, inmueble, asesor, 0, 60)
    visita(solicitud, otro_inmueble, otro_asesor, 0, 60)
    assert Visita.objects.count() == 2


def test_visita_cancelada_libera_el_horario(solicitud, inmueble, asesor):
    v = visita(solicitud, inmueble, asesor, 0, 60)
    v.estado = "CANCELADA"
    v.save()
    visita(solicitud, inmueble, asesor, 30, 90)
    assert Visita.objects.filter(estado="PROGRAMADA").count() == 1


def test_visita_cancelada_no_bloquea_al_crearse(solicitud, inmueble, asesor):
    visita(solicitud, inmueble, asesor, 0, 60)
    visita(solicitud, inmueble, asesor, 10, 50, estado="CANCELADA")  # no cuenta como cruce
    assert Visita.objects.count() == 2


def test_reprogramar_conserva_historial(solicitud, inmueble, asesor):
    original = visita(solicitud, inmueble, asesor, 0, 60)
    original.estado = "CANCELADA"
    original.save()
    nueva = Visita.objects.create(
        solicitud=solicitud,
        inmueble=inmueble,
        asesor=asesor,
        inicio=hora(120),
        fin=hora(180),
        reemplaza_a=original,
    )
    assert list(original.reprogramaciones.all()) == [nueva]


def test_fin_debe_ser_posterior_al_inicio(solicitud, inmueble, asesor):
    with pytest.raises(IntegrityError), transaction.atomic():
        visita(solicitud, inmueble, asesor, 60, 60)


def test_horario_fin_posterior_al_inicio(asesor):
    with pytest.raises(IntegrityError), transaction.atomic():
        HorarioAsesor.objects.create(
            asesor=asesor, dia_semana=0, hora_inicio=dt.time(10), hora_fin=dt.time(9)
        )


def test_horario_turno_unico(asesor):
    datos = dict(asesor=asesor, dia_semana=0, hora_inicio=dt.time(8), hora_fin=dt.time(12))
    HorarioAsesor.objects.create(**datos)
    with pytest.raises(IntegrityError), transaction.atomic():
        HorarioAsesor.objects.create(**datos)
