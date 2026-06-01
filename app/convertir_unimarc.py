import csv
import re
from pathlib import Path

try:
    from .url_utils import generar_url_busqueda
except ImportError:
    from url_utils import generar_url_busqueda


INPUT = Path("data/unimarc_real.csv")
OUTPUT = Path("data/productos_supermercados.csv")


def limpiar_precio(precio):
    numeros = re.sub(r"[^0-9]", "", precio)
    return numeros if numeros else "0"


def detectar_formato(nombre):
    patrones = [
        r"\d+(\.\d+)?\s?L",
        r"\d+(\.\d+)?\s?l",
        r"\d+(\.\d+)?\s?lt",
        r"\d+(\.\d+)?\s?litro",
        r"\d+(\.\d+)?\s?ml",
        r"\d+(\.\d+)?\s?cc",
        r"\d+(\.\d+)?\s?kg",
        r"\d+(\.\d+)?\s?g",
        r"\d+\s?unidades",
        r"\d+\s?un",
    ]

    for patron in patrones:
        match = re.search(patron, nombre, re.IGNORECASE)
        if match:
            return (
                match.group(0)
                .replace("lt", "L")
                .replace("l", "L")
                .replace("litro", "L")
            )

    return ""


def detectar_marca(nombre):
    marcas = [
        "Colun", "Soprole", "Loncoleche", "Lonco Leche", "Surlat",
        "Nestlé", "Quillayes", "Cuisine & Co", "Unimarc",
        "Nuestra Cocina", "Merkat", "Tucapel", "Miraflores",
        "Carozzi", "Lucchetti", "Coca Cola", "Coca-Cola",
        "Pepsi", "Watts", "Omo", "Ariel", "Drive",
        "Smart Clean", "Bio Frescura", "Nido", "Danone",
        "Milo", "Nesquik", "Svelty", "Calo", "Cola Cao"
    ]

    for marca in marcas:
        if marca.lower() in nombre.lower():
            return marca

    return "Sin marca"


def detectar_tipo(nombre):
    texto = nombre.lower()

    tipos = [
        "sin lactosa",
        "semidescremada",
        "descremada",
        "entera",
        "proteína",
        "light",
        "zero",
        "normal",
        "líquido",
        "liquido",
        "polvo"
    ]

    for tipo in tipos:
        if tipo in texto:
            return tipo

    return "general"


def convertir():
    if not INPUT.exists():
        print("No existe el archivo:", INPUT)
        return

    with open(INPUT, newline="", encoding="utf-8-sig") as entrada, \
         open(OUTPUT, "w", newline="", encoding="utf-8-sig") as salida:

        lector = csv.DictReader(entrada)

        columnas = [
            "categoria",
            "subcategoria",
            "nombre",
            "marca",
            "tipo",
            "formato",
            "precio",
            "supermercado",
            "url",
            "producto_base"
        ]

        writer = csv.DictWriter(salida, fieldnames=columnas)
        writer.writeheader()

        for fila in lector:
            nombre = fila["nombre"]
            precio = limpiar_precio(fila["precio"])
            url = fila.get("url") or generar_url_busqueda(
                "https://www.unimarc.cl/search",
                "q",
                nombre
            )

            writer.writerow({
                "categoria": fila.get("categoria") or "",
                "subcategoria": fila.get("subcategoria") or "",
                "nombre": nombre,
                "marca": detectar_marca(nombre),
                "tipo": detectar_tipo(nombre),
                "formato": detectar_formato(nombre),
                "precio": precio,
                "supermercado": "Unimarc",
                "url": url,
                "producto_base": ""
            })

    print("CSV de Unimarc convertido correctamente.")


if __name__ == "__main__":
    convertir()
