"""Endurecimiento de la API (Fase 2.3).

Regla de diseño: sin variables de entorno la API se comporta como siempre. El
endurecimiento se enciende en el servidor, no estorba en desarrollo ni en tests.
"""

import pytest

from app.seguridad import (
    LimitadorMemoria,
    ORIGENES_LOCALES,
    origenes_permitidos,
    verificar_admin,
)


class _Request:
    """Request minimo: solo lo que mira verificar_admin / ip_del_cliente."""

    def __init__(self, headers=None, query=None, ip="1.2.3.4"):
        self.headers = headers or {}
        self.query_params = query or {}
        self.client = type("C", (), {"host": ip})()


# --- CORS -------------------------------------------------------------------

def test_sin_configurar_solo_acepta_la_red_local(monkeypatch):
    monkeypatch.delenv("AHORRAGO_ORIGENES", raising=False)
    assert origenes_permitidos() == ORIGENES_LOCALES


def test_los_dominios_configurados_se_suman_sin_perder_la_red_local(monkeypatch):
    monkeypatch.setenv("AHORRAGO_ORIGENES", "https://ahorrago.cl, https://www.ahorrago.cl")
    patron = origenes_permitidos()
    assert ORIGENES_LOCALES in patron
    import re
    assert re.fullmatch(patron, "https://ahorrago.cl")
    assert re.fullmatch(patron, "http://localhost:5500")
    assert not re.fullmatch(patron, "https://sitio-cualquiera.cl")


# --- endpoints internos -----------------------------------------------------

def test_sin_token_configurado_los_internos_siguen_abiertos(monkeypatch):
    """Modo desarrollo: nadie tiene que definir variables para trabajar local."""
    monkeypatch.delenv("AHORRAGO_ADMIN_TOKEN", raising=False)
    assert verificar_admin(_Request()) is True


def test_con_token_configurado_exige_el_header(monkeypatch):
    monkeypatch.setenv("AHORRAGO_ADMIN_TOKEN", "secreto")
    from fastapi import HTTPException

    with pytest.raises(HTTPException) as exc:
        verificar_admin(_Request())
    # 404 y no 401: no confirmamos que el endpoint exista
    assert exc.value.status_code == 404

    assert verificar_admin(_Request(headers={"x-admin-token": "secreto"})) is True
    assert verificar_admin(_Request(query={"token": "secreto"})) is True


def test_token_equivocado_no_pasa(monkeypatch):
    monkeypatch.setenv("AHORRAGO_ADMIN_TOKEN", "secreto")
    from fastapi import HTTPException

    with pytest.raises(HTTPException):
        verificar_admin(_Request(headers={"x-admin-token": "otro"}))


# --- rate limiting ----------------------------------------------------------

def test_corta_al_pasarse_del_limite():
    lim = LimitadorMemoria(limite=3, ventana=60)
    assert [lim.permitido("1.1.1.1", ahora=0) for _ in range(3)] == [True] * 3
    assert lim.permitido("1.1.1.1", ahora=0) is False


def test_el_limite_es_por_ip():
    lim = LimitadorMemoria(limite=2, ventana=60)
    lim.permitido("1.1.1.1", ahora=0)
    lim.permitido("1.1.1.1", ahora=0)
    assert lim.permitido("1.1.1.1", ahora=0) is False
    assert lim.permitido("2.2.2.2", ahora=0) is True     # otra IP no se ve afectada


def test_la_ventana_es_deslizante():
    lim = LimitadorMemoria(limite=2, ventana=60)
    lim.permitido("1.1.1.1", ahora=0)
    lim.permitido("1.1.1.1", ahora=30)
    assert lim.permitido("1.1.1.1", ahora=31) is False
    # a los 61s la primera visita ya salio de la ventana
    assert lim.permitido("1.1.1.1", ahora=61) is True


def test_limite_cero_desactiva_el_control():
    lim = LimitadorMemoria(limite=0)
    assert all(lim.permitido("1.1.1.1", ahora=0) for _ in range(500))


def test_limpiar_no_deja_crecer_la_memoria():
    lim = LimitadorMemoria(limite=5, ventana=60)
    for i in range(50):
        lim.permitido(f"10.0.0.{i}", ahora=0)
    assert len(lim._visitas) == 50
    lim.limpiar(ahora=120)          # todas viejas
    assert lim._visitas == {}


# --- integracion con la app real -------------------------------------------

def test_la_api_responde_429_al_pasarse(monkeypatch):
    """El middleware corta de verdad, no solo el limitador aislado."""
    from fastapi.testclient import TestClient
    from app import seguridad
    from app.main import app

    monkeypatch.setattr(seguridad, "limitador", LimitadorMemoria(limite=3, ventana=60))
    cliente = TestClient(app)

    codigos = [cliente.get("/").status_code for _ in range(5)]
    assert codigos[:3] == [200, 200, 200]
    assert codigos[3:] == [429, 429]
    assert "Demasiadas" in cliente.get("/").json()["detail"]


def test_los_endpoints_internos_quedan_ocultos_con_token(monkeypatch):
    from fastapi.testclient import TestClient
    from app import seguridad
    from app.main import app

    monkeypatch.setattr(seguridad, "limitador", LimitadorMemoria(limite=0))
    monkeypatch.setenv("AHORRAGO_ADMIN_TOKEN", "s3cr3t0")
    cliente = TestClient(app)

    assert cliente.get("/").status_code == 200                  # publico, sigue abierto
    assert cliente.get("/estado-datos").status_code == 404       # oculto
    assert cliente.get("/diagnostico/matching").status_code == 404
    assert cliente.get("/estado-datos",
                       headers={"x-admin-token": "s3cr3t0"}).status_code == 200
