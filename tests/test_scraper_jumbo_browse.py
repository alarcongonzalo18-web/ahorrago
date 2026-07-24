import json
from pathlib import Path

from app.scraper_jumbo_real import CATEGORIAS, extraer_producto, construir_url
from app.fase5b_apply import TODAS_LAS_CATEGORIAS

FIXTURE = Path(__file__).parent / "fixtures" / "jumbo_browse.json"


def _resultados():
    return json.loads(FIXTURE.read_text(encoding="utf-8"))["results"]


def test_mapeo_solo_usa_categorias_internas_validas():
    for categoria, _sub, _gid in CATEGORIAS:
        assert categoria in TODAS_LAS_CATEGORIAS, f"categoria interna invalida: {categoria}"


def test_mapeo_sin_group_ids_ni_subcategorias_duplicadas():
    gids = [gid for _c, _s, gid in CATEGORIAS]
    assert len(gids) == len(set(gids)), "hay group_ids repetidos"
    subs = [sub for _c, sub, _s in CATEGORIAS]
    assert len(subs) == len(set(subs)), "hay subcategorias repetidas"


def test_construir_url_usa_browse_por_group_id():
    url = construir_url("953", 2)
    assert "/browse/group_id/953" in url
    assert "page=2" in url and "num_results_per_page=100" in url


def test_extraer_producto_parsea_browse():
    prod = extraer_producto(_resultados()[0], "Lacteos, Huevos y Congelados", "Mantequillas y Margarinas")
    assert prod is not None
    assert prod["nombre"]
    assert isinstance(prod["precio"], int) and prod["precio"] > 0
    assert prod["categoria"] == "Lacteos, Huevos y Congelados"
    # Jumbo no expone EAN en el listado: lo llena app.backfill_ean despues.
    assert prod["ean"] == ""


def test_extraer_producto_trae_precio_referencia():
    # las mantequillas tienen ppum ($ / kg)
    refs = [extraer_producto(r, "Lacteos, Huevos y Congelados", "Mantequillas y Margarinas")["precio_referencia"]
            for r in _resultados()]
    assert any(ref for ref in refs), "ninguna fila trajo precio de referencia"
