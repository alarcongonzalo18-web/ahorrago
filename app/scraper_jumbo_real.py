import csv
import json
import os
import time
import http.client
import urllib.error
import urllib.request
from pathlib import Path
from urllib.parse import urlencode, quote

BASE_URL = "https://www.jumbo.cl"
API_URL = "https://ac.cnstrc.com/search/{query}"
API_KEY = os.environ.get("JUMBO_API_KEY", "key_JopvNXKS61kwGkBe")
OUTPUT = Path("data/jumbo_real.csv")
PAGE_SIZE = 100

CATEGORIAS = [
    # Lácteos y refrigerados
    ("Lacteos, Huevos y Congelados", "Leche",           "leche"),
    ("Lacteos, Huevos y Congelados", "Huevos",          "huevos"),
    ("Lacteos, Huevos y Congelados", "Yogurt",          "yogurt"),
    ("Lacteos, Huevos y Congelados", "Quesos",          "queso"),
    ("Lacteos, Huevos y Congelados", "Mantequilla",     "mantequilla"),
    ("Lacteos, Huevos y Congelados", "Crema",           "crema"),
    # Frutas y verduras
    ("Frutas y Verduras",            "Frutas",          "fruta"),
    ("Frutas y Verduras",            "Verduras",        "verdura"),
    # Carnes y pescados
    ("Carnes y Pescados",            "Carnes",          "carne"),
    ("Carnes y Pescados",            "Aves",            "pollo"),
    ("Carnes y Pescados",            "Cecinas",         "cecinas"),
    ("Carnes y Pescados",            "Pescados",        "pescado"),
    ("Carnes y Pescados",            "Mariscos",        "mariscos"),
    # Congelados
    ("Congelados",                   "Congelados",      "congelado"),
    # Despensa
    ("Despensa", "Arroz y Legumbres", "arroz"),
    ("Despensa", "Aceites",           "aceite"),
    ("Despensa", "Cafe",              "cafe"),
    ("Despensa", "Azucar",            "azucar"),
    ("Despensa", "Fideos",            "fideos"),
    ("Despensa", "Conservas",         "conservas"),
    ("Despensa", "Salsas",            "salsa"),
    ("Despensa", "Condimentos",       "condimento"),
    ("Despensa", "Legumbres",         "legumbres"),
    # Desayuno y snacks
    ("Desayuno y Snacks", "Cereales",    "cereal"),
    ("Desayuno y Snacks", "Galletas",    "galleta"),
    ("Desayuno y Snacks", "Chocolates",  "chocolate"),
    ("Desayuno y Snacks", "Snacks",      "snack"),
    ("Desayuno y Snacks", "Mermeladas",  "mermelada"),
    # Bebidas
    ("Bebidas", "Bebidas",             "bebida gaseosa"),
    ("Bebidas", "Jugos",               "jugo"),
    ("Bebidas", "Aguas",               "agua mineral"),
    ("Bebidas", "Cervezas",            "cerveza"),
    ("Bebidas", "Vinos",               "vino"),
    ("Bebidas", "Bebidas Energeticas", "bebida energetica"),
    # Panadería
    ("Panaderia", "Pan",               "pan"),
    # Limpieza del hogar
    ("Limpieza", "Detergentes",        "detergente"),
    ("Limpieza", "Papel higienico",    "papel higienico"),
    ("Limpieza", "Limpiadores",        "limpiador"),
    ("Limpieza", "Lavavajillas",       "lavavajillas"),
    ("Limpieza", "Suavizantes",        "suavizante"),
    ("Limpieza", "Blanqueadores",      "blanqueador"),
    # Higiene personal
    ("Higiene Personal", "Shampoo",        "shampoo"),
    ("Higiene Personal", "Acondicionador", "acondicionador"),
    ("Higiene Personal", "Jabon",          "jabon"),
    ("Higiene Personal", "Desodorantes",   "desodorante"),
    ("Higiene Personal", "Cuidado Bucal",  "pasta dental"),
    ("Higiene Personal", "Cuidado Facial", "crema facial"),
    # Bebé
    ("Bebe", "Panales",                "panales"),
    ("Bebe", "Alimentos Bebe",         "alimento bebe"),
    # Mascotas
    ("Mascotas", "Alimento Perros",    "alimento perro"),
    ("Mascotas", "Alimento Gatos",     "alimento gato"),
]

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json",
    "Referer": "https://www.jumbo.cl/",
}


def construir_url(termino, pagina):
    params = urlencode({
        "key": API_KEY,
        "num_results_per_page": PAGE_SIZE,
        "page": pagina,
    })
    return API_URL.format(query=quote(termino)) + "?" + params


def descargar(url, intentos=4):
    req = urllib.request.Request(url, headers=HEADERS)
    ultimo_error = None
    for intento in range(1, intentos + 1):
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except (urllib.error.URLError, http.client.HTTPException, TimeoutError) as exc:
            ultimo_error = exc
            if intento < intentos:
                time.sleep(2 * intento)
    raise RuntimeError(f"Error descargando {url}: {ultimo_error}")


def _parsear_sku(sku_raw):
    try:
        if not sku_raw:
            return {}
        sku = json.loads(sku_raw[0])
        sku_id = list(sku.keys())[0]
        return sku[sku_id]
    except Exception:
        return {}


def _precio_referencia(precio, sku_info):
    unidad = sku_info.get("measurement_unit_un", "")
    multiplicador = sku_info.get("unit_multiplier_un", 1)
    if not unidad or unidad == "un" or not precio or not multiplicador:
        return ""
    try:
        valor = int(precio / float(multiplicador))
        return f"${valor:,} / {unidad}".replace(",", ".")
    except Exception:
        return ""


def extraer_producto(resultado, categoria, subcategoria):
    nombre = (resultado.get("value") or "").strip()
    if not nombre:
        return None

    d = resultado.get("data", {})
    precio_raw = d.get("price")
    if not precio_raw:
        return None

    try:
        precio_actual = round(float(precio_raw))
    except (ValueError, TypeError):
        return None

    url = d.get("url") or d.get("DetailUrl") or ""
    if url and not url.startswith("http"):
        url = BASE_URL + url

    imagenes = d.get("images", [])
    imagen = imagenes[0] if imagenes else ""

    sku_info = _parsear_sku(d.get("SkuData", []))
    promos = sku_info.get("promotions", [])

    precio_normal = precio_actual
    precio_oferta = ""
    promocion = ""

    if promos:
        promo = promos[0]
        precio_original = promo.get("price_from") or promo.get("original_price")
        if precio_original:
            try:
                precio_original_int = int(float(precio_original))
                if precio_original_int > precio_actual:
                    precio_normal = precio_original_int
                    precio_oferta = precio_actual
                    promocion = promo.get("name") or "Oferta"
            except (ValueError, TypeError):
                pass

    precio_ref = _precio_referencia(precio_actual, sku_info)

    return {
        "categoria":        categoria,
        "subcategoria":     subcategoria,
        "nombre":           nombre,
        "precio":           precio_oferta if precio_oferta else precio_normal,
        "precio_normal":    precio_normal,
        "precio_oferta":    precio_oferta,
        "precio_referencia": precio_ref,
        "promocion":        promocion,
        "url":              url,
        "imagen_url":       imagen,
    }


def scrape_categoria(categoria, subcategoria, termino):
    productos = []
    vistos = set()
    pagina = 1
    total = None

    print(f"Scrapeando Jumbo (API) {subcategoria}...")

    while True:
        url = construir_url(termino, pagina)
        try:
            data = descargar(url)
        except RuntimeError as e:
            print(f"  Error: {e}")
            break

        response = data.get("response", {})
        if total is None:
            total = response.get("total_num_results")

        resultados = response.get("results", [])
        if not resultados:
            break

        for r in resultados:
            producto = extraer_producto(r, categoria, subcategoria)
            if not producto:
                continue
            key = (producto["nombre"], producto["precio"], producto["url"])
            if key in vistos:
                continue
            vistos.add(key)
            productos.append(producto)

        obtenidos = (pagina - 1) * PAGE_SIZE + len(resultados)
        print(f"  pagina {pagina} -> {len(productos)} productos" + (f" / {total} totales" if total else ""))

        if total and obtenidos >= total:
            break
        if len(resultados) < PAGE_SIZE:
            break

        pagina += 1
        time.sleep(0.3)

    return productos


def guardar_productos(productos, path=OUTPUT):
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "categoria", "subcategoria", "nombre", "precio",
        "precio_normal", "precio_oferta", "precio_referencia",
        "promocion", "url", "imagen_url",
    ]
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(productos)


def main(categorias=None):
    todos = []
    vistos_global = set()
    cats = categorias or CATEGORIAS

    for categoria, subcategoria, termino in cats:
        try:
            for prod in scrape_categoria(categoria, subcategoria, termino):
                key = (prod["nombre"], prod["precio"], prod["url"])
                if key in vistos_global:
                    continue
                vistos_global.add(key)
                todos.append(prod)
        except Exception as e:
            print(f"Error en {subcategoria}: {e}. Continuando...")

    guardar_productos(todos)
    print(f"\n{len(todos)} productos Jumbo guardados en {OUTPUT}")
    return todos


if __name__ == "__main__":
    main()
