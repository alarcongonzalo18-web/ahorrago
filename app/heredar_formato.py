"""Herencia de formato entre cadenas via EAN.

Las cadenas son inconsistentes al nombrar: Lider publica "Bebida Leche Lactea
Trencito Chocolate Caja" (sin tamaño) y Unimarc, para el MISMO codigo de
barras, "Leche entera trencito nestle sabor chocolate 200 ml". Como el EAN
identifica al producto exacto, el que no trae tamaño puede heredarlo de un
hermano que si lo trae — sin scrapear nada extra. Al 19-07-2026 esto rellena
~1.160 productos.
"""

from collections import Counter

from app import models


def heredar_formato_por_ean(db):
    """Rellena formato vacio con el del mismo EAN en otra cadena. Devuelve cuantos."""
    con_ean = (db.query(models.Producto)
                 .filter(models.Producto.ean.isnot(None), models.Producto.ean != "")
                 .all())

    por_ean = {}
    for producto in con_ean:
        por_ean.setdefault(producto.ean, []).append(producto)

    heredados = 0
    for hermanos in por_ean.values():
        formatos = [p.formato for p in hermanos if (p.formato or "").strip()]
        if not formatos:
            continue
        # el mas repetido en el grupo; ante empate, el mas especifico (largo)
        elegido, _ = Counter(formatos).most_common(1)[0]
        for producto in hermanos:
            if not (producto.formato or "").strip():
                producto.formato = elegido
                heredados += 1

    db.commit()
    return heredados
