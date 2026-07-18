"""Snapshot diario de precios, para poder calcular medias y detectar bajas.

Por que existe: `Precio` sólo guarda el precio de HOY, y `reconstruir_base` lo
borra y recrea en cada corrida. Sin una tabla que acumule, no hay historia — y
sin historia no hay media, ni "bajó de precio", ni alertas
(ver `docs/roadmap-producto.md`).

Diseño: los ids de producto/proveedor cambian en cada reconstrucción, así que el
historial se apoya en identificadores **estables**:

- `clave` = `ean:<codigo>` si el producto tiene EAN, si no `nombre:<normalizado>`
- `proveedor` = el nombre, no el id

Se guarda **un punto por clave/proveedor/día**: correr el pipeline dos veces el
mismo día actualiza el punto en vez de duplicarlo.
"""

from datetime import date

from sqlalchemy import func

from . import models
from .normalizacion import normalizar_texto


def clave_estable(ean, nombre):
    """Identificador que sobrevive a las reconstrucciones de la base."""
    if ean:
        return f"ean:{ean}"
    normalizado = normalizar_texto(nombre or "").strip()
    return f"nombre:{normalizado}" if normalizado else ""


def _valor_precio(precio):
    """Lo que efectivamente se paga: oferta si la hay, si no el normal."""
    if precio.precio_oferta:
        return precio.precio_oferta
    return precio.precio_normal


def registrar_snapshot(db, fecha=None):
    """Vuelca los precios actuales al historial. Devuelve (nuevos, actualizados)."""
    fecha = fecha or date.today()

    # lo ya guardado hoy, para no duplicar ni pisar a ciegas
    existentes = {
        (h.clave, h.proveedor): h
        for h in db.query(models.HistorialPrecio).filter(
            models.HistorialPrecio.fecha == fecha
        )
    }

    filas = (
        db.query(models.Precio, models.Producto, models.Proveedor)
        .join(models.Producto, models.Precio.producto_id == models.Producto.id)
        .join(models.Proveedor, models.Precio.proveedor_id == models.Proveedor.id)
        .yield_per(1000)
    )

    nuevos = actualizados = 0
    vistos = set()

    for precio, producto, proveedor in filas:
        valor = _valor_precio(precio)
        if not valor or valor <= 0:
            continue

        clave = clave_estable(producto.ean, producto.nombre)
        if not clave:
            continue

        par = (clave, proveedor.nombre)
        if par in vistos:
            # varios productos comparten clave (mismo EAN en la misma cadena):
            # se queda el mas barato, que es el que la app mostraria
            previo = existentes.get(par)
            if previo and valor < previo.precio:
                previo.precio = valor
            continue
        vistos.add(par)

        registro = existentes.get(par)
        if registro:
            if registro.precio != valor:
                registro.precio = valor
                actualizados += 1
            continue

        db.add(
            models.HistorialPrecio(
                clave=clave,
                ean=producto.ean or None,
                producto_nombre=producto.nombre,
                proveedor=proveedor.nombre,
                precio=valor,
                fecha=fecha,
            )
        )
        existentes[par] = None  # marca de insertado en esta pasada
        nuevos += 1

    db.commit()
    return nuevos, actualizados


def resumen(db):
    """(dias distintos, puntos totales) — para reportar en el pipeline."""
    dias = db.query(func.count(func.distinct(models.HistorialPrecio.fecha))).scalar() or 0
    puntos = db.query(func.count(models.HistorialPrecio.id)).scalar() or 0
    return dias, puntos
