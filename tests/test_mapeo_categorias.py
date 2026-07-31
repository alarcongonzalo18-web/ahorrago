"""Invariantes de los mapeos de categorías de las 4 cadenas.

Cada scraper traduce el árbol real de su supermercado a las 12 categorías
internas. Estos tests cubren los errores que ya aparecieron al construirlos:
categorías internas inventadas, subcategorías repetidas (una pisa a la otra en
el guard) y el mismo id/slug mapeado dos veces (scrapea lo mismo dos veces).
"""

import pytest

from app.fase5b_apply import TODAS_LAS_CATEGORIAS
from app.scraper_jumbo_real import CATEGORIAS as JUMBO
from app.scraper_lider_browse import CATEGORIAS_BROWSE as LIDER
from app.scraper_tottus import CATEGORIAS as TOTTUS
from app.scraper_unimarc import CATEGORIAS as UNIMARC

MAPEOS = [
    ("Jumbo", JUMBO),
    ("Tottus", TOTTUS),
    ("Unimarc", UNIMARC),
    ("Lider /browse", LIDER),
]


@pytest.mark.parametrize("cadena,mapeo", MAPEOS)
def test_solo_usa_categorias_internas_validas(cadena, mapeo):
    """Una categoría interna inventada queda fuera del matching sin avisar."""
    invalidas = {c for c, _s, _i in mapeo if c not in TODAS_LAS_CATEGORIAS}
    assert not invalidas, f"{cadena} usa categorías internas inexistentes: {invalidas}"


@pytest.mark.parametrize("cadena,mapeo", MAPEOS)
def test_sin_subcategorias_repetidas(cadena, mapeo):
    """El guard cuenta por subcategoría: dos con el mismo nombre se pisan.

    Se compara en minúsculas porque "Bebidas Vegetales" y "Bebidas vegetales"
    son la misma para una persona, y confundirlas ya pasó en Unimarc.
    """
    vistas, repetidas = set(), set()
    for _c, sub, _i in mapeo:
        clave = sub.lower()
        if clave in vistas:
            repetidas.add(sub)
        vistas.add(clave)
    assert not repetidas, f"{cadena} repite subcategorías: {repetidas}"


@pytest.mark.parametrize("cadena,mapeo", MAPEOS)
def test_sin_ids_repetidos(cadena, mapeo):
    """Un id/slug repetido scrapea dos veces la misma categoría."""
    vistos, repetidos = set(), set()
    for _c, _s, ident in mapeo:
        if ident in vistos:
            repetidos.add(ident)
        vistos.add(ident)
    assert not repetidos, f"{cadena} repite ids: {repetidos}"


@pytest.mark.parametrize("cadena,mapeo", MAPEOS)
def test_cubre_las_categorias_de_alimentos(cadena, mapeo):
    """Un comparador de supermercados sin alimentos no sirve.

    Ya pasó: al migrar Líder se excluyó "la-boti" creyendo que era una farmacia
    (es la botillería) y "frescos-y-lacteos" quedó sin la leche.
    """
    esenciales = {
        "Lacteos, Huevos y Congelados",
        "Carnes y Pescados",
        "Frutas y Verduras",
        "Despensa",
        "Bebidas",
    }
    cubiertas = {c for c, _s, _i in mapeo}
    assert esenciales <= cubiertas, f"{cadena} no cubre: {esenciales - cubiertas}"


def test_las_cuatro_cadenas_alimentan_cada_categoria_interna():
    """Comparar precios necesita al menos dos cadenas por categoría."""
    fuentes = {}
    for cadena, mapeo in MAPEOS:
        for interna, _s, _i in mapeo:
            fuentes.setdefault(interna, set()).add(cadena)
    flojas = {c: sorted(v) for c, v in fuentes.items() if len(v) < 2}
    assert not flojas, f"categorías con una sola fuente: {flojas}"
