import csv
import re
from pathlib import Path


INPUT = Path("data/jumbo_real.csv")
OUTPUT = Path("data/productos_supermercados.csv")


def limpiar_precio(precio):
    numeros = re.sub(r"[^0-9]", "", precio)
    return numeros if numeros else "0"


def detectar_formato(nombre):
    patrones = [
        r"\d+(\.\d+)?\s?L",
        r"\d+(\.\d+)?\s?l",
        r"\d+(\.\d+)?\s?ml",
        r"\d+(\.\d+)?\s?kg",
        r"\d+(\.\d+)?\s?g",
        r"\d+\s?unidades",
        r"\d+\s?un",
    ]

    for patron in patrones:
        match = re.search(patron, nombre, re.IGNORECASE)
        if match:
            return match.group(0).replace("l", "L")

    return ""


def detectar_marca(nombre):
    marcas = [
        "Colun", "Soprole", "Loncoleche", "Surlat",
        "Nestlé", "Quillayes", "Cuisine & Co",
        "Jumbo", "Lider", "Tucapel", "Carozzi",
        "Lucchetti", "Coca-Cola", "Pepsi", "Watts",
        "Nutren", "Nido", "Danone", "Milo", "Nesquik",
        "Svelty", "Ecoterra", "Edra", "Calo", "Cola Cao",
        "Ensure", "Glucerna", "Copacabana", "San Ignacio"
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
        "normal"
    ]

    for tipo in tipos:
        if tipo in texto:
            return tipo

    return "general"


def convertir():
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
            url = fila.get("url") or "https://www.jumbo.cl/search?ft=" + nombre.replace(" ", "%20")

            writer.writerow({
                "categoria": fila.get("categoria") or "Lácteos, Huevos y Congelados",
                "subcategoria": fila.get("subcategoria") or "Leche",
                "nombre": nombre,
                "marca": detectar_marca(nombre),
                "tipo": detectar_tipo(nombre),
                "formato": detectar_formato(nombre),
                "precio": precio,
                "supermercado": "Jumbo",
                "url": url,
                "producto_base": ""
            })

    print("CSV de Jumbo convertido correctamente.")


if __name__ == "__main__":
    convertir()
