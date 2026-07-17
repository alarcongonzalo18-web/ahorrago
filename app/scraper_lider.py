import csv
import http.client
import json
import re
import time
import urllib.error
import urllib.request
from html import unescape
from pathlib import Path
from urllib.parse import urljoin

from app.category_validator import is_valid_row
from app.url_utils import extraer_ean_lider


OUTPUT = Path("data/lider_real.csv")

CATEGORIAS = [
    # Lácteos y refrigerados
    ("Lacteos, Huevos y Congelados", "Leche",           "https://super.lider.cl/v/leches"),
    ("Lacteos, Huevos y Congelados", "Huevos",          "https://super.lider.cl/v/huevos"),
    ("Lacteos, Huevos y Congelados", "Yogurt",          "https://super.lider.cl/v/yogurt"),
    ("Lacteos, Huevos y Congelados", "Quesos",          "https://super.lider.cl/v/quesos"),
    ("Lacteos, Huevos y Congelados", "Mantequilla",     "https://super.lider.cl/v/mantequilla"),
    ("Lacteos, Huevos y Congelados", "Crema",           "https://super.lider.cl/v/crema"),
    ("Lacteos, Huevos y Congelados", "Margarina",       "https://super.lider.cl/v/margarina"),
    ("Lacteos, Huevos y Congelados", "Manjar",          "https://super.lider.cl/v/manjar"),
    ("Lacteos, Huevos y Congelados", "Flanes y Postres", "https://super.lider.cl/v/flanes"),
    ("Lacteos, Huevos y Congelados", "Kefir",           "https://super.lider.cl/v/kefir"),
    # Frutas y verduras
    ("Frutas y Verduras",            "Frutas",          "https://super.lider.cl/v/frutas"),
    ("Frutas y Verduras",            "Verduras",        "https://super.lider.cl/v/verduras"),
    # Carnes y pescados
    ("Carnes y Pescados",            "Carnes",          "https://super.lider.cl/v/carnes"),
    ("Carnes y Pescados",            "Aves",            "https://super.lider.cl/v/aves"),
    ("Carnes y Pescados",            "Cecinas",         "https://super.lider.cl/v/cecinas"),
    ("Carnes y Pescados",            "Pescados",        "https://super.lider.cl/v/pescados"),
    ("Carnes y Pescados",            "Mariscos",        "https://super.lider.cl/v/mariscos"),
    ("Carnes y Pescados",            "Cerdo",           "https://super.lider.cl/v/cerdo"),
    ("Carnes y Pescados",            "Pavo",            "https://super.lider.cl/v/pavo"),
    ("Carnes y Pescados",            "Vacuno",          "https://super.lider.cl/v/vacuno"),
    ("Carnes y Pescados",            "Jamon",           "https://super.lider.cl/v/jamon"),
    ("Carnes y Pescados",            "Salchichas",      "https://super.lider.cl/v/salchichas"),
    ("Carnes y Pescados",            "Chorizo",         "https://super.lider.cl/v/chorizo"),
    ("Carnes y Pescados",            "Salmon",          "https://super.lider.cl/v/salmon"),
    # Congelados
    ("Congelados",                   "Congelados",      "https://super.lider.cl/v/congelados"),
    ("Congelados",                   "Nuggets",         "https://super.lider.cl/v/nuggets"),
    ("Congelados",                   "Hamburguesas",    "https://super.lider.cl/v/hamburguesas"),
    ("Congelados",                   "Helados",         "https://super.lider.cl/v/helados"),
    # Despensa
    ("Despensa", "Arroz",            "https://super.lider.cl/v/arroz"),
    ("Despensa", "Aceite",           "https://super.lider.cl/v/aceites"),
    ("Despensa", "Cafe",             "https://super.lider.cl/v/cafe"),
    ("Despensa", "Azucar",           "https://super.lider.cl/v/azucar"),
    ("Despensa", "Fideos",           "https://super.lider.cl/v/fideos"),
    ("Despensa", "Conservas",        "https://super.lider.cl/v/conservas"),
    ("Despensa", "Salsas",           "https://super.lider.cl/v/salsas"),
    ("Despensa", "Condimentos",      "https://super.lider.cl/v/condimentos"),
    ("Despensa", "Legumbres",        "https://super.lider.cl/v/legumbres"),
    ("Despensa", "Harina",           "https://super.lider.cl/v/harina"),
    ("Despensa", "Avena",            "https://super.lider.cl/v/avena"),
    ("Despensa", "Miel",             "https://super.lider.cl/v/miel"),
    ("Despensa", "Mayonesa",         "https://super.lider.cl/v/mayonesa"),
    ("Despensa", "Ketchup",          "https://super.lider.cl/v/ketchup"),
    ("Despensa", "Mostaza",          "https://super.lider.cl/v/mostaza"),
    ("Despensa", "Vinagre",          "https://super.lider.cl/v/vinagre"),
    ("Despensa", "Atun",             "https://super.lider.cl/v/atun"),
    ("Despensa", "Aceitunas",        "https://super.lider.cl/v/aceitunas"),
    ("Despensa", "Pure",             "https://super.lider.cl/v/pure"),
    ("Despensa", "Quinoa",           "https://super.lider.cl/v/quinoa"),
    ("Despensa", "Endulzantes",      "https://super.lider.cl/v/endulzante"),
    # Desayuno y snacks
    ("Desayuno y Snacks",            "Cereales",        "https://super.lider.cl/v/cereales"),
    ("Desayuno y Snacks",            "Galletas",        "https://super.lider.cl/v/galletas"),
    ("Desayuno y Snacks",            "Chocolates",      "https://super.lider.cl/v/chocolates"),
    ("Desayuno y Snacks",            "Snacks",          "https://super.lider.cl/v/snacks"),
    ("Desayuno y Snacks",            "Mermeladas",      "https://super.lider.cl/v/mermeladas"),
    ("Desayuno y Snacks",            "Granola",         "https://super.lider.cl/v/granola"),
    ("Desayuno y Snacks",            "Caramelos",       "https://super.lider.cl/v/caramelos"),
    ("Desayuno y Snacks",            "Gomitas",         "https://super.lider.cl/v/gomitas"),
    ("Desayuno y Snacks",            "Mani",            "https://super.lider.cl/v/mani"),
    # Bebidas
    ("Bebidas",                      "Bebidas",         "https://super.lider.cl/v/bebidas"),
    ("Bebidas",                      "Jugos",           "https://super.lider.cl/v/jugos"),
    ("Bebidas",                      "Aguas",           "https://super.lider.cl/v/aguas"),
    ("Bebidas",                      "Cervezas",        "https://super.lider.cl/v/cervezas"),
    ("Bebidas",                      "Vinos",           "https://super.lider.cl/v/vinos"),
    ("Bebidas",                      "Bebidas Energeticas", "https://super.lider.cl/v/bebidas-energeticas"),
    ("Bebidas",                      "Licores",         "https://super.lider.cl/v/licores"),
    ("Bebidas",                      "Pisco",           "https://super.lider.cl/v/pisco"),
    ("Bebidas",                      "Whisky",          "https://super.lider.cl/v/whisky"),
    ("Bebidas",                      "Vodka",           "https://super.lider.cl/v/vodka"),
    ("Bebidas",                      "Limonadas",       "https://super.lider.cl/v/limonadas"),
    # Panadería
    ("Panaderia",                    "Pan",             "https://super.lider.cl/v/pan"),
    ("Panaderia",                    "Marraqueta",      "https://super.lider.cl/v/marraqueta"),
    ("Panaderia",                    "Hallulla",        "https://super.lider.cl/v/hallulla"),
    ("Panaderia",                    "Tortas",          "https://super.lider.cl/v/tortas"),
    # Limpieza del hogar
    ("Limpieza",                     "Detergentes",     "https://super.lider.cl/v/detergentes"),
    ("Limpieza",                     "Papel higienico", "https://super.lider.cl/v/papel-higienico"),
    ("Limpieza",                     "Limpiadores",     "https://super.lider.cl/v/limpiadores"),
    ("Limpieza",                     "Lavavajillas",    "https://super.lider.cl/v/lavavajillas"),
    ("Limpieza",                     "Suavizantes",     "https://super.lider.cl/v/suavizantes"),
    ("Limpieza",                     "Blanqueadores",   "https://super.lider.cl/v/blanqueadores"),
    ("Limpieza",                     "Cloro",           "https://super.lider.cl/v/cloro"),
    ("Limpieza",                     "Servilletas",     "https://super.lider.cl/v/servilletas"),
    ("Limpieza",                     "Desinfectantes",  "https://super.lider.cl/v/desinfectantes"),
    # Higiene personal
    ("Higiene Personal",             "Shampoo",         "https://super.lider.cl/v/shampoo"),
    ("Higiene Personal",             "Acondicionador",  "https://super.lider.cl/v/acondicionador"),
    ("Higiene Personal",             "Jabon",           "https://super.lider.cl/v/jabones"),
    ("Higiene Personal",             "Desodorantes",    "https://super.lider.cl/v/desodorantes"),
    ("Higiene Personal",             "Cuidado Bucal",   "https://super.lider.cl/v/cuidado-bucal"),
    ("Higiene Personal",             "Cuidado Facial",  "https://super.lider.cl/v/cuidado-facial"),
    # Bebé
    ("Bebe",                         "Panales",         "https://super.lider.cl/v/panales"),
    ("Bebe",                         "Alimentos Bebe",  "https://super.lider.cl/v/alimentos-bebe"),
    # Mascotas
    ("Mascotas",                     "Alimento Perros", "https://super.lider.cl/v/alimento-para-perros"),
    ("Mascotas",                     "Alimento Gatos",  "https://super.lider.cl/v/alimento-para-gatos"),
    ("Mascotas",                     "Arena Sanitaria", "https://super.lider.cl/v/arena-sanitaria"),
]


def descargar_html(url, intentos=4):
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            )
        }
    )

    ultimo_error = None
    for intento in range(1, intentos + 1):
        try:
            with urllib.request.urlopen(request, timeout=45) as response:
                return response.read().decode("utf-8", errors="replace")
        except (
            TimeoutError,
            ConnectionError,
            http.client.HTTPException,
            urllib.error.URLError,
        ) as exc:
            ultimo_error = exc
            if intento == intentos:
                break

            espera = 2 * intento
            print(f"Descarga fallida ({intento}/{intentos}) para {url}: {exc}. Reintentando en {espera}s...")
            time.sleep(espera)

    raise RuntimeError(f"No se pudo descargar {url} tras {intentos} intentos: {ultimo_error}")


def extraer_json_ld(html):
    scripts = re.findall(
        r"<script[^>]+type=[\"']application/ld\+json[\"'][^>]*>(.*?)</script>",
        html,
        flags=re.S | re.I
    )

    for script in scripts:
        try:
            data = json.loads(unescape(script.strip()))
        except json.JSONDecodeError:
            continue

        if isinstance(data, dict) and data.get("@type") == "ItemList":
            return data.get("itemListElement", [])

    return []


def extraer_productos_desde_html(categoria, subcategoria, url, html):
    productos = []

    for item_lista in extraer_json_ld(html):
        item = item_lista.get("item", {})
        oferta = item.get("offers", {})
        nombre = item.get("name")
        precio = oferta.get("price")
        link = item.get("url")
        imagen = item.get("image")

        if isinstance(imagen, list):
            imagen = imagen[0] if imagen else ""

        if not nombre or not precio:
            continue

        producto = {
            "categoria": categoria,
            "subcategoria": subcategoria,
            "nombre": nombre,
            "precio": precio,
            "precio_normal": precio,
            "precio_oferta": "",
            "precio_referencia": "",
            "promocion": "",
            "url": urljoin(url, link) if link else "",
            "imagen_url": urljoin(url, imagen) if imagen else "",
            "ean": extraer_ean_lider(urljoin(url, link) if link else "")
        }
        if not is_valid_row(producto, "scraper_lider", Path("reports") / "pipeline_category_rejections.csv"):
            continue
        productos.append(producto)

    return productos


MAX_PAGINAS = 60


def extraer_productos(categoria, subcategoria, url):
    """Recorre la categoria pagina a pagina hasta que venga vacia.

    El widget de paginacion del sitio muestra solo algunos links (ej: 3 de
    8 paginas reales en /v/bebidas), asi que no sirve para saber cuantas
    paginas hay: se avanza secuencialmente con ?pagenumber=N hasta que una
    pagina no traiga productos.
    """
    print(f"Scrapeando Lider {subcategoria}...")
    productos = []
    vistos = set()

    for pagina in range(1, MAX_PAGINAS + 1):
        pagina_url = url if pagina == 1 else f"{url}?pagenumber={pagina}"
        try:
            html_pagina = descargar_html(pagina_url)
        except RuntimeError as exc:
            print(f"{pagina_url} -> error, se detiene la categoria: {exc}")
            break

        productos_pagina = extraer_productos_desde_html(
            categoria,
            subcategoria,
            pagina_url,
            html_pagina
        )
        if not productos_pagina:
            break

        nuevos = 0
        for producto in productos_pagina:
            key = (producto["nombre"], producto["precio"], producto["url"])
            if key in vistos:
                continue
            vistos.add(key)
            productos.append(producto)
            nuevos += 1

        print(f"{pagina_url} -> {len(productos)} acumulados")

        # si la pagina entera eran repetidos, el sitio esta reciclando
        # contenido mas alla del final real: cortar
        if nuevos == 0:
            break

        time.sleep(0.3)

    return productos


def guardar_productos(productos):
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)

    with open(OUTPUT, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "categoria",
                "subcategoria",
                "nombre",
                "precio",
                "precio_normal",
                "precio_oferta",
                "precio_referencia",
                "promocion",
                "url",
                "imagen_url",
                "ean",
            ]
        )
        writer.writeheader()
        writer.writerows(productos)


def main():
    productos = []
    vistos = set()

    for categoria, subcategoria, url in CATEGORIAS:
        try:
            for producto in extraer_productos(categoria, subcategoria, url):
                key = (
                    producto["categoria"],
                    producto["subcategoria"],
                    producto["nombre"],
                    producto["precio"],
                    producto["url"]
                )
                if key in vistos:
                    continue

                vistos.add(key)
                productos.append(producto)
        except Exception as e:
            print(f"Error en {subcategoria} ({url}): {e}. Continuando...")

    guardar_productos(productos)
    print(f"{len(productos)} productos Lider guardados")


if __name__ == "__main__":
    main()
