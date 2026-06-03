from __future__ import annotations

import argparse
import csv
from collections import Counter
from pathlib import Path

from sqlalchemy import create_engine, distinct, func
from sqlalchemy.orm import sessionmaker

from app import models
from app.database import Base
from app.matching_diagnostics import diagnosticar_matching
from app.scripts.auditoria_categorias import auditar_categorias, escribir_reportes as escribir_auditoria_categorias
from app.scripts.auditoria_clasificacion_masiva import auditar as auditar_clasificacion_masiva
from app.scripts.auditoria_clasificacion_masiva import escribir_reportes as escribir_clasificacion_masiva
from app.scripts.auditoria_datos import ejecutar_auditoria, escribir_reportes as escribir_auditoria_datos
from app.scripts.report_pdf import markdown_to_pdf


ROOT = Path(__file__).resolve().parents[2]
CURRENT_DB = ROOT / "supercheck.db"
RELOAD_DB = ROOT / "supercheck_reload_test.db"
REPORTS_DIR = ROOT / "reports"


def _resolver(path: Path) -> Path:
    return path if path.is_absolute() else ROOT / path


def crear_session(db_path: Path):
    engine = create_engine(f"sqlite:///{db_path}", connect_args={"check_same_thread": False})
    return sessionmaker(autocommit=False, autoflush=False, bind=engine)()


def _equivalencias(db) -> tuple[int, int, int]:
    rows = db.query(models.Producto.producto_base, func.count(models.Producto.id)).filter(
        models.Producto.producto_base.isnot(None),
        models.Producto.producto_base != "",
    ).group_by(models.Producto.producto_base).all()
    grupos = [count for _, count in rows if count > 1]
    productos_con_equivalencia = sum(grupos)
    return len(grupos), productos_con_equivalencia, db.query(models.Producto).count() - productos_con_equivalencia


def _conteo_categoria(db) -> Counter:
    return Counter(
        categoria or "Sin categoria"
        for (categoria,) in db.query(models.Categoria.nombre).join(
            models.Producto, models.Producto.categoria_id == models.Categoria.id
        ).all()
    )


def medir_bd(db_path: Path, generar_reportes_reload: bool = False) -> dict:
    db = crear_session(db_path)
    try:
        auditoria_datos = ejecutar_auditoria(db)
        hallazgos_categorias = auditar_categorias(db)
        hallazgos_masivos = auditar_clasificacion_masiva(db)
        por_confianza = Counter(item["confianza"] for item in hallazgos_masivos)
        grupos_equivalencia, productos_con_equivalencia, productos_sin_equivalencia = _equivalencias(db)
        categorias = db.query(models.Categoria).count()
        subcategorias = db.query(models.Subcategoria).count()

        if generar_reportes_reload:
            reload_reports = REPORTS_DIR / "reload_test"
            escribir_auditoria_datos(auditoria_datos, reload_reports)
            escribir_auditoria_categorias(hallazgos_categorias, reload_reports)
            escribir_clasificacion_masiva(hallazgos_masivos, reload_reports)
            diagnosticar_matching(db, reload_reports)

        return {
            "productos": db.query(models.Producto).count(),
            "precios": db.query(models.Precio).count(),
            "categorias": categorias,
            "subcategorias": subcategorias,
            "producto_base_unicos": db.query(func.count(distinct(models.Producto.producto_base))).scalar() or 0,
            "equivalencias": grupos_equivalencia,
            "productos_con_equivalencia": productos_con_equivalencia,
            "productos_sin_equivalencia": productos_sin_equivalencia,
            "conflictos": len(auditoria_datos.producto_base_conflictivos),
            "hallazgos_categorias": len(hallazgos_categorias),
            "hallazgos_clasificacion_masiva": len(hallazgos_masivos),
            "hallazgos_alta_confianza": por_confianza.get("Alta", 0),
            "hallazgos_media_confianza": por_confianza.get("Media", 0),
            "productos_sospechosos": auditoria_datos.resumen["productos_sospechosos"],
            "producto_base_conflictivos": auditoria_datos.resumen["producto_base_conflictivos"],
            "categorias_top": _conteo_categoria(db).most_common(10),
        }
    finally:
        db.close()


def _pct_delta(actual: int | float, reload: int | float) -> float:
    if actual == 0:
        return 0.0 if reload == 0 else 100.0
    return round(((reload - actual) / actual) * 100, 2)


def escribir_comparacion(actual: dict, reload: dict, output_csv: Path) -> list[dict]:
    metricas = [
        "productos",
        "precios",
        "categorias",
        "subcategorias",
        "producto_base_unicos",
        "equivalencias",
        "productos_con_equivalencia",
        "productos_sin_equivalencia",
        "conflictos",
        "hallazgos_categorias",
        "hallazgos_clasificacion_masiva",
        "hallazgos_alta_confianza",
        "hallazgos_media_confianza",
        "productos_sospechosos",
        "producto_base_conflictivos",
    ]
    filas = []
    for metrica in metricas:
        valor_actual = actual[metrica]
        valor_reload = reload[metrica]
        filas.append({
            "metrica": metrica,
            "actual": valor_actual,
            "reload": valor_reload,
            "diferencia": valor_reload - valor_actual,
            "diferencia_porcentual": _pct_delta(valor_actual, valor_reload),
        })

    output_csv.parent.mkdir(parents=True, exist_ok=True)
    with output_csv.open("w", newline="", encoding="utf-8-sig") as archivo:
        writer = csv.DictWriter(archivo, fieldnames=list(filas[0].keys()))
        writer.writeheader()
        writer.writerows(filas)
    return filas


def _decision(actual: dict, reload: dict) -> dict:
    actual_errores = actual["hallazgos_clasificacion_masiva"]
    reload_errores = reload["hallazgos_clasificacion_masiva"]
    menos_errores = reload_errores < actual_errores
    reaparecen = reload_errores >= max(1, int(actual_errores * 0.8))
    return {
        "menos_errores": menos_errores,
        "reaparecen": reaparecen,
        "origen_probable": "scripts_datos_fuente" if reaparecen else "bd_actual_modificada",
        "reemplazar_bd": menos_errores and not reaparecen,
        "arreglar_importadores": reaparecen,
        "seguir_fase5f_fix": not menos_errores or reaparecen,
    }


def escribir_reporte(actual: dict, reload: dict, filas: list[dict], md_path: Path) -> None:
    decision = _decision(actual, reload)
    lines = [
        "# Fase 5G - Reload Test Paralelo",
        "",
        "Modo: comparacion controlada. No se modifica supercheck.db.",
        "",
        "## Resumen Ejecutivo",
        "",
        f"- Productos en BD actual: {actual['productos']}",
        f"- Productos en BD reload: {reload['productos']}",
        f"- Hallazgos actuales: {actual['hallazgos_clasificacion_masiva']}",
        f"- Hallazgos reload: {reload['hallazgos_clasificacion_masiva']}",
        f"- Hallazgos alta confianza actual: {actual['hallazgos_alta_confianza']}",
        f"- Hallazgos alta confianza reload: {reload['hallazgos_alta_confianza']}",
        f"- Diferencia porcentual de hallazgos: {_pct_delta(actual['hallazgos_clasificacion_masiva'], reload['hallazgos_clasificacion_masiva'])}%",
        "",
        "## Decision Tecnica",
        "",
        f"- La BD recargada tiene menos errores que la actual: {'si' if decision['menos_errores'] else 'no'}",
        f"- Los errores reaparecen en la recarga: {'si' if decision['reaparecen'] else 'no'}",
        f"- Origen probable: {decision['origen_probable']}",
        f"- Conviene reemplazar la BD actual: {'si' if decision['reemplazar_bd'] else 'no'}",
        f"- Conviene arreglar importadores/datos fuente antes: {'si' if decision['arreglar_importadores'] else 'no'}",
        f"- Conviene seguir con Fase 5F-FIX: {'si' if decision['seguir_fase5f_fix'] else 'no'}",
        "",
        "## Comparacion",
        "",
        "| Metrica | Actual | Reload | Diferencia | Diferencia % |",
        "|---|---:|---:|---:|---:|",
    ]
    for fila in filas:
        lines.append(
            f"| {fila['metrica']} | {fila['actual']} | {fila['reload']} | "
            f"{fila['diferencia']} | {fila['diferencia_porcentual']} |"
        )

    lines.extend([
        "",
        "## Categorias Top Actual",
        "",
    ])
    for categoria, cantidad in actual["categorias_top"]:
        lines.append(f"- {categoria}: {cantidad}")

    lines.extend(["", "## Categorias Top Reload", ""])
    for categoria, cantidad in reload["categorias_top"]:
        lines.append(f"- {categoria}: {cantidad}")

    lines.extend([
        "",
        "## Auditorias Ejecutadas Sobre Reload",
        "",
        "- reports/reload_test/auditoria_categorias.md",
        "- reports/reload_test/fase5f_clasificacion_masiva.md",
        "- reports/reload_test/diagnostico_matching.md",
        "- reports/reload_test/auditoria_datos.md",
        "",
        "## Recomendacion",
        "",
        "- No reemplazar supercheck.db solo por esta prueba si los errores reaparecen.",
        "- Corregir reglas de importacion/clasificacion de datos fuente antes de una recarga productiva.",
        "- Mantener Fase 5F-FIX como siguiente fase quirurgica para datos actuales, con backup y rollback.",
        "",
    ])
    md_path.write_text("\n".join(lines), encoding="utf-8")


def comparar(actual_db: Path = CURRENT_DB, reload_db: Path = RELOAD_DB) -> dict:
    actual_db = _resolver(actual_db)
    reload_db = _resolver(reload_db)
    if not actual_db.exists():
        raise FileNotFoundError(f"No existe BD actual: {actual_db}")
    if not reload_db.exists():
        raise FileNotFoundError(f"No existe BD reload: {reload_db}")
    if actual_db.resolve() == reload_db.resolve():
        raise ValueError("La BD actual y reload no pueden ser la misma ruta.")

    actual = medir_bd(actual_db, generar_reportes_reload=False)
    reload = medir_bd(reload_db, generar_reportes_reload=True)
    filas = escribir_comparacion(actual, reload, REPORTS_DIR / "comparacion_actual_vs_reload.csv")
    md_path = REPORTS_DIR / "FASE_5G_RELOAD_TEST.md"
    escribir_reporte(actual, reload, filas, md_path)
    markdown_to_pdf(md_path, REPORTS_DIR / "FASE_5G_RELOAD_TEST.pdf", "Fase 5G - Reload Test Paralelo")
    (REPORTS_DIR / "auditoria_reload_test.md").write_text(
        "\n".join([
            "# Auditoria Reload Test",
            "",
            "Auditorias read-only ejecutadas sobre supercheck_reload_test.db.",
            "",
            f"- Hallazgos categorias: {reload['hallazgos_categorias']}",
            f"- Hallazgos clasificacion masiva: {reload['hallazgos_clasificacion_masiva']}",
            f"- Alta confianza: {reload['hallazgos_alta_confianza']}",
            f"- Media confianza: {reload['hallazgos_media_confianza']}",
            f"- Conflictos producto_base: {reload['producto_base_conflictivos']}",
            "",
            "Detalle en reports/reload_test/.",
            "",
        ]),
        encoding="utf-8",
    )
    return {"actual": actual, "reload": reload, "decision": _decision(actual, reload)}


def main() -> int:
    parser = argparse.ArgumentParser(description="Compara supercheck.db contra supercheck_reload_test.db.")
    parser.add_argument("--actual-db", default=str(CURRENT_DB))
    parser.add_argument("--reload-db", default=str(RELOAD_DB))
    args = parser.parse_args()

    resultado = comparar(Path(args.actual_db), Path(args.reload_db))
    actual = resultado["actual"]
    reload = resultado["reload"]
    print("Comparacion actual vs reload completada.")
    print(f"productos_actual: {actual['productos']}")
    print(f"productos_reload: {reload['productos']}")
    print(f"hallazgos_actual: {actual['hallazgos_clasificacion_masiva']}")
    print(f"hallazgos_reload: {reload['hallazgos_clasificacion_masiva']}")
    print(f"pdf: {REPORTS_DIR / 'FASE_5G_RELOAD_TEST.pdf'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
