"""PoC del scraper de Lider por el endpoint NUEVO (SPA de Walmart / Next.js).

NO cableado al pipeline todavia: el endpoint `/browse` esta protegido por Akamai
y bloquea urllib y Selenium (headless y no-headless). Ver
app/docs/lider-endpoint-nuevo.md. Lo que falta es SOLO el transporte (una funcion
que baje el HTML pasando el anti-bot); el parseo del `__NEXT_DATA__` ya funciona y
esta cubierto por tests con un fixture real.

Cuando haya transporte, `productos_desde_next_data(html, ...)` devuelve los
productos ya normalizados con las mismas columnas que scraper_lider.py, con la
ventaja de traer el EAN directo en `usItemId` (no hace falta backfill para Lider).
"""

import json
import re

# Categorias del arbol /browse: (categoria, subcategoria, path). Los ids salen del
# home (a[href*="/browse/"]). Semilla minima para el PoC; completar al cablear.
CATEGORIAS_BROWSE = [
    ("Higiene", "Jabon", "/browse/higiene-y-cuidado-personal/jabones/72387472_38253071"),
]

_NEXT_DATA_RE = re.compile(r'id=(["\']?)__NEXT_DATA__\1[^>]*>')


def _normalizar_ean(us_item_id):
    """usItemId (GTIN-14, ej '00780500031555') -> EAN sin ceros a la izquierda."""
    if not us_item_id:
        return ""
    return str(us_item_id).lstrip("0")


def extraer_next_data(html):
    """Devuelve el dict de __NEXT_DATA__, o None si la respuesta es un challenge."""
    m = _NEXT_DATA_RE.search(html)
    if not m:
        return None
    inicio = m.end()
    fin = html.index("</script>", inicio)
    return json.loads(html[inicio:fin])


def _item_stack(next_data):
    return next_data["props"]["pageProps"]["initialData"]["searchResult"]["itemStacks"][0]


def total_y_paginas(next_data):
    """(count total, maxPage) de la categoria. Para saber cuantas paginas pedir."""
    sr = next_data["props"]["pageProps"]["initialData"]["searchResult"]
    return _item_stack(next_data).get("count"), (sr.get("paginationV2") or {}).get("maxPage")


def productos_desde_next_data(next_data, categoria, subcategoria):
    """Productos de una pagina, con las columnas de scraper_lider.CAMPOS."""
    productos = []
    for it in _item_stack(next_data)["items"]:
        us = it.get("usItemId")
        if not us:
            continue  # banners / no-producto
        precio = it.get("priceInfo") or {}
        productos.append({
            "categoria": categoria,
            "subcategoria": subcategoria,
            "nombre": it.get("name", ""),
            "precio": precio.get("linePrice") or precio.get("itemPrice") or "",
            "precio_normal": precio.get("wasPrice") or "",
            "precio_oferta": precio.get("linePrice") or "",
            "precio_referencia": precio.get("unitPrice") or "",
            "promocion": precio.get("savings") or "",
            "url": it.get("canonicalUrl", ""),
            "imagen_url": (it.get("imageInfo") or {}).get("thumbnailUrl", ""),
            "ean": _normalizar_ean(us),
        })
    return productos
