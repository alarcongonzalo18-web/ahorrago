from __future__ import annotations

import csv
import shutil
import sqlite3
from collections import Counter
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from sqlalchemy.orm import Session

from app import models
from app.database import SessionLocal
from app.normalizacion import normalizar_texto
from app.scripts.report_pdf import markdown_to_pdf


ROOT = Path(__file__).resolve().parents[2]
DB_PATH = ROOT / "supercheck.db"
BACKUPS_DIR = ROOT / "backups"
REPORTS_DIR = ROOT / "reports"
CLASIFICACION_CSV = REPORTS_DIR / "clasificacion_hallazgos_fase5d.csv"
TRACE_CSV = REPORTS_DIR / "fase5d_fix_cambios.csv"
MASTER_REPORT = REPORTS_DIR / "AHORRAGO_MASTER_REPORT.md"

FALSOS_POSITIVOS = [
    "hair food",
    "aguacate",
    "cantu",
    "original remedies",
    "avena",
    "pink stuff",
    "betun",
    "betún",
    "pasta limpiadora",
    "pasta de limpieza",
    "trocitos jugosos",
    "alimento humedo",
    "alimento húmedo",
]


@dataclass
class Fix5DResult:
    aplicados: int
    noop: int
    backup: Path | None
    trace_csv: Path
    por_tipo: dict[str, int]


def crear_backup() -> Path:
    BACKUPS_DIR.mkdir(parents=True, exist_ok=True)
    destino = BACKUPS_DIR / f"supercheck_pre_fase5d_fix_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
    shutil.copy2(DB_PATH, destino)
    if destino.stat().st_size <= 0:
        raise RuntimeError(f"Backup vacio: {destino}")
    conn = sqlite3.connect(destino)
    try:
        check = conn.execute("PRAGMA quick_check").fetchone()[0]
    finally:
        conn.close()
    if check != "ok":
        raise RuntimeError(f"Backup invalido: {destino} -> {check}")
    return destino


def _leer_csv(path: Path) -> list[dict]:
    with path.open(newline="", encoding="utf-8-sig") as archivo:
        return list(csv.DictReader(archivo))


def _es_falso_positivo(row: dict) -> bool:
    texto = normalizar_texto(row.get("producto_nombre", ""))
    tipo = row.get("tipo_hallazgo", "")
    sugerida = row.get("categoria_sugerida", "")
    actual = row.get("categoria_actual", "")
    if sugerida == actual:
        return True
    if tipo == "bebida_en_mascotas":
        return True
    if any(normalizar_texto(token) in texto for token in FALSOS_POSITIVOS):
        if not ("leche" in texto and sugerida == "Higiene Personal"):
            return True
    return False


def cargar_correcciones(path: Path = CLASIFICACION_CSV) -> list[dict]:
    rows = _leer_csv(path)
    correcciones = []
    for row in rows:
        if row.get("confianza_correccion") != "Alta":
            continue
        if row.get("categoria_sugerida") == row.get("categoria_actual"):
            continue
        if _es_falso_positivo(row):
            continue
        correcciones.append(row)
    return correcciones


def _destino_mascotas(nombre: str) -> tuple[str, str]:
    texto = normalizar_texto(nombre)
    if "gato" in texto or "gatito" in texto:
        return "Mascotas", "Alimento Gatos"
    return "Mascotas", "Alimento Perros"


def resolver_destino(row: dict) -> tuple[str, str]:
    sugerida = row["categoria_sugerida"]
    if sugerida == "Despensa":
        return "Despensa", "Fideos"
    if sugerida == "Higiene Personal":
        return "Higiene Personal", "Cuidado Facial"
    if sugerida == "Mascotas":
        return _destino_mascotas(row["producto_nombre"])
    raise RuntimeError(f"Categoria sugerida no soportada: {sugerida}")


def _categoria_subcategoria(db: Session, categoria: str, subcategoria: str) -> tuple[models.Categoria, models.Subcategoria]:
    categoria_obj = db.query(models.Categoria).filter(models.Categoria.nombre == categoria).one()
    subcategoria_obj = db.query(models.Subcategoria).filter(
        models.Subcategoria.categoria_id == categoria_obj.id,
        models.Subcategoria.nombre == subcategoria,
    ).one()
    return categoria_obj, subcategoria_obj


def escribir_trace(filas: list[dict], path: Path = TRACE_CSV) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    campos = [
        "producto_id",
        "producto_nombre",
        "categoria_anterior",
        "subcategoria_anterior",
        "categoria_nueva",
        "subcategoria_nueva",
        "producto_base",
        "motivo",
        "timestamp",
    ]
    with path.open("w", newline="", encoding="utf-8-sig") as archivo:
        writer = csv.DictWriter(archivo, fieldnames=campos)
        writer.writeheader()
        writer.writerows(filas)


def aplicar_fix(
    db: Session,
    clasificacion_path: Path = CLASIFICACION_CSV,
    trace_path: Path = TRACE_CSV,
    crear_backup_previo: bool = True,
) -> Fix5DResult:
    correcciones = cargar_correcciones(clasificacion_path)
    timestamp = datetime.now().isoformat(timespec="seconds")
    filas = []
    aplicados = 0
    noop = 0
    por_tipo = Counter()

    for row in correcciones:
        producto = db.get(models.Producto, int(row["producto_id"]))
        if not producto:
            continue
        categoria_destino, subcategoria_destino = resolver_destino(row)
        categoria_obj, subcategoria_obj = _categoria_subcategoria(db, categoria_destino, subcategoria_destino)
        categoria_anterior = producto.categoria.nombre if producto.categoria else ""
        subcategoria_anterior = producto.subcategoria.nombre if producto.subcategoria else ""
        ya_corregido = producto.categoria_id == categoria_obj.id and producto.subcategoria_id == subcategoria_obj.id

        filas.append({
            "producto_id": producto.id,
            "producto_nombre": producto.nombre,
            "categoria_anterior": categoria_anterior,
            "subcategoria_anterior": subcategoria_anterior,
            "categoria_nueva": categoria_destino,
            "subcategoria_nueva": subcategoria_destino,
            "producto_base": producto.producto_base or "",
            "motivo": row.get("motivo", ""),
            "timestamp": timestamp,
        })

        if ya_corregido:
            noop += 1
            continue
        producto.categoria_id = categoria_obj.id
        producto.subcategoria_id = subcategoria_obj.id
        aplicados += 1
        por_tipo[row["tipo_hallazgo"]] += 1

    backup = crear_backup() if crear_backup_previo and aplicados else None
    db.commit()
    if aplicados or not trace_path.exists():
        escribir_trace(filas, trace_path)
    return Fix5DResult(aplicados, noop, backup, trace_path, dict(por_tipo))


def escribir_reportes(result: Fix5DResult, hallazgos_restantes: int | None = None) -> None:
    cambios_md = ROOT / "CAMBIOS_FASE_5D_FIX.md"
    reporte_md = REPORTS_DIR / "FASE_5D_FIX_REPORTE.md"
    por_tipo = Counter(result.por_tipo)
    lines = [
        "# Cambios Fase 5D-FIX - AhorraGo",
        "",
        "Fecha: 2026-06-01",
        "",
        "## Objetivo",
        "",
        "Aplicar correcciones reales de categoria detectadas en Fase 5D, sin tocar falsos positivos.",
        "",
        "## Resultado",
        "",
        f"- Productos corregidos en esta ejecucion: {result.aplicados}.",
        f"- Productos ya corregidos/idempotentes: {result.noop}.",
        f"- Backup previo: {result.backup if result.backup else 'no creado porque no habia cambios pendientes'}.",
        f"- CSV de trazabilidad: {result.trace_csv}.",
        f"- Hallazgos restantes post-auditoria: {hallazgos_restantes if hallazgos_restantes is not None else 'pendiente'}.",
        "",
        "## Detalle por Tipo",
        "",
        f"- alimento_en_limpieza: {por_tipo.get('alimento_en_limpieza', 0)}.",
        f"- mascota_en_higiene: {por_tipo.get('mascota_en_higiene', 0)}.",
        f"- bebida_en_mascotas: {por_tipo.get('bebida_en_mascotas', 0)}.",
        "",
        "## Seguridad",
        "",
        "- No se ejecuto rollback completo.",
        "- No se modificaron falsos positivos.",
        "- No se modificaron bebidas en Mascotas.",
        "- No se toco frontend, usuarios, scraping ni migracion de base.",
        "- producto_base se mantuvo sin recalcular.",
        "",
        "## Rollback Especifico",
        "",
        "```powershell",
        "python -m app.scripts.rollback_fix_categorias_fase5d",
        "```",
        "",
    ]
    text = "\n".join(lines)
    cambios_md.write_text(text, encoding="utf-8")
    reporte_md.write_text(text.replace("# Cambios", "# Reporte"), encoding="utf-8")
    markdown_to_pdf(reporte_md, REPORTS_DIR / "FASE_5D_FIX_REPORTE.pdf", "Fase 5D-FIX - AhorraGo")

    master = MASTER_REPORT.read_text(encoding="utf-8") if MASTER_REPORT.exists() else ""
    marker = "# Fase 5D-FIX"
    if marker not in master:
        MASTER_REPORT.write_text(master.rstrip() + "\n---\n\n# Fase 5D-FIX\n\n" + "\n".join(lines[2:]) + "\n", encoding="utf-8")
    markdown_to_pdf(MASTER_REPORT, REPORTS_DIR / "AHORRAGO_MASTER_REPORT.pdf", "AhorraGo Master Report")


def main() -> int:
    db = SessionLocal()
    try:
        result = aplicar_fix(db)
        if result.aplicados or not (REPORTS_DIR / "FASE_5D_FIX_REPORTE.md").exists():
            escribir_reportes(result)
    finally:
        db.close()
    print("FASE 5D-FIX completada")
    print(f"Productos corregidos: {result.aplicados}")
    print(f"Productos ya corregidos: {result.noop}")
    print(f"Backup: {result.backup if result.backup else 'no creado'}")
    print(f"Trazabilidad: {result.trace_csv}")
    print(f"Detalle por tipo: {result.por_tipo}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
