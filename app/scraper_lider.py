import csv
import json
import re
import urllib.request
from html import unescape
from pathlib import Path


OUTPUT = Path("data/lider_real.csv")

CATEGORIAS = [
    ("Lácteos, Huevos y Congelados", "Leche", "https://super.lider.cl/v/leches"),
    ("Despensa", "Arroz", "https://super.lider.cl/v/arroz"),
    ("Despensa", "Aceite", "https://super.lider.cl/v/aceites"),
    ("Bebidas", "Bebidas", "https://super.lider.cl/v/bebidas"),
    ("Limpieza", "Detergentes", "https://super.lider.cl/v/detergentes"),
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
        data = json.loads(unescape(script.strip()))

        if isinstance(data, dict) and data.get("@type") == "ItemList":
            return data.get("itemListElement", [])

    return []


def extraer_productos(categoria, subcategoria, url):
    print(f"Scrapeando Líder {subcategoria}...")
    html = descargar_html(url)
    productos = []

    for item_lista in extraer_json_ld(html):
        item = item_lista.get("item", {})
        oferta = item.get("offers", {})
        nombre = item.get("name")
        precio = oferta.get("price")
        link = item.get("url")

        if not nombre or not precio:
            continue

        productos.append({
            "categoria": categoria,
            "subcategoria": subcategoria,
            "nombre": nombre,
            "precio": precio,
            "url": link or url
        })

    print(f"{subcategoria}: {len(productos)} productos")
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
    productos = []
    vistos = set()

    for categoria, subcategoria, url in CATEGORIAS:
        for producto in extraer_productos(categoria, subcategoria, url):
            key = (producto["categoria"], producto["subcategoria"], producto["nombre"], producto["precio"])
            if key in vistos:
                continue

            vistos.add(key)
            productos.append(producto)

    guardar_productos(productos)
    print(f"{len(productos)} productos Líder guardados")


if __name__ == "__main__":
    main()
