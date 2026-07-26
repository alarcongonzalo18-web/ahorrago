"""Scraper de Lider por el endpoint NUEVO (SPA de Walmart / Next.js).

TRANSPORTE RESUELTO 26-07-2026: `undetected-chromedriver` **pasa Akamai** (urllib
y Selenium normal, headless o no, seguian bloqueados). Verificado contra
/browse/higiene-y-cuidado-personal/jabones: **143 productos, maxPage=4**, contra
los ~10 que da el endpoint viejo /v/jabones. Ver app/docs/lider-endpoint-nuevo.md.

FALTA para cablearlo al pipeline: el arbol de categorias /browse. El sitio NO lo
expone en el HTML (el home no trae links /browse, el sitemap esta vacio, y el
menu se hidrata por JS sin dejar hrefs). Hay que sacarlo interceptando la llamada
de red que hidrata el menu, o navegandolo a mano una vez.

`productos_desde_next_data(...)` devuelve los productos con las mismas columnas
que scraper_lider.py y con el EAN directo en `usItemId` (Lider no necesita
backfill).
"""

import json
import re
import time

# Categorias del arbol /browse: (categoria, subcategoria, path). Los ids salen del
# home (a[href*="/browse/"]). Semilla minima para el PoC; completar al cablear.
CATEGORIAS_BROWSE = [
    ("Higiene", "Jabon", "/browse/higiene-y-cuidado-personal/jabones/72387472_38253071"),
]

_NEXT_DATA_RE = re.compile(r'id=(["\']?)__NEXT_DATA__\1[^>]*>')

HOST = "https://super.lider.cl"
# Chrome real de este equipo. undetected-chromedriver baja el driver de la ultima
# version, que no siempre coincide: si no, tira SessionNotCreatedException.
CHROME_MAJOR = 150
ESPERA_HIDRATACION = 6.0


def crear_driver(version_main=CHROME_MAJOR):
    """Chrome parcheado que pasa el Akamai de Lider.

    NO usar headless: es una de las señales que el anti-bot mira (probado el
    23-07, bloqueado). El costo es que abre una ventana real.
    """
    import undetected_chromedriver as uc

    opciones = uc.ChromeOptions()
    opciones.add_argument("--window-size=1280,900")
    return uc.Chrome(options=opciones, use_subprocess=True, version_main=version_main)


def bajar_categoria(driver, path, pagina=1, espera=ESPERA_HIDRATACION):
    """HTML de una pagina de categoria ya hidratada por el SPA."""
    driver.get(f"{HOST}{path}?page={pagina}")
    time.sleep(espera)
    return driver.page_source


def _a_entero(precio):
    """'$14.690' -> 14690. El SPA nuevo da los precios formateados, no numericos."""
    if precio is None:
        return ""
    digitos = re.sub(r"[^\d]", "", str(precio))
    return int(digitos) if digitos else ""


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
        info = it.get("priceInfo") or {}
        # itemPrice es el de lista y linePrice el que se paga; vienen como
        # "$14.690" (string formateado), no como numero.
        lista = _a_entero(info.get("itemPrice") or info.get("wasPrice"))
        paga = _a_entero(info.get("linePrice")) or lista
        productos.append({
            "categoria": categoria,
            "subcategoria": subcategoria,
            "nombre": it.get("name", ""),
            "precio": paga,
            "precio_normal": lista or paga,
            "precio_oferta": paga if (lista and paga and paga < lista) else "",
            "precio_referencia": info.get("unitPrice") or "",
            "promocion": info.get("savings") or "",
            "url": it.get("canonicalUrl", ""),
            "imagen_url": (it.get("imageInfo") or {}).get("thumbnailUrl", ""),
            "ean": _normalizar_ean(us),
        })
    return productos
