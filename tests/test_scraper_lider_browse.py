"""Tests del PoC del endpoint nuevo de Lider (SPA de Walmart).

Cubren el PARSEO del __NEXT_DATA__ con un fixture real (3 productos + 1 banner).
El transporte (bajar el HTML pasando Akamai) queda fuera: es lo unico pendiente
para cablear este scraper al pipeline. Ver app/docs/lider-endpoint-nuevo.md.
"""

import json
from pathlib import Path

from app.scraper_lider import CAMPOS
from app.scraper_lider_browse import (
    _normalizar_ean,
    extraer_next_data,
    productos_desde_next_data,
    total_y_paginas,
)

FIXTURE = Path(__file__).parent / "fixtures" / "lider_browse_jabon_p2.json"


def _next_data():
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def test_normalizar_ean_saca_ceros_a_la_izquierda():
    assert _normalizar_ean("00780500031555") == "780500031555"
    assert _normalizar_ean("") == ""
    assert _normalizar_ean(None) == ""


def test_extraer_next_data_devuelve_none_ante_challenge():
    assert extraer_next_data("<html><head><title>Robot or human?</title></head></html>") is None


def test_extraer_next_data_parsea_el_script():
    html = '<html><body><script id="__NEXT_DATA__" type="application/json">' \
           + FIXTURE.read_text(encoding="utf-8") + "</script></body></html>"
    nd = extraer_next_data(html)
    assert nd is not None
    assert total_y_paginas(nd) == (144, 4)


def test_productos_desde_next_data_ignora_banners_y_mapea_campos():
    prods = productos_desde_next_data(_next_data(), "Higiene", "Jabon")
    # 3 productos con usItemId; el banner sin usItemId se ignora
    assert len(prods) == 3
    # todas las columnas esperadas por el pipeline
    for p in prods:
        assert set(p) == set(CAMPOS)
    primero = prods[0]
    assert primero["ean"] == "773021902133"          # EAN sin ceros a la izquierda
    assert primero["subcategoria"] == "Jabon"
    # Los precios se guardan como ENTEROS, igual que en las otras 3 cadenas: el
    # SPA los entrega formateados ("$1.000") y el CSV del pipeline usa numeros.
    assert primero["precio"] == 1000                 # linePrice (lo que se paga)
    assert primero["precio_normal"] == 1450          # wasPrice (lista)
    assert primero["url"] == "/ip/jabones/00773021902133"


def test_productos_toma_itemprice_si_no_hay_oferta():
    # El tercer item no tiene wasPrice ni itemPrice, solo linePrice.
    prods = productos_desde_next_data(_next_data(), "Higiene", "Jabon")
    tercero = prods[2]
    assert tercero["precio"] == 2150


def test_precios_formateados_pasan_a_enteros():
    """El SPA nuevo da "$14.690" (string), no numeros. Caso real de Jabones."""
    from app.scraper_lider_browse import productos_desde_next_data

    next_data = {"props": {"pageProps": {"initialData": {"searchResult": {"itemStacks": [{"items": [{
        "usItemId": "00780500031555",
        "name": "Jabon Corporal Dove Revitalizante",
        "priceInfo": {"itemPrice": "$14.690", "linePrice": "$11.690",
                      "wasPrice": "$14.690", "savings": "Ahorra $3.000"},
    }]}]}}}}}
    p = productos_desde_next_data(next_data, "Higiene Personal", "Jabones")[0]
    assert p["precio"] == 11690          # el que se paga
    assert p["precio_normal"] == 14690   # el de lista
    assert p["precio_oferta"] == 11690   # hay descuento
    assert p["ean"] == "780500031555"    # usItemId sin ceros a la izquierda


def test_sin_descuento_no_marca_oferta():
    from app.scraper_lider_browse import productos_desde_next_data

    next_data = {"props": {"pageProps": {"initialData": {"searchResult": {"itemStacks": [{"items": [{
        "usItemId": "00780500031555", "name": "X",
        "priceInfo": {"itemPrice": "$3.690", "linePrice": "$3.690"},
    }]}]}}}}}
    p = productos_desde_next_data(next_data, "C", "S")[0]
    assert p["precio"] == 3690 and p["precio_normal"] == 3690
    assert p["precio_oferta"] == ""
