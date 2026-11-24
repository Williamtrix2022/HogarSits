"""El sitio de la presentacion (site/) no debe tener enlaces rotos ni afirmar lo que no esta probado."""
import re
from html.parser import HTMLParser
from pathlib import Path

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
        assert len(img.get("alt", "")) > 20, img["src"]
        assert img.get("width") and img.get("height"), img["src"]


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
    for nombre in ("William Moya Santana", "Natalia Durango", "Camilo Diaz", "Elizabeth Camaño"):
        assert nombre in readme and nombre in HTML


_CLAVE_ESCRITA = re.compile(r"(?i)(contrase(?:ñ|n)a|password|clave)\s*[:=]\s*[`'\"]?[A-Za-z0-9]{6,}")


def test_el_sitio_enlaza_al_sistema_en_vivo_sin_credenciales():
    assert "https://hogarsits.onrender.com/" in HTML
    assert not _CLAVE_ESCRITA.search(HTML)


def test_la_sustentacion_corta_remite_a_las_claves_sin_escribirlas():
    texto = (RAIZ / "docs/presentacion/SUSTENTACION_CORTA.md").read_text(encoding="utf-8")
    assert "hogarsits.onrender.com" in texto and "no están en el repositorio" in texto
    assert not _CLAVE_ESCRITA.search(texto)
