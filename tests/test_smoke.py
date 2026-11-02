import pytest
from django.urls import reverse

from apps.clientes.models import Cliente
from apps.inmuebles.models import Inmueble
from apps.seguimiento.models import SeguimientoEtapa, SolicitudAtencion


@pytest.mark.django_db
def test_flujo_basico_de_modelos():
    cliente = Cliente.objects.create(nombre="Ana", correo="ana@example.com", telefono="300")
    inmueble = Inmueble.objects.create(
        titulo="Casa", direccion="Calle 1", precio=100000000, tipo="VENTA"
    )
    solicitud = SolicitudAtencion.objects.create(cliente=cliente, inmueble=inmueble)
    SeguimientoEtapa.objects.create(solicitud=solicitud, estado_origen=1, estado_destino=2)

    assert inmueble.estado == "DISPONIBLE"
    assert solicitud.estado == "EN_ESPERA"
    assert solicitud.seguimientos.count() == 1


@pytest.mark.django_db
def test_admin_login_page_carga(client):
    assert client.get(reverse("admin:login")).status_code == 200
