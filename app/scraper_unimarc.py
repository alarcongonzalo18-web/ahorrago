import csv
import re
import time
from pathlib import Path
from urllib.parse import quote_plus, urljoin

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.common.exceptions import StaleElementReferenceException


BASE = "https://www.unimarc.cl/search"
OUTPUT = Path("data/unimarc_real.csv")

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
    ("Despensa", "Arroz",            "arroz"),
    ("Despensa", "Aceite",           "aceite"),
    ("Despensa", "Cafe",             "cafe"),
    ("Despensa", "Azucar",           "azucar"),
    ("Despensa", "Fideos",           "fideos"),
    ("Despensa", "Conservas",        "conservas"),
    ("Despensa", "Salsas",           "salsa"),
    ("Despensa", "Condimentos",      "condimento"),
    ("Despensa", "Legumbres",        "legumbres"),
    # Desayuno y snacks
    ("Desayuno y Snacks", "Cereales",   "cereal"),
    ("Desayuno y Snacks", "Galletas",   "galleta"),
    ("Desayuno y Snacks", "Chocolates", "chocolate"),
    ("Desayuno y Snacks", "Snacks",     "snack"),
    ("Desayuno y Snacks", "Mermeladas", "mermelada"),
    # Bebidas
    ("Bebidas", "Bebidas",             "bebida"),
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
    ("Higiene Personal", "Shampoo",       "shampoo"),
    ("Higiene Personal", "Acondicionador","acondicionador"),
    ("Higiene Personal", "Jabon",         "jabon"),
    ("Higiene Personal", "Desodorantes",  "desodorante"),
    ("Higiene Personal", "Cuidado Bucal", "pasta dental"),
    ("Higiene Personal", "Cuidado Facial","crema facial"),
    # Bebé
    ("Bebe", "Panales",                "panales"),
    ("Bebe", "Alimentos Bebe",         "alimento bebe"),
    # Mascotas
    ("Mascotas", "Alimento Perros",    "alimento perro"),
    ("Mascotas", "Alimento Gatos",     "alimento gato"),
]


def crear_driver():
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--window-size=1366,900")
    return webdriver.Chrome(options=options)


def limpiar_precio(texto):
    match = re.search(r"\$[\d.]+", texto)
    return match.group(0) if match else ""


def quitar_precios_referencia(texto):
    texto = texto or ""
    texto = re.sub(
        r"\(\s*\$?\s*[\d.]+\s*(?:/|x)\s*[A-Za-zÁÉÍÓÚáéíóúñÑ0-9.]+\s*\)",
        "",
        texto,
        flags=re.IGNORECASE,
    )
    texto = re.sub(
        r"\$?\s*[\d.]+\s*(?:/|x)\s*[A-Za-zÁÉÍÓÚáéíóúñÑ0-9.]+",
        "",
        texto,
        flags=re.IGNORECASE,
    )
    return texto


def extraer_precios(texto):
    texto = quitar_precios_referencia(texto)
    valores = [
        int(valor.replace(".", ""))
        for valor in re.findall(r"\$\s*([\d.]+)", texto or "")
    ]
    valores = [valor for valor in valores if valor > 0]

    if not valores:
        return "", ""

    precio_actual = min(valores)
    precio_normal = max(valores)

    if precio_normal > precio_actual:
        return precio_normal, precio_actual

    return precio_actual, ""


def extraer_precio_referencia(texto):
    match = re.search(
        r"\$?\s*([\d.]+)\s*(?:/|x)\s*([A-Za-zÁÉÍÓÚáéíóúñÑ0-9.]+)",
        texto or "",
        flags=re.IGNORECASE,
    )
    if match:
        return f"${match.group(1)} / {match.group(2)}"

    for linea in (texto or "").splitlines():
        if "/" in linea and "$" in linea:
            return linea.strip()

    return ""


def obtener_tarjeta(driver, nombre_elemento):
    return driver.execute_script(
        """
        let e = arguments[0];
        while (e && e.tagName !== 'SECTION') {
            e = e.parentElement;
        }
        return e;
        """,
        nombre_elemento
    )


def extraer_producto(driver, nombre_elemento):
    try:
        tarjeta = obtener_tarjeta(driver, nombre_elemento)

        if not tarjeta:
            return None

        nombre = nombre_elemento.text.strip()
        texto = tarjeta.text.strip()
        precio_normal, precio_oferta = extraer_precios(texto)
        precio = precio_oferta or precio_normal or limpiar_precio(texto)

        try:
            link = tarjeta.find_element(By.CSS_SELECTOR, "a[href*='/product/']").get_attribute("href")
        except Exception:
            link = ""

        try:
            imagen_elemento = tarjeta.find_element(By.CSS_SELECTOR, "img")
            imagen = (
                imagen_elemento.get_attribute("src") or
                imagen_elemento.get_attribute("data-src") or
                imagen_elemento.get_attribute("data-nimg")
            )
            if not imagen:
                srcset = imagen_elemento.get_attribute("srcset") or ""
                imagen = srcset.split(",")[0].strip().split(" ")[0] if srcset else ""
        except Exception:
            imagen = ""

        if not nombre or not precio:
            return None

        return {
            "nombre": nombre,
            "precio": precio,
            "precio_normal": precio_normal,
            "precio_oferta": precio_oferta,
            "precio_referencia": extraer_precio_referencia(texto),
            "promocion": "Oferta" if precio_oferta else "",
            "url": link,
            "imagen_url": urljoin("https://www.unimarc.cl", imagen) if imagen else ""
        }
    except StaleElementReferenceException:
        return None


def extraer_producto_por_indice(driver, indice, intentos=3):
    for intento in range(intentos):
        try:
            nombres = driver.find_elements(By.CSS_SELECTOR, ".Shelf_nameProduct__0KIRG")
            if indice >= len(nombres):
                return None

            producto = extraer_producto(driver, nombres[indice])
            if producto:
                return producto
        except StaleElementReferenceException:
            pass

        time.sleep(0.6 + intento * 0.4)

    return None


def scrape_categoria(driver, categoria, subcategoria, termino):
    productos = []

    print(f"Scrapeando Unimarc {subcategoria}...")

    page = 1
    paginas_vacias_consecutivas = 0

    while True:
        url = f"{BASE}?q={quote_plus(termino)}&page={page}"
        driver.get(url)
        time.sleep(5)

        nombres = driver.find_elements(By.CSS_SELECTOR, ".Shelf_nameProduct__0KIRG")
        if not nombres and page == 1:
            time.sleep(4)
            driver.refresh()
            time.sleep(5)
            nombres = driver.find_elements(By.CSS_SELECTOR, ".Shelf_nameProduct__0KIRG")

        if not nombres:
            paginas_vacias_consecutivas += 1
            print(f"{url} -> 0 productos")
            if paginas_vacias_consecutivas >= 2:
                break
            page += 1
            continue

        paginas_vacias_consecutivas = 0
        encontrados_pagina = 0

        for indice in range(len(nombres)):
            producto = extraer_producto_por_indice(driver, indice)

            if not producto:
                continue

            producto["categoria"] = categoria
            producto["subcategoria"] = subcategoria
            productos.append(producto)
            encontrados_pagina += 1

        print(f"{url} -> {encontrados_pagina} productos")

        if encontrados_pagina == 0:
            break

        page += 1

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
            ]
        )
        writer.writeheader()
        writer.writerows(productos)


def main():
    driver = crear_driver()
    productos = []
    vistos = set()

    try:
        for categoria, subcategoria, termino in CATEGORIAS:
            try:
                for producto in scrape_categoria(driver, categoria, subcategoria, termino):
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
                print(f"Error en {subcategoria}: {e}. Continuando...")
    finally:
        driver.quit()

    guardar_productos(productos)
    print(f"{len(productos)} productos Unimarc guardados")


if __name__ == "__main__":
    main()
