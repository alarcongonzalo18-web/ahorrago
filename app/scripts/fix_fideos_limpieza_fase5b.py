from __future__ import annotations

import csv
import shutil
import sqlite3
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from sqlalchemy.orm import Session

from app import models
from app.database import SessionLocal
from app.scripts.report_pdf import markdown_to_pdf


ROOT = Path(__file__).resolve().parents[2]
DB_PATH = ROOT / "supercheck.db"
BACKUPS_DIR = ROOT / "backups"
REPORTS_DIR = ROOT / "reports"
FASE5B_CSV = REPORTS_DIR / "fase5b_cambios.csv"
TRACE_CSV = REPORTS_DIR / "fix_fideos_fase5b.csv"
MASTER_REPORT = REPORTS_DIR / "AHORRAGO_MASTER_REPORT.md"

EXPECTED_IDS = {
    386, 387, 390, 391, 392, 404, 3475, 3479, 3483, 3484,
    3485, 3486, 3506, 3507, 3514, 3516, 3518, 3521, 3522,
    3523, 3524, 3525, 3526, 3527, 3529,
}


@dataclass
class FixResult:
    aplicados: int
    pendientes: int
    noop: int
    backup: Path | None
    trace_csv: Path
    ids: list[int]


def crear_backup() -> Path:
    BACKUPS_DIR.mkdir(parents=True, exist_ok=True)
    destino = BACKUPS_DIR / f"supercheck_pre_fix_fideos_fase5b_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
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


def cargar_bases_anteriores(path: Path = FASE5B_CSV) -> dict[int, str]:
    with path.open(newline="", encoding="utf-8-sig") as archivo:
        rows = list(csv.DictReader(archivo))
    cambios = {}
    for row in rows:
        nombre = (row.get("producto_original") or "").lower()
        producto_id = int(row["producto_id"])
        if (
            producto_id in EXPECTED_IDS
            and "fideo" in nombre
            and row.get("categoria") == "Limpieza"
            and (row.get("producto_base_nuevo") or "").startswith("limpieza_")
        ):
            cambios[producto_id] = row.get("producto_base_anterior") or ""
    if set(cambios) != EXPECTED_IDS:
        faltantes = sorted(EXPECTED_IDS - set(cambios))
        extras = sorted(set(cambios) - EXPECTED_IDS)
        raise RuntimeError(f"CSV Fase 5B no coincide con IDs esperados. faltantes={faltantes}; extras={extras}")
    return cambios


def _categoria_subcategoria(db: Session, categoria: str, subcategoria: str) -> tuple[models.Categoria, models.Subcategoria]:
    categoria_obj = db.query(models.Categoria).filter(models.Categoria.nombre == categoria).one()
    subcategoria_obj = db.query(models.Subcategoria).filter(
        models.Subcategoria.categoria_id == categoria_obj.id,
        models.Subcategoria.nombre == subcategoria,
    ).one()
    return categoria_obj, subcategoria_obj


def _fila_trace(producto, categoria_nueva, subcategoria_nueva, base_nueva, accion, timestamp) -> dict:
    return {
        "producto_id": producto.id,
        "producto_nombre": producto.nombre,
        "categoria_anterior": producto.categoria.nombre if producto.categoria else "",
        "subcategoria_anterior": producto.subcategoria.nombre if producto.subcategoria else "",
        "producto_base_anterior": producto.producto_base or "",
        "categoria_nueva": categoria_nueva,
        "subcategoria_nueva": subcategoria_nueva,
        "producto_base_nuevo": base_nueva,
        "accion": accion,
        "timestamp": timestamp,
    }


def escribir_trace(filas: list[dict], path: Path = TRACE_CSV) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    campos = [
        "producto_id",
        "producto_nombre",
        "categoria_anterior",
        "subcategoria_anterior",
        "producto_base_anterior",
        "categoria_nueva",
        "subcategoria_nueva",
        "producto_base_nuevo",
        "accion",
        "timestamp",
    ]
    with path.open("w", newline="", encoding="utf-8-sig") as archivo:
        writer = csv.DictWriter(archivo, fieldnames=campos)
        writer.writeheader()
        writer.writerows(filas)


def aplicar_fix(db: Session, trace_path: Path = TRACE_CSV, crear_backup_previo: bool = True) -> FixResult:
    bases_anteriores = cargar_bases_anteriores()
    despensa, fideos = _categoria_subcategoria(db, "Despensa", "Fideos")
    timestamp = datetime.now().isoformat(timespec="seconds")
    filas = []
    aplicados = 0
    noop = 0

    productos = db.query(models.Producto).filter(models.Producto.id.in_(sorted(EXPECTED_IDS))).all()
    por_id = {producto.id: producto for producto in productos}
    if set(por_id) != EXPECTED_IDS:
        raise RuntimeError(f"No se encontraron todos los productos esperados: {sorted(EXPECTED_IDS - set(por_id))}")

    for producto_id in sorted(EXPECTED_IDS):
        producto = por_id[producto_id]
        base_nueva = bases_anteriores[producto_id]
        ya_corregido = (
            producto.categoria_id == despensa.id
            and producto.subcategoria_id == fideos.id
            and (producto.producto_base or "") == base_nueva
        )
        accion = "sin_cambios" if ya_corregido else "fix_aplicado"
        filas.append(_fila_trace(producto, "Despensa", "Fideos", base_nueva, accion, timestamp))
        if ya_corregido:
            noop += 1
            continue
        producto.categoria_id = despensa.id
        producto.subcategoria_id = fideos.id
        producto.producto_base = base_nueva
        aplicados += 1

    backup = crear_backup() if crear_backup_previo and aplicados else None
    db.commit()
    if aplicados or not trace_path.exists():
        escribir_trace(filas, trace_path)
    return FixResult(
        aplicados=aplicados,
        pendientes=len(EXPECTED_IDS) - aplicados - noop,
        noop=noop,
        backup=backup,
        trace_csv=trace_path,
        ids=sorted(EXPECTED_IDS),
    )


def _contar_residuales(db: Session) -> int:
    return db.query(models.Producto).join(models.Categoria).join(models.Subcategoria).filter(
        models.Categoria.nombre == "Limpieza",
        models.Subcategoria.nombre == "Blanqueadores",
        models.Producto.id.in_(sorted(EXPECTED_IDS)),
    ).count()


def escribir_reportes(result: FixResult, residuales: int) -> None:
    md = ROOT / "CAMBIOS_FASE_5B_FIX.md"
    reporte = REPORTS_DIR / "FASE_5B_FIX_REPORTE.md"
    lines = [
        "# Cambios Fase 5B-FIX - AhorraGo",
        "",
        "Fecha: 2026-06-01",
        "",
        "## Objetivo",
        "",
        "Corregir de forma quirurgica 25 productos tipo fideo/pasta afectados por Fase 5B.",
        "",
        "## Alcance",
        "",
        "- No se ejecuto rollback completo de Fase 5B.",
        "- No se modifico Mascotas.",
        "- No se toco frontend, usuarios, scraping ni migracion de base.",
        "- Se modificaron solo los 25 IDs confirmados por reports/fase5b_cambios.csv.",
        "",
        "## Resultado",
        "",
        f"- Productos corregidos en esta ejecucion: {result.aplicados}.",
        f"- Productos ya corregidos/idempotentes: {result.noop}.",
        f"- IDs objetivo restantes en Limpieza > Blanqueadores: {residuales}.",
        f"- Backup previo: {result.backup if result.backup else 'no creado porque no habia cambios pendientes'}.",
        f"- CSV de trazabilidad: {result.trace_csv}.",
        "",
        "## Rollback Especifico",
        "",
        "```powershell",
        "python -m app.scripts.rollback_fix_fideos_fase5b",
        "```",
        "",
        "## IDs Corregidos",
        "",
        ", ".join(str(item) for item in result.ids),
        "",
        "## Validacion Esperada",
        "",
        "- 25 productos quedan en Despensa > Fideos.",
        "- producto_base vuelve al valor anterior registrado en Fase 5B.",
        "- Mascotas no cambia.",
        "- Productos validos de Limpieza no cambian.",
        "",
    ]
    text = "\n".join(lines)
    md.write_text(text, encoding="utf-8")
    reporte.write_text(text.replace("# Cambios", "# Reporte"), encoding="utf-8")
    markdown_to_pdf(reporte, REPORTS_DIR / "FASE_5B_FIX_REPORTE.pdf", "Fase 5B-FIX - AhorraGo")
    markdown_to_pdf(md, ROOT / "CAMBIOS_FASE_5B_FIX.pdf", "Cambios Fase 5B-FIX - AhorraGo")

    section = "\n---\n\n# Fase 5B-FIX\n\n" + "\n".join(lines[2:])
    master = MASTER_REPORT.read_text(encoding="utf-8") if MASTER_REPORT.exists() else ""
    marker = "# Fase 5B-FIX"
    if marker not in master:
        MASTER_REPORT.write_text(master.rstrip() + section + "\n", encoding="utf-8")
    markdown_to_pdf(MASTER_REPORT, REPORTS_DIR / "AHORRAGO_MASTER_REPORT.pdf", "AhorraGo Master Report")


def main() -> int:
    db = SessionLocal()
    try:
        result = aplicar_fix(db)
        residuales = _contar_residuales(db)
        escribir_reportes(result, residuales)
    finally:
        db.close()
    print("FASE 5B-FIX completada")
    print(f"Productos corregidos: {result.aplicados}")
    print(f"Productos ya corregidos: {result.noop}")
    print(f"Backup: {result.backup if result.backup else 'no creado'}")
    print(f"Trazabilidad: {result.trace_csv}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
