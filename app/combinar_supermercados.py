import csv
import re
from pathlib import Path

from app import ean_cache
from app.category_validator import is_valid_row
from app.ean_fetch import slug_jumbo, slug_tottus, slug_unimarc
from app.url_utils import extraer_ean_lider


OUTPUT = Path("data/productos_supermercados.csv")

# Cadenas cuyo EAN vive en la cache (poblada por app.backfill_ean). Lider no
# esta aca porque su EAN se reconstruye de la URL, sin consultar nada.
SLUG_POR_CADENA = {
    "Jumbo": slug_jumbo,
    "Unimarc": slug_unimarc,
    "Tottus": slug_tottus,
}

# Lider tiene DOS fuentes que se complementan y se fusionan por EAN en combinar():
# el SPA /browse cubre mejor higiene, limpieza, mascotas y bebe; el endpoint viejo
# /v/ cubre mejor los alimentos. Juntas dan 13.481 productos contra los 8.646 del
# viejo solo, todos con EAN. El /browse va primero: cuando un producto esta en las
# dos, gana su version (categoria real del sitio y precio del SPA).
FUENTES = [
    ("data/lider_browse.csv", "Líder"),
    ("data/lider_real.csv", "Líder"),
    ("data/jumbo_real.csv", "Jumbo"),
    ("data/unimarc_real.csv", "Unimarc"),
    ("data/tottus_real.csv", "Tottus"),
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


def leer_filas(path, supermercado, cache=None):
    if not path.exists():
        print(f"No existe {path}, se omite.")
        return []

    cache = cache if cache is not None else {}
    filas = []

    with open(path, newline="", encoding="utf-8-sig") as archivo:
        lector = csv.DictReader(archivo)

        for fila in lector:
            nombre = (fila.get("nombre") or "").strip()
            if not nombre:
                continue
            fila_normalizada = {
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
                "ean": (fila.get("ean") or "").strip(),
            }
            if not fila_normalizada["ean"]:
                if supermercado == "Líder":
                    # retroactivo: las URLs de Lider traen el GTIN aunque el CSV
                    # crudo venga de una corrida anterior sin columna ean
                    fila_normalizada["ean"] = extraer_ean_lider(fila_normalizada["url"])
                elif supermercado in SLUG_POR_CADENA:
                    # Jumbo/Unimarc: el EAN sale de la cache (app.backfill_ean),
                    # que sobrevive a los re-scrapes que reescriben el CSV.
                    slug = SLUG_POR_CADENA[supermercado](fila_normalizada["url"])
                    if slug:
                        fila_normalizada["ean"] = ean_cache.obtener(cache, supermercado, slug)
            if not is_valid_row(fila_normalizada, f"combinar_supermercados:{supermercado}", Path("reports") / "pipeline_category_rejections.csv"):
                continue
            filas.append(fila_normalizada)

    return filas


def combinar():
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    filas = []
    vistos = set()
    cache = ean_cache.cargar()

    # Lider llega por dos fuentes complementarias (ver FUENTES). El mismo producto
    # puede venir en ambas, asi que dentro de una cadena el EAN manda: es identidad
    # exacta, mientras que (nombre, precio) cambia entre endpoints. Sin esto, los
    # ~7.000 productos que traen las dos fuentes entrarian duplicados.
    por_ean = set()

    for archivo, supermercado in FUENTES:
        for fila in leer_filas(Path(archivo), supermercado, cache):
            ean = (fila.get("ean") or "").strip()
            if ean:
                clave_ean = (fila["supermercado"], ean)
                if clave_ean in por_ean:
                    continue
                por_ean.add(clave_ean)

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
        "ean",
    ]

    with open(OUTPUT, "w", newline="", encoding="utf-8-sig") as salida:
        writer = csv.DictWriter(salida, fieldnames=columnas)
        writer.writeheader()
        writer.writerows(filas)

    con_ean = sum(1 for f in filas if f["ean"])
    print(f"CSV combinado actualizado: {len(filas)} productos ({con_ean} con EAN)")


if __name__ == "__main__":
    combinar()
