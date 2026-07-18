"""Scraper de Tottus (grupo Falabella).

Tottus corre Next.js: cada pagina de busqueda trae sus datos embebidos en
`<script id="__NEXT_DATA__">`, asi que se scrapea con urllib puro, sin navegador
ni API key. Contrato completo en `app/docs/tottus.md`.

    GET /tottus-cl/buscar?Ntt=<termino>&page=<N>
      -> props.pageProps.results     (48 productos por pagina)
      -> props.pageProps.pagination  {count, perPage, currentPage}

`pagination.count` da el total real de resultados, asi que se sabe de antemano
cuantas paginas pedir (a diferencia de Lider, donde hay que avanzar a ciegas).

El EAN NO viene en el listado: sale de la ficha de cada producto y lo puebla
`app.backfill_ean` en la cache (ver `app/ean_cache.py`).
"""

import csv
import http.client
import json
import re
import time
import urllib.error
import urllib.request
from pathlib import Path

from app.category_validator import is_valid_row
# El guard anti-regresion es generico y ya esta testeado en scraper_lider:
# se reutiliza en vez de duplicarlo.
from app.scraper_lider import (
    contar_por_subcategoria,
    leer_conteo_previo,
    validar_anti_regresion,
)


OUTPUT = Path("data/tottus_real.csv")
BASE = "https://www.tottus.cl/tottus-cl/buscar"
POR_PAGINA = 48
MAX_PAGINAS = 40          # techo de seguridad (~1.900 productos por categoria)
MIN_HTML_BYTES = 5000     # por debajo, es pagina de bloqueo y no un listado

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)

CAMPOS = [
    "categoria", "subcategoria", "nombre", "precio", "precio_normal",
    "precio_oferta", "precio_referencia", "promocion", "url", "imagen_url", "ean",
]

CATEGORIAS = [
    ("Lacteos, Huevos y Congelados", "Leche",        "leche"),
    ("Lacteos, Huevos y Congelados", "Huevos",       "huevos"),
    ("Lacteos, Huevos y Congelados", "Yogurt",       "yogurt"),
    ("Lacteos, Huevos y Congelados", "Quesos",       "queso"),
    ("Lacteos, Huevos y Congelados", "Mantequilla",  "mantequilla"),
    ("Lacteos, Huevos y Congelados", "Crema",        "crema"),
    ("Frutas y Verduras",            "Frutas",       "fruta"),
    ("Frutas y Verduras",            "Verduras",     "verdura"),
    ("Carnes y Pescados",            "Carnes",       "carne"),
    ("Carnes y Pescados",            "Aves",         "pollo"),
    ("Carnes y Pescados",            "Cecinas",      "cecinas"),
    ("Carnes y Pescados",            "Pescados",     "pescado"),
    ("Carnes y Pescados",            "Mariscos",     "mariscos"),
    ("Congelados",                   "Congelados",   "congelado"),
    ("Despensa", "Arroz",            "arroz"),
    ("Despensa", "Aceite",           "aceite"),
    ("Despensa", "Cafe",             "cafe"),
    ("Despensa", "Azucar",           "azucar"),
    ("Despensa", "Fideos",           "fideos"),
    ("Despensa", "Conservas",        "conservas"),
    ("Despensa", "Salsas",           "salsa"),
    ("Despensa", "Condimentos",      "condimento"),
    ("Despensa", "Legumbres",        "legumbres"),
    ("Desayuno y Snacks", "Cereales",   "cereal"),
    ("Desayuno y Snacks", "Galletas",   "galleta"),
    ("Desayuno y Snacks", "Chocolates", "chocolate"),
    ("Desayuno y Snacks", "Snacks",     "snack"),
    ("Desayuno y Snacks", "Mermeladas", "mermelada"),
    ("Bebidas", "Bebidas",             "bebida"),
    ("Bebidas", "Jugos",               "jugo"),
    ("Bebidas", "Aguas",               "agua mineral"),
    ("Bebidas", "Cervezas",            "cerveza"),
    ("Bebidas", "Vinos",               "vino"),
    ("Bebidas", "Bebidas Energeticas", "bebida energetica"),
    ("Panaderia", "Pan",               "pan"),
    ("Limpieza", "Detergentes",        "detergente"),
    ("Limpieza", "Papel higienico",    "papel higienico"),
    ("Limpieza", "Limpiadores",        "limpiador"),
    ("Limpieza", "Lavavajillas",       "lavavajillas"),
    ("Limpieza", "Suavizantes",        "suavizante"),
    ("Higiene Personal", "Shampoo",        "shampoo"),
    ("Higiene Personal", "Acondicionador", "acondicionador"),
    ("Higiene Personal", "Jabon",          "jabon"),
    ("Higiene Personal", "Desodorantes",   "desodorante"),
    ("Higiene Personal", "Cuidado Bucal",  "pasta dental"),
    ("Bebe", "Panales",                "panales"),
    ("Bebe", "Alimentos Bebe",         "alimento bebe"),
    ("Mascotas", "Alimento Perros",    "alimento perro"),
    ("Mascotas", "Alimento Gatos",     "alimento gato"),
]


class BloqueoError(Exception):
    """Throttling (429/403/5xx) o cuerpo sospechosamente corto."""


def descargar_html(url, intentos=5):
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    ultimo = None
    for intento in range(1, intentos + 1):
        try:
            with urllib.request.urlopen(request, timeout=45) as resp:
                html = resp.read().decode("utf-8", errors="replace")
            if len(html) < MIN_HTML_BYTES:
                raise BloqueoError(f"cuerpo corto ({len(html)} bytes)")
            return html
        except urllib.error.HTTPError as exc:
            ultimo = exc
            if exc.code in (429, 403, 500, 502, 503, 504):
                if intento == intentos:
                    break
                time.sleep(min(60, 5 * 2 ** (intento - 1)))
                continue
            raise
        except (
            TimeoutError, ConnectionError, http.client.HTTPException,
            urllib.error.URLError, BloqueoError,
        ) as exc:
            ultimo = exc
            if intento == intentos:
                break
            time.sleep(min(30, 3 * intento))
    raise RuntimeError(f"No se pudo descargar {url} tras {intentos} intentos: {ultimo}")


def extraer_next_data(html):
    """El JSON embebido de Next.js, o None si no esta."""
    m = re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', html, re.S)
    if not m:
        return None
    try:
        return json.loads(m.group(1))
    except json.JSONDecodeError:
        return None


def precio_a_entero(valor):
    """'1.390' -> 1390. Devuelve None si no hay numero."""
    if isinstance(valor, list):
        valor = valor[0] if valor else ""
    digitos = re.sub(r"[^\d]", "", str(valor or ""))
    return int(digitos) if digitos else None


def _precio_de_tipo(precios, tipo):
    for p in precios or []:
        if p.get("type") == tipo:
            return p
    return None


def extraer_producto(item, categoria, subcategoria):
    """Un producto del listado -> fila del CSV (o None si no sirve)."""
    nombre = (item.get("displayName") or "").strip()
    if not nombre:
        return None

    precios = item.get("prices") or []
    # internetPrice es lo que se paga; normalPrice (tachado) solo aparece si hay
    # descuento, y es el precio de lista.
    actual = _precio_de_tipo(precios, "internetPrice") or (precios[0] if precios else None)
    if not actual:
        return None
    precio = precio_a_entero(actual.get("price"))
    if not precio:
        return None

    lista = _precio_de_tipo(precios, "normalPrice")
    precio_lista = precio_a_entero(lista.get("price")) if lista else None
    hay_oferta = bool(precio_lista and precio_lista > precio)

    pum = actual.get("pum") or {}
    valor_pum = precio_a_entero(pum.get("price"))
    referencia = f"${valor_pum:,} / {pum.get('label')}".replace(",", ".") if valor_pum and pum.get("label") else ""

    medios = item.get("mediaUrls") or []

    producto = {
        "categoria": categoria,
        "subcategoria": subcategoria,
        "nombre": nombre,
        "precio": precio,
        "precio_normal": precio_lista if hay_oferta else precio,
        "precio_oferta": precio if hay_oferta else "",
        "precio_referencia": referencia,
        "promocion": "Oferta" if hay_oferta else "",
        "url": item.get("url") or "",
        "imagen_url": medios[0] if medios else "",
        # El EAN no viene en el listado: lo puebla app.backfill_ean en la cache.
        "ean": "",
    }
    if not is_valid_row(producto, "scraper_tottus", Path("reports") / "pipeline_category_rejections.csv"):
        return None
    return producto


def extraer_productos(categoria, subcategoria, termino):
    """Recorre las paginas de una categoria usando pagination.count."""
    print(f"Scrapeando Tottus {subcategoria}...", flush=True)
    productos, vistos = [], set()
    total_paginas = None

    for pagina in range(1, MAX_PAGINAS + 1):
        url = f"{BASE}?Ntt={urllib.request.quote(termino)}&page={pagina}"
        try:
            datos = extraer_next_data(descargar_html(url))
        except RuntimeError as exc:
            if pagina == 1:
                raise      # la categoria entera no cargo: que main lo marque ERROR
            print(f"  pagina {pagina} -> error, se corta la categoria: {exc}", flush=True)
            break

        page_props = ((datos or {}).get("props") or {}).get("pageProps") or {}
        resultados = page_props.get("results") or []
        if not resultados:
            break

        if total_paginas is None:
            paginacion = page_props.get("pagination") or {}
            total = paginacion.get("count") or 0
            por_pagina = paginacion.get("perPage") or POR_PAGINA
            if total:
                total_paginas = min(MAX_PAGINAS, -(-total // por_pagina))  # techo

        nuevos = 0
        for item in resultados:
            producto = extraer_producto(item, categoria, subcategoria)
            if not producto:
                continue
            clave = (producto["nombre"], producto["url"])
            if clave in vistos:
                continue
            vistos.add(clave)
            productos.append(producto)
            nuevos += 1

        print(f"  pagina {pagina} -> {len(productos)} acumulados", flush=True)

        if nuevos == 0:
            break                                   # el sitio recicla contenido
        if total_paginas and pagina >= total_paginas:
            break                                   # se pidieron todas las paginas reales

        time.sleep(1.0)

    return productos


def guardar_productos(productos, destino=OUTPUT):
    destino = Path(destino)
    destino.parent.mkdir(parents=True, exist_ok=True)
    with open(destino, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CAMPOS)
        writer.writeheader()
        writer.writerows(productos)


def main():
    productos, vistos = [], set()

    for categoria, subcategoria, termino in CATEGORIAS:
        try:
            for producto in extraer_productos(categoria, subcategoria, termino):
                clave = (categoria, subcategoria, producto["nombre"], producto["url"])
                if clave in vistos:
                    continue
                vistos.add(clave)
                productos.append(producto)
        except Exception as exc:
            print(f"Error en {subcategoria} ({termino}): {exc}. Continuando...", flush=True)

    # Mismo guard que Lider: nunca pisar datos buenos con una corrida degradada.
    previos = leer_conteo_previo(OUTPUT)
    caidas = validar_anti_regresion(contar_por_subcategoria(productos), previos)

    if caidas:
        destino = OUTPUT.with_suffix(OUTPUT.suffix + ".nuevo")
        guardar_productos(productos, destino)
        print(f"\n*** REGRESION DETECTADA: no se piso {OUTPUT} ***", flush=True)
        print(f"La corrida nueva ({len(productos)} productos) quedo en {destino}", flush=True)
        for sub, antes, ahora in sorted(caidas, key=lambda c: c[1] - c[2], reverse=True):
            print(f"  - {sub}: {antes} -> {ahora}", flush=True)
        return

    guardar_productos(productos)
    print(f"{len(productos)} productos Tottus guardados", flush=True)


if __name__ == "__main__":
    main()
