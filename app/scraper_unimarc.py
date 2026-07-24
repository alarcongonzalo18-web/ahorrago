"""Scraper de Unimarc (grupo SMU) por categoria real.

Unimarc corre Next.js: cada pagina de categoria trae sus productos embebidos en
`<script id="__NEXT_DATA__">`, con EAN, precio y formato ya estructurados. Pero
el HTML y el endpoint `_next/data` estan protegidos por WAF (Akamai) y dan 403 a
cualquier cliente que no sea un navegador real — por eso se usa Selenium (Chrome
headless), que ya es dependencia del proyecto. Con `page_load_strategy="eager"`
y sin cargar imagenes, cada pagina tarda ~2.5 s.

    GET /category/<rubro>/<sub>?page=<N>   (via Selenium)
      -> props.pageProps.dehydratedState.queries[0].state.data
           .availableProducts[]   (50 por pagina, con item.ean directo)
           .resource              (total real de la categoria)

A diferencia del scraper viejo (busqueda por keyword + CSS hasheado fragil),
este recorre el arbol de categorias real y trae el EAN en el propio listado, asi
que los productos nacen comparables sin depender de app.backfill_ean.

El arbol se descubre con `python -m app.descubrir_taxonomia unimarc`; el mapeo
curado (subcategoria real -> categoria interna) vive en CATEGORIAS, abajo.
"""

import csv
import json
import re
import sys
import time
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.chrome.options import Options

from app.category_validator import is_valid_row
# Guard anti-regresion generico, ya testeado en scraper_lider (no duplicar).
from app.scraper_lider import (
    fusionar_preservando,
    leer_conteo_previo,
    leer_productos_previos,
    solo_subcategorias,
)


OUTPUT = Path("data/unimarc_real.csv")
BASE_CATEGORIA = "https://www.unimarc.cl/category"
POR_PAGINA = 50
MAX_PAGINAS = 60          # techo de seguridad (~3.000 productos por categoria)
PAUSA_ENTRE_PAGINAS = 1.0
ESPERA_RENDER = 2.0       # el __NEXT_DATA__ es SSR; alcanza con una espera corta

CAMPOS = [
    "categoria", "subcategoria", "nombre", "precio", "precio_normal",
    "precio_oferta", "precio_referencia", "promocion", "url", "imagen_url", "ean",
]

# Mapeo curado del arbol real de Unimarc (15 rubros -> subcategorias nivel-2) a
# las 12 categorias internas de AhorraGo. Formato: (categoria_interna,
# subcategoria_visible, slug). Solo rubros de consumo.
#
# Excluidos a proposito (no-consumo o duplicados):
#   - Rubro "Hogar" completo (electrohogar, ferreteria, libreria, cocina y mesa).
#   - "perfumeria/farmacia" (farmacia, no alimentacion ni aseo).
#   - Rubro "Veganos y vegetarianos": sus productos ya se scrapean en su
#     categoria normal; incluirlo duplicaria el recorrido.
# Regla especial: la perfumeria de bebe va a "Higiene Personal" (no "Bebe"),
# porque el validador rechaza higiene bajo la categoria "Bebe".
CATEGORIAS = [
    # Carnes -> Carnes y Pescados
    ("Carnes y Pescados", "Vacuno", "carnes/vacuno"),
    ("Carnes y Pescados", "Pollo", "carnes/pollo"),
    ("Carnes y Pescados", "Cerdo", "carnes/cerdo"),
    ("Carnes y Pescados", "Pavo", "carnes/pavo"),
    ("Carnes y Pescados", "Cordero y otros", "carnes/cordero-y-otros"),
    # Frutas y Verduras
    ("Frutas y Verduras", "Frutas", "frutas-y-verduras/frutas"),
    ("Frutas y Verduras", "Verduras", "frutas-y-verduras/verduras"),
    ("Frutas y Verduras", "Frutos secos", "frutas-y-verduras/frutos-secos"),
    # Lacteos, Huevos y Refrigerados -> Lacteos, Huevos y Congelados
    ("Lacteos, Huevos y Congelados", "Leches y cremas", "lacteos-huevos-y-refrigerados/leches-y-cremas"),
    ("Lacteos, Huevos y Congelados", "Yoghurt", "lacteos-huevos-y-refrigerados/yoghurt"),
    ("Lacteos, Huevos y Congelados", "Mantequillas", "lacteos-huevos-y-refrigerados/mantequillas"),
    ("Lacteos, Huevos y Congelados", "Huevos", "lacteos-huevos-y-refrigerados/huevos"),
    ("Lacteos, Huevos y Congelados", "Postres", "lacteos-huevos-y-refrigerados/postres"),
    ("Lacteos, Huevos y Congelados", "Bebidas vegetales", "lacteos-huevos-y-refrigerados/bebidas-vegetales"),
    # Quesos y Fiambres: quesos -> Lacteos; fiambres -> Carnes y Pescados
    ("Carnes y Pescados", "Fiambres y embutidos", "quesos-y-fiambres/fiambres-y-embutidos"),
    ("Lacteos, Huevos y Congelados", "Quesos", "quesos-y-fiambres/quesos"),
    # Panaderia y Pasteleria -> Panaderia
    ("Panaderia", "Pan", "panaderia-y-pasteleria/pan"),
    ("Panaderia", "Pan envasado", "panaderia-y-pasteleria/pan-envasado"),
    ("Panaderia", "Pasteleria", "panaderia-y-pasteleria/pasteleria"),
    ("Panaderia", "Asaduria", "panaderia-y-pasteleria/asaduria"),
    # Congelados
    ("Congelados", "Hielo, helados y postres", "congelados/hielo-helados-y-postres"),
    ("Congelados", "Frutas y verduras congeladas", "congelados/frutas-y-verduras-congeladas"),
    ("Congelados", "Hamburguesas, apanados y churrascos", "congelados/hamburguesas-apanados-y-churrascos"),
    ("Congelados", "Pescados y mariscos", "congelados/pescados-y-mariscos"),
    ("Congelados", "Platos congelados", "congelados/platos-congelados"),
    # Despensa
    ("Despensa", "Arroz y legumbres", "despensa/arroz-y-legumbres"),
    ("Despensa", "Fideos, pastas y salsas", "despensa/fideos-pastas-y-salsas"),
    ("Despensa", "Aceite y aliños", "despensa/aceite-y-alinos"),
    ("Despensa", "Azucar y endulzantes", "despensa/azucar-y-endulzantes"),
    ("Despensa", "Condimentos y salsas", "despensa/condimentos-y-salsas"),
    ("Despensa", "Harina y reposteria", "despensa/harina-y-reposteria"),
    ("Despensa", "Conservas", "despensa/conservas"),
    ("Despensa", "Coctel y snacks", "despensa/coctel-y-snacks"),
    ("Despensa", "Comida instantanea y preparada", "despensa/comida-instantanea-y-preparada"),
    ("Despensa", "Cocina internacional", "despensa/cocina-internacional"),
    ("Despensa", "Productos naturales", "despensa/productos-naturales"),
    # Desayuno y Dulces -> Desayuno y Snacks
    ("Desayuno y Snacks", "Cafe, te y hierbas", "desayuno-y-dulces/cafe-te-y-hierbas"),
    ("Desayuno y Snacks", "Cereales", "desayuno-y-dulces/cereales"),
    ("Desayuno y Snacks", "Chocolates y confites", "desayuno-y-dulces/chocolates-y-confites"),
    ("Desayuno y Snacks", "Galletas y colaciones dulces", "desayuno-y-dulces/galletas-y-colaciones-dulces"),
    ("Desayuno y Snacks", "Mermelada y manjar", "desayuno-y-dulces/mermelada-y-manjar"),
    ("Desayuno y Snacks", "Miel y salsas", "desayuno-y-dulces/miel-y-salsas"),
    # Bebidas y Licores -> Bebidas
    ("Bebidas", "Aguas", "bebidas-y-licores/aguas"),
    ("Bebidas", "Bebidas", "bebidas-y-licores/bebidas"),
    ("Bebidas", "Jugos", "bebidas-y-licores/jugos"),
    ("Bebidas", "Cervezas", "bebidas-y-licores/cervezas"),
    ("Bebidas", "Vinos y espumantes", "bebidas-y-licores/vinos-y-espumantes"),
    ("Bebidas", "Destilados y licores", "bebidas-y-licores/destilados-y-licores"),
    # Limpieza
    ("Limpieza", "Detergente", "limpieza/detergente"),
    ("Limpieza", "Papeles", "limpieza/papeles"),
    ("Limpieza", "Baño y cocina", "limpieza/bano-y-cocina"),
    ("Limpieza", "Limpieza hogar", "limpieza/limpieza-hogar"),
    ("Limpieza", "Pisos y muebles", "limpieza/pisos-y-muebles"),
    ("Limpieza", "Accesorios aseo", "limpieza/accesorios-aseo"),
    # Perfumeria -> Higiene Personal (sin farmacia)
    ("Higiene Personal", "Cuidado capilar", "perfumeria/cuidado-capilar"),
    ("Higiene Personal", "Cuidado bucal", "perfumeria/cuidado-bucal"),
    ("Higiene Personal", "Cuidado personal", "perfumeria/cuidado-personal"),
    ("Higiene Personal", "Cuidado corporal y facial", "perfumeria/cuidado-corporal-y-facial"),
    ("Higiene Personal", "Cuidado femenino", "perfumeria/cuidado-femenino"),
    ("Higiene Personal", "Cuidado masculino", "perfumeria/cuidado-masculino"),
    ("Higiene Personal", "Cuidado adulto", "perfumeria/cuidado-adulto"),
    # Bebes y Niños -> Bebe (perfumeria de bebe va a Higiene Personal)
    ("Bebe", "Alimentacion bebe", "bebes-y-ninos/alimentacion"),
    ("Bebe", "Pañales y toallas humedas", "bebes-y-ninos/panales-y-toallas-humedas"),
    ("Higiene Personal", "Perfumeria bebe", "bebes-y-ninos/perfumeria"),
    # Mascotas
    ("Mascotas", "Alimento perro", "mascotas/alimento-perro"),
    ("Mascotas", "Alimento gato", "mascotas/alimento-gato"),
    ("Mascotas", "Alimento otras mascotas", "mascotas/alimento-otras-mascotas"),
    ("Mascotas", "Accesorios mascota", "mascotas/accesorios-mascota"),
]


def crear_driver():
    opciones = Options()
    opciones.add_argument("--headless=new")
    opciones.add_argument("--window-size=1200,800")
    # No cargar imagenes: el __NEXT_DATA__ ya trae la URL de la imagen y bajarlas
    # solo suma tiempo.
    opciones.add_experimental_option(
        "prefs", {"profile.managed_default_content_settings.images": 2}
    )
    opciones.page_load_strategy = "eager"   # esperar el DOM, no todos los recursos
    return webdriver.Chrome(options=opciones)


def extraer_next_data(html):
    """El JSON embebido de Next.js, o None si no esta."""
    m = re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', html, re.S)
    if not m:
        return None
    try:
        return json.loads(m.group(1))
    except json.JSONDecodeError:
        return None


def _datos_listado(next_data):
    """(availableProducts, resource) desde el dehydratedState de la categoria."""
    try:
        estado = next_data["props"]["pageProps"]["dehydratedState"]["queries"]
        data = estado[0]["state"]["data"]
        productos = data.get("availableProducts") or []
        resource = int(data.get("resource") or 0)
        return productos, resource
    except (KeyError, IndexError, TypeError, ValueError):
        return [], 0


def _entero(valor):
    digitos = re.sub(r"[^\d]", "", str(valor if valor is not None else ""))
    return int(digitos) if digitos else None


def extraer_producto(prod, categoria, subcategoria):
    """Un producto del __NEXT_DATA__ -> fila del CSV (o None si no sirve)."""
    nombre = (prod.get("name") or prod.get("nameComplete") or "").strip()
    if not nombre:
        return None

    vendedores = prod.get("sellers") or []
    vendedor = vendedores[0] if vendedores else {}
    precio = _entero(vendedor.get("price"))
    if not precio:
        return None

    precio_lista = _entero(vendedor.get("listPrice"))
    hay_oferta = bool(vendedor.get("inOffer") and precio_lista and precio_lista > precio)

    detalle = prod.get("detailUrl") or prod.get("slug") or ""
    imagenes = prod.get("images") or []

    producto = {
        "categoria": categoria,
        "subcategoria": subcategoria,
        "nombre": nombre,
        "precio": precio,
        "precio_normal": precio_lista if hay_oferta else precio,
        "precio_oferta": precio if hay_oferta else "",
        "precio_referencia": (vendedor.get("ppumListPrice") if hay_oferta else vendedor.get("ppum")) or "",
        "promocion": "Oferta" if hay_oferta else "",
        "url": ("https://www.unimarc.cl" + detalle) if detalle.startswith("/") else detalle,
        "imagen_url": imagenes[0] if imagenes else "",
        # El listado SI trae EAN (a diferencia de Tottus): producto comparable ya.
        "ean": re.sub(r"\D", "", str(prod.get("ean") or "")),
    }
    if not is_valid_row(producto, "scraper_unimarc", Path("reports") / "pipeline_category_rejections.csv"):
        return None
    return producto


def scrape_categoria(driver, categoria, subcategoria, slug):
    """Recorre las paginas de una categoria usando `resource` como techo real."""
    print(f"Scrapeando Unimarc {subcategoria}...", flush=True)
    productos, vistos = [], set()
    total_paginas = None

    for pagina in range(1, MAX_PAGINAS + 1):
        driver.get(f"{BASE_CATEGORIA}/{slug}?page={pagina}")
        time.sleep(ESPERA_RENDER)
        next_data = extraer_next_data(driver.page_source)
        resultados, resource = _datos_listado(next_data)

        if not resultados:
            if pagina == 1:
                raise RuntimeError(f"categoria {slug} sin productos (¿bloqueo o slug malo?)")
            break

        if total_paginas is None and resource:
            total_paginas = min(MAX_PAGINAS, -(-resource // POR_PAGINA))   # techo

        nuevos = 0
        for prod in resultados:
            producto = extraer_producto(prod, categoria, subcategoria)
            if not producto:
                continue
            clave = producto["ean"] or producto["url"] or producto["nombre"]
            if clave in vistos:
                continue
            vistos.add(clave)
            productos.append(producto)
            nuevos += 1

        print(f"  pagina {pagina} -> {len(productos)} acumulados", flush=True)

        if nuevos == 0:
            break                                    # el sitio recicla contenido
        if total_paginas and pagina >= total_paginas:
            break
        time.sleep(PAUSA_ENTRE_PAGINAS)

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

    driver = crear_driver()
    try:
        for categoria, subcategoria, slug in categorias:
            try:
                for producto in scrape_categoria(driver, categoria, subcategoria, slug):
                    clave = (subcategoria, producto["ean"] or producto["url"] or producto["nombre"])
                    if clave in vistos:
                        continue
                    vistos.add(clave)
                    productos.append(producto)
            except Exception as exc:
                print(f"Error en {subcategoria} ({slug}): {exc}. Continuando...", flush=True)
    finally:
        driver.quit()

    _publicar_con_guard(productos, {sub for _, sub, _ in categorias})


def _publicar_con_guard(productos, subcats_actuales):
    """Guard anti-regresion + red de seguridad de totales.

    - Filtra el baseline a las subcategorias vigentes: al migrar keyword->
      categoria, las subcats viejas del CSV no deben verse como caidas a 0.
    - Guard por subcategoria (carry-forward): una categoria que retrocede por
      throttling conserva sus filas previas; el resto se publica fresco.
    - Total: la migracion multiplica el catalogo, asi que si el total nuevo es
      MENOR que el previo, algo se rompio -> no pisar, dejar .nuevo y avisar.
    """
    previos_conteo = solo_subcategorias(leer_conteo_previo(OUTPUT), subcats_actuales)
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
    print(f"{len(fusion)} productos Unimarc guardados", flush=True)


if __name__ == "__main__":
    main()
