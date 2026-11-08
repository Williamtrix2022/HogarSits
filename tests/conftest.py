from datetime import UTC, datetime, timedelta

import pytest
from django.contrib.auth import get_user_model

from apps.clientes.models import Cliente
from apps.inmuebles.models import Inmueble
from apps.seguimiento.models import SolicitudAtencion

T0 = datetime(2026, 3, 2, 9, 0, tzinfo=UTC)  # lunes 09:00 UTC


def hora(minutos=0):
    """Instante de referencia + minutos (para escribir horarios legibles en los tests)."""
    return T0 + timedelta(minutes=minutos)


@pytest.fixture
def asesor(db):
    return get_user_model().objects.create_user("asesor1", password="x")


@pytest.fixture
def otro_asesor(db):
    return get_user_model().objects.create_user("asesor2", password="x")


@pytest.fixture
def cliente(db):
    return Cliente.objects.create(nombre="Ana", correo="ana@example.com", telefono="300")


@pytest.fixture
def inmueble(db):
    return Inmueble.objects.create(
        titulo="Casa 1", direccion="Calle 1", precio=100_000_000, operacion="VENTA"
    )


@pytest.fixture
def otro_inmueble(db):
    return Inmueble.objects.create(
        titulo="Apto 2", direccion="Calle 2", precio=900_000, operacion="ALQUILER"
    )


@pytest.fixture
def solicitud(cliente, inmueble):
    return SolicitudAtencion.objects.create(
        cliente=cliente, inmueble=inmueble, tipo_interes="COMPRA"
    )
