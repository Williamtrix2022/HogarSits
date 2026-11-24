"""El informe final (docs/informe) debe coincidir con sus fuentes y no inventar datos reales."""
import re
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
INFORME = (RAIZ / "docs" / "informe" / "INFORME_FINAL.md").read_text(encoding="utf-8")


def _leer(ruta: str) -> str:
    return (RAIZ / ruta).read_text(encoding="utf-8")


def test_las_cifras_de_pruebas_coinciden_con_el_informe_de_pruebas():
    fuente = _leer("docs/pruebas/INFORME_DE_PRUEBAS.md")
    for cifra in ("98,2 %", "3 052", "532 ms", "10 262", "31 de 31"):
        assert cifra in fuente, cifra
        assert cifra in INFORME, cifra
    assert "**700**" in fuente and "700 pruebas" in INFORME
    assert "681" in fuente and "681" in INFORME


def test_las_cifras_de_validacion_coinciden_con_su_documento():
    fuente = _leer("docs/diseno/VALIDACION_MODELOS.md")
    for cifra in ("9,7 min", "0,15", "1,6", "12,3", "2,6 a 6,5"):
        assert cifra in fuente, cifra
        assert cifra in INFORME, cifra


def test_la_encuesta_citada_coincide_con_sus_resultados():
    fuente = _leer("docs/investigacion/resultados/RESULTADOS_ENCUESTA.md")
    assert "**3 de 3**" in fuente and "n = 3" in INFORME
    assert "Perder una solicitud sin seguimiento (P4) | **3 de 3**" in fuente


def test_la_seccion_de_datos_reales_sigue_marcada_como_pendiente():
    seccion = INFORME.split("## 7. Resultados con datos reales")[1].split("\n## 8.")[0]
    assert "PENDIENTE" in seccion
    assert "No se rellena con datos simulados ni inventados" in seccion
    assert seccion.count("*por completar*") >= 5


def test_declara_los_limites_principales():
    for frase in ("Nunca se probó con datos reales", "orden de magnitud", "RN-33", "No está desplegado en AWS"):
        assert frase in INFORME, frase


def test_los_documentos_del_anexo_existen():
    rutas = set(re.findall(r"`((?:docs|site|tests|apps)/[^`\s]+?)`", INFORME))
    assert len(rutas) >= 10
    faltan = [r for r in sorted(rutas) if not (RAIZ / r.rstrip("/")).exists()]
    assert not faltan, faltan


def test_el_equipo_coincide_con_el_readme():
    readme = _leer("README.md")
    for nombre in ("William Moya Santana", "Natalia Durango", "Camilo Diaz", "Elizabeth Camaño"):
        assert nombre in readme and nombre in INFORME
