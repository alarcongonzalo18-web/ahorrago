import json
from pathlib import Path

from app.scraper_unimarc import (
    CAMPOS,
    CATEGORIAS,
    extraer_producto,
    _datos_listado,
)
from app.fase5b_apply import TODAS_LAS_CATEGORIAS

FIXTURE = Path(__file__).parent / "fixtures" / "unimarc_categoria.json"


def _fixture():
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def test_mapeo_solo_usa_categorias_internas_validas():
    for categoria, _sub, _slug in CATEGORIAS:
        assert categoria in TODAS_LAS_CATEGORIAS, f"categoria interna invalida: {categoria}"


def test_mapeo_sin_slugs_ni_subcategorias_duplicadas():
    slugs = [slug for _c, _s, slug in CATEGORIAS]
    assert len(slugs) == len(set(slugs)), "hay slugs repetidos"
    subs = [sub for _c, sub, _s in CATEGORIAS]
    assert len(subs) == len(set(subs)), "hay subcategorias repetidas"


def test_mapeo_excluye_rubros_no_consumo():
    slugs = " ".join(slug for _c, _s, slug in CATEGORIAS)
    for excluido in ("hogar/", "perfumeria/farmacia"):
        assert excluido not in slugs, f"no deberia mapear {excluido}"


def test_mapeo_incluye_los_veganos():
    """Se excluia por creer que duplicaba los rubros normales; no es asi.

    Trae sustitutos (hamburguesas vegetales, quesos veganos) que no aparecen en
    ninguna otra categoria. Se sumo el 27-07 al auditar la cobertura real.
    """
    veganos = [s for _c, _s, s in CATEGORIAS if s.startswith("veganos-y-vegetarianos/")]
    assert len(veganos) == 4, f"faltan subcategorias veganas: {veganos}"


def test_datos_listado_lee_productos_y_total():
    productos, resource = _datos_listado(_fixture_como_nextdata())
    assert len(productos) >= 1
    assert resource > 0


def _fixture_como_nextdata():
    """El fixture guarda {resource, availableProducts}; lo envuelve como el
    __NEXT_DATA__ real para probar _datos_listado."""
    f = _fixture()
    return {"props": {"pageProps": {"dehydratedState": {"queries": [
        {"state": {"data": {"availableProducts": f["availableProducts"],
                            "resource": f["resource"]}}}
    ]}}}}


def test_extraer_producto_trae_ean_precio_y_columnas():
    prod = _fixture()["availableProducts"][0]
    fila = extraer_producto(prod, "Lacteos, Huevos y Congelados", "Leches y cremas")
    assert fila is not None
    assert set(fila.keys()) == set(CAMPOS)
    assert fila["ean"] and fila["ean"].isdigit()      # EAN directo del listado
    assert isinstance(fila["precio"], int) and fila["precio"] > 0
    assert fila["categoria"] == "Lacteos, Huevos y Congelados"


def test_extraer_producto_detecta_oferta():
    # busca en el fixture un producto en oferta (inOffer + listPrice > price)
    en_oferta = [
        p for p in _fixture()["availableProducts"]
        if (p.get("sellers") or [{}])[0].get("inOffer")
    ]
    if not en_oferta:
        return
    fila = extraer_producto(en_oferta[0], "Bebidas", "Jugos")
    assert fila["precio_oferta"] != ""
    assert fila["precio_normal"] > fila["precio"]
    assert fila["promocion"] == "Oferta"


def test_extraer_producto_sin_precio_devuelve_none():
    assert extraer_producto({"name": "X", "ean": "123", "sellers": []}, "Despensa", "Arroz y legumbres") is None
