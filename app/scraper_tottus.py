"""Scraper de Tottus (grupo Falabella) por categoria real.

Tottus corre Next.js: cada pagina de categoria trae sus datos embebidos en
`<script id="__NEXT_DATA__">`, asi que se scrapea con urllib puro, sin navegador
ni API key (a diferencia de Unimarc, Tottus NO tiene WAF). Contrato en
`app/docs/tottus.md`.

    GET /tottus-cl/lista/CATG<id>/<slug>?page=<N>
      -> props.pageProps.results     (48 productos por pagina)
      -> props.pageProps.pagination  {count, perPage, currentPage}

`pagination.count` da el total real de la categoria, asi que se sabe de antemano
cuantas paginas pedir. El arbol de categorias se descubre con
`python -m app.descubrir_taxonomia tottus`; el mapeo curado (subcategoria real
-> categoria interna) vive en CATEGORIAS.

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
    es_migracion_de_taxonomia,
    fusionar_preservando,
    leer_conteo_previo,
    leer_productos_previos,
    solo_subcategorias,
)


OUTPUT = Path("data/tottus_real.csv")
TOTTUS_HOST = "https://www.tottus.cl"
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

# Mapeo curado del arbol real de Tottus a las 12 categorias internas de
# AhorraGo. Formato: (categoria_interna, subcategoria_visible, path_categoria).
# Solo rubros de consumo; los paths salen de
# `python -m app.descubrir_taxonomia tottus` (item_url de second_level_categories).
#
# Excluidos: rubros Ofertas (duplican), Electrohogar y Tv, Aire Libre, Hogar y
# Libreria, Otras Categorias, y las subs "Productos Nuevos" / "Marcas Propias"
# (landings/filtros que duplican). La perfumeria de bebe va a "Higiene Personal".
CATEGORIAS = [
    ("Bebe", "Pañales y Toallas Húmedas", "/tottus-cl/lista/CATG27222/Panales-y-Toallas-Humedas"),
    ("Bebe", "Alimentación y Lactancia", "/tottus-cl/lista/CATG27224/Alimentacion-y-Lactancia"),
    ("Bebidas", "Bebidas", "/tottus-cl/lista/CATG27217/Bebidas"),
    ("Bebidas", "Jugos y Néctar", "/tottus-cl/lista/CATG27216/Jugos-y-Nectar"),
    ("Bebidas", "Aguas", "/tottus-cl/lista/CATG27215/Aguas"),
    ("Bebidas", "Isotónicas y Energéticas", "/tottus-cl/lista/CATG27218/Isotonicas-y-Energeticas"),
    ("Bebidas", "Té Líquido y Limonadas", "/tottus-cl/lista/CATG27219/Te-Liquido-y-Limonadas"),
    ("Bebidas", "Cervezas", "/tottus-cl/lista/CATG27083/Cervezas"),
    ("Bebidas", "Vinos", "/tottus-cl/lista/CATG29203/Vinos"),
    ("Bebidas", "Licores", "/tottus-cl/lista/CATG29204/Licores"),
    ("Carnes y Pescados", "Vacuno", "/tottus-cl/lista/CATG27090/Vacuno"),
    ("Carnes y Pescados", "Pollo", "/tottus-cl/lista/CATG27092/Pollo"),
    ("Carnes y Pescados", "Cerdo", "/tottus-cl/lista/CATG27091/Cerdo"),
    ("Carnes y Pescados", "Pavo", "/tottus-cl/lista/CATG27093/Pavo"),
    ("Carnes y Pescados", "Carnes Molidas y Trozadas", "/tottus-cl/lista/CATG27094/Carnes-Molidas-y-Trozadas"),
    ("Carnes y Pescados", "Jamón", "/tottus-cl/lista/CATG27203/Jamon"),
    ("Carnes y Pescados", "Chorizos y Longanizas", "/tottus-cl/lista/CATG27267/Chorizos-y-Longanizas"),
    ("Carnes y Pescados", "Salchichas y Vienesas", "/tottus-cl/lista/CATG27268/Salchichas-y-Vienesas"),
    ("Carnes y Pescados", "Salame y Cocktail", "/tottus-cl/lista/CATG27269/Salame-y-Cocktail"),
    ("Carnes y Pescados", "Pates", "/tottus-cl/lista/CATG27270/Pates"),
    ("Carnes y Pescados", "Jamonadas y Otros", "/tottus-cl/lista/CATG27271/Jamonadas-y-Otros"),
    ("Congelados", "Hielo", "/tottus-cl/lista/CATG27131/Hielo"),
    ("Congelados", "Verduras Congeladas", "/tottus-cl/lista/CATG27123/Verduras-Congeladas"),
    ("Congelados", "Hamburguesas y Churrascos", "/tottus-cl/lista/CATG27125/Hamburguesas-y-Churrascos"),
    ("Congelados", "Helados", "/tottus-cl/lista/CATG27129/Helados"),
    ("Congelados", "Pollo Congelado", "/tottus-cl/lista/CATG27126/Pollo-Congelado"),
    ("Congelados", "Frutas Congeladas", "/tottus-cl/lista/CATG27124/Frutas-Congeladas"),
    ("Congelados", "Pescados y Mariscos", "/tottus-cl/lista/CATG27127/Pescados-y-Mariscos"),
    ("Congelados", "Comida Congelada", "/tottus-cl/lista/CATG27132/Comida-Congelada"),
    ("Congelados", "Vegetariano y Vegano", "/tottus-cl/lista/CATG27130/Vegetariano-y-Vegano"),
    ("Desayuno y Snacks", "Cocktail y Snack", "/tottus-cl/lista/CATG27669/Cocktail-y-Snack"),
    ("Desayuno y Snacks", "Desayunos", "/tottus-cl/lista/CATG27072/Desayuno-y-Dulces"),
    ("Despensa", "Aceites", "/tottus-cl/lista/CATG27056/Aceites"),
    ("Despensa", "Arroz, Legumbres y Semillas", "/tottus-cl/lista/CATG27060/Arroz--Legumbres-y-Semillas"),
    ("Despensa", "Conservas y Enlatados", "/tottus-cl/lista/CATG27059/Conservas-y-Enlatados"),
    ("Despensa", "Pastas y Salsas", "/tottus-cl/lista/CATG27062/Pastas-y-Salsas"),
    ("Despensa", "Harinas", "/tottus-cl/lista/CATG27063/Harinas"),
    ("Despensa", "Condimentos y Vinagres", "/tottus-cl/lista/CATG27067/Condimentos-y-Vinagres"),
    ("Despensa", "Aderezos", "/tottus-cl/lista/CATG27066/Aderezos"),
    ("Despensa", "Sopas e Instantáneos", "/tottus-cl/lista/CATG27064/Sopas-e-Instantaneos"),
    ("Despensa", "Postres y Repostería", "/tottus-cl/lista/CATG27065/Postres-y-Reposteria"),
    ("Frutas y Verduras", "Verduras", "/tottus-cl/lista/CATG27098/Verduras"),
    ("Frutas y Verduras", "Frutas", "/tottus-cl/lista/CATG27099/Frutas"),
    ("Frutas y Verduras", "Frutos Secos y Deshidratados", "/tottus-cl/lista/CATG27100/Frutos-Secos-y-Deshidratados"),
    ("Frutas y Verduras", "Colaciones Saludables", "/tottus-cl/lista/CATG27101/Colaciones-Saludables"),
    ("Frutas y Verduras", "Detox", "/tottus-cl/lista/CATG27102/Detox"),
    ("Frutas y Verduras", "Orgánicos", "/tottus-cl/lista/CATG27103/Organicos"),
    ("Higiene Personal", "Belleza", "/tottus-cl/lista/CATG27076/Belleza"),
    ("Higiene Personal", "Cuidado Personal", "/tottus-cl/lista/CATG27696/Cuidado-Personal"),
    ("Higiene Personal", "Perfumería Bebé", "/tottus-cl/lista/CATG27223/Perfumeria-Bebe"),
    ("Lacteos, Huevos y Congelados", "Quesos", "/tottus-cl/lista/CATG27180/Quesos"),
    ("Lacteos, Huevos y Congelados", "Leches", "/tottus-cl/lista/CATG27179/Leches"),
    ("Lacteos, Huevos y Congelados", "Mantequillas y Margarinas", "/tottus-cl/lista/CATG27185/Mantequillas-y-Mantecas"),
    ("Lacteos, Huevos y Congelados", "Yoghurt", "/tottus-cl/lista/CATG27182/Yoghurt"),
    ("Lacteos, Huevos y Congelados", "Postres Listos", "/tottus-cl/lista/CATG27189/Postres-Listos"),
    ("Lacteos, Huevos y Congelados", "Cremas", "/tottus-cl/lista/CATG27192/Cremas"),
    ("Lacteos, Huevos y Congelados", "Huevos", "/tottus-cl/lista/CATG27266/Huevos"),
    ("Limpieza", "Detergente y Cuidado para la Ropa", "/tottus-cl/lista/CATG27133/Detergente-y-Cuidado-para-la-Ropa"),
    ("Limpieza", "Papeles para el Hogar", "/tottus-cl/lista/CATG27134/Papeles-para-el-Hogar"),
    ("Limpieza", "Baño y Cocina", "/tottus-cl/lista/CATG27135/Bano-y-Cocina"),
    ("Limpieza", "Pisos y Muebles", "/tottus-cl/lista/CATG27136/Pisos-y-Muebles"),
    ("Limpieza", "Aerosoles y Desinfectantes", "/tottus-cl/lista/CATG27137/Aerosoles-y-Desinfectantes"),
    ("Limpieza", "Accesorios de Aseo y Cocina", "/tottus-cl/lista/CATG27138/Accesorios-de-Aseo-y-Cocina"),
    ("Mascotas", "Perros", "/tottus-cl/lista/CATG27166/Perros"),
    ("Mascotas", "Gatos", "/tottus-cl/lista/CATG27167/Gatos"),
    ("Mascotas", "Snack y Huesos", "/tottus-cl/lista/CATG27756/Snack-y-Huesos"),
    ("Mascotas", "Higiene y Cuidados", "/tottus-cl/lista/CATG27168/Higiene-y-Cuidados"),
    ("Mascotas", "Accesorios y Juguetes", "/tottus-cl/lista/CATG27752/Accesorios-y-Juguetes"),
    ("Panaderia", "Panadería", "/tottus-cl/lista/CATG27140/Panaderia"),
    ("Panaderia", "Masas y Tortillas", "/tottus-cl/lista/CATG27144/Masas-y-Tortillas"),
    ("Panaderia", "Pastelería", "/tottus-cl/lista/CATG27142/Pasteleria"),
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


def extraer_productos(categoria, subcategoria, path):
    """Recorre las paginas de una categoria usando pagination.count."""
    print(f"Scrapeando Tottus {subcategoria}...", flush=True)
    productos, vistos = [], set()
    total_paginas = None

    for pagina in range(1, MAX_PAGINAS + 1):
        url = f"{TOTTUS_HOST}{path}?page={pagina}"
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


def main(categorias=None):
    categorias = categorias if categorias is not None else CATEGORIAS
    productos, vistos = [], set()

    for categoria, subcategoria, path in categorias:
        try:
            for producto in extraer_productos(categoria, subcategoria, path):
                clave = (categoria, subcategoria, producto["nombre"], producto["url"])
                if clave in vistos:
                    continue
                vistos.add(clave)
                productos.append(producto)
        except Exception as exc:
            print(f"Error en {subcategoria} ({path}): {exc}. Continuando...", flush=True)

    _publicar_con_guard(productos, {sub for _, sub, _ in categorias})


def _publicar_con_guard(productos, subcats_actuales):
    """Guard anti-regresion + red de seguridad de totales.

    - Filtra el baseline a las subcategorias vigentes: al migrar keyword->
      categoria, las subcats viejas del CSV no deben verse como caidas a 0.
    - Carry-forward por subcategoria: una categoria que retrocede por throttling
      conserva sus filas previas; el resto se publica fresco (antes: todo-o-nada).
    - Total: la migracion multiplica el catalogo; si el total nuevo es MENOR que
      el previo, algo se rompio -> no pisar, dejar .nuevo y avisar.
    """
    conteo_previo_crudo = leer_conteo_previo(OUTPUT)
    if es_migracion_de_taxonomia(conteo_previo_crudo, subcats_actuales):
        # Corrida de migracion: el CSV previo usa otra taxonomia, no hay contra
        # que comparar. Publicar directo (el guard vuelve solo la corrida siguiente).
        guardar_productos(productos)
        print(f"{len(productos)} productos Tottus guardados (migracion de taxonomia: guard omitido)", flush=True)
        return

    previos_conteo = solo_subcategorias(conteo_previo_crudo, subcats_actuales)
    previos_filas = solo_subcategorias(leer_productos_previos(OUTPUT), subcats_actuales)

    fusion, preservadas = fusionar_preservando(productos, previos_filas)
    for sub, antes, ahora in sorted(preservadas, key=lambda c: c[1] - c[2], reverse=True):
        print(f"  carry-forward {sub}: {antes} -> {ahora} (se conservan las filas previas)", flush=True)

    total_previo = sum(previos_conteo.values())
    if total_previo and len(fusion) < total_previo:
        destino = OUTPUT.with_suffix(OUTPUT.suffix + ".nuevo")
        guardar_productos(fusion, destino)
        print(f"\n*** TOTAL A LA BAJA: {total_previo} -> {len(fusion)}. No se piso {OUTPUT} ***", flush=True)
        print(f"La corrida nueva quedo en {destino} para inspeccion", flush=True)
        return

    guardar_productos(fusion)
    print(f"{len(fusion)} productos Tottus guardados", flush=True)


if __name__ == "__main__":
    main()
