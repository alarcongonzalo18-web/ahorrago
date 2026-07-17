from app.chat import (
    MENSAJE_BIENVENIDA,
    MENSAJE_SIN_RESULTADOS,
    interpretar_item,
    interpretar_lista,
)
from app.main import app

from tests.test_integration import crear_cliente_con_datos


def test_interpretar_item_formatos_de_cantidad():
    assert interpretar_item("leche") == ("leche", 1)
    assert interpretar_item("2 leches") == ("leche", 2)
    assert interpretar_item("leche x2") == ("leche", 2)
    assert interpretar_item("leche x 2") == ("leche", 2)
    assert interpretar_item("3x arroz") == ("arroz", 3)
    assert interpretar_item("") is None
    assert interpretar_item("42") is None


def test_interpretar_item_acota_cantidad_maxima():
    assert interpretar_item("500 leches") == ("leche", 99)


def test_interpretar_lista_separadores_mixtos():
    items = interpretar_lista("2 leches, arroz y aceite\ndetergente x3")
    assert items == [("leche", 2), ("arroz", 1), ("aceite", 1), ("detergente", 3)]


def test_webhook_whatsapp_saludo_devuelve_bienvenida():
    client = crear_cliente_con_datos()
    try:
        response = client.post("/webhook/whatsapp", data={"Body": "hola"})
        assert response.status_code == 200
        assert response.headers["content-type"].startswith("application/xml")
        assert "AhorraGo" in response.text
        assert "<Response><Message>" in response.text
    finally:
        app.dependency_overrides.clear()


def test_webhook_whatsapp_lista_devuelve_comparacion():
    client = crear_cliente_con_datos()
    try:
        # Fixture: Leche Soprole en Lider ($1200) y Jumbo ($1100), mismo producto_base.
        response = client.post("/webhook/whatsapp", data={"Body": "2 leches"})
        assert response.status_code == 200
        texto = response.text
        assert "Jumbo" in texto
        assert "$1.100" in texto
        assert "Más barato" in texto or "barato" in texto
    finally:
        app.dependency_overrides.clear()


def test_webhook_whatsapp_producto_inexistente():
    client = crear_cliente_con_datos()
    try:
        response = client.post("/webhook/whatsapp", data={"Body": "kriptonita"})
        assert response.status_code == 200
        assert MENSAJE_SIN_RESULTADOS.split("\n")[0] in response.text
    finally:
        app.dependency_overrides.clear()


def test_webhook_whatsapp_body_vacio_no_revienta():
    client = crear_cliente_con_datos()
    try:
        response = client.post("/webhook/whatsapp", data={})
        assert response.status_code == 200
        assert MENSAJE_BIENVENIDA.split("\n")[0] in response.text
    finally:
        app.dependency_overrides.clear()
