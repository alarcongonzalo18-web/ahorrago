"""Reporte de cobertura del catalogo: cuanto hay por proveedor y cuanto es comparable.

La metrica que importa en un comparador no es cuantos productos hay, sino
cuantos grupos producto_base existen en 2+ proveedores (solo esos se pueden
comparar). Correr despues de cada actualizacion de datos:

    python -m app.reporte_cobertura
"""

from collections import defaultdict

from sqlalchemy.orm import joinedload

from . import models


def calcular_cobertura(db):
    productos = db.query(models.Producto).options(
        joinedload(models.Producto.categoria)
    ).all()
    precios = db.query(models.Precio).options(
        joinedload(models.Precio.proveedor)
    ).all()

    proveedores_por_producto = defaultdict(set)
    for precio in precios:
        if precio.proveedor:
            proveedores_por_producto[precio.producto_id].add(precio.proveedor.nombre)

    por_proveedor = defaultdict(int)
    ean_por_proveedor = defaultdict(int)
    matriz_categoria = defaultdict(lambda: defaultdict(int))
    grupos = defaultdict(set)
    grupos_categoria = defaultdict(lambda: defaultdict(set))

    for producto in productos:
        categoria = producto.categoria.nombre if producto.categoria else "Sin categoria"
        supers = proveedores_por_producto.get(producto.id, set())
        for s in supers:
            por_proveedor[s] += 1
            if producto.ean:
                ean_por_proveedor[s] += 1
            matriz_categoria[categoria][s] += 1
        base = producto.producto_base or f"producto:{producto.id}"
        grupos[base] |= supers
        grupos_categoria[categoria][base] |= supers

    total_grupos = len(grupos)
    comparables = sum(1 for s in grupos.values() if len(s) >= 2)
    en_todos = sum(1 for s in grupos.values() if len(s) >= 3)

    comparables_por_categoria = {}
    for categoria, bases in grupos_categoria.items():
        total_cat = len(bases)
        comp_cat = sum(1 for s in bases.values() if len(s) >= 2)
        comparables_por_categoria[categoria] = {
            "grupos": total_cat,
            "comparables": comp_cat,
            "porcentaje": round(comp_cat / total_cat * 100, 1) if total_cat else 0.0,
        }

    return {
        "productos_totales": len(productos),
        "precios_totales": len(precios),
        "productos_por_proveedor": dict(por_proveedor),
        "ean_por_proveedor": dict(ean_por_proveedor),
        "matriz_categoria_proveedor": {c: dict(m) for c, m in matriz_categoria.items()},
        "grupos_producto_base": total_grupos,
        "grupos_comparables": comparables,
        "porcentaje_comparable": round(comparables / total_grupos * 100, 1) if total_grupos else 0.0,
        "grupos_en_todos": en_todos,
        "comparables_por_categoria": comparables_por_categoria,
    }


def formatear_reporte(datos):
    lineas = []
    lineas.append("=== Cobertura del catalogo ===")
    lineas.append(f"Productos: {datos['productos_totales']} | Precios: {datos['precios_totales']}")
    lineas.append("")
    lineas.append("Productos por proveedor (y % con EAN):")
    for proveedor, cantidad in sorted(datos["productos_por_proveedor"].items(), key=lambda x: -x[1]):
        con_ean = datos.get("ean_por_proveedor", {}).get(proveedor, 0)
        pct = f"{con_ean / cantidad * 100:.0f}%" if cantidad else "0%"
        lineas.append(f"  {proveedor:12} {cantidad}  (ean: {con_ean}, {pct})")
    lineas.append("")
    lineas.append(
        f"Grupos producto_base: {datos['grupos_producto_base']} | "
        f"comparables (2+ proveedores): {datos['grupos_comparables']} "
        f"({datos['porcentaje_comparable']}%) | "
        f"en todos: {datos['grupos_en_todos']}"
    )
    lineas.append("")
    lineas.append(f"{'Categoria':34}{'grupos':>8}{'compar.':>9}{'%':>7}")
    orden = sorted(
        datos["comparables_por_categoria"].items(),
        key=lambda x: x[1]["porcentaje"],
    )
    for categoria, info in orden:
        lineas.append(
            f"{categoria[:33]:34}{info['grupos']:>8}{info['comparables']:>9}{info['porcentaje']:>7}"
        )
    lineas.append("")
    lineas.append("Las categorias de arriba son las que menos se pueden comparar:")
    lineas.append("ahi es donde mas paga profundizar el scraping o mejorar el matching.")
    return "\n".join(lineas)


def main():
    from .database import SessionLocal

    db = SessionLocal()
    try:
        print(formatear_reporte(calcular_cobertura(db)))
    finally:
        db.close()


if __name__ == "__main__":
    main()
