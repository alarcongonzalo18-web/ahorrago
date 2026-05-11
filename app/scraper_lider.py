import base64
import csv
import json
import re
import urllib.request
from html import unescape
from pathlib import Path
from urllib.parse import urljoin


OUTPUT = Path("data/lider_real.csv")

CATEGORIAS = [
    ("Lacteos, Huevos y Congelados", "Leche", "https://super.lider.cl/v/leches"),
    ("Lacteos, Huevos y Congelados", "Huevos", "https://super.lider.cl/v/huevos"),
    ("Lacteos, Huevos y Congelados", "Yogurt", "https://super.lider.cl/v/yogurt"),
    ("Lacteos, Huevos y Congelados", "Quesos", "https://super.lider.cl/v/quesos"),
    ("Despensa", "Arroz", "https://super.lider.cl/v/arroz"),
    ("Despensa", "Aceite", "https://super.lider.cl/v/aceites"),
    ("Despensa", "Cafe", "https://super.lider.cl/v/cafe"),
    ("Despensa", "Azucar", "https://super.lider.cl/v/azucar"),
    ("Despensa", "Fideos", "https://super.lider.cl/v/fideos"),
    ("Bebidas", "Bebidas", "https://super.lider.cl/v/bebidas"),
    ("Panaderia", "Pan", "https://super.lider.cl/v/pan"),
    ("Limpieza", "Detergentes", "https://super.lider.cl/v/detergentes"),
    ("Limpieza", "Papel higienico", "https://super.lider.cl/v/papel-higienico"),
]


def descargar_html(url):
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

    with urllib.request.urlopen(request, timeout=30) as response:
        return response.read().decode("utf-8", errors="replace")


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


def decodificar_data_value(valor):
    texto = valor.rstrip(".")
    padding = "=" * ((4 - len(texto) % 4) % 4)

    try:
        return base64.b64decode(texto + padding).decode("utf-8")
    except Exception:
        return ""


def detectar_urls_paginas(html, url_base):
    urls = {url_base}

    for valor in re.findall(r'data-value="([^"]+)"', html):
        ruta = decodificar_data_value(valor)
        if ruta and "pagenumber=" in ruta:
            urls.add(urljoin(url_base, ruta))

    paginas = []
    for pagina_url in urls:
        match = re.search(r"pagenumber=(\d+)", pagina_url)
        pagina = int(match.group(1)) if match else 1
        paginas.append((pagina, pagina_url))

    paginas = [(pagina, pagina_url) for pagina, pagina_url in paginas if pagina == 1 or "pagenumber=" in pagina_url]

    if len(paginas) > 1:
        max_pagina = max(pagina for pagina, _ in paginas)
        plantilla = next((pagina_url for pagina, pagina_url in paginas if pagina > 1), "")

        if plantilla:
            for pagina in range(1, max_pagina + 1):
                if pagina == 1:
                    paginas.append((pagina, url_base))
                else:
                    paginas.append((
                        pagina,
                        re.sub(r"pagenumber=\d+", f"pagenumber={pagina}", plantilla)
                    ))

    paginas_unicas = {}
    for pagina, pagina_url in paginas:
        paginas_unicas[pagina] = pagina_url

    return [pagina_url for _, pagina_url in sorted(paginas_unicas.items())]


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

        productos.append({
            "categoria": categoria,
            "subcategoria": subcategoria,
            "nombre": nombre,
            "precio": precio,
            "precio_normal": precio,
            "precio_oferta": "",
            "precio_referencia": "",
            "promocion": "",
            "url": urljoin(url, link) if link else "",
            "imagen_url": urljoin(url, imagen) if imagen else ""
        })

    return productos


def extraer_productos(categoria, subcategoria, url):
    print(f"Scrapeando Lider {subcategoria}...")
    html = descargar_html(url)
    urls_paginas = detectar_urls_paginas(html, url)
    productos = []

    print(f"{subcategoria}: {len(urls_paginas)} paginas")

    for pagina_url in urls_paginas:
        html_pagina = html if pagina_url == url else descargar_html(pagina_url)
        productos_pagina = extraer_productos_desde_html(
            categoria,
            subcategoria,
            pagina_url,
            html_pagina
        )
        productos.extend(productos_pagina)
        print(f"{pagina_url} -> {len(productos)} acumulados")

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
    productos = []
    vistos = set()

    for categoria, subcategoria, url in CATEGORIAS:
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

    guardar_productos(productos)
    print(f"{len(productos)} productos Lider guardados")


if __name__ == "__main__":
    main()
