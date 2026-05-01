import csv
from pathlib import Path


OUTPUT = Path("data/productos_supermercados.csv")

categorias = [
    ("Lácteos, Huevos y Congelados", "Leche"),
    ("Despensa", "Arroz"),
    ("Despensa", "Fideos"),
    ("Licores, Bebidas y Aguas", "Bebidas"),
]

marcas = {
    "Leche": ["Colun", "Soprole", "Loncoleche"],
    "Arroz": ["Tucapel", "Miraflores"],
    "Fideos": ["Carozzi", "Lucchetti"],
    "Bebidas": ["Coca-Cola", "Pepsi"],
}

tipos = {
    "Leche": ["entera", "semidescremada", "sin lactosa"],
    "Arroz": ["grado 1", "integral"],
    "Fideos": ["espagueti", "tallarines"],
    "Bebidas": ["normal", "zero"],
}

formatos = {
    "Leche": ["1 L"],
    "Arroz": ["1 kg"],
    "Fideos": ["400 g"],
    "Bebidas": ["1.5 L"],
}

supermercados = [
    ("Jumbo", 1.0),
    ("Líder", 0.9),
    ("Unimarc", 1.1),
]

dominios = {
    "Jumbo": "jumbo",
    "Líder": "lider",
    "Unimarc": "unimarc",
}


def generar():
    filas = []

    for categoria, subcategoria in categorias:
        for marca in marcas[subcategoria]:
            for tipo in tipos[subcategoria]:
                for formato in formatos[subcategoria]:
                    nombre = f"{subcategoria} {marca} {tipo} {formato}"

                    for supermercado, factor in supermercados:
                        precio_base = 1000
                        precio = int(precio_base * factor)
                        query = nombre.replace(" ", "%20")
                        dominio = dominios[supermercado]
                        url = f"https://www.{dominio}.cl/search?q={query}"

                        filas.append({
                            "categoria": categoria,
                            "subcategoria": subcategoria,
                            "nombre": nombre,
                            "marca": marca,
                            "tipo": tipo,
                            "formato": formato,
                            "precio": precio,
                            "supermercado": supermercado,
                            "url": url,
                            "producto_base": ""
                        })

    with open(OUTPUT, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=filas[0].keys())
        writer.writeheader()
        writer.writerows(filas)

    print(f"Generados {len(filas)} productos")


if __name__ == "__main__":
    generar()
