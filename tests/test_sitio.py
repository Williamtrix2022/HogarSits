"""El sitio de la presentacion (site/) no debe tener enlaces rotos ni afirmar lo que no esta probado."""
import json
import re
import shutil
import subprocess
from html.parser import HTMLParser
from pathlib import Path

import pytest

from apps.analitica.services import colas

RAIZ = Path(__file__).resolve().parent.parent
SITIO = RAIZ / "site"
HTML = (SITIO / "index.html").read_text(encoding="utf-8")


class _Etiquetas(HTMLParser):
    def __init__(self):
        super().__init__()
        self.imagenes, self.enlaces, self.scripts, self.ids = [], [], [], []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if "id" in a:
            self.ids.append(a["id"])
        if tag == "img":
            self.imagenes.append(a)
        elif tag == "a" and "href" in a:
            self.enlaces.append(a["href"])
        elif tag == "script":
            self.scripts.append(a)
        elif tag == "link" and a.get("rel") == "stylesheet":
            self.enlaces.append(a["href"])


def _parsear():
    p = _Etiquetas()
    p.feed(HTML)
    return p


def test_los_archivos_locales_referenciados_existen():
    p = _parsear()
    rutas = [i["src"] for i in p.imagenes] + [s["src"] for s in p.scripts if "src" in s]
    rutas += [h for h in p.enlaces if not h.startswith(("http", "#"))]
    assert len(rutas) >= 12
    faltan = [r for r in rutas if not (SITIO / r).exists()]
    assert not faltan, faltan


def test_los_enlaces_internos_apuntan_a_secciones_existentes():
    p = _parsear()
    anclas = {h[1:] for h in p.enlaces if h.startswith("#")}
    assert anclas
    assert anclas - set(p.ids) == set()


def test_toda_imagen_tiene_texto_alternativo_y_tamano():
    for img in _parsear().imagenes:
        assert img.get("width") and img.get("height"), img["src"]
        if img.get("aria-hidden") == "true":  # decorativa: alt vacio a proposito
            assert img.get("alt") == "", img["src"]
        else:
            assert len(img.get("alt", "")) > 20, img["src"]


def test_no_carga_scripts_de_terceros():
    for s in _parsear().scripts:
        assert not s.get("src", "").startswith("http"), s


def test_declara_que_las_capturas_son_datos_simulados():
    assert "datos simulados" in HTML.lower()


def test_dice_que_aws_no_esta_verificado():
    assert "no se han verificado" in HTML
    assert "desplegado en AWS" not in HTML


def test_las_cifras_clave_coinciden_con_los_informes():
    informe = (RAIZ / "docs/pruebas/INFORME_DE_PRUEBAS.md").read_text(encoding="utf-8")
    for cifra in ("98,2 %", "3 052", "532 ms", "10 262", "31 de 31"):
        assert cifra in informe, cifra
        assert cifra in HTML.replace("&nbsp;", " "), cifra
    encuesta = (RAIZ / "docs/investigacion/resultados/RESULTADOS_ENCUESTA.md").read_text(encoding="utf-8")
    assert "**3 de 3**" in encuesta and "3 de 3" in HTML
    assert "22,748 %" in HTML


def test_el_equipo_coincide_con_el_readme():
    readme = (RAIZ / "README.md").read_text(encoding="utf-8")
    for nombre in ("William Moya Santana", "Natalia Durango", "Camilo Diaz"):
        assert nombre in readme and nombre in HTML
    assert "Elizabeth" not in HTML and "Elizabeth" not in readme  # ya no integra el equipo


_CLAVE_ESCRITA = re.compile(r"(?i)(contrase(?:ñ|n)a|password|clave)\s*[:=]\s*[`'\"]?[A-Za-z0-9]{6,}")


def test_el_sitio_enlaza_al_sistema_en_vivo_sin_credenciales():
    assert "https://hogarsits.onrender.com/" in HTML
    assert not _CLAVE_ESCRITA.search(HTML)


def test_la_sustentacion_corta_remite_a_las_claves_sin_escribirlas():
    texto = (RAIZ / "docs/presentacion/SUSTENTACION_CORTA.md").read_text(encoding="utf-8")
    assert "hogarsits.onrender.com" in texto and "no están en el repositorio" in texto
    assert not _CLAVE_ESCRITA.search(texto)


def test_no_quedan_imagenes_sin_usar_en_el_sitio():
    usadas = {Path(i["src"]).name for i in _parsear().imagenes}
    en_disco = {p.name for p in (SITIO / "img").iterdir() if p.is_file()}
    assert en_disco - usadas == set(), en_disco - usadas


def test_el_plano_respeta_reducir_movimiento():
    css = (SITIO / "css" / "sitio.css").read_text(encoding="utf-8")
    animada = css.split("@media (prefers-reduced-motion: no-preference)")[1].split("@keyframes")[0]
    assert "stroke-dashoffset" in animada
    # fuera de ese bloque el plano no debe quedar oculto ni animado
    assert "animation: trazo" not in css.replace(animada, "")


@pytest.mark.skipif(shutil.which("node") is None, reason="Node no esta instalado")
@pytest.mark.parametrize("clientes, minutos, c", [(20, 45, 2), (20, 45, 3), (20, 45, 4), (12, 25, 3), (60, 20, 2), (35, 30, 5)])
def test_la_calculadora_del_sitio_coincide_con_el_servicio_de_colas(clientes, minutos, c):
    lam, mu = clientes / 12, 60 / minutos
    salida = subprocess.run(
        ["node", "-e", f"console.log(JSON.stringify(require('./site/js/erlang.js').colaMMc({lam!r}, {mu!r}, {c})))"],
        cwd=RAIZ, capture_output=True, text=True, check=True, timeout=30,
    ).stdout
    js = json.loads(salida)
    py = colas.mmc(lam, mu, c)
    assert js["estable"] == py.estable
    assert js["rho"] == pytest.approx(py.rho, rel=1e-9)
    if py.estable:
        assert js["pEsperar"] == pytest.approx(py.p_espera, rel=1e-9)
        assert js["wqMin"] == pytest.approx(py.Wq * 60, rel=1e-9)


@pytest.mark.skipif(shutil.which("node") is None, reason="Node no esta instalado")
def test_la_calculadora_reproduce_el_ejemplo_de_la_propuesta():
    salida = subprocess.run(
        ["node", "-e", "const {colaMMc}=require('./site/js/erlang.js');"
         "console.log(JSON.stringify([2,3].map(c=>colaMMc(20/12,60/45,c).wqMin)))"],
        cwd=RAIZ, capture_output=True, text=True, check=True, timeout=30,
    ).stdout
    dos, tres = json.loads(salida)
    assert round(dos, 1) == 28.8 and round(tres, 1) == 4.0


def test_la_calculadora_dice_que_no_es_un_pronostico():
    assert "comparar escenarios" in HTML and "no para prometer minutos" in HTML
