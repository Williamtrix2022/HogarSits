"""RN-33: cada transición guarda origen, destino, fecha y hora; el historial
no se borra ni se edita.

La regla se expresa por el efecto: tras intentar editar o borrar una fila ya
guardada de SeguimientoEtapa, el intento debe rechazarse (cualquier error de
validación, permiso, integridad o protección) y la fila debe quedar intacta.
"""

import pytest
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import IntegrityError, transaction
from django.db.models import ProtectedError

from apps.seguimiento.models import SeguimientoEtapa

pytestmark = pytest.mark.django_db

RECHAZOS = (ValidationError, PermissionDenied, IntegrityError, ProtectedError)

# HALLAZGO ABIERTO (docs/requerimientos/COBERTURA_REGLAS.md): hoy la aplicación NO impide editar ni
# borrar el historial. Estas pruebas dicen cómo debe comportarse y se marcan xfail(strict=True)
# para no romper el CI: cuando se implemente la inmutabilidad pasarán, `strict` hará fallar la
# suite y bastará quitar la marca.
PENDIENTE_RN33 = pytest.mark.xfail(
    strict=True, reason="RN-33: SeguimientoEtapa aún se puede editar y borrar (hallazgo abierto)"
)


@pytest.fixture
def registro(solicitud, asesor):
    return SeguimientoEtapa.objects.create(
        solicitud=solicitud,
        estado_origen=1,
        estado_destino=2,
        registrado_por=asesor,
        nota="original",
    )


def _instantanea(pk):
    return SeguimientoEtapa.objects.values().get(pk=pk)


@PENDIENTE_RN33
def test_no_se_edita_el_destino_de_una_transicion_guardada(registro):
    """RN-33: editar una transición ya guardada se rechaza y no cambia nada."""
    antes = _instantanea(registro.pk)
    registro.estado_destino = 3
    with pytest.raises(RECHAZOS), transaction.atomic():
        registro.save()
    assert _instantanea(registro.pk) == antes


@PENDIENTE_RN33
def test_no_se_edita_la_nota_de_una_transicion_guardada(registro):
    """RN-33: ningún campo del historial se puede reescribir."""
    antes = _instantanea(registro.pk)
    registro.nota = "reescrita"
    with pytest.raises(RECHAZOS), transaction.atomic():
        registro.save()
    assert _instantanea(registro.pk) == antes


@PENDIENTE_RN33
def test_no_se_borra_una_transicion_guardada(registro):
    """RN-33: borrar una transición del historial se rechaza y la fila sigue ahí."""
    with pytest.raises(RECHAZOS), transaction.atomic():
        registro.delete()
    assert SeguimientoEtapa.objects.filter(pk=registro.pk).exists()


@PENDIENTE_RN33
def test_no_se_borra_el_historial_en_bloque(registro, solicitud):
    """RN-33: tampoco se borra por queryset."""
    with pytest.raises(RECHAZOS), transaction.atomic():
        SeguimientoEtapa.objects.filter(solicitud=solicitud).delete()
    assert SeguimientoEtapa.objects.filter(pk=registro.pk).exists()


def test_crear_nuevas_transiciones_sigue_permitido(registro, solicitud):
    """RN-33: el historial solo crece; añadir filas nuevas no se bloquea."""
    SeguimientoEtapa.objects.create(solicitud=solicitud, estado_origen=2, estado_destino=3)
    assert SeguimientoEtapa.objects.filter(solicitud=solicitud).count() == 2
