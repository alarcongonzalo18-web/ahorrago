"""Scraper de Lider por el endpoint NUEVO (SPA de Walmart / Next.js).

TRANSPORTE RESUELTO 26-07-2026: `undetected-chromedriver` **pasa Akamai** (urllib
y Selenium normal, headless o no, seguian bloqueados). Verificado contra
/browse/higiene-y-cuidado-personal/jabones: **143 productos, maxPage=4**, contra
los ~10 que da el endpoint viejo /v/jabones. Ver app/docs/lider-endpoint-nuevo.md.

ARBOL RESUELTO 26-07-2026: los 1.135 paths /browse estan en el JSON del home,
escapados como \\/browse\\/... — no como href, por eso las busquedas por enlaces
daban cero. De ahi salen las 94 subcategorias nivel-2 de consumo (el endpoint
viejo daba 93, pero capadas: 13 topaban en 48 productos).

`productos_desde_next_data(...)` devuelve los productos con las mismas columnas
que scraper_lider.py y con el EAN directo en `usItemId` (Lider no necesita
backfill).

    python -m app.scraper_lider_browse        # corrida completa
"""

import csv
import json
import re
import time
from pathlib import Path

from app.category_validator import is_valid_row
from app.url_utils import ean13_check_digit
from app.scraper_lider import (
    CAMPOS,
    es_migracion_de_taxonomia,
    fusionar_preservando,
    leer_conteo_previo,
    leer_productos_previos,
    solo_subcategorias,
)

# Mapeo curado del arbol /browse (nivel 2) a las 12 categorias internas.
# Formato: (categoria_interna, subcategoria_visible, path).
#
# El arbol NO se saca del home: el home solo menciona parte de el y por eso la
# primera version perdio el 80% de carnes y el 70% de bebidas. Hay que visitar
# cada rubro, que si lista a sus hermanas (`descubrir_taxonomia lider`).
# Dos trampas de nombres: "la-boti" es la BOTILLERIA (vinos, cervezas, licores),
# no una farmacia; y "frescos-y-lacteos" —no "lacteos"— es el rubro que trae la
# leche. Excluidos: automovil, ferreteria, hogar, libreria, parrillas-y-jardin,
# tecno-y-electro, vestuario, deporte, salud-y-estilos-de-vida (suplementos) y
# marcas-propias / marcas-americanas (duplican productos de otros rubros).
CATEGORIAS_BROWSE = [
    # -> Bebe
    ("Bebe", "Alimentacion Y Lactancia", "/browse/mundo-bebe-y-jugueteria/alimentacion-y-lactancia/11780484_23586822"),
    ("Bebe", "Panales Y Toallas Humedas", "/browse/mundo-bebe-y-jugueteria/panales-y-toallas-humedas/11780484_12671170"),
    ("Bebe", "Perfumeria E Higiene", "/browse/mundo-bebe-y-jugueteria/perfumeria-e-higiene/11780484_96645034"),
    # -> Bebidas
    ("Bebidas", "Aguas", "/browse/bebidas-y-snacks/aguas/13901022_67311042"),
    ("Bebidas", "Bebidas", "/browse/bebidas-y-snacks/bebidas/13901022_56657077"),
    ("Bebidas", "Bebidas Funcionales", "/browse/bebidas-y-snacks/bebidas-funcionales/13901022_63687960"),
    ("Bebidas", "Jugos", "/browse/bebidas-y-snacks/jugos/13901022_61163586"),
    ("Bebidas", "Cerveza", "/browse/la-boti/cerveza/60338008_25254512"),
    ("Bebidas", "Coctel", "/browse/la-boti/coctel/60338008_30587707"),
    ("Bebidas", "Destilados", "/browse/la-boti/destilados/60338008_18800914"),
    ("Bebidas", "Espumantes", "/browse/la-boti/espumantes/60338008_75569554"),
    ("Bebidas", "Preparalo Tu Mismo", "/browse/la-boti/preparalo-tu-mismo/60338008_59156238"),
    ("Bebidas", "Sin Alcohol", "/browse/la-boti/sin-alcohol/60338008_15483971"),
    ("Bebidas", "Vinos", "/browse/la-boti/vinos/60338008_85836428"),
    # -> Carnes y Pescados
    ("Carnes y Pescados", "Cerdo", "/browse/carnes-y-pescados/cerdo/21856785_97025819"),
    ("Carnes y Pescados", "Cordero", "/browse/carnes-y-pescados/cordero/21856785_32675613"),
    ("Carnes y Pescados", "Para Parrilla", "/browse/carnes-y-pescados/para-parrilla/21856785_96130591"),
    ("Carnes y Pescados", "Pavo", "/browse/carnes-y-pescados/pavo/21856785_66365889"),
    ("Carnes y Pescados", "Pescados Y Mariscos", "/browse/carnes-y-pescados/pescados-y-mariscos/21856785_89519682"),
    ("Carnes y Pescados", "Pollo", "/browse/carnes-y-pescados/pollo/21856785_36612818"),
    ("Carnes y Pescados", "Vacuno", "/browse/carnes-y-pescados/vacuno/21856785_29265944"),
    ("Carnes y Pescados", "Fiambres Y Embutidos", "/browse/frescos-y-lacteos/fiambres-y-embutidos/45669105_22196003"),
    # -> Congelados
    ("Congelados", "Comidas Congeladas", "/browse/congelados/comidas-congeladas/13010356_98401550"),
    ("Congelados", "Hamburguesas Y Churrascos", "/browse/congelados/hamburguesas-y-churrascos/13010356_13257607"),
    ("Congelados", "Helados", "/browse/congelados/helados/13010356_52337906"),
    ("Congelados", "Verduras Y Frutas Congeladas", "/browse/congelados/verduras-y-frutas-congeladas/13010356_19939301"),
    # -> Desayuno y Snacks
    ("Desayuno y Snacks", "Snacks Y Picoteo", "/browse/bebidas-y-snacks/snacks-y-picoteo/13901022_66742898"),
    ("Desayuno y Snacks", "Barritas Y Cereales", "/browse/colaciones/barritas-y-cereales/49858221_71008317"),
    ("Desayuno y Snacks", "Galletas Y Snack Colacion", "/browse/colaciones/galletas-y-snack-colacion/49858221_84316329"),
    ("Desayuno y Snacks", "Jugos Colacion", "/browse/colaciones/jugos-colacion/49858221_87081691"),
    ("Desayuno y Snacks", "Cafe Te Y Hierbas", "/browse/desayunos-y-dulces/cafe-te-y-hierbas/23483116_11894805"),
    ("Desayuno y Snacks", "Cereales", "/browse/desayunos-y-dulces/cereales/23483116_70936805"),
    ("Desayuno y Snacks", "Chocolates Y Candy", "/browse/desayunos-y-dulces/chocolates-y-candy/23483116_82062599"),
    ("Desayuno y Snacks", "Dulces Mermeladas Y Manjar", "/browse/desayunos-y-dulces/dulces-mermeladas-y-manjar/23483116_35492092"),
    ("Desayuno y Snacks", "Galletas Y Colaciones Dulces", "/browse/desayunos-y-dulces/galletas-y-colaciones-dulces/23483116_20760251"),
    ("Desayuno y Snacks", "Postres Para Preparar", "/browse/desayunos-y-dulces/postres-para-preparar/23483116_58016199"),
    # -> Despensa
    ("Despensa", "Aceites Y Aderezos", "/browse/despensa/aceites-y-aderezos/46589040_87511978"),
    ("Despensa", "Alimentos Instantaneos", "/browse/despensa/alimentos-instantaneos/46589040_52225904"),
    ("Despensa", "Arroz Y Legumbres", "/browse/despensa/arroz-y-legumbres/46589040_29552324"),
    ("Despensa", "Cocina Internacional", "/browse/despensa/cocina-internacional/46589040_15612080"),
    ("Despensa", "Conservas", "/browse/despensa/conservas/46589040_33283038"),
    ("Despensa", "Harinas Y Polvos", "/browse/despensa/harinas-y-polvos/46589040_37852653"),
    ("Despensa", "Pastas Y Salsas", "/browse/despensa/pastas-y-salsas/46589040_59615139"),
    ("Despensa", "Salsas", "/browse/despensa/salsas/46589040_47278253"),
    # -> Frutas y Verduras
    ("Frutas y Verduras", "Frutas", "/browse/frutas-y-verduras/frutas/22884697_93034836"),
    ("Frutas y Verduras", "Frutos Secos", "/browse/frutas-y-verduras/frutos-secos/22884697_77940868"),
    ("Frutas y Verduras", "Verduras", "/browse/frutas-y-verduras/verduras/22884697_56981658"),
    # -> Higiene Personal
    ("Higiene Personal", "Afeitado Y Depilacion", "/browse/belleza/afeitado-y-depilacion/70159643_75593741"),
    ("Higiene Personal", "Rutina Corporal", "/browse/belleza/rutina-corporal/70159643_38045396"),
    ("Higiene Personal", "Rutina Para El Cabello", "/browse/belleza/rutina-para-el-cabello/70159643_23785819"),
    ("Higiene Personal", "Cuidado Adulto Mayor", "/browse/higiene-y-cuidado-personal/cuidado-adulto-mayor/72387472_32027656"),
    ("Higiene Personal", "Cuidado Bucal", "/browse/higiene-y-cuidado-Personal/cuidado-bucal/72387472_88733049"),
    ("Higiene Personal", "Desodorantes Y Cuidado Corporal", "/browse/higiene-y-cuidado-personal/desodorantes-y-cuidado-corporal/72387472_37200412"),
    ("Higiene Personal", "Jabones", "/browse/higiene-y-cuidado-personal/jabones/72387472_38253071"),
    ("Higiene Personal", "Proteccion Femenina", "/browse/higiene-y-cuidado-personal/proteccion-femenina/72387472_69099803"),
    ("Higiene Personal", "Protectores Solares", "/browse/higiene-y-cuidado-personal/protectores-solares/72387472_47232852"),
    ("Higiene Personal", "Belleza", "/browse/perfumeria-y-salud/belleza/79913105_14554833"),
    ("Higiene Personal", "Cuidado Capilar", "/browse/perfumeria-y-salud/cuidado-capilar/79913105_63165426"),
    ("Higiene Personal", "Cuidado Facial Y Corporal", "/browse/perfumeria-y-salud/cuidado-facial-y-corporal/79913105_20985429"),
    ("Higiene Personal", "Cuidado Hombre", "/browse/perfumeria-y-salud/cuidado-hombre/79913105_46480165"),
    ("Higiene Personal", "Cuidado Mujer", "/browse/perfumeria-y-salud/cuidado-mujer/79913105_95389554"),
    ("Higiene Personal", "Cuidado Personal", "/browse/perfumeria-y-salud/cuidado-personal/79913105_16440401"),
    ("Higiene Personal", "Proteccion Solar", "/browse/perfumeria-y-salud/proteccion-solar/79913105_35040711"),
    ("Higiene Personal", "Salud", "/browse/perfumeria-y-salud/salud/79913105_94972302"),
    # -> Lacteos, Huevos y Congelados
    ("Lacteos, Huevos y Congelados", "Refrigerados", "/browse/bebidas-y-snacks/refrigerados/13901022_41934663"),
    ("Lacteos, Huevos y Congelados", "Leches Colacion", "/browse/colaciones/leches-colacion/49858221_52536805"),
    ("Lacteos, Huevos y Congelados", "Yoghurt", "/browse/colaciones/yoghurt/49858221_10191488"),
    ("Lacteos, Huevos y Congelados", "Bebidas Vegetales", "/browse/frescos-y-lacteos/bebidas-vegetales/45669105_53011137"),
    ("Lacteos, Huevos y Congelados", "Cremas", "/browse/frescos-y-lacteos/cremas/45669105_27824002"),
    ("Lacteos, Huevos y Congelados", "Huevos", "/browse/frescos-y-lacteos/huevos/45669105_43398659"),
    ("Lacteos, Huevos y Congelados", "Leche", "/browse/frescos-y-lacteos/leche/45669105_39354732"),
    ("Lacteos, Huevos y Congelados", "Mantequillas Y Margarinas", "/browse/frescos-y-lacteos/mantequillas-y-margarinas/45669105_15064481"),
    ("Lacteos, Huevos y Congelados", "Postres Refrigerados", "/browse/frescos-y-lacteos/postres-refrigerados/45669105_15349134"),
    ("Lacteos, Huevos y Congelados", "Quesos", "/browse/frescos-y-lacteos/quesos/45669105_72564080"),
    # -> Limpieza
    ("Limpieza", "Accesorios Aseo", "/browse/limpieza-y-aseo/accesorios-aseo/43390617_61764352"),
    ("Limpieza", "Ambientadores", "/browse/limpieza-y-aseo/ambientadores/43390617_32024397"),
    ("Limpieza", "Bano Y Cocina", "/browse/limpieza-y-aseo/bano-y-cocina/43390617_15090475"),
    ("Limpieza", "Desinfeccion", "/browse/limpieza-y-aseo/desinfeccion/43390617_57052803"),
    ("Limpieza", "Detergentes", "/browse/limpieza-y-aseo/detergentes/43390617_23557375"),
    ("Limpieza", "Insecticidas Y Control De Plagas", "/browse/limpieza-y-aseo/insecticidas-y-control-de-plagas/43390617_74938748"),
    ("Limpieza", "Mas Sustentables", "/browse/limpieza-y-aseo/mas-sustentables/43390617_56006489"),
    ("Limpieza", "Papeles", "/browse/limpieza-y-aseo/papeles/43390617_72719306"),
    ("Limpieza", "Pisos Y Muebles", "/browse/limpieza-y-aseo/pisos-y-muebles/43390617_45008163"),
    # -> Mascotas
    ("Mascotas", "Mascotas En Casa", "/browse/limpieza-y-aseo/mascotas-en-casa/43390617_43573441"),
    ("Mascotas", "Gato", "/browse/mascotas/gato/07089592_85723699"),
    ("Mascotas", "Higiene Y Bienestar", "/browse/mascotas/higiene-y-bienestar/07089592_02342029"),
    ("Mascotas", "Otras Mascotas", "/browse/mascotas/otras-mascotas/07089592_42714284"),
    ("Mascotas", "Perro", "/browse/mascotas/perro/07089592_29432822"),
    # -> Panaderia
    ("Panaderia", "Panaderia Envasada", "/browse/panaderia-y-pasteleria/panaderia-envasada/73535247_22477361"),
    ("Panaderia", "Panaderia Granel", "/browse/panaderia-y-pasteleria/panaderia-granel/73535247_87066079"),
    ("Panaderia", "Pasteleria", "/browse/panaderia-y-pasteleria/pasteleria/73535247_90671850"),
    ("Panaderia", "Reposteria", "/browse/panaderia-y-pasteleria/reposteria/73535247_58054857"),
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
    """usItemId de Walmart -> EAN-13, el mismo formato que usan las otras cadenas.

    OJO: el usItemId NO trae el digito verificador. '00780500031555' son los 12
    digitos de datos con dos ceros de relleno adelante; el EAN real es
    '7805000315559'. Hacer solo lstrip('0') devuelve 12 digitos y entonces
    NINGUN producto de Lider matchea con Jumbo/Tottus/Unimarc: la cadena aporta
    cero comparables y el KPI se cae sin causa aparente (detectado el 27-07 al
    ver 0 EAN en comun entre el scrape viejo y el nuevo).

    Misma reconstruccion que `extraer_ean_lider` (app/url_utils.py), que ya lo
    hacia bien desde la URL del endpoint viejo.
    """
    if not us_item_id:
        return ""
    digitos = re.sub(r"\D", "", str(us_item_id))
    if len(digitos) < 12:
        return digitos.lstrip("0")   # codigos cortos (EAN-8 y similares): sin reconstruir
    datos12 = digitos[-12:]          # el relleno va adelante; los datos son los ultimos 12
    return (datos12 + ean13_check_digit(datos12)).lstrip("0")


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


# Archivo propio: NO pisa el del endpoint viejo. Las dos fuentes de Lider se
# complementan y combinar_supermercados las fusiona por EAN (ver FUENTES alli).
OUTPUT = Path("data/lider_browse.csv")
MAX_PAGINAS = 25
PAUSA_ENTRE_PAGINAS = 1.5


def scrape_categoria(driver, categoria, subcategoria, path):
    """Recorre las paginas de una categoria usando paginationV2.maxPage."""
    print(f"Scrapeando Lider {subcategoria}...", flush=True)
    productos, vistos = [], set()
    max_pagina = None

    for pagina in range(1, MAX_PAGINAS + 1):
        try:
            data = extraer_next_data(bajar_categoria(driver, path, pagina))
        except Exception as exc:
            print(f"  pagina {pagina}: {type(exc).__name__}, se corta la categoria", flush=True)
            break
        if not data:      # challenge de Akamai o pagina rota
            print(f"  pagina {pagina}: sin __NEXT_DATA__ (bloqueo?), se corta", flush=True)
            break

        if max_pagina is None:
            _total, max_pagina = total_y_paginas(data)

        nuevos = 0
        for producto in productos_desde_next_data(data, categoria, subcategoria):
            clave = (producto["nombre"], producto["url"])
            if clave in vistos or not producto["precio"]:
                continue
            if not is_valid_row(producto, "scraper_lider_browse",
                                Path("reports") / "pipeline_category_rejections.csv"):
                continue
            vistos.add(clave)
            productos.append(producto)
            nuevos += 1

        print(f"  pagina {pagina}/{max_pagina or '?'} -> {len(productos)} acumulados", flush=True)
        if nuevos == 0 or (max_pagina and pagina >= max_pagina):
            break
        time.sleep(PAUSA_ENTRE_PAGINAS)

    return productos


def main(categorias=None):
    categorias = categorias if categorias is not None else CATEGORIAS_BROWSE
    driver = crear_driver()
    productos, vistos = [], set()
    try:
        for categoria, subcategoria, path in categorias:
            try:
                for producto in scrape_categoria(driver, categoria, subcategoria, path):
                    clave = (producto["nombre"], producto["url"])
                    if clave in vistos:
                        continue
                    vistos.add(clave)
                    productos.append(producto)
            except Exception as exc:
                print(f"Error en {subcategoria}: {exc}. Continuando...", flush=True)
    finally:
        try:
            driver.quit()
        except Exception:
            pass

    _publicar_con_guard(productos, {sub for _, sub, _ in categorias})
    return productos


def guardar_productos(productos, path=OUTPUT):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CAMPOS, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(productos)


def _publicar_con_guard(productos, subcats_actuales):
    """Mismo guard que las otras cadenas: migracion, carry-forward y totales."""
    conteo_previo = leer_conteo_previo(OUTPUT)
    if es_migracion_de_taxonomia(conteo_previo, subcats_actuales):
        guardar_productos(productos)
        print(f"{len(productos)} productos Lider guardados "
              f"(migracion de taxonomia: guard omitido)", flush=True)
        return

    previos_filas = solo_subcategorias(leer_productos_previos(OUTPUT), subcats_actuales)
    fusion, preservadas = fusionar_preservando(productos, previos_filas)
    for sub, antes, ahora in sorted(preservadas, key=lambda c: c[1] - c[2], reverse=True):
        print(f"  carry-forward {sub}: {antes} -> {ahora}", flush=True)

    total_previo = sum(solo_subcategorias(conteo_previo, subcats_actuales).values())
    if total_previo and len(fusion) < total_previo:
        destino = OUTPUT.with_suffix(OUTPUT.suffix + ".nuevo")
        guardar_productos(fusion, destino)
        print(f"\n*** TOTAL A LA BAJA: {total_previo} -> {len(fusion)}. "
              f"No se piso {OUTPUT}; quedo en {destino} ***", flush=True)
        return

    guardar_productos(fusion)
    print(f"{len(fusion)} productos Lider guardados", flush=True)


if __name__ == "__main__":
    main()
