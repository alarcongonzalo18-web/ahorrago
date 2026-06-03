from __future__ import annotations

import csv
import json
import shutil
import time
from collections import Counter
from datetime import datetime
from pathlib import Path

from sqlalchemy import create_engine, distinct, func
from sqlalchemy.orm import sessionmaker

from app import models
from app.category_validator import DEFAULT_REJECT_LOG, is_valid_row
from app.combinar_supermercados import FUENTES
from app.database import Base
from app.importar_csv import crear_session_local_para_db, importar_productos
from app.matching_diagnostics import diagnosticar_matching
from app.scripts.agregar_indices import agregar_indices
from app.scripts.auditoria_categorias import auditar_categorias, escribir_reportes as escribir_auditoria_categorias
from app.scripts.auditoria_clasificacion_masiva import auditar as auditar_clasificacion_masiva
from app.scripts.auditoria_clasificacion_masiva import escribir_reportes as escribir_clasificacion_masiva
from app.scripts.auditoria_datos import ejecutar_auditoria, escribir_reportes as escribir_auditoria_datos
from app.scripts.comparar_bd_actual_vs_reload import _pct_delta, escribir_comparacion
from app.scripts.report_pdf import markdown_to_pdf


ROOT = Path(__file__).resolve().parents[2]
CURRENT_DB = ROOT / "supercheck.db"
RELOAD_DB = ROOT / "supercheck_reload_v3.db"
REPORTS_DIR = ROOT / "reports"
BACKUP_DIR = ROOT / "backups" / "recovery_5j"
RELOAD_DIR = REPORTS_DIR / "reload_v3"
RELOAD_CSV = RELOAD_DIR / "productos_supermercados_v3.csv"
CHECKPOINT_DIR = REPORTS_DIR / "reload_v3_checkpoints"
REJECT_LOG = REPORTS_DIR / "pipeline_category_rejections_v3.csv"
COMPARACION_CSV = REPORTS_DIR / "comparacion_actual_vs_reload_v3.csv"
REPORT_MD = REPORTS_DIR / "FASE_5JR_RELOAD_V3.md"
REPORT_PDF = REPORTS_DIR / "FASE_5JR_RELOAD_V3.pdf"
CAMBIOS_MD = ROOT / "CAMBIOS_FASE_5JR.md"
MASTER_MD = REPORTS_DIR / "AHORRAGO_MASTER_REPORT.md"
MASTER_PDF = REPORTS_DIR / "AHORRAGO_MASTER_REPORT.pdf"


def now() -> str:
    return datetime.now().isoformat(timespec="seconds")


def checkpoint_path(stage: int, name: str) -> Path:
    return CHECKPOINT_DIR / f"stage_{stage}_{name}_complete.json"


def read_checkpoint(stage: int, name: str) -> dict | None:
    path = checkpoint_path(stage, name)
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None
    return data if data.get("status") == "complete" else None


def write_checkpoint(stage: int, name: str, records: int, duration: float, errors: list[str], extra: dict | None = None) -> None:
    CHECKPOINT_DIR.mkdir(parents=True, exist_ok=True)
    payload = {
        "timestamp": now(),
        "stage": stage,
        "name": name,
        "records_processed": records,
        "duration_seconds": round(duration, 2),
        "status": "complete",
        "errors": errors,
    }
    if extra:
        payload.update(extra)
    checkpoint_path(stage, name).write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def count_csv_rows(path: Path) -> int:
    if not path.exists():
        return 0
    with path.open(newline="", encoding="utf-8-sig") as file:
        return sum(1 for _ in csv.DictReader(file))


def inspect_csv(path: Path) -> dict:
    data = path.read_bytes() if path.exists() else b""
    rows = count_csv_rows(path) if data else 0
    return {
        "path": str(path),
        "exists": path.exists(),
        "bytes": len(data),
        "rows": rows,
        "nul_bytes": data.count(b"\x00"),
        "lf_count": data.count(b"\n"),
        "integrity_ok": bool(data) and data.count(b"\x00") == 0 and rows > 0,
    }


def move_if_exists(path: Path) -> str | None:
    if not path.exists():
        return None
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    destination = BACKUP_DIR / path.name
    if destination.exists():
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        destination = BACKUP_DIR / f"{path.stem}_{stamp}{path.suffix}"
    shutil.move(str(path), str(destination))
    return str(destination)


def recovery_cleanup() -> list[dict]:
    targets = [
        ROOT / "supercheck_reload_v2.db",
        ROOT / "supercheck_reload_v2.db-journal",
        REPORTS_DIR / "FASE_5J_RELOAD_V2.md",
        REPORTS_DIR / "FASE_5J_RELOAD_V2.pdf",
        REPORTS_DIR / "comparacion_actual_vs_reload_v2.csv",
        REPORTS_DIR / "pipeline_category_rejections.csv",
    ]
    reload_v2_dir = REPORTS_DIR / "reload_v2"
    if reload_v2_dir.exists():
        targets.extend(path for path in reload_v2_dir.iterdir() if path.is_file())

    moved = []
    for target in targets:
        info = {
            "path": str(target),
            "existed": target.exists(),
            "bytes": target.stat().st_size if target.exists() else 0,
            "moved_to": move_if_exists(target) if target.exists() else None,
        }
        moved.append(info)
    return moved


def patch_validator_log(module) -> None:
    def _wrapped(row: dict, source: str = "", log_path: Path | None = None) -> bool:
        return is_valid_row(row, source, REJECT_LOG)

    module.is_valid_row = _wrapped


def run_scrapers() -> dict:
    checkpoint = read_checkpoint(1, "scrapers")
    if checkpoint:
        return checkpoint

    start = time.perf_counter()
    errors: list[str] = []
    if REJECT_LOG.exists():
        REJECT_LOG.unlink()

    import app.scraper_jumbo_real as jumbo
    import app.scraper_lider as lider
    import app.scraper_unimarc as unimarc

    for module in (lider, jumbo, unimarc):
        patch_validator_log(module)

    for name, module in [("lider", lider), ("jumbo", jumbo), ("unimarc", unimarc)]:
        try:
            module.main()
        except Exception as exc:
            errors.append(f"{name}: {exc}")

    outputs = {
        "lider": count_csv_rows(ROOT / "data" / "lider_real.csv"),
        "jumbo": count_csv_rows(ROOT / "data" / "jumbo_real.csv"),
        "unimarc": count_csv_rows(ROOT / "data" / "unimarc_real.csv"),
    }
    records = sum(outputs.values())
    rejected = count_csv_rows(REJECT_LOG)
    write_checkpoint(
        1,
        "scrapers",
        records,
        time.perf_counter() - start,
        errors,
        {"productos_obtenidos": outputs, "productos_rechazados": rejected},
    )
    if errors:
        raise RuntimeError("; ".join(errors))
    return read_checkpoint(1, "scrapers") or {}


def run_validator() -> dict:
    checkpoint = read_checkpoint(2, "validator")
    if checkpoint:
        return checkpoint

    start = time.perf_counter()
    errors: list[str] = []
    processed = 0
    rejected_before = count_csv_rows(REJECT_LOG)
    for source_path, supermercado in FUENTES:
        path = ROOT / source_path
        if not path.exists():
            errors.append(f"missing source csv: {path}")
            continue
        with path.open(newline="", encoding="utf-8-sig") as file:
            for row in csv.DictReader(file):
                processed += 1
                is_valid_row(row, f"fase5jr_validator:{supermercado}", REJECT_LOG)

    rejected_after = count_csv_rows(REJECT_LOG)
    write_checkpoint(
        2,
        "validator",
        processed,
        time.perf_counter() - start,
        errors,
        {"reject_log": str(REJECT_LOG), "new_rejections": rejected_after - rejected_before, "total_rejections": rejected_after},
    )
    return read_checkpoint(2, "validator") or {}


def run_combine() -> dict:
    checkpoint = read_checkpoint(3, "combine")
    if checkpoint:
        return checkpoint

    start = time.perf_counter()
    import app.combinar_supermercados as combinar_supermercados

    patch_validator_log(combinar_supermercados)
    combinar_supermercados.OUTPUT = RELOAD_CSV
    combinar_supermercados.combinar()

    csv_info = inspect_csv(RELOAD_CSV)
    errors = [] if csv_info["integrity_ok"] else [f"CSV invalido: {csv_info}"]
    write_checkpoint(3, "combine", csv_info["rows"], time.perf_counter() - start, errors, {"csv": csv_info})
    if errors:
        raise RuntimeError(errors[0])
    return read_checkpoint(3, "combine") or {}


def run_import() -> dict:
    checkpoint = read_checkpoint(4, "import")
    if checkpoint:
        return checkpoint

    start = time.perf_counter()
    errors: list[str] = []
    if RELOAD_DB.exists():
        moved = move_if_exists(RELOAD_DB)
        errors.append(f"existing reload_v3 moved before fresh import: {moved}")
    journal = ROOT / "supercheck_reload_v3.db-journal"
    if journal.exists():
        moved = move_if_exists(journal)
        errors.append(f"existing reload_v3 journal moved before fresh import: {moved}")

    session_factory, target_engine = crear_session_local_para_db(RELOAD_DB)
    Base.metadata.create_all(bind=target_engine)
    imported = importar_productos(csv_path=RELOAD_CSV, session_factory=session_factory, target_engine=target_engine)
    indices = agregar_indices(RELOAD_DB)
    metrics = measure_db(RELOAD_DB, generate_reports=False)
    write_checkpoint(
        4,
        "import",
        imported,
        time.perf_counter() - start,
        errors,
        {"db": str(RELOAD_DB), "bytes": RELOAD_DB.stat().st_size, "indices": len(indices), "metrics": metrics},
    )
    return read_checkpoint(4, "import") or {}


def create_session(db_path: Path):
    engine = create_engine(f"sqlite:///{db_path}", connect_args={"check_same_thread": False})
    return sessionmaker(autocommit=False, autoflush=False, bind=engine)()


def equivalences(db) -> tuple[int, int, int]:
    rows = db.query(models.Producto.producto_base, func.count(models.Producto.id)).filter(
        models.Producto.producto_base.isnot(None),
        models.Producto.producto_base != "",
    ).group_by(models.Producto.producto_base).all()
    groups = [count for _, count in rows if count > 1]
    products_with_equivalence = sum(groups)
    return len(groups), products_with_equivalence, db.query(models.Producto).count() - products_with_equivalence


def category_counts(db) -> Counter:
    return Counter(
        category or "Sin categoria"
        for (category,) in db.query(models.Categoria.nombre).join(
            models.Producto, models.Producto.categoria_id == models.Categoria.id
        ).all()
    )


def measure_db(db_path: Path, generate_reports: bool) -> dict:
    db = create_session(db_path)
    try:
        data_audit = ejecutar_auditoria(db)
        category_findings = auditar_categorias(db)
        mass_findings = auditar_clasificacion_masiva(db)
        confidence = Counter(item["confianza"] for item in mass_findings)
        eq_groups, products_with_eq, products_without_eq = equivalences(db)

        if generate_reports:
            RELOAD_DIR.mkdir(parents=True, exist_ok=True)
            escribir_auditoria_datos(data_audit, RELOAD_DIR)
            escribir_auditoria_categorias(category_findings, RELOAD_DIR)
            escribir_clasificacion_masiva(mass_findings, RELOAD_DIR)
            diagnosticar_matching(db, RELOAD_DIR)

        return {
            "productos": db.query(models.Producto).count(),
            "precios": db.query(models.Precio).count(),
            "categorias": db.query(models.Categoria).count(),
            "subcategorias": db.query(models.Subcategoria).count(),
            "producto_base_unicos": db.query(func.count(distinct(models.Producto.producto_base))).scalar() or 0,
            "equivalencias": eq_groups,
            "productos_con_equivalencia": products_with_eq,
            "productos_sin_equivalencia": products_without_eq,
            "conflictos": len(data_audit.producto_base_conflictivos),
            "hallazgos_categorias": len(category_findings),
            "hallazgos_clasificacion_masiva": len(mass_findings),
            "hallazgos_alta_confianza": confidence.get("Alta", 0),
            "hallazgos_media_confianza": confidence.get("Media", 0),
            "productos_sospechosos": data_audit.resumen["productos_sospechosos"],
            "producto_base_conflictivos": data_audit.resumen["producto_base_conflictivos"],
            "categorias_top": category_counts(db).most_common(10),
        }
    finally:
        db.close()


def run_audit() -> dict:
    checkpoint = read_checkpoint(5, "audit")
    if checkpoint:
        return checkpoint

    start = time.perf_counter()
    actual = measure_db(CURRENT_DB, generate_reports=False)
    reload = measure_db(RELOAD_DB, generate_reports=True)
    rows = escribir_comparacion(actual, reload, COMPARACION_CSV)
    rejected = analyze_rejections()
    write_report(actual, reload, rows, rejected)
    update_master_report(actual, reload, rejected)
    write_changes_report(actual, reload, rejected)
    markdown_to_pdf(MASTER_MD, MASTER_PDF, "AhorraGo Master Report")
    write_checkpoint(
        5,
        "audit",
        reload["productos"],
        time.perf_counter() - start,
        [],
        {"actual": actual, "reload": reload, "rejects": rejected, "comparison_csv": str(COMPARACION_CSV)},
    )
    return read_checkpoint(5, "audit") or {}


def analyze_rejections() -> dict:
    if not REJECT_LOG.exists():
        return {"total": 0, "top_motivos": [], "top_categorias_sugeridas": []}
    with REJECT_LOG.open(newline="", encoding="utf-8-sig") as file:
        rows = list(csv.DictReader(file))
    return {
        "total": len(rows),
        "top_motivos": Counter(row.get("reason", "") for row in rows).most_common(10),
        "top_categorias_sugeridas": Counter(
            f"{row.get('suggested_category', '')} > {row.get('suggested_subcategory', '')}".strip()
            for row in rows
        ).most_common(10),
    }


def is_reload_better(actual: dict, reload: dict) -> bool:
    enough_coverage = reload["productos"] >= int(actual["productos"] * 0.9)
    fewer_findings = reload["hallazgos_clasificacion_masiva"] < actual["hallazgos_clasificacion_masiva"]
    fewer_high = reload["hallazgos_alta_confianza"] < actual["hallazgos_alta_confianza"]
    return enough_coverage and fewer_findings and fewer_high


def write_report(actual: dict, reload: dict, rows: list[dict], rejects: dict) -> None:
    better = is_reload_better(actual, reload)
    lines = [
        "# Fase 5J-R - Recovery + Reload V3 Post-Hardening",
        "",
        f"Fecha: {datetime.now().date().isoformat()}",
        "",
        "## Resumen Ejecutivo",
        "",
        "- `supercheck.db` se mantiene intacta y sigue siendo la fuente valida productiva.",
        "- Los artefactos corruptos de Fase 5J se movieron a `backups/recovery_5j/`.",
        "- La nueva base paralela es `supercheck_reload_v3.db`.",
        "- La ejecucion genero checkpoints reanudables en `reports/reload_v3_checkpoints/`.",
        "",
        "## Metricas Principales",
        "",
        f"- Productos actual: {actual['productos']}.",
        f"- Productos reload v3: {reload['productos']}.",
        f"- Precios actual: {actual['precios']}.",
        f"- Precios reload v3: {reload['precios']}.",
        f"- Categorias actual: {actual['categorias']}.",
        f"- Categorias reload v3: {reload['categorias']}.",
        f"- Subcategorias actual: {actual['subcategorias']}.",
        f"- Subcategorias reload v3: {reload['subcategorias']}.",
        f"- Equivalencias actual: {actual['equivalencias']}.",
        f"- Equivalencias reload v3: {reload['equivalencias']}.",
        f"- Conflictos actual: {actual['conflictos']}.",
        f"- Conflictos reload v3: {reload['conflictos']}.",
        f"- Hallazgos clasificacion actual: {actual['hallazgos_clasificacion_masiva']}.",
        f"- Hallazgos clasificacion reload v3: {reload['hallazgos_clasificacion_masiva']}.",
        f"- Hallazgos alta confianza actual: {actual['hallazgos_alta_confianza']}.",
        f"- Hallazgos alta confianza reload v3: {reload['hallazgos_alta_confianza']}.",
        f"- Productos sin equivalencia actual: {actual['productos_sin_equivalencia']}.",
        f"- Productos sin equivalencia reload v3: {reload['productos_sin_equivalencia']}.",
        f"- Rechazos pipeline v3: {rejects['total']}.",
        "",
        "## Decision Final",
        "",
        f"- `supercheck_reload_v3.db` es mejor que `supercheck.db`: {'SI' if better else 'NO'}.",
        "- Criterio: cobertura >= 90%, menos hallazgos totales y menos hallazgos de alta confianza.",
        "",
        "## Comparacion",
        "",
        "| Metrica | Actual | Reload V3 | Diferencia | Diferencia % |",
        "|---|---:|---:|---:|---:|",
    ]
    for row in rows:
        lines.append(
            f"| {row['metrica']} | {row['actual']} | {row['reload']} | {row['diferencia']} | {row['diferencia_porcentual']} |"
        )

    lines.extend(["", "## Rechazos - Top Motivos", ""])
    for reason, count in rejects["top_motivos"]:
        lines.append(f"- {reason}: {count}")
    lines.extend(["", "## Archivos", ""])
    for path in [REPORT_MD, REPORT_PDF, COMPARACION_CSV, REJECT_LOG, RELOAD_CSV, RELOAD_DB]:
        lines.append(f"- `{path.relative_to(ROOT).as_posix()}`")

    REPORT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")
    markdown_to_pdf(REPORT_MD, REPORT_PDF, "Fase 5J-R - Reload V3")


def update_master_report(actual: dict, reload: dict, rejects: dict) -> None:
    better = is_reload_better(actual, reload)
    block = "\n".join([
        "",
        "---",
        "",
        "# Fase 5J-R - Recovery + Reload V3 Post-Hardening",
        "",
        f"Fecha: {datetime.now().date().isoformat()}",
        "",
        "## Objetivo",
        "",
        "Recuperar la ejecucion interrumpida de Fase 5J sin tocar `supercheck.db`, crear una BD paralela v3 y validar el pipeline endurecido.",
        "",
        "## Resultado",
        "",
        f"- Productos actual: {actual['productos']}.",
        f"- Productos reload v3: {reload['productos']}.",
        f"- Precios actual: {actual['precios']}.",
        f"- Precios reload v3: {reload['precios']}.",
        f"- Hallazgos actual: {actual['hallazgos_clasificacion_masiva']}.",
        f"- Hallazgos reload v3: {reload['hallazgos_clasificacion_masiva']}.",
        f"- Alta confianza actual: {actual['hallazgos_alta_confianza']}.",
        f"- Alta confianza reload v3: {reload['hallazgos_alta_confianza']}.",
        f"- Rechazos pipeline v3: {rejects['total']}.",
        f"- Decision: `supercheck_reload_v3.db` es mejor que `supercheck.db`: {'SI' if better else 'NO'}.",
        "",
        "## Archivos",
        "",
        "- `reports/FASE_5JR_RELOAD_V3.md`",
        "- `reports/FASE_5JR_RELOAD_V3.pdf`",
        "- `reports/comparacion_actual_vs_reload_v3.csv`",
        "- `reports/pipeline_category_rejections_v3.csv`",
        "- `reports/reload_v3_checkpoints/`",
        "- `CAMBIOS_FASE_5JR.md`",
        "",
    ])
    current = MASTER_MD.read_text(encoding="utf-8") if MASTER_MD.exists() else "# AhorraGo Master Report\n"
    if "# Fase 5J-R - Recovery + Reload V3 Post-Hardening" not in current:
        MASTER_MD.write_text(current.rstrip() + block, encoding="utf-8")


def write_changes_report(actual: dict, reload: dict, rejects: dict) -> None:
    better = is_reload_better(actual, reload)
    lines = [
        "# Cambios Fase 5J-R",
        "",
        f"Fecha: {datetime.now().date().isoformat()}",
        "",
        "## Cambios",
        "",
        "- Se movieron artefactos corruptos de Fase 5J a `backups/recovery_5j/`.",
        "- Se creo `app/scripts/reload_v3_fase5jr.py` para recuperacion, reload v3, checkpoints y reportes.",
        "- Se genero `supercheck_reload_v3.db` como BD paralela.",
        "- Se generaron checkpoints en `reports/reload_v3_checkpoints/`.",
        "- Se generaron reportes Fase 5J-R en Markdown y PDF.",
        "",
        "## Resultado",
        "",
        f"- Productos actual: {actual['productos']}.",
        f"- Productos reload v3: {reload['productos']}.",
        f"- Hallazgos actual: {actual['hallazgos_clasificacion_masiva']}.",
        f"- Hallazgos reload v3: {reload['hallazgos_clasificacion_masiva']}.",
        f"- Rechazos pipeline v3: {rejects['total']}.",
        f"- Decision tecnica: {'SI' if better else 'NO'}, reload v3 es mejor que actual.",
        "",
        "## Seguridad",
        "",
        "- `supercheck.db` no fue modificada por la fase.",
        "- `frontend`, usuarios, favoritos y login no fueron modificados por la fase.",
        "- La BD reload v2 no se reutilizo.",
        "",
    ]
    CAMBIOS_MD.write_text("\n".join(lines), encoding="utf-8")


def execute() -> dict:
    cleanup = recovery_cleanup()
    stage1 = run_scrapers()
    stage2 = run_validator()
    stage3 = run_combine()
    stage4 = run_import()
    stage5 = run_audit()
    return {"cleanup": cleanup, "stage1": stage1, "stage2": stage2, "stage3": stage3, "stage4": stage4, "stage5": stage5}


def main() -> int:
    result = execute()
    audit = result["stage5"]
    actual = audit["actual"]
    reload = audit["reload"]
    better = is_reload_better(actual, reload)
    print("Fase 5J-R Reload V3 completada.")
    print(f"productos_actual: {actual['productos']}")
    print(f"productos_reload_v3: {reload['productos']}")
    print(f"precios_actual: {actual['precios']}")
    print(f"precios_reload_v3: {reload['precios']}")
    print(f"hallazgos_actual: {actual['hallazgos_clasificacion_masiva']}")
    print(f"hallazgos_reload_v3: {reload['hallazgos_clasificacion_masiva']}")
    print(f"reload_v3_mejor: {'SI' if better else 'NO'}")
    print(f"reporte: {REPORT_MD}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
