from __future__ import annotations

import csv
from collections import Counter
from pathlib import Path

from sqlalchemy.orm import Session

from app import models
from app.database import SessionLocal
from app.normalizacion import normalizar_texto
from app.scripts.report_pdf import markdown_to_pdf


ROOT = Path(__file__).resolve().parents[2]
REPORTS_DIR = ROOT / "reports"

BEBIDAS = [
    "bebida", "coca cola", "coca-cola", "pepsi", "sprite", "fanta", "bilz",
    "limon soda", "limón soda", "canada dry", "agua mineral", "agua purificada",
    "agua saborizada", "nectar", "néctar", "jugo", "kombucha", "red bull",
    "energetica", "energética", "cerveza", "vino",
]
SNACKS = ["mani", "maní", "castana", "castaña", "caju", "cajú", "snack", "papas fritas"]
LIMPIEZA = ["detergente", "cloro", "lavavajillas", "limpiador", "suavizante", "desinfectante"]
MASCOTAS = [
    "perro", "perros", "gato", "gatos", "gatito", "cachorro", "master dog",
    "master cat", "pet's fun", "pets & friends", "canish", "traper", "buddy pet",
    "alimento seco", "alimento humedo", "alimento húmedo", "snack perro", "snack gato",
]
HIGIENE = [
    "shampoo", "acondicionador", "desodorante", "jabon", "jabón", "pasta dental",
    "cepillo dental", "crema facial", "limpieza facial", "micelar", "tonico", "tónico",
    "leche limpiadora",
]
BEBE_REAL = [
    "pañal", "panal", "toallita humeda", "toallita húmeda", "baby", "bebe", "bebé",
    "formula infantil", "fórmula infantil", "colado", "picado", "mamadera", "chupete",
]

FALSOS_POSITIVOS_MASCOTA = ["aguacate", "hair food", "cantu", "original remedies", "avena"]
FALSOS_POSITIVOS_BEBIDA_MASCOTA = ["trocitos jugosos", "al jugo", "alimento humedo", "alimento húmedo"]
FALSOS_POSITIVOS_LIMPIEZA = ["pasta limpiadora", "pasta de limpieza", "betun pasta", "betún pasta", "pink stuff"]


def _contiene(texto: str, keywords: list[str]) -> bool:
    return any(normalizar_texto(keyword) in texto for keyword in keywords)


def _destino_bebida(texto: str) -> tuple[str, str]:
    if "agua" in texto:
        return "Bebidas", "Aguas"
    if "jugo" in texto or "nectar" in texto or "néctar" in texto or "kombucha" in texto:
        return "Bebidas", "Jugos"
    if "vino" in texto:
        return "Bebidas", "Vinos"
    if "cerveza" in texto:
        return "Bebidas", "Cervezas"
    if "energetica" in texto or "energética" in texto or "red bull" in texto:
        return "Bebidas", "Bebidas Energeticas"
    return "Bebidas", "Bebidas"


def _destino_mascota(texto: str) -> tuple[str, str]:
    if "gato" in texto or "gatito" in texto or "master cat" in texto:
        return "Mascotas", "Alimento Gatos"
    return "Mascotas", "Alimento Perros"


def _destino_despensa(texto: str) -> tuple[str, str]:
    if "fideo" in texto or "pasta" in texto:
        return "Despensa", "Fideos"
    if "arroz" in texto:
        return "Despensa", "Arroz"
    if "salsa" in texto:
        return "Despensa", "Salsas"
    if "aceite" in texto:
        return "Despensa", "Aceite"
    if "cafe" in texto or "café" in texto or "te " in texto or "té " in texto:
        return "Despensa", "Cafe"
    if "conserva" in texto:
        return "Despensa", "Conservas"
    if "legumbre" in texto or "lenteja" in texto or "garbanzo" in texto or "poroto" in texto:
        return "Despensa", "Legumbres"
    return "Despensa", "Condimentos"


def _destino_higiene(texto: str) -> tuple[str, str]:
    if "acondicionador" in texto:
        return "Higiene Personal", "Acondicionador"
    if "shampoo" in texto:
        return "Higiene Personal", "Shampoo"
    if "desodorante" in texto:
        return "Higiene Personal", "Desodorantes"
    if "pasta dental" in texto or "cepillo dental" in texto:
        return "Higiene Personal", "Cuidado Bucal"
    if "facial" in texto or "micelar" in texto or "tonico" in texto or "tónico" in texto or "leche limpiadora" in texto:
        return "Higiene Personal", "Cuidado Facial"
    return "Higiene Personal", "Jabon"


def clasificar_producto(nombre: str, categoria: str, subcategoria: str) -> dict | None:
    texto = normalizar_texto(nombre)
    categoria_actual = categoria or ""

    if _contiene(texto, FALSOS_POSITIVOS_MASCOTA):
        return None
    if categoria_actual == "Mascotas" and _contiene(texto, FALSOS_POSITIVOS_BEBIDA_MASCOTA):
        return None
    if categoria_actual == "Limpieza" and _contiene(texto, FALSOS_POSITIVOS_LIMPIEZA):
        return None

    if categoria_actual == "Bebe" and _contiene(texto, BEBIDAS):
        cat, sub = _destino_bebida(texto)
        return {
            "categoria_sugerida": cat,
            "subcategoria_sugerida": sub,
            "confianza": "Alta",
            "motivo": "Bebida detectada dentro de categoria Bebe",
            "accion_recomendada": "mover_categoria",
        }
    if categoria_actual == "Bebe" and _contiene(texto, SNACKS):
        return {
            "categoria_sugerida": "Desayuno y Snacks",
            "subcategoria_sugerida": "Snacks",
            "confianza": "Alta",
            "motivo": "Snack/fruto seco detectado dentro de categoria Bebe",
            "accion_recomendada": "mover_categoria",
        }
    if categoria_actual == "Bebe" and _contiene(texto, LIMPIEZA):
        return {
            "categoria_sugerida": "Limpieza",
            "subcategoria_sugerida": "Detergentes",
            "confianza": "Media" if "bebe" in texto or "bebé" in texto else "Alta",
            "motivo": "Producto de limpieza detectado dentro de categoria Bebe",
            "accion_recomendada": "revisar_y_mover",
        }

    if categoria_actual != "Mascotas" and _contiene(texto, MASCOTAS):
        cat, sub = _destino_mascota(texto)
        return {
            "categoria_sugerida": cat,
            "subcategoria_sugerida": sub,
            "confianza": "Alta",
            "motivo": "Producto de mascotas fuera de Mascotas",
            "accion_recomendada": "mover_categoria",
        }

    if categoria_actual not in {"Higiene Personal", "Limpieza"} and _contiene(texto, HIGIENE):
        cat, sub = _destino_higiene(texto)
        return {
            "categoria_sugerida": cat,
            "subcategoria_sugerida": sub,
            "confianza": "Alta" if categoria_actual not in {"Limpieza", "Mascotas"} else "Media",
            "motivo": "Producto de higiene personal fuera de Higiene Personal",
            "accion_recomendada": "mover_categoria" if categoria_actual not in {"Limpieza", "Mascotas"} else "revisar_y_mover",
        }

    if categoria_actual not in {"Limpieza", "Higiene Personal"} and _contiene(texto, LIMPIEZA):
        return {
            "categoria_sugerida": "Limpieza",
            "subcategoria_sugerida": "Limpiadores",
            "confianza": "Alta",
            "motivo": "Producto de limpieza fuera de Limpieza",
            "accion_recomendada": "mover_categoria",
        }

    if categoria_actual not in {"Bebidas", "Bebe"} and _contiene(texto, BEBIDAS):
        cat, sub = _destino_bebida(texto)
        return {
            "categoria_sugerida": cat,
            "subcategoria_sugerida": sub,
            "confianza": "Media",
            "motivo": "Bebida fuera de Bebidas",
            "accion_recomendada": "revisar_y_mover",
        }

    return None


def auditar(db: Session) -> list[dict]:
    productos = db.query(models.Producto).outerjoin(models.Categoria).outerjoin(models.Subcategoria).all()
    hallazgos = []
    for producto in productos:
        categoria = producto.categoria.nombre if producto.categoria else ""
        subcategoria = producto.subcategoria.nombre if producto.subcategoria else ""
        clasificacion = clasificar_producto(producto.nombre, categoria, subcategoria)
        if not clasificacion:
            continue
        hallazgos.append({
            "producto_id": producto.id,
            "nombre": producto.nombre,
            "categoria_actual": categoria,
            "subcategoria_actual": subcategoria,
            **clasificacion,
        })
    return hallazgos


def escribir_reportes(hallazgos: list[dict], output_dir: Path = REPORTS_DIR) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    csv_path = output_dir / "fase5f_clasificacion_masiva.csv"
    fields = [
        "producto_id",
        "nombre",
        "categoria_actual",
        "subcategoria_actual",
        "categoria_sugerida",
        "subcategoria_sugerida",
        "confianza",
        "motivo",
        "accion_recomendada",
    ]
    with csv_path.open("w", newline="", encoding="utf-8-sig") as archivo:
        writer = csv.DictWriter(archivo, fieldnames=fields)
        writer.writeheader()
        writer.writerows(hallazgos)

    por_confianza = Counter(item["confianza"] for item in hallazgos)
    por_categoria = Counter(item["categoria_actual"] for item in hallazgos)
    por_motivo = Counter(item["motivo"] for item in hallazgos)
    alta = [item for item in hallazgos if item["confianza"] == "Alta"]

    lines = [
        "# Fase 5F - Clasificacion Masiva de Categorias",
        "",
        "Modo: READ ONLY. No modifica base de datos, producto_base ni categorias.",
        "",
        "## Resumen",
        "",
        f"- Hallazgos totales: {len(hallazgos)}",
        f"- Alta confianza: {por_confianza.get('Alta', 0)}",
        f"- Media confianza: {por_confianza.get('Media', 0)}",
        f"- Baja confianza: {por_confianza.get('Baja', 0)}",
        f"- Falso positivo probable: {por_confianza.get('Falso positivo probable', 0)}",
        "",
        "## Categorias Mas Afectadas",
        "",
    ]
    for categoria, cantidad in por_categoria.most_common(10):
        lines.append(f"- {categoria}: {cantidad}")

    lines.extend(["", "## Motivos Principales", ""])
    for motivo, cantidad in por_motivo.most_common(10):
        lines.append(f"- {motivo}: {cantidad}")

    lines.extend([
        "",
        "## Productos Criticos Alta Confianza",
        "",
        "| ID | Producto | Actual | Sugerida | Motivo |",
        "|---:|---|---|---|---|",
    ])
    for item in alta[:100]:
        nombre = item["nombre"].replace("|", "/")[:140]
        actual = f"{item['categoria_actual']} > {item['subcategoria_actual']}"
        sugerida = f"{item['categoria_sugerida']} > {item['subcategoria_sugerida']}"
        lines.append(f"| {item['producto_id']} | {nombre} | {actual} | {sugerida} | {item['motivo']} |")

    lines.extend([
        "",
        "## Recomendacion Fase 5F-FIX",
        "",
        "- Aplicar solo hallazgos de Alta confianza en una fase separada con backup y rollback especifico.",
        "- Revisar manualmente hallazgos de Media confianza antes de mover datos.",
        "- Mantener sin cambios los falsos positivos probables.",
        "- No recalcular producto_base hasta completar la correccion de categorias.",
        "",
    ])
    md_path = output_dir / "fase5f_clasificacion_masiva.md"
    md_path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    db = SessionLocal()
    try:
        hallazgos = auditar(db)
        escribir_reportes(hallazgos)
    finally:
        db.close()
    print(f"Auditoria masiva Fase 5F completada. Hallazgos: {len(hallazgos)}")
    print(f"Reportes en {REPORTS_DIR}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
