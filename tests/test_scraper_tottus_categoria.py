import json
from pathlib import Path

from app.scraper_tottus import CATEGORIAS, extraer_producto
from app.fase5b_apply import TODAS_LAS_CATEGORIAS

FIXTURE = Path(__file__).parent / "fixtures" / "tottus_categoria.json"


def _resultados():
    return json.loads(FIXTURE.read_text(encoding="utf-8"))["results"]


def test_mapeo_solo_usa_categorias_internas_validas():
    for categoria, _sub, _path in CATEGORIAS:
        assert categoria in TODAS_LAS_CATEGORIAS, f"categoria interna invalida: {categoria}"


def test_mapeo_sin_paths_ni_subcategorias_duplicadas():
    paths = [p for _c, _s, p in CATEGORIAS]
    assert len(paths) == len(set(paths)), "hay paths repetidos"
    subs = [sub for _c, sub, _p in CATEGORIAS]
    assert len(subs) == len(set(subs)), "hay subcategorias repetidas"


def test_mapeo_usa_solo_paths_de_categoria_lista():
    for _c, _s, path in CATEGORIAS:
        assert path.startswith("/tottus-cl/lista/CATG"), f"path no es de categoria: {path}"


def test_extraer_producto_parsea_listado():
    prod = extraer_producto(_resultados()[0], "Lacteos, Huevos y Congelados", "Leches")
    assert prod is not None
    assert prod["nombre"]
    assert isinstance(prod["precio"], int) and prod["precio"] > 0
    assert prod["categoria"] == "Lacteos, Huevos y Congelados"
    # Tottus no expone EAN en el listado: lo llena app.backfill_ean.
    assert prod["ean"] == ""
