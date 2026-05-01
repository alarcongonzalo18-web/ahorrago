import csv
import re
import time
from pathlib import Path
from urllib.parse import quote_plus

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By


BASE = "https://www.unimarc.cl/search"
OUTPUT = Path("data/unimarc_real.csv")

CATEGORIAS = [
    ("Lácteos, Huevos y Congelados", "Leche", "leche", 5),
    ("Despensa", "Arroz", "arroz", 3),
    ("Despensa", "Aceite", "aceite", 3),
    ("Bebidas", "Bebidas", "bebida", 5),
    ("Limpieza", "Detergentes", "detergente", 3),
]


def crear_driver():
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--window-size=1366,900")
    return webdriver.Chrome(options=options)


def limpiar_precio(texto):
    match = re.search(r"\$[\d.]+", texto)
    return match.group(0) if match else ""


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
    tarjeta = obtener_tarjeta(driver, nombre_elemento)

    if not tarjeta:
        return None

    nombre = nombre_elemento.text.strip()
    texto = tarjeta.text.strip()
    precio = limpiar_precio(texto)

    try:
        link = tarjeta.find_element(By.CSS_SELECTOR, "a[href*='/product/']").get_attribute("href")
    except Exception:
        link = ""

    if not nombre or not precio:
        return None

    return {
        "nombre": nombre,
        "precio": precio,
        "url": link
    }


def scrape_categoria(driver, categoria, subcategoria, termino, max_paginas):
    productos = []

    print(f"Scrapeando Unimarc {subcategoria}...")

    for page in range(1, max_paginas + 1):
        url = f"{BASE}?q={quote_plus(termino)}&page={page}"
        driver.get(url)
        time.sleep(5)

        nombres = driver.find_elements(By.CSS_SELECTOR, ".Shelf_nameProduct__0KIRG")

        if not nombres:
            print(f"{url} -> 0 productos")
            break

        encontrados_pagina = 0
        for nombre_elemento in nombres:
            producto = extraer_producto(driver, nombre_elemento)

            if not producto:
                continue

            producto["categoria"] = categoria
            producto["subcategoria"] = subcategoria
            productos.append(producto)
            encontrados_pagina += 1

        print(f"{url} -> {encontrados_pagina} productos")

    return productos


def guardar_productos(productos):
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)

    with open(OUTPUT, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["categoria", "subcategoria", "nombre", "precio", "url"]
        )
        writer.writeheader()
        writer.writerows(productos)


def main():
    driver = crear_driver()
    productos = []
    vistos = set()

    try:
        for categoria, subcategoria, termino, max_paginas in CATEGORIAS:
            for producto in scrape_categoria(driver, categoria, subcategoria, termino, max_paginas):
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
    finally:
        driver.quit()

    guardar_productos(productos)
    print(f"{len(productos)} productos Unimarc guardados")


if __name__ == "__main__":
    main()
