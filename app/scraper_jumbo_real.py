import csv
import math
import re
import time
from pathlib import Path
from urllib.parse import parse_qsl, urlencode, urljoin, urlsplit, urlunsplit

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By


BASE_URL = "https://www.jumbo.cl"
OUTPUT = Path("data/jumbo_real.csv")

CATEGORIAS = [
    {
        "categoria": "Lácteos, Huevos y Congelados",
        "subcategoria": "Leche",
        "path": "/lacteos-huevos-y-congelados/leches"
    },
    {
        "categoria": "Lacteos, Huevos y Congelados",
        "subcategoria": "Huevos",
        "path": "/busqueda?ft=huevos"
    },
    {
        "categoria": "Lacteos, Huevos y Congelados",
        "subcategoria": "Yogurt",
        "path": "/busqueda?ft=yogurt"
    },
    {
        "categoria": "Lacteos, Huevos y Congelados",
        "subcategoria": "Quesos",
        "path": "/busqueda?ft=queso"
    },
    {
        "categoria": "Despensa",
        "subcategoria": "Arroz y Legumbres",
        "path": "/despensa/arroz-quinoa-cuscus"
    },
    {
        "categoria": "Despensa",
        "subcategoria": "Aceites",
        "path": "/despensa/aceites-sal-y-condimentos/aceite"
    },
    {
        "categoria": "Despensa",
        "subcategoria": "Cafe",
        "path": "/busqueda?ft=cafe"
    },
    {
        "categoria": "Despensa",
        "subcategoria": "Azucar",
        "path": "/busqueda?ft=azucar"
    },
    {
        "categoria": "Despensa",
        "subcategoria": "Fideos",
        "path": "/busqueda?ft=fideos"
    },
    {
        "categoria": "Licores, Bebidas y Aguas",
        "subcategoria": "Bebidas",
        "path": "/licores-bebidas-y-aguas/bebidas-gaseosas"
    },
    {
        "categoria": "Panaderia",
        "subcategoria": "Pan",
        "path": "/busqueda?ft=pan"
    },
    {
        "categoria": "Limpieza",
        "subcategoria": "Detergentes",
        "path": "/busqueda?ft=detergentes"
    },
    {
        "categoria": "Limpieza",
        "subcategoria": "Papel higienico",
        "path": "/busqueda?ft=papel%20higienico"
    },
]


def crear_driver():
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--window-size=1366,768")
    return webdriver.Chrome(options=options)


def url_con_pagina(url, pagina):
    partes = urlsplit(url)
    query = dict(parse_qsl(partes.query))
    query["page"] = str(pagina)
    return urlunsplit((
        partes.scheme,
        partes.netloc,
        partes.path,
        urlencode(query),
        partes.fragment
    ))


def numero_pagina(url):
    match = re.search(r"page=(\d+)", url)
    return int(match.group(1)) if match else 1


def detectar_urls_paginas(driver):
    urls = []

    for link in driver.find_elements(By.CSS_SELECTOR, ".select-page-dropdown-content a[href*='page=']"):
        href = link.get_attribute("href")
        if href:
            urls.append(href)

    if urls:
        return sorted(set(urls), key=numero_pagina)

    texto_pagina = driver.find_element(By.TAG_NAME, "body").text
    match = re.search(r"P.gina\s+1\s+de\s+(\d+)", texto_pagina)

    if match:
        total_paginas = int(match.group(1))
        return [url_con_pagina(driver.current_url, pagina) for pagina in range(1, total_paginas + 1)]

    match = re.search(r"(\d+)\s+productos", texto_pagina)

    if not match:
        return [driver.current_url]

    total_productos = int(match.group(1))
    total_paginas = max(1, math.ceil(total_productos / 40))
    return [url_con_pagina(driver.current_url, pagina) for pagina in range(1, total_paginas + 1)]


def obtener_url_producto(item):
    try:
        link = item.find_element(By.CSS_SELECTOR, "a[href*='/p']")
        href = link.get_attribute("href")
        return urljoin(BASE_URL, href) if href else ""
    except Exception:
        return ""


def obtener_imagen_producto(item):
    try:
        imagen = item.find_element(By.CSS_SELECTOR, "img")
        src = (
            imagen.get_attribute("src") or
            imagen.get_attribute("data-src") or
            imagen.get_attribute("data-lazy-src")
        )
        if src:
            return urljoin(BASE_URL, src)

        srcset = imagen.get_attribute("srcset") or ""
        if srcset:
            primera = srcset.split(",")[0].strip().split(" ")[0]
            return urljoin(BASE_URL, primera)
    except Exception:
        return ""

    return ""


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


def extraer_precios_desde_texto(texto, precio_respaldo):
    texto = quitar_precios_referencia(texto)
    valores = [
        int(valor.replace(".", ""))
        for valor in re.findall(r"\$\s*([\d.]+)", texto or "")
    ]
    valores = [valor for valor in valores if valor > 0]

    if not valores:
        precio = int(float(precio_respaldo))
        return precio, ""

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


def recolectar_productos(driver, productos, vistos, categoria, subcategoria):
    items = driver.find_elements(By.CSS_SELECTOR, ".shelf-content [data-cnstrc-item-name][data-cnstrc-item-price]")

    for item in items:
        try:
            nombre = item.get_attribute("data-cnstrc-item-name")
            precio = item.get_attribute("data-cnstrc-item-price")
            url = obtener_url_producto(item)
            imagen = obtener_imagen_producto(item)
            texto = item.text
            precio_normal, precio_oferta = extraer_precios_desde_texto(texto, precio)
            precio_referencia = extraer_precio_referencia(texto)

            if not nombre or not precio:
                continue

            key = (categoria, subcategoria, nombre, precio, url)
            if key in vistos:
                continue

            vistos.add(key)
            productos.append({
                "categoria": categoria,
                "subcategoria": subcategoria,
                "nombre": nombre,
                "precio": precio_oferta or precio_normal,
                "precio_normal": precio_normal,
                "precio_oferta": precio_oferta,
                "precio_referencia": precio_referencia,
                "promocion": "Oferta" if precio_oferta else "",
                "url": url,
                "imagen_url": imagen
            })
        except Exception:
            continue


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
        for bloque in CATEGORIAS:
            categoria = bloque["categoria"]
            subcategoria = bloque["subcategoria"]
            url_categoria = urljoin(BASE_URL, bloque["path"])

            driver.get(url_categoria)
            time.sleep(5)
            urls_paginas = detectar_urls_paginas(driver)

            print(f"{subcategoria}: {len(urls_paginas)} paginas")

            for pagina_url in urls_paginas:
                driver.get(pagina_url)
                time.sleep(4)
                recolectar_productos(
                    driver,
                    productos,
                    vistos,
                    categoria,
                    subcategoria
                )
                print(f"{pagina_url} -> {len(productos)} acumulados")
    finally:
        driver.quit()

    guardar_productos(productos)
    print(f"{len(productos)} productos guardados")


if __name__ == "__main__":
    main()
