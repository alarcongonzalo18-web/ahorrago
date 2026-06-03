from __future__ import annotations

import csv
import unicodedata
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REJECT_LOG = ROOT / "reports" / "pipeline_category_rejections.csv"


@dataclass(frozen=True)
class CategoryValidation:
    accepted: bool
    reason: str = ""
    suggested_category: str = ""
    suggested_subcategory: str = ""
    confidence: str = ""


def normalize(value: str) -> str:
    text = unicodedata.normalize("NFKD", str(value or ""))
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    return " ".join(text.lower().strip().split())


def contains(text: str, keywords: list[str]) -> bool:
    return any(normalize(keyword) in text for keyword in keywords)


BEBIDAS = [
    "bebida", "coca cola", "coca-cola", "pepsi", "sprite", "fanta", "bilz",
    "limon soda", "canada dry", "agua mineral", "agua purificada", "agua saborizada",
    "nectar", "jugo", "kombucha", "red bull", "energetica", "cerveza", "vino",
    "notmilk", "yogu yogu", "milo",
]
SNACKS = ["mani", "castana", "caju", "snack", "papas fritas"]
MASCOTAS = [
    "perro", "perros", "gato", "gatos", "gatito", "cachorro", "master dog",
    "master cat", "champion dog", "champion cat", "pedigree", "pet food",
    "alimento seco", "alimento humedo", "snack perro", "snack gato",
]
HIGIENE = [
    "nivea", "rexona", "dove", "desodorante", "shampoo", "acondicionador",
    "jabon", "pasta dental", "cepillo dental", "micelar", "tonico", "crema facial",
    "limpieza facial", "leche limpiadora",
]
LIMPIEZA = ["detergente", "cloro", "lavavajillas", "limpiador", "suavizante", "desinfectante"]
BEBE_REAL = ["panal", "panales", "toallita bebe", "colado", "picado", "mamadera", "chupete"]

FALSE_MASCOTA_HIGIENE = ["hair food", "aguacate", "original remedies", "cantu", "avena"]
FALSE_BEBIDA_MASCOTA = ["trocitos jugosos", "al jugo", "alimento humedo"]
FALSE_LIMPIEZA = ["pasta limpiadora", "pasta de limpieza", "betun pasta", "pink stuff"]


def suggested_bebida(text: str) -> tuple[str, str]:
    if "agua" in text:
        return "Bebidas", "Aguas"
    if "jugo" in text or "nectar" in text or "kombucha" in text:
        return "Bebidas", "Jugos"
    if "vino" in text:
        return "Bebidas", "Vinos"
    if "cerveza" in text:
        return "Bebidas", "Cervezas"
    if "red bull" in text or "energetica" in text:
        return "Bebidas", "Bebidas Energeticas"
    return "Bebidas", "Bebidas"


def suggested_mascota(text: str) -> tuple[str, str]:
    if "gato" in text or "cat" in text:
        return "Mascotas", "Alimento Gatos"
    return "Mascotas", "Alimento Perros"


def suggested_higiene(text: str) -> tuple[str, str]:
    if "desodorante" in text or "rexona" in text:
        return "Higiene Personal", "Desodorantes"
    if "acondicionador" in text:
        return "Higiene Personal", "Acondicionador"
    if "shampoo" in text:
        return "Higiene Personal", "Shampoo"
    if "pasta dental" in text or "cepillo dental" in text:
        return "Higiene Personal", "Cuidado Bucal"
    if "micelar" in text or "tonico" in text or "facial" in text or "nivea" in text or "dove" in text:
        return "Higiene Personal", "Cuidado Facial"
    return "Higiene Personal", "Jabon"


def validate_category(nombre: str, categoria: str, subcategoria: str = "") -> CategoryValidation:
    text = normalize(nombre)
    cat = str(categoria or "").strip()

    if cat == "Mascotas" and contains(text, FALSE_BEBIDA_MASCOTA):
        return CategoryValidation(True)
    if cat == "Limpieza" and contains(text, FALSE_LIMPIEZA):
        return CategoryValidation(True)
    if contains(text, FALSE_MASCOTA_HIGIENE):
        return CategoryValidation(True)

    if cat == "Bebe" and contains(text, BEBIDAS):
        suggested = suggested_bebida(text)
        return CategoryValidation(False, "bebida_en_bebe", *suggested, "Alta")
    if cat == "Bebe" and contains(text, SNACKS):
        return CategoryValidation(False, "snack_en_bebe", "Desayuno y Snacks", "Snacks", "Alta")
    if cat == "Bebe" and contains(text, LIMPIEZA):
        return CategoryValidation(False, "limpieza_en_bebe", "Limpieza", "Limpiadores", "Alta")

    if cat != "Mascotas" and contains(text, MASCOTAS):
        suggested = suggested_mascota(text)
        return CategoryValidation(False, "mascota_fuera_de_mascotas", *suggested, "Alta")

    if cat not in {"Higiene Personal", "Limpieza", "Mascotas"} and contains(text, HIGIENE):
        suggested = suggested_higiene(text)
        return CategoryValidation(False, "higiene_fuera_de_higiene", *suggested, "Alta")

    if cat not in {"Limpieza", "Higiene Personal"} and contains(text, LIMPIEZA):
        return CategoryValidation(False, "limpieza_fuera_de_limpieza", "Limpieza", "Limpiadores", "Alta")

    if cat not in {"Bebidas", "Bebe"} and contains(text, BEBIDAS):
        suggested = suggested_bebida(text)
        return CategoryValidation(False, "bebida_fuera_de_bebidas", *suggested, "Media")

    return CategoryValidation(True)


def validate_row(row: dict) -> CategoryValidation:
    return validate_category(
        row.get("nombre", ""),
        row.get("categoria", ""),
        row.get("subcategoria", ""),
    )


def log_rejection(
    row: dict,
    validation: CategoryValidation,
    source: str,
    log_path: Path = DEFAULT_REJECT_LOG,
) -> None:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "timestamp",
        "source",
        "nombre",
        "categoria",
        "subcategoria",
        "reason",
        "suggested_category",
        "suggested_subcategory",
        "confidence",
    ]
    exists = log_path.exists()
    with log_path.open("a", newline="", encoding="utf-8-sig") as file:
        writer = csv.DictWriter(file, fieldnames=fields)
        if not exists:
            writer.writeheader()
        writer.writerow({
            "timestamp": datetime.now().isoformat(timespec="seconds"),
            "source": source,
            "nombre": row.get("nombre", ""),
            "categoria": row.get("categoria", ""),
            "subcategoria": row.get("subcategoria", ""),
            "reason": validation.reason,
            "suggested_category": validation.suggested_category,
            "suggested_subcategory": validation.suggested_subcategory,
            "confidence": validation.confidence,
        })


def is_valid_row(row: dict, source: str = "", log_path: Path | None = None) -> bool:
    validation = validate_row(row)
    if validation.accepted:
        return True
    if log_path:
        log_rejection(row, validation, source, log_path)
    return False
