"""category_validator.py - v2 (Fase 5J-R hardening fix)

Cambios vs v1:
- Coincidencia por PALABRA COMPLETA (regex \\b) en vez de substring crudo.
  Elimina falsos positivos tipo "jugoso"->jugo, "cajun"->caju, "manilla"->mani.
- Comparacion de categoria INSENSIBLE A ACENTOS ("Lacteos" == "Lácteos").
- Exclusiones explicitas para la regla de bebidas (vinagre, "en vino",
  bebida lactea, saborizante, polvo) -> condimentos y lacteos no se mandan a Bebidas.
- POLITICA DE CUARENTENA: confianza Alta => se rechaza (se quita del load);
  confianza Media => se CONSERVA y se registra para revision humana. Nunca se
  pierde un producto por un match de confianza media.
"""
from __future__ import annotations

import csv
import re
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


def _compile(keywords: list[str]) -> re.Pattern:
    # Devuelve un patron que matchea cualquier keyword como palabra completa.
    alts = sorted((re.escape(normalize(k)) for k in keywords), key=len, reverse=True)
    return re.compile(r"\b(?:" + "|".join(alts) + r")\b")


def hit(pattern: re.Pattern, text: str) -> bool:
    return bool(pattern.search(text))


BEBIDAS = _compile([
    "bebida", "coca cola", "pepsi", "sprite", "fanta", "bilz",
    "limon soda", "canada dry", "agua mineral", "agua purificada", "agua saborizada",
    "nectar", "jugo", "kombucha", "red bull", "energetica", "cerveza", "vino",
    "notmilk", "yogu yogu", "milo",
])
SNACKS = _compile(["mani", "castana", "caju", "snack", "papas fritas"])
MASCOTAS = _compile([
    "perro", "perros", "gato", "gatos", "gatito", "cachorro", "master dog",
    "master cat", "champion dog", "champion cat", "pedigree", "pet food",
    "alimento seco", "alimento humedo", "snack perro", "snack gato",
])
HIGIENE = _compile([
    "nivea", "rexona", "dove", "desodorante", "shampoo", "acondicionador",
    "jabon", "pasta dental", "cepillo dental", "micelar", "tonico", "crema facial",
    "limpieza facial", "leche limpiadora",
])
LIMPIEZA = _compile(["detergente", "cloro", "lavavajillas", "limpiador", "suavizante", "desinfectante"])

# Exclusiones: si el nombre matchea esto, NO se aplica la regla de bebidas
EXCLUDE_BEBIDA = _compile([
    "vinagre", "en vino", "al vino", "bebida lactea", "saborizante", "polvo", "salsa",
])

FALSE_MASCOTA_HIGIENE = _compile(["hair food", "aguacate", "original remedies", "cantu", "avena"])
FALSE_BEBIDA_MASCOTA = _compile(["trocitos jugosos", "al jugo", "alimento humedo"])
FALSE_LIMPIEZA = _compile(["pasta limpiadora", "pasta de limpieza", "betun pasta", "pink stuff"])


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
    cat = normalize(categoria)  # insensible a acentos

    if cat == "mascotas" and hit(FALSE_BEBIDA_MASCOTA, text):
        return CategoryValidation(True)
    if cat == "limpieza" and hit(FALSE_LIMPIEZA, text):
        return CategoryValidation(True)
    if hit(FALSE_MASCOTA_HIGIENE, text):
        return CategoryValidation(True)

    beb_excl = hit(EXCLUDE_BEBIDA, text)

    if cat == "bebe" and hit(BEBIDAS, text) and not beb_excl:
        return CategoryValidation(False, "bebida_en_bebe", *suggested_bebida(text), "Alta")
    if cat == "bebe" and hit(SNACKS, text):
        return CategoryValidation(False, "snack_en_bebe", "Desayuno y Snacks", "Snacks", "Alta")
    if cat == "bebe" and hit(LIMPIEZA, text):
        return CategoryValidation(False, "limpieza_en_bebe", "Limpieza", "Limpiadores", "Alta")

    if cat != "mascotas" and hit(MASCOTAS, text):
        return CategoryValidation(False, "mascota_fuera_de_mascotas", *suggested_mascota(text), "Alta")

    if cat not in {"higiene personal", "limpieza", "mascotas"} and hit(HIGIENE, text):
        return CategoryValidation(False, "higiene_fuera_de_higiene", *suggested_higiene(text), "Alta")

    if cat not in {"limpieza", "higiene personal"} and hit(LIMPIEZA, text):
        return CategoryValidation(False, "limpieza_fuera_de_limpieza", "Limpieza", "Limpiadores", "Alta")

    if cat not in {"bebidas", "bebe"} and hit(BEBIDAS, text) and not beb_excl:
        return CategoryValidation(False, "bebida_fuera_de_bebidas", *suggested_bebida(text), "Media")

    return CategoryValidation(True)


def validate_row(row: dict) -> CategoryValidation:
    return validate_category(row.get("nombre", ""), row.get("categoria", ""), row.get("subcategoria", ""))


# --- Politica de accion -------------------------------------------------
# keep   -> producto valido, se conserva
# review -> sospecha de confianza Media: se CONSERVA pero se marca para revision
# reject -> error de confianza Alta: se quita del load
def decide_action(v: CategoryValidation) -> str:
    if v.accepted:
        return "keep"
    if v.confidence == "Alta":
        return "reject"
    return "review"


def is_valid_row(row: dict, source: str = "", log_path: Path | None = None) -> bool:
    """True = el producto se CONSERVA en el load (keep o review).
    Solo confianza Alta (reject) devuelve False. Media se conserva y se cuarentena."""
    v = validate_row(row)
    action = decide_action(v)
    if action == "keep":
        return True
    if log_path:
        if action == "reject":
            _log(row, v, source, Path(log_path), action)
        else:  # review -> cuarentena (sibling file)
            q = Path(log_path).with_name("pipeline_category_quarantine.csv")
            _log(row, v, source, q, action)
    return action != "reject"


def _log(row: dict, v: CategoryValidation, source: str, log_path: Path, action: str) -> None:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    fields = ["timestamp", "action", "source", "nombre", "categoria", "subcategoria",
              "reason", "suggested_category", "suggested_subcategory", "confidence"]
    exists = log_path.exists()
    with log_path.open("a", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        if not exists:
            w.writeheader()
        w.writerow({
            "timestamp": datetime.now().isoformat(timespec="seconds"),
            "action": action, "source": source,
            "nombre": row.get("nombre", ""), "categoria": row.get("categoria", ""),
            "subcategoria": row.get("subcategoria", ""), "reason": v.reason,
            "suggested_category": v.suggested_category,
            "suggested_subcategory": v.suggested_subcategory, "confidence": v.confidence,
        })


# compat: nombre antiguo
def log_rejection(row, validation, source, log_path=DEFAULT_REJECT_LOG):
    _log(row, validation, source, Path(log_path), decide_action(validation))
