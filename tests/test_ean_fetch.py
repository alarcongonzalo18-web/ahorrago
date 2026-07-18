from app.ean_fetch import (
    ean_desde_respuesta_jumbo,
    ean_desde_respuesta_tottus,
    ean_desde_respuesta_unimarc,
    extraer_next_data,
    normalizar_ean,
    slug_jumbo,
    slug_tottus,
    slug_unimarc,
)


def test_normalizar_ean_quita_no_digitos_y_ceros():
    assert normalizar_ean("00780292077754") == "780292077754"
    assert normalizar_ean("7802920000084") == "7802920000084"
    # separadores se limpian; queda EAN válido de 13 dígitos
    assert normalizar_ean("7-802-920-000-084") == "7802920000084"
    # demasiado corto tras limpiar -> ""
    assert normalizar_ean("7802920") == ""
    assert normalizar_ean("0000123") == ""
    assert normalizar_ean("") == ""
    assert normalizar_ean(None) == ""


def test_slug_jumbo():
    assert slug_jumbo("https://www.jumbo.cl/leche-entera-colun-caja-1-l-natural/p") == "leche-entera-colun-caja-1-l-natural"
    assert slug_jumbo("https://www.jumbo.cl/m-ideal-bco-xl-750/p?utm=x") == "m-ideal-bco-xl-750"
    assert slug_jumbo("https://www.jumbo.cl/leches") == ""
    assert slug_jumbo("") == ""


def test_slug_unimarc():
    assert slug_unimarc("https://www.unimarc.cl/product/leche-entera-natural-colun-sin-tapa-1-l-2") == "leche-entera-natural-colun-sin-tapa-1-l-2"
    assert slug_unimarc("https://www.unimarc.cl/product/arroz-g2?ref=1") == "arroz-g2"
    assert slug_unimarc("https://www.unimarc.cl/search?q=leche") == ""
    assert slug_unimarc("") == ""


def test_ean_desde_respuesta_jumbo():
    data = {"slug": "x", "items": [{"ean": "7803473002662", "name": "Pan"}]}
    assert ean_desde_respuesta_jumbo(data) == "7803473002662"
    # sin items o sin ean
    assert ean_desde_respuesta_jumbo({"items": []}) == ""
    assert ean_desde_respuesta_jumbo({}) == ""
    assert ean_desde_respuesta_jumbo(None) == ""
    # primer item sin ean, segundo con ean
    assert ean_desde_respuesta_jumbo({"items": [{"ean": ""}, {"ean": "7801234567890"}]}) == "7801234567890"


def test_ean_desde_respuesta_unimarc():
    data = {"products": [{"item": {"ean": "7848004940150", "name": "Arroz"}}]}
    assert ean_desde_respuesta_unimarc(data) == "7848004940150"
    assert ean_desde_respuesta_unimarc({"products": []}) == ""
    assert ean_desde_respuesta_unimarc({"products": [{"item": {}}]}) == ""
    assert ean_desde_respuesta_unimarc(None) == ""


def test_slug_tottus():
    u = "https://www.tottus.cl/tottus-cl/articulo/112737597/leche-natural-colun-st-1-lt"
    assert slug_tottus(u) == "/tottus-cl/articulo/112737597/leche-natural-colun-st-1-lt"
    # con query o fragmento se corta ahi
    assert slug_tottus(u + "?utm=x") == "/tottus-cl/articulo/112737597/leche-natural-colun-st-1-lt"
    # urls que no son de articulo
    assert slug_tottus("https://www.tottus.cl/tottus-cl/buscar?Ntt=leche") == ""
    assert slug_tottus("") == ""


def test_extraer_next_data():
    html = '<html><body><script id="__NEXT_DATA__" type="application/json">{"a":1}</script></body></html>'
    assert extraer_next_data(html) == {"a": 1}
    assert extraer_next_data("<html>sin next data</html>") is None
    # JSON roto no revienta
    assert extraer_next_data('<script id="__NEXT_DATA__">{roto</script>') is None
    assert extraer_next_data("") is None


def test_ean_desde_respuesta_tottus():
    # el EAN vive en variants[].okayToShopBarcodes (el nombre no dice "ean")
    data = {"props": {"pageProps": {"productData": {
        "variants": [{"okayToShopBarcodes": ["7802920777542"]}]
    }}}}
    assert ean_desde_respuesta_tottus(data) == "7802920777542"
    # sin codigos / sin variantes / vacio
    assert ean_desde_respuesta_tottus({"props": {"pageProps": {"productData": {"variants": [{}]}}}}) == ""
    assert ean_desde_respuesta_tottus({"props": {"pageProps": {}}}) == ""
    assert ean_desde_respuesta_tottus(None) == ""
    # primera variante sin codigo, segunda con codigo
    data2 = {"props": {"pageProps": {"productData": {"variants": [
        {"okayToShopBarcodes": []}, {"okayToShopBarcodes": ["7801234567890"]},
    ]}}}}
    assert ean_desde_respuesta_tottus(data2) == "7801234567890"
