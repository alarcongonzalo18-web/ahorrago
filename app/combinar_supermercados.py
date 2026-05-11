import csv
import re
from pathlib import Path


OUTPUT = Path("data/productos_supermercados.csv")

FUENTES = [
    ("data/lider_real.csv", "Líder"),
    ("data/jumbo_real.csv", "Jumbo"),
    ("data/unimarc_real.csv", "Unimarc"),
]

MARCAS = [
    "Colun", "Soprole", "Loncoleche", "Lonco Leche", "Surlat",
    "Nestle", "Nestlé", "Quillayes", "Cuisine & Co", "Jumbo",
    "Lider", "Líder", "Unimarc", "Nuestra Cocina", "Merkat",
    "Tucapel", "Miraflores", "Carozzi", "Lucchetti", "Coca Cola",
    "Coca-Cola", "Pepsi", "Watts", "Omo", "Ariel", "Drive",
    "Smart Clean", "Bio Frescura", "Nido", "Danone", "Milo",
    "Nesquik", "Svelty", "Ecoterra", "Edra", "Calo", "Cola Cao",
    "Ensure", "Glucerna", "Copacabana", "San Ignacio",
]

TIPOS = [
    "sin lactosa",
    "semidescremada",
    "descremada",
    "entera",
    "proteina",
    "proteína",
    "light",
    "zero",
    "normal",
    "liquido",
    "líquido",
    "polvo",
]


def limpiar_precio(precio):
    numeros = re.sub(r"[^0-9]", "", str(precio or ""))
    return numeros if numeros else "0"


def limpiar_precio_opcional(precio):
    numeros = re.sub(r"[^0-9]", "", str(precio or ""))
    return numeros if numeros else ""


def detectar_formato(nombre):
    patrones = [
        r"\d+(?:[.,]\d+)?\s?L\b",
        r"\d+(?:[.,]\d+)?\s?l\b",
        r"\d+(?:[.,]\d+)?\s?lt\b",
        r"\d+(?:[.,]\d+)?\s?litro\b",
        r"\d+(?:[.,]\d+)?\s?ml\b",
        r"\d+(?:[.,]\d+)?\s?cc\b",
        r"\d+(?:[.,]\d+)?\s?kg\b",
        r"\d+(?:[.,]\d+)?\s?g\b",
        r"\d+\s?unidades\b",
        r"\d+\s?un\b",
    ]

    for patron in patrones:
        match = re.search(patron, nombre, re.IGNORECASE)
        if match:
            return (
                match.group(0)
                .replace(",", ".")
                .replace("lt", "L")
                .replace("l", "L")
                .replace("litro", "L")
            )

    return ""


def detectar_marca(nombre):
    nombre_lower = nombre.lower()

    for marca in MARCAS:
        if marca.lower() in nombre_lower:
            return marca

    return "Sin marca"


def detectar_tipo(nombre):
    nombre_lower = nombre.lower()

    for tipo in TIPOS:
        if tipo in nombre_lower:
            return tipo

    return "general"


def leer_filas(path, supermercado):
    if not path.exists():
        print(f"No existe {path}, se omite.")
        return []

    filas = []

    with open(path, newline="", encoding="utf-8-sig") as archivo:
        lector = csv.DictReader(archivo)

        for fila in lector:
            nombre = (fila.get("nombre") or "").strip()
            if not nombre:
                continue

            filas.append({
                "categoria": (fila.get("categoria") or "").strip(),
                "subcategoria": (fila.get("subcategoria") or "").strip(),
                "nombre": nombre,
                "marca": detectar_marca(nombre),
                "tipo": detectar_tipo(nombre),
                "formato": detectar_formato(nombre),
                "precio": limpiar_precio(fila.get("precio_oferta") or fila.get("precio")),
                "precio_normal": limpiar_precio(fila.get("precio_normal") or fila.get("precio")),
                "precio_oferta": limpiar_precio_opcional(fila.get("precio_oferta")),
                "precio_referencia": (fila.get("precio_referencia") or "").strip(),
                "promocion": (fila.get("promocion") or "").strip(),
                "supermercado": supermercado,
                "url": (fila.get("url") or "").strip(),
                "imagen_url": (fila.get("imagen_url") or "").strip(),
                "producto_base": "",
            })

    return filas


def combinar():
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    filas = []
    vistos = set()

    for archivo, supermercado in FUENTES:
        for fila in leer_filas(Path(archivo), supermercado):
            key = (
                fila["supermercado"],
                fila["categoria"],
                fila["subcategoria"],
                fila["nombre"],
                fila["precio"],
            )

            if key in vistos:
                continue

            vistos.add(key)
            filas.append(fila)

    columnas = [
        "categoria",
        "subcategoria",
        "nombre",
        "marca",
        "tipo",
        "formato",
        "precio",
        "precio_normal",
        "precio_oferta",
        "precio_referencia",
        "promocion",
        "supermercado",
        "url",
        "imagen_url",
        "producto_base",
    ]

    with open(OUTPUT, "w", newline="", encoding="utf-8-sig") as salida:
        writer = csv.DictWriter(salida, fieldnames=columnas)
        writer.writeheader()
        writer.writerows(filas)

    print(f"CSV combinado actualizado: {len(filas)} productos")


if __name__ == "__main__":
    combinar()
