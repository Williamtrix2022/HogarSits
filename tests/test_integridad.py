"""Reglas de integridad que la BD debe garantizar (RNF-03), no solo la interfaz."""

import pytest
from django.db import IntegrityError, transaction

from apps.clientes.models import Cliente
from apps.inmuebles.models import HistorialEstadoInmueble, Inmueble
from apps.seguimiento.models import SeguimientoEtapa, SolicitudAtencion

from .conftest import hora

pytestmark = pytest.mark.django_db


def viola(**kwargs):
    """Contexto que espera un IntegrityError sin romper la transacción del test."""
    return pytest.raises(IntegrityError)


# --- Clientes (RN-10) ---------------------------------------------------------------------
def test_correo_unico_sin_distinguir_mayusculas(cliente):
    with viola(), transaction.atomic():
        Cliente.objects.create(nombre="Otra", correo="ANA@Example.com", telefono="1")


def test_correo_se_normaliza_a_minusculas():
    c = Cliente.objects.create(nombre="Luis", correo="  Luis@Example.COM ", telefono="1")
    assert c.correo == "luis@example.com"


# --- Inmuebles ----------------------------------------------------------------------------
def test_precio_debe_ser_positivo():
    with viola(), transaction.atomic():
        Inmueble.objects.create(titulo="X", direccion="d", precio=0, operacion="VENTA")


def test_alquiler_no_puede_quedar_vendido(otro_inmueble):
    otro_inmueble.estado = "VENDIDO"
    with viola(), transaction.atomic():
        otro_inmueble.save()


def test_venta_no_puede_quedar_arrendada(inmueble):
    inmueble.estado = "ARRENDADO"
    with viola(), transaction.atomic():
        inmueble.save()


def test_historial_exige_cambio_real_de_estado(inmueble):
    with viola(), transaction.atomic():
        HistorialEstadoInmueble.objects.create(
            inmueble=inmueble, estado_anterior="DISPONIBLE", estado_nuevo="DISPONIBLE"
        )


# --- Solicitudes (RN-11, RN-20) -----------------------------------------------------------
def test_llegada_se_puede_fijar_para_datos_historicos(cliente):
    s = SolicitudAtencion.objects.create(
        cliente=cliente, tipo_interes="ALQUILER", timestamp_llegada=hora(0)
    )
    s.refresh_from_db()
    assert s.timestamp_llegada == hora(0)


def test_inicio_no_puede_ser_anterior_a_la_llegada(cliente):
    with viola(), transaction.atomic():
        SolicitudAtencion.objects.create(
            cliente=cliente,
            tipo_interes="COMPRA",
            timestamp_llegada=hora(10),
            timestamp_inicio_atencion=hora(5),
            estado="EN_ATENCION",
        )


def test_fin_no_puede_ser_anterior_al_inicio(cliente):
    with viola(), transaction.atomic():
        SolicitudAtencion.objects.create(
            cliente=cliente,
            tipo_interes="COMPRA",
            timestamp_llegada=hora(0),
            timestamp_inicio_atencion=hora(10),
            timestamp_fin_atencion=hora(5),
            estado="FINALIZADO",
        )


def test_finalizada_exige_hora_de_fin(cliente):
    with viola(), transaction.atomic():
        SolicitudAtencion.objects.create(
            cliente=cliente,
            tipo_interes="COMPRA",
            timestamp_llegada=hora(0),
            timestamp_inicio_atencion=hora(5),
            estado="FINALIZADO",
        )


def test_solicitud_valida_completa(cliente):
    s = SolicitudAtencion.objects.create(
        cliente=cliente,
        tipo_interes="COMPRA",
        presupuesto=150_000_000,
        timestamp_llegada=hora(0),
        timestamp_inicio_atencion=hora(12),
        timestamp_fin_atencion=hora(40),
        estado="FINALIZADO",
    )
    espera = s.timestamp_inicio_atencion - s.timestamp_llegada
    servicio = s.timestamp_fin_atencion - s.timestamp_inicio_atencion
    assert espera.total_seconds() == 12 * 60 and servicio.total_seconds() == 28 * 60


def test_no_se_borra_un_cliente_con_solicitudes(solicitud):
    from django.db.models import ProtectedError

    with pytest.raises(ProtectedError):
        solicitud.cliente.delete()


# --- Etapas (RN-31) -----------------------------------------------------------------------
def test_etapa_fuera_de_rango_es_invalida(solicitud):
    with viola(), transaction.atomic():
        SeguimientoEtapa.objects.create(solicitud=solicitud, estado_origen=1, estado_destino=9)


@pytest.mark.parametrize("absorbente", [4, 5])
def test_no_se_sale_de_cierre_ni_abandono(solicitud, absorbente):
    with viola(), transaction.atomic():
        SeguimientoEtapa.objects.create(
            solicitud=solicitud, estado_origen=absorbente, estado_destino=1
        )


def test_autotransicion_permitida_hasta_decidir_adr_002(solicitud):
    """Consulta -> Consulta está en la matriz P del README; ADR-002 definirá cuándo se registra."""
    SeguimientoEtapa.objects.create(solicitud=solicitud, estado_origen=1, estado_destino=1)
    assert solicitud.seguimientos.count() == 1
