from __future__ import annotations

import csv
from collections import Counter
from pathlib import Path

from sqlalchemy.orm import Session

from app import models
from app.database import SessionLocal
from app.normalizacion import normalizar_texto


ROOT = Path(__file__).resolve().parents[2]
REPORTS_DIR = ROOT / "reports"

RULES = [
    ("alimento_en_limpieza", "Limpieza", ["fideo", "pasta", "arroz", "galleta", "salsa", "sopa", "leche", "yogurt"]),
    ("bebida_en_mascotas", "Mascotas", ["bebida", "jugo", "agua mineral", "cerveza", "vino"]),
    ("panal_en_bebidas", "Bebidas", ["panal", "pañal", "toallita bebe"]),
    ("mascota_en_higiene", "Higiene Personal", ["perro", "gato", "dog", "master dog", "master cat"]),
    ("limpieza_en_despensa", "Despensa", ["detergente", "cloro", "lavavajillas", "suavizante", "limpiador"]),
]

PASTA_LIMPIEZA = [
    "pasta limpiadora",
    "pasta de limpieza",
    "pink stuff",
    "fibro glow",
    "betun pasta",
    "betún pasta",
    "pasta calzado",
]
LECHE_COSMETICA = [
    "leche limpiadora",
    "facial",
    "micelar",
    "tonico",
    "tónico",
    "crema",
    "nivea",
    "petrizzio",
    "la roche posay",
]
MASCOTA_HUMEDO = ["alimento humedo", "alimento húmedo", "trocitos jugosos", "al jugo", "jugosos"]
HUMANO_HAIR_FALSE_POSITIVE = ["aguacate", "hair food", "cantu", "original remedies", "avena"]


def _contiene(texto: str, keywords: list[str]) -> bool:
    return any(normalizar_texto(keyword) in texto for keyword in keywords)


def _es_falso_positivo(regla: str, texto: str) -> bool:
    if regla == "alimento_en_limpieza":
        if _contiene(texto, PASTA_LIMPIEZA):
            return True
        if "leche" in texto and _contiene(texto, LECHE_COSMETICA):
            return False
    if regla == "bebida_en_mascotas" and _contiene(texto, MASCOTA_HUMEDO):
        return True
    if regla == "mascota_en_higiene" and _contiene(texto, HUMANO_HAIR_FALSE_POSITIVE):
        return True
    return False


def auditar_categorias(db: Session) -> list[dict]:
    rows = db.query(models.Producto).outerjoin(models.Categoria).outerjoin(models.Subcategoria).all()
    hallazgos = []
    for producto in rows:
        categoria = producto.categoria.nombre if producto.categoria else ""
        subcategoria = producto.subcategoria.nombre if producto.subcategoria else ""
        texto = normalizar_texto(producto.nombre)
        for regla, categoria_objetivo, keywords in RULES:
            if categoria != categoria_objetivo:
                continue
            if any(normalizar_texto(keyword) in texto for keyword in keywords):
                if _es_falso_positivo(regla, texto):
                    continue
                if "pasta dental" in texto and regla == "alimento_en_limpieza":
                    continue
                hallazgos.append({
                    "producto_id": producto.id,
                    "producto_nombre": producto.nombre,
                    "categoria": categoria,
                    "subcategoria": subcategoria,
                    "producto_base": producto.producto_base or "",
                    "regla": regla,
                    "detalle": f"Keyword incompatible en categoria {categoria}",
                })
    return hallazgos


def escribir_reportes(hallazgos: list[dict], output_dir: Path = REPORTS_DIR) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    csv_path = output_dir / "auditoria_categorias.csv"
    campos = ["producto_id", "producto_nombre", "categoria", "subcategoria", "producto_base", "regla", "detalle"]
    with csv_path.open("w", newline="", encoding="utf-8-sig") as archivo:
        writer = csv.DictWriter(archivo, fieldnames=campos)
        writer.writeheader()
        writer.writerows(hallazgos)

    conteo = Counter(item["regla"] for item in hallazgos)
    lines = [
        "# Auditoria de Categorias - AhorraGo",
        "",
        "Auditoria read-only. No modifica datos.",
        "",
        "## Resumen",
        "",
        f"- Hallazgos totales: {len(hallazgos)}",
    ]
    for regla, cantidad in conteo.most_common():
        lines.append(f"- {regla}: {cantidad}")
    lines.extend([
        "",
        "## Archivos",
        "",
        "- reports/auditoria_categorias.csv",
        "- reports/auditoria_categorias.md",
        "",
        "## Nota",
        "",
        "Los hallazgos son candidatos para revision manual; esta auditoria no aplica correcciones automaticas.",
        "",
    ])
    (output_dir / "auditoria_categorias.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    db = SessionLocal()
    try:
        hallazgos = auditar_categorias(db)
        escribir_reportes(hallazgos)
    finally:
        db.close()
    print(f"Auditoria de categorias completada. Hallazgos: {len(hallazgos)}")
    print(f"Reportes en {REPORTS_DIR}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
