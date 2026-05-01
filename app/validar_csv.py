import csv
from pathlib import Path


CSV_PATH = Path("data/productos_supermercados.csv")

COLUMNAS_REQUERIDAS = [
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


def validar_csv():
    if not CSV_PATH.exists():
        print("No existe el archivo:", CSV_PATH)
        return

    errores = []

    with open(CSV_PATH, newline="", encoding="utf-8-sig") as archivo:
        lector = csv.DictReader(archivo)

        columnas = lector.fieldnames

        for columna in COLUMNAS_REQUERIDAS:
            if columna not in columnas:
                errores.append(f"Falta columna: {columna}")

        for numero_fila, fila in enumerate(lector, start=2):
            if not fila["categoria"]:
                errores.append(f"Fila {numero_fila}: falta categoria")

            if not fila["subcategoria"]:
                errores.append(f"Fila {numero_fila}: falta subcategoria")

            if not fila["nombre"]:
                errores.append(f"Fila {numero_fila}: falta nombre")

            if not fila["precio"]:
                errores.append(f"Fila {numero_fila}: falta precio")

            try:
                float(fila["precio"])
            except Exception:
                errores.append(f"Fila {numero_fila}: precio invalido")

            if not fila["supermercado"]:
                errores.append(f"Fila {numero_fila}: falta supermercado")

    if errores:
        print("Errores encontrados:")
        for error in errores:
            print("-", error)
    else:
        print("CSV valido. Puedes importar productos.")


if __name__ == "__main__":
    validar_csv()
