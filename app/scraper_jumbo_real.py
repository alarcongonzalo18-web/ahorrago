import csv
import json
import os
import time
import http.client
import urllib.error
import urllib.request
from pathlib import Path
from urllib.parse import urlencode, quote

from app.category_validator import is_valid_row
from app.config import cargar_env
from app.ean_fetch import VTEX_LOTE, fetch_eans_jumbo_por_id
# Guard anti-regresion generico, ya testeado en scraper_lider (no duplicar).
from app.scraper_lider import (
    es_migracion_de_taxonomia,
    fusionar_preservando,
    leer_conteo_previo,
    leer_productos_previos,
    solo_subcategorias,
)

BASE_URL = "https://www.jumbo.cl"
API_URL = "https://ac.cnstrc.com/browse/group_id/{group_id}"
OUTPUT = Path("data/jumbo_real.csv")
PAGE_SIZE = 100
PAUSA_ENTRE_PAGINAS = 1.0
PAUSA_ENTRE_CATEGORIAS = 3.0

# Mapeo curado del arbol real de Jumbo (Constructor.io) a las 12 categorias
# internas de AhorraGo. Formato: (categoria_interna, subcategoria_visible,
# group_id). Solo rubros de consumo; los group_id salen de
# `python -m app.descubrir_taxonomia jumbo`.
#
# Excluidos: rubros Hogar/Jugueteria/Libreria (335), Experiencias Jumbo (831),
# Catering (1025), Farmacia (1165), y Mi bebe (393, vestuario/rodados).
# Jumbo mete los congelados dentro del rubro "Lacteos, Huevos y Congelados": se
# rutean a la categoria interna "Congelados". La perfumeria de bebe va a
# "Higiene Personal" (el validador rechaza higiene bajo "Bebe").
CATEGORIAS = [
    # Rubro [1] Lacteos, Huevos y Congelados -> lacteos + congelados
    ("Lacteos, Huevos y Congelados", "Leches", "3"),
    ("Lacteos, Huevos y Congelados", "Yoghurt", "8"),
    ("Lacteos, Huevos y Congelados", "Mantequillas y Margarinas", "13"),
    ("Lacteos, Huevos y Congelados", "Postres Refrigerados", "12"),
    ("Lacteos, Huevos y Congelados", "Huevos", "19"),
    ("Lacteos, Huevos y Congelados", "Leches Cultivadas y Bebidas Lacteas", "691"),
    ("Lacteos, Huevos y Congelados", "Bebidas Vegetales", "690"),
    ("Congelados", "Verduras Congeladas", "1157"),
    ("Congelados", "Hamburguesas", "1139"),
    ("Congelados", "Comidas Congeladas", "1129"),
    ("Congelados", "Nuggets, Apanados y Embutidos", "1152"),
    ("Congelados", "Frutas y Pulpas Congeladas", "1135"),
    ("Congelados", "Helados y Postres", "1143"),
    ("Congelados", "Churrascos, Lomitos y Otros", "1126"),
    ("Congelados", "Hielo", "1151"),
    # Rubro [20] Frutas y Verduras
    ("Frutas y Verduras", "Frutas", "783"),
    ("Frutas y Verduras", "Verduras", "786"),
    ("Frutas y Verduras", "Frutos Secos y Semillas", "788"),
    ("Frutas y Verduras", "Frutas y verduras organicas", "23"),
    # Rubro [27] Despensa
    ("Despensa", "Conservas", "42"),
    ("Despensa", "Fideos, Pastas y Salsas", "33"),
    ("Despensa", "Arroz, Quinoa, Cuscus", "30"),
    ("Despensa", "Harinas, Postres y Reposteria", "62"),
    ("Despensa", "Aderezos y Salsas", "54"),
    ("Despensa", "Aceites, Sal y Condimentos", "299"),
    ("Despensa", "Azucar y Endulzantes", "1083"),
    ("Despensa", "Sopas, Cremas e Instantaneos", "313"),
    ("Despensa", "Legumbres", "1043"),
    # Cafe/te/cereales/mermelada/manjar -> Desayuno y Snacks
    ("Desayuno y Snacks", "Cafe y Cafeteras", "1046"),
    ("Desayuno y Snacks", "Te, Infusiones y Mate", "1089"),
    ("Desayuno y Snacks", "Cereales, Avenas y Barras", "1095"),
    ("Desayuno y Snacks", "Mermeladas, Miel y Otros", "1100"),
    ("Desayuno y Snacks", "Manjar y Dulce de Leche", "1106"),
    # Rubro [47] Chocolates, Galletas y Snacks -> Desayuno y Snacks
    ("Desayuno y Snacks", "Chocolates", "74"),
    ("Desayuno y Snacks", "Galletas Dulces", "1041"),
    ("Desayuno y Snacks", "Galletas Saladas", "1042"),
    ("Desayuno y Snacks", "Dulces", "825"),
    ("Desayuno y Snacks", "Snacks", "1044"),
    ("Desayuno y Snacks", "Pastas para Coctel y Untables", "1045"),
    # Rubro [75] Carnes y Pescados
    ("Carnes y Pescados", "Pollo", "108"),
    ("Carnes y Pescados", "Vacuno", "76"),
    ("Carnes y Pescados", "Pescados", "994"),
    ("Carnes y Pescados", "Cerdo y Cordero", "82"),
    ("Carnes y Pescados", "Gourmet del Mar", "989"),
    ("Carnes y Pescados", "Camarones", "983"),
    ("Carnes y Pescados", "Mariscos", "990"),
    ("Carnes y Pescados", "Pavo", "109"),
    # Rubro [86] Quesos y Fiambres -> split
    ("Carnes y Pescados", "Fiambres", "88"),
    ("Carnes y Pescados", "Salchichas y Parrilleros", "98"),
    ("Lacteos, Huevos y Congelados", "Quesos", "1109"),
    ("Despensa", "Aceitunas, Pepinillos y Otros", "91"),
    # Rubro [157] Panaderia
    ("Panaderia", "Panaderia granel", "161"),
    ("Panaderia", "Panaderia envasada", "573"),
    ("Panaderia", "Pasteleria", "159"),
    ("Panaderia", "Masas y Tortillas", "162"),
    # Rubro [204] Licores, Bebidas y Aguas -> Bebidas
    ("Bebidas", "Bebidas Gaseosas", "958"),
    ("Bebidas", "Jugos", "969"),
    ("Bebidas", "Cocteles", "206"),
    ("Bebidas", "Aguas", "953"),
    ("Bebidas", "Cervezas", "205"),
    ("Bebidas", "Vinos", "207"),
    ("Bebidas", "Licores y Spritz", "977"),
    ("Bebidas", "Espumantes y Sidras", "221"),
    ("Bebidas", "Bebidas Isotonicas y Sueros", "963"),
    ("Bebidas", "Destilados", "699"),
    ("Bebidas", "Infusiones Frias", "966"),
    ("Bebidas", "Sin Alcohol", "794"),
    ("Bebidas", "Bebidas Energeticas", "957"),
    ("Bebidas", "Agua Tonica y Ginger Beer", "950"),
    # Rubro [230] Cuidado Personal y Bebe -> Higiene Personal
    ("Higiene Personal", "Cuidado Capilar", "233"),
    ("Higiene Personal", "Cuidado Bebe", "235"),
    ("Higiene Personal", "Jabones", "231"),
    ("Higiene Personal", "Cuidado Facial", "255"),
    ("Higiene Personal", "Cuidado Corporal", "256"),
    ("Higiene Personal", "Higiene Bucal", "232"),
    ("Higiene Personal", "Proteccion Femenina", "234"),
    ("Higiene Personal", "Desodorantes", "636"),
    ("Higiene Personal", "Cuidado Masculino", "236"),
    ("Higiene Personal", "Incontinencia y Panales Adulto", "224"),
    ("Higiene Personal", "Depilacion", "470"),
    ("Higiene Personal", "Maquillaje", "602"),
    ("Higiene Personal", "Packs de Cuidado y Belleza", "285"),
    ("Higiene Personal", "Solares y Autobronceantes", "524"),
    # Rubro [261] Limpieza
    ("Limpieza", "Papeles Hogar", "262"),
    ("Limpieza", "Limpieza de Ropa", "263"),
    ("Limpieza", "Pisos y Muebles", "265"),
    ("Limpieza", "Bano", "942"),
    ("Limpieza", "Accesorios de Limpieza", "267"),
    ("Limpieza", "Cocina", "943"),
    ("Limpieza", "Aerosoles y Aromatizantes", "266"),
    # Rubro [400] Mascotas
    ("Mascotas", "Perros", "401"),
    ("Mascotas", "Gatos", "402"),
    ("Mascotas", "Otras Mascotas", "403"),
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


def obtener_api_key():
    # En la tarea programada no hay shell que exporte variables: se completa
    # desde .env (ver app/config.py). Lo ya definido en el entorno tiene prioridad.
    cargar_env()
    api_key = os.environ.get("JUMBO_API_KEY")
    if not api_key:
        raise RuntimeError(
            "Falta JUMBO_API_KEY. Definila en el entorno o en el archivo .env "
            "de la raíz del proyecto (ver .env.example)."
        )
    return api_key


def construir_url(group_id, pagina):
    params = urlencode({
        "key": obtener_api_key(),
        "num_results_per_page": PAGE_SIZE,
        "page": pagina,
    })
    return API_URL.format(group_id=quote(str(group_id))) + "?" + params


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
        # El listado de Constructor.io no trae EAN (RefId es interno de
        # Cencosud), pero si el ProductId: con el se resuelve por lotes contra
        # el catalogo VTEX en _resolver_eans, antes de guardar el CSV.
        "ean":              "",
        "_product_id":      str(d.get("ProductId") or d.get("productId") or ""),
    }


def scrape_categoria(categoria, subcategoria, group_id):
    productos = []
    vistos = set()
    pagina = 1
    total = None

    print(f"Scrapeando Jumbo {subcategoria}...")

    while True:
        url = construir_url(group_id, pagina)
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
            if not is_valid_row(producto, "scraper_jumbo_real", Path("reports") / "pipeline_category_rejections.csv"):
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
        time.sleep(PAUSA_ENTRE_PAGINAS)

    return productos


def _resolver_eans(productos, pausa=0.3):
    """Completa el EAN de los productos consultando VTEX por lotes de 50.

    Antes Jumbo salia sin EAN y lo llenaba backfill_ean de a uno contra el BFF,
    que bloquea a las pocas consultas: con 34.000 fichas nunca iba a terminar.
    Aca se resuelve en ~700 requests mientras corre el scrape.
    """
    pendientes = {}
    for producto in productos:
        pid = producto.get("_product_id")
        if pid and not producto.get("ean"):
            pendientes.setdefault(pid, []).append(producto)

    if not pendientes:
        return 0

    ids = list(pendientes)
    resueltos = 0
    print(f"Resolviendo EAN de {len(ids)} productos ({-(-len(ids) // VTEX_LOTE)} lotes)...")
    for inicio in range(0, len(ids), VTEX_LOTE):
        lote = ids[inicio:inicio + VTEX_LOTE]
        try:
            encontrados = fetch_eans_jumbo_por_id(lote)
        except Exception as exc:   # una tanda perdida no puede matar la corrida
            print(f"  lote {inicio // VTEX_LOTE + 1}: {type(exc).__name__}, se continua")
            continue
        for pid, ean in encontrados.items():
            for producto in pendientes.get(pid, []):
                producto["ean"] = ean
                resueltos += 1
        time.sleep(pausa)

    print(f"  EAN resuelto en {resueltos} de {len(productos)} productos")
    return resueltos


def guardar_productos(productos, path=OUTPUT):
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "categoria", "subcategoria", "nombre", "precio",
        "precio_normal", "precio_oferta", "precio_referencia",
        "promocion", "url", "imagen_url", "ean",
    ]
    with open(path, "w", newline="", encoding="utf-8") as f:
        # extrasaction="ignore": los productos llevan _product_id para resolver
        # el EAN por lotes (ver _resolver_eans); no es parte del contrato del CSV.
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(productos)


def main(categorias=None):
    obtener_api_key()
    todos = []
    vistos_global = set()
    cats = categorias if categorias is not None else CATEGORIAS

    for categoria, subcategoria, group_id in cats:
        try:
            for prod in scrape_categoria(categoria, subcategoria, group_id):
                key = (prod["nombre"], prod["precio"], prod["url"])
                if key in vistos_global:
                    continue
                vistos_global.add(key)
                todos.append(prod)
        except Exception as e:
            print(f"Error en {subcategoria}: {e}. Continuando...")
        time.sleep(PAUSA_ENTRE_CATEGORIAS)

    _resolver_eans(todos)
    _publicar_con_guard(todos, {sub for _, sub, _ in cats})
    return todos


def _publicar_con_guard(productos, subcats_actuales):
    """Guard anti-regresion + red de seguridad de totales.

    - Filtra el baseline a las subcategorias vigentes: al migrar keyword->
      categoria, las subcats viejas del CSV no deben verse como caidas a 0.
    - Carry-forward por subcategoria: una categoria que retrocede por throttling
      conserva sus filas previas; el resto se publica fresco.
    - Total: la migracion multiplica el catalogo; si el total nuevo es MENOR que
      el previo, algo se rompio -> no pisar, dejar .nuevo y avisar.
    """
    conteo_previo_crudo = leer_conteo_previo(OUTPUT)
    if es_migracion_de_taxonomia(conteo_previo_crudo, subcats_actuales):
        # Corrida de migracion: el CSV previo usa otra taxonomia, no hay contra
        # que comparar. Publicar directo (el guard vuelve solo la corrida siguiente).
        guardar_productos(productos)
        print(f"\n{len(productos)} productos Jumbo guardados (migracion de taxonomia: guard omitido)")
        return

    previos_conteo = solo_subcategorias(conteo_previo_crudo, subcats_actuales)
    previos_filas = solo_subcategorias(leer_productos_previos(OUTPUT), subcats_actuales)

    fusion, preservadas = fusionar_preservando(productos, previos_filas)
    for sub, antes, ahora in sorted(preservadas, key=lambda c: c[1] - c[2], reverse=True):
        print(f"  carry-forward {sub}: {antes} -> {ahora} (se conservan las filas previas)")

    total_previo = sum(previos_conteo.values())
    if total_previo and len(fusion) < total_previo:
        destino = OUTPUT.with_suffix(OUTPUT.suffix + ".nuevo")
        guardar_productos(fusion, destino)
        print(f"\n*** TOTAL A LA BAJA: {total_previo} -> {len(fusion)}. No se piso {OUTPUT} ***")
        print(f"La corrida nueva quedo en {destino} para inspeccion")
        return

    guardar_productos(fusion)
    print(f"\n{len(fusion)} productos Jumbo guardados en {OUTPUT}")


if __name__ == "__main__":
    main()
