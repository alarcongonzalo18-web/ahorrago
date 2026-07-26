"""EAN de Jumbo por lotes via el catalogo VTEX.

El BFF de a uno (fetch_ean_jumbo) bloquea a las pocas consultas — medido el
26-07-2026: corta en la 3a — asi que con ~34.000 fichas el backfill nunca
terminaba. VTEX responde 50 productos por request y trae el EAN.
"""

from app.ean_fetch import eans_desde_respuesta_vtex, fetch_eans_jumbo_por_id


def _producto(pid, ean, nombre="X"):
    return {"productId": pid, "productName": nombre, "items": [{"ean": ean}]}


def test_extrae_ean_por_product_id():
    data = [_producto("6797", "7802900121013"), _producto("6782", "7802930005710")]
    assert eans_desde_respuesta_vtex(data) == {
        "6797": "7802900121013",
        "6782": "7802930005710",
    }


def test_ignora_productos_sin_ean_o_sin_items():
    data = [
        _producto("1", ""),
        {"productId": "2", "items": []},
        {"productId": "3"},
        _producto("4", "7802900121013"),
    ]
    assert eans_desde_respuesta_vtex(data) == {"4": "7802900121013"}


def test_respuesta_vacia_o_none_no_revienta():
    assert eans_desde_respuesta_vtex([]) == {}
    assert eans_desde_respuesta_vtex(None) == {}


def test_sin_ids_no_hace_request():
    # si intentara pegarle a la red, el test fallaria offline
    assert fetch_eans_jumbo_por_id([]) == {}
    assert fetch_eans_jumbo_por_id([None, ""]) == {}
