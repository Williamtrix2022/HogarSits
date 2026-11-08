import pytest
from django.urls import reverse

from apps.seguimiento.models import SeguimientoEtapa


@pytest.mark.django_db
def test_flujo_basico_de_modelos(solicitud, inmueble):
    SeguimientoEtapa.objects.create(solicitud=solicitud, estado_origen=1, estado_destino=2)

    assert inmueble.estado == "DISPONIBLE"
    assert solicitud.estado == "EN_ESPERA"
    assert solicitud.etapa_actual == 1
    assert solicitud.seguimientos.count() == 1


@pytest.mark.django_db
def test_admin_login_page_carga(client):
    assert client.get(reverse("admin:login")).status_code == 200
