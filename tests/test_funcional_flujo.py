"""Pruebas funcionales: la jornada completa de una inmobiliaria, de punta a punta (#42).

Recorre las pantallas por HTTP, como lo haría una persona, y comprueba en cada paso lo que
vería en pantalla y lo que queda guardado. Une las historias HU-01 a HU-13 en un solo recorrido:
no reemplaza a las pruebas unitarias de cada regla, comprueba que **las piezas encajan**.
"""

from datetime import timedelta

import pytest
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import Client
from django.urls import reverse
from django.utils import timezone

from apps.agenda.models import HorarioAsesor, Visita
from apps.clientes.models import Cliente
from apps.cuentas.roles import ROL_ADMIN, asignar_rol
from apps.inmuebles.models import Inmueble
from apps.seguimiento.models import Etapa, SeguimientoEtapa, SolicitudAtencion

User = get_user_model()

pytestmark = pytest.mark.django_db

CLAVE_ADMIN = "Clave-Del-Jefe-2026"
CLAVE_ASESOR = "Clave-Segura-2026"
CLAVE_NUEVA = "Otra-Clave-Mas-Larga-2026"


def texto(respuesta) -> str:
    return respuesta.content.decode()


def entrar(usuario: str, clave: str) -> Client:
    c = Client()
    r = c.post(reverse("cuentas:login"), {"username": usuario, "password": clave})
    assert r.status_code == 302, f"{usuario} no pudo iniciar sesión"
    return c


def en_dos_dias(hora=10, minuto=0) -> str:
    base = timezone.localtime(timezone.now()) + timedelta(days=2)
    return base.replace(hour=hora, minute=minuto, second=0, microsecond=0).strftime("%Y-%m-%dT%H:%M")


@pytest.fixture
def jefe():
    u = User.objects.create_user("jefe", password=CLAVE_ADMIN, first_name="Jefa")
    asignar_rol(u, ROL_ADMIN)
    return u


def test_jornada_completa_de_una_inmobiliaria(jefe):  # noqa: PLR0915  (es un recorrido largo)
    admin = entrar("jefe", CLAVE_ADMIN)

    # --- 1. El administrador da de alta a un asesor y le carga el horario (HU-11, RF-36) -------
    r = admin.post(reverse("cuentas:usuario_nuevo"), {
        "username": "ana", "first_name": "Ana", "last_name": "Pérez", "email": "ana@inmo.co",
        "password1": CLAVE_ASESOR, "password2": CLAVE_ASESOR, "rol": "Asesor",
    }, follow=True)
    assert "Usuario ana creado" in texto(r)
    ana = User.objects.get(username="ana")
    r = admin.post(reverse("horarios:asesor", args=[ana.pk]),
                   {"dias": ["0", "1", "2", "3", "4", "5"], "hora_inicio": "08:00", "hora_fin": "18:00"},
                   follow=True)
    assert "Turno agregado a 6 día(s)" in texto(r)
    assert HorarioAsesor.objects.filter(asesor=ana).count() == 6

    # --- 2. El administrador registra un inmueble (HU-01) ---------------------------------------
    r = admin.post(reverse("inmuebles:crear"), {
        "titulo": "Casa en Cantaclaro", "tipo_inmueble": "CASA", "operacion": "VENTA",
        "direccion": "Calle 30 # 12-45", "barrio": "Cantaclaro", "precio": "240.000.000",
        "area_m2": "120", "habitaciones": "3", "estado": "DISPONIBLE", "descripcion": "Esquinera",
    }, follow=True)
    assert "creado" in texto(r)
    casa = Inmueble.objects.get(titulo="Casa en Cantaclaro")
    assert casa.estado == "DISPONIBLE" and casa.activo and casa.precio == 240_000_000

    # --- 3. La asesora entra: una clave mala no la bloquea, la buena sí la deja pasar (RNF-04) --
    anonimo = Client()
    for _ in range(3):
        r = anonimo.post(reverse("cuentas:login"), {"username": "ana", "password": "incorrecta"})
        assert "Usuario o contraseña incorrectos" in texto(r)
    asesora = entrar("ana", CLAVE_ASESOR)
    inicio = texto(asesora.get(reverse("cuentas:inicio")))
    assert "Todo al día" in inicio  # aún no hay solicitudes pendientes

    # --- 4. Registra al cliente; el correo repetido se rechaza (HU-03, RN-10) -------------------
    datos_cliente = {"nombre": "Pedro Ramírez", "correo": "pedro@correo.com", "telefono": "300 123 4567"}
    r = asesora.post(reverse("clientes:crear"), datos_cliente, follow=True)
    assert "Pedro Ramírez" in texto(r)
    r = asesora.post(reverse("clientes:crear"), {**datos_cliente, "correo": "PEDRO@correo.com"})
    assert r.status_code == 200 and "Ya existe un cliente con este correo" in texto(r)
    assert Cliente.objects.count() == 1
    pedro = Cliente.objects.get()

    # --- 5. Llega Pedro: solicitud con hora automática, en espera (HU-04, RN-11) ---------------
    r = asesora.post(reverse("seguimiento:crear"), {
        "cliente": pedro.pk, "tipo_interes": "COMPRA", "inmueble": casa.pk, "presupuesto": "250.000.000",
    }, follow=True)
    assert "registrada: en espera" in texto(r) and "Pedro Ramírez" in texto(r)
    sol = SolicitudAtencion.objects.get()
    assert sol.estado == "EN_ESPERA" and sol.timestamp_llegada is not None
    assert sol.etapa_actual == Etapa.CONSULTA  # RN-32

    # --- 6. La asesora lo atiende: pasa a «en atención» y queda como responsable (RN-12) -------
    asesora.post(reverse("seguimiento:tomar", args=[sol.pk]))
    sol.refresh_from_db()
    assert sol.estado == "EN_ATENCION" and sol.asesor == ana
    assert sol.timestamp_inicio_atencion >= sol.timestamp_llegada  # RN-20

    # --- 7. Agenda una visita; un cruce se rechaza y nombra con qué se cruza (HU-05) ------------
    r = asesora.post(reverse("agenda:crear"), {
        "solicitud": sol.pk, "inmueble": casa.pk, "asesor": ana.pk,
        "inicio": en_dos_dias(10), "duracion": 60,
    }, follow=True)
    assert "Visita agendada" in texto(r)
    visita = Visita.objects.get()
    cruce = asesora.post(reverse("agenda:crear"), {
        "solicitud": sol.pk, "inmueble": casa.pk, "asesor": ana.pk,
        "inicio": en_dos_dias(10, 30), "duracion": 60,
    })
    assert cruce.status_code == 200 and "ya tiene una visita" in texto(cruce)
    assert Visita.objects.count() == 1
    # un horario contiguo sí se permite (RN-01: [inicio, fin))
    asesora.post(reverse("agenda:crear"), {
        "solicitud": sol.pk, "inmueble": casa.pk, "asesor": ana.pk,
        "inicio": en_dos_dias(11), "duracion": 30,
    })
    assert Visita.objects.exclude(estado="CANCELADA").count() == 2

    # --- 8. Reprogramar conserva la original como cancelada; cancelar libera el horario --------
    asesora.post(reverse("agenda:reprogramar", args=[visita.pk]),
                 {"inicio": en_dos_dias(15), "duracion": 60})
    visita.refresh_from_db()
    assert visita.estado == "CANCELADA"
    nueva = Visita.objects.get(reemplaza_a=visita)
    assert nueva.estado == "PROGRAMADA"
    asesora.post(reverse("agenda:cancelar", args=[nueva.pk]))
    asesora.post(reverse("agenda:crear"), {  # el horario liberado se puede volver a usar (RN-04)
        "solicitud": sol.pk, "inmueble": casa.pk, "asesor": ana.pk,
        "inicio": en_dos_dias(15), "duracion": 60,
    })
    assert Visita.objects.filter(estado="PROGRAMADA", inicio__hour__in=[15, 20]).exists()

    # --- 9. Avanza por las etapas: no se puede saltar (RN-30), se cierra y se marca el inmueble --
    saltar = asesora.post(reverse("seguimiento:etapa", args=[sol.pk]), {"etapa": Etapa.CIERRE.value})
    assert saltar.status_code == 200  # el formulario no ofrece Cierre desde Consulta
    sol.refresh_from_db()
    assert sol.etapa_actual == Etapa.CONSULTA
    asesora.post(reverse("seguimiento:etapa", args=[sol.pk]),
                 {"etapa": Etapa.CONSULTA.value, "nota": "no contestó"})  # sin avance (ADR-002)
    asesora.post(reverse("seguimiento:etapa", args=[sol.pk]), {"etapa": Etapa.VISITA.value})
    asesora.post(reverse("seguimiento:etapa", args=[sol.pk]), {"etapa": Etapa.NEGOCIACION.value})
    r = asesora.post(reverse("seguimiento:etapa", args=[sol.pk]),
                     {"etapa": Etapa.CIERRE.value, "marcar_inmueble": "on"}, follow=True)
    assert "quedó como Vendido" in texto(r)
    sol.refresh_from_db()
    casa.refresh_from_db()
    assert sol.etapa_actual == Etapa.CIERRE and casa.estado == "VENDIDO"
    pares = list(SeguimientoEtapa.objects.order_by("id").values_list("estado_origen", "estado_destino"))
    assert pares == [(1, 1), (1, 2), (2, 3), (3, 4)]  # el historial, incluida la autotransición
    final = asesora.post(reverse("seguimiento:etapa", args=[sol.pk]), {"etapa": Etapa.VISITA.value})
    assert final.status_code == 200  # una solicitud cerrada no admite más cambios (RN-31)

    # --- 10. Termina la atención; un inmueble vendido ya no se ofrece (HU-02, RN-03) ------------
    asesora.post(reverse("seguimiento:finalizar", args=[sol.pk]))
    sol.refresh_from_db()
    assert sol.estado == "FINALIZADO" and sol.timestamp_fin_atencion >= sol.timestamp_inicio_atencion
    r = asesora.post(reverse("seguimiento:crear"), {
        "cliente": pedro.pk, "tipo_interes": "COMPRA", "inmueble": casa.pk})
    assert r.status_code == 200 and "no se puede ofrecer" in texto(r)

    # --- 11. Otro cliente deja una solicitud sin seguimiento: sale en «a quién contactar» ------
    luis = Cliente.objects.create(nombre="Luis Gómez", correo="luis@correo.com", telefono="3110000000")
    vieja = SolicitudAtencion.objects.create(
        cliente=luis, asesor=ana, tipo_interes="ALQUILER",
        timestamp_llegada=timezone.now() - timedelta(days=9), estado="EN_ATENCION",
        timestamp_inicio_atencion=timezone.now() - timedelta(days=9))
    inicio = texto(asesora.get(reverse("cuentas:inicio")))
    assert "Luis Gómez" in inicio and "Sin seguimiento" in inicio and "sin movimiento hace 9 días" in inicio
    assert vieja.etapa_actual == Etapa.CONSULTA

    # --- 12. Permisos: la asesora no entra a la administración ni al análisis (RF-02) -----------
    for destino in ("cuentas:usuarios", "analitica:inicio", "horarios:lista"):
        assert asesora.get(reverse(destino)).status_code == 403, destino

    # --- 13. Sus indicadores reflejan lo que hizo (HU-13); solo ve los suyos --------------------
    mis = texto(asesora.get(reverse("analitica:asesores")))
    assert "Mis indicadores" in mis and "Ana Pérez" in mis
    assert "Jefa" not in mis and "Equipo" not in mis  # solo su fila

    # --- 14. Cambia su contraseña y la nueva funciona (RF-03) -----------------------------------
    r = asesora.post(reverse("cuentas:clave_cambiar"), {
        "old_password": CLAVE_ASESOR, "new_password1": CLAVE_NUEVA, "new_password2": CLAVE_NUEVA})
    assert r.status_code == 302
    entrar("ana", CLAVE_NUEVA)

    # --- 15. El administrador ve el análisis, los indicadores del equipo y descarga un CSV ------
    panel = admin.get(reverse("analitica:inicio"))
    assert panel.status_code == 200 and "¿Cuándo llegan los clientes?" in texto(panel)
    equipo = texto(admin.get(reverse("analitica:asesores")))
    assert "Equipo" in equipo and "Ana Pérez" in equipo
    descarga = admin.get(reverse("analitica:exportar"), {"tabla": "asesores"})
    assert descarga.status_code == 200 and "attachment" in descarga["Content-Disposition"]
    assert "Ana Pérez;2;0;1;" in descarga.content.decode("utf-8-sig")  # 2 atendidas, 1 cierre


def test_jornada_de_analisis_con_datos_simulados(jefe):
    """El administrador genera datos de prueba y recorre todo el análisis sin errores."""
    call_command("seed_datos_simulados", "--dias", "45", "--semilla", "3")
    admin = entrar("jefe", CLAVE_ADMIN)
    for destino, args in [("analitica:inicio", {}), ("analitica:asesores", {}),
                          ("horarios:lista", {}), ("horarios:disponibilidad", {}),
                          ("seguimiento:cola", {}), ("seguimiento:pendientes", {}),
                          ("agenda:semana", {}), ("inmuebles:lista", {}), ("clientes:lista", {}),
                          ("cuentas:inicio", {}), ("cuentas:usuarios", {})]:
        r = admin.get(reverse(destino), args)
        assert r.status_code == 200, destino
    for tabla in ("lambda", "poisson", "colas", "matriz", "absorcion", "asesores"):
        assert admin.get(reverse("analitica:exportar"), {"tabla": tabla}).status_code == 200, tabla
    assert "incluye datos simulados" in texto(admin.get(reverse("analitica:inicio")))


def test_ninguna_pantalla_es_publica_salvo_el_acceso():
    """RNF-04: toda ruta exige sesión; solo el inicio de sesión es público."""
    anonimo = Client()
    protegidas = [
        reverse(n) for n in ("cuentas:inicio", "cuentas:usuarios", "inmuebles:lista", "clientes:lista",
                             "seguimiento:cola", "seguimiento:pendientes", "agenda:semana",
                             "analitica:inicio", "analitica:asesores", "horarios:lista",
                             "cuentas:clave_cambiar")
    ]
    for url in protegidas:
        r = anonimo.get(url)
        assert r.status_code == 302 and "ingresar" in r["Location"], url
    assert anonimo.get(reverse("cuentas:login")).status_code == 200
