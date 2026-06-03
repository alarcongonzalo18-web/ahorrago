from __future__ import annotations

import argparse
import csv
from collections import Counter
from pathlib import Path

from app.category_validator import DEFAULT_REJECT_LOG, is_valid_row
from app.combinar_supermercados import (
    FUENTES,
    detectar_formato,
    detectar_marca,
    detectar_tipo,
    limpiar_precio,
    limpiar_precio_opcional,
)
from app.database import Base
from app.importar_csv import crear_session_local_para_db, importar_productos
from app.scripts.agregar_indices import agregar_indices
from app.scripts.comparar_bd_actual_vs_reload import _pct_delta, escribir_comparacion, medir_bd
from app.scripts.report_pdf import markdown_to_pdf


ROOT = Path(__file__).resolve().parents[2]
CURRENT_DB = ROOT / "supercheck.db"
RELOAD_V2_DB = ROOT / "supercheck_reload_v2.db"
REPORTS_DIR = ROOT / "reports"
RELOAD_V2_DIR = REPORTS_DIR / "reload_v2"
RELOAD_V2_CSV = RELOAD_V2_DIR / "productos_supermercados_v2.csv"
COMPARACION_CSV = REPORTS_DIR / "comparacion_actual_vs_reload_v2.csv"
REPORT_MD = REPORTS_DIR / "FASE_5J_RELOAD_V2.md"
REPORT_PDF = REPORTS_DIR / "FASE_5J_RELOAD_V2.pdf"


def _resolver(path: Path) -> Path:
    return path if path.is_absolute() else ROOT / path


def _limpiar_log_rechazos() -> None:
    if DEFAULT_REJECT_LOG.exists():
        DEFAULT_REJECT_LOG.unlink()


def _fila_normalizada(fila: dict, supermercado: str) -> dict:
    nombre = (fila.get("nombre") or "").strip()
    return {
        "categoria": (fila.get("categoria") or "").strip(),
        "subcategoria": (fila.get("subcategoria") or "").strip(),
        "nombre": nombre,
        "marca": detectar_marca(nombre),
        "tipo": detectar_tipo(nombre),
        "formato": detectar_formato(nombre),
        "precio": limpiar_precio(fila.get("precio_oferta") or fila.get("precio")),
        "precio_normal": limpiar_precio(fila.get("precio_normal") or fila.get("precio")),
        "precio_oferta": limpiar_precio_opcional(fila.get("precio_oferta")),
        "precio_referencia": (fila.get("precio_referencia") or "").strip(),
        "promocion": (fila.get("promocion") or "").strip(),
        "supermercado": supermercado,
        "url": (fila.get("url") or "").strip(),
        "imagen_url": (fila.get("imagen_url") or "").strip(),
        "producto_base": "",
    }


def generar_csv_reload_v2(output_csv: Path = RELOAD_V2_CSV, reset_rejection_log: bool = True) -> dict:
    if reset_rejection_log:
        _limpiar_log_rechazos()

    output_csv.parent.mkdir(parents=True, exist_ok=True)
    filas = []
    vistos = set()
    fuentes_leidas = Counter()

    for archivo, supermercado in FUENTES:
        path = _resolver(Path(archivo))
        if not path.exists():
            continue
        with path.open(newline="", encoding="utf-8-sig") as file:
            lector = csv.DictReader(file)
            for raw in lector:
                nombre = (raw.get("nombre") or "").strip()
                if not nombre:
                    continue
                fuentes_leidas[supermercado] += 1
                fila = _fila_normalizada(raw, supermercado)
                if not is_valid_row(fila, f"fase5j_reload_v2:{supermercado}", DEFAULT_REJECT_LOG):
                    continue
                key = (
                    fila["supermercado"],
                    fila["categoria"],
                    fila["subcategoria"],
                    fila["nombre"],
                    fila["precio"],
                )
                if key in vistos:
                    continue
                vistos.add(key)
                filas.append(fila)

    columnas = [
        "categoria",
        "subcategoria",
        "nombre",
        "marca",
        "tipo",
        "formato",
        "precio",
        "precio_normal",
        "precio_oferta",
        "precio_referencia",
        "promocion",
        "supermercado",
        "url",
        "imagen_url",
        "producto_base",
    ]
    with output_csv.open("w", newline="", encoding="utf-8-sig") as file:
        writer = csv.DictWriter(file, fieldnames=columnas)
        writer.writeheader()
        writer.writerows(filas)

    return {
        "csv_path": str(output_csv),
        "filas_aceptadas": len(filas),
        "fuentes_leidas": dict(fuentes_leidas),
    }


def crear_bd_reload_v2(db_path: Path = RELOAD_V2_DB, csv_path: Path = RELOAD_V2_CSV) -> dict:
    db_path = _resolver(db_path)
    csv_path = _resolver(csv_path)
    if db_path.resolve() == CURRENT_DB.resolve():
        raise ValueError("La reload v2 no puede apuntar a supercheck.db.")
    if not csv_path.exists():
        raise FileNotFoundError(f"No existe CSV reload v2: {csv_path}")

    if db_path.exists():
        db_path.unlink()
    session_factory, target_engine = crear_session_local_para_db(db_path)
    Base.metadata.create_all(bind=target_engine)
    filas_importadas = importar_productos(csv_path=csv_path, session_factory=session_factory, target_engine=target_engine)
    indices = agregar_indices(db_path)
    return {
        "db_path": str(db_path),
        "bytes": db_path.stat().st_size if db_path.exists() else 0,
        "filas_importadas": filas_importadas,
        "indices": len(indices),
    }


def analizar_rechazos(path: Path = DEFAULT_REJECT_LOG) -> dict:
    if not path.exists():
        return {
            "total": 0,
            "top_motivos": [],
            "top_marcas": [],
            "top_categorias_sugeridas": [],
        }
    with path.open(newline="", encoding="utf-8-sig") as file:
        rows = list(csv.DictReader(file))
    motivos = Counter(row.get("reason", "") for row in rows)
    marcas = Counter(detectar_marca(row.get("nombre", "")) for row in rows)
    sugeridas = Counter(
        f"{row.get('suggested_category', '')} > {row.get('suggested_subcategory', '')}".strip()
        for row in rows
    )
    return {
        "total": len(rows),
        "top_motivos": motivos.most_common(10),
        "top_marcas": marcas.most_common(10),
        "top_categorias_sugeridas": sugeridas.most_common(10),
    }


def _reduccion(actual: int, reload: int) -> float:
    if actual == 0:
        return 0.0
    return round(((actual - reload) / actual) * 100, 2)


def escribir_reporte(actual: dict, reload: dict, rechazos: dict, csv_info: dict, db_info: dict, filas_comparacion: list[dict]) -> None:
    hallazgos_actual = actual["hallazgos_clasificacion_masiva"]
    hallazgos_reload = reload["hallazgos_clasificacion_masiva"]
    mejor = hallazgos_reload < hallazgos_actual and reload["hallazgos_alta_confianza"] < actual["hallazgos_alta_confianza"]

    lines = [
        "# Fase 5J - Reload V2 Post-Hardening",
        "",
        "Modo seguro: no modifica `supercheck.db`, no reemplaza bases y no toca frontend/usuarios.",
        "",
        "## Resumen Ejecutivo",
        "",
        f"- Nueva BD: `supercheck_reload_v2.db`.",
        f"- CSV reload v2: `{Path(csv_info['csv_path']).as_posix()}`.",
        f"- Filas aceptadas por pipeline endurecido: {csv_info['filas_aceptadas']}.",
        f"- Filas importadas en reload v2: {db_info['filas_importadas']}.",
        f"- Productos actual: {actual['productos']}.",
        f"- Productos reload v2: {reload['productos']}.",
        f"- Hallazgos actuales: {hallazgos_actual}.",
        f"- Hallazgos reload v2: {hallazgos_reload}.",
        f"- Reduccion de hallazgos: {_reduccion(hallazgos_actual, hallazgos_reload)}%.",
        f"- Alta confianza actual: {actual['hallazgos_alta_confianza']}.",
        f"- Alta confianza reload v2: {reload['hallazgos_alta_confianza']}.",
        f"- Conflictos actual: {actual['conflictos']}.",
        f"- Conflictos reload v2: {reload['conflictos']}.",
        f"- Productos rechazados por validator: {rechazos['total']}.",
        "",
        "## Decision",
        "",
        f"- La nueva BD es mejor que la actual: {'SI' if mejor else 'NO'}.",
        "- Justificacion: se compara reduccion de hallazgos, alta confianza y conflictos; la decision de reemplazo requiere revisar cobertura y rechazos.",
        "",
        "## Comparacion",
        "",
        "| Metrica | Actual | Reload V2 | Diferencia | Diferencia % |",
        "|---|---:|---:|---:|---:|",
    ]
    for row in filas_comparacion:
        lines.append(
            f"| {row['metrica']} | {row['actual']} | {row['reload']} | {row['diferencia']} | {row['diferencia_porcentual']} |"
        )

    lines.extend(["", "## Rechazos - Top Motivos", ""])
    for motivo, cantidad in rechazos["top_motivos"]:
        lines.append(f"- {motivo}: {cantidad}")
    lines.extend(["", "## Rechazos - Top Marcas", ""])
    for marca, cantidad in rechazos["top_marcas"]:
        lines.append(f"- {marca}: {cantidad}")
    lines.extend(["", "## Rechazos - Top Categorias Sugeridas", ""])
    for categoria, cantidad in rechazos["top_categorias_sugeridas"]:
        lines.append(f"- {categoria}: {cantidad}")

    lines.extend([
        "",
        "## Recomendacion",
        "",
        "- Mantener BD actual hasta revisar rechazos y cobertura.",
        "- Ajustar validator solo si aparecen falsos positivos relevantes en rechazos.",
        "- Ejecutar Fase 5K para clasificar rechazos: corregir categoria, descartar o permitir con excepcion.",
        "- No reemplazar `supercheck.db` antes de validar cobertura funcional y matching sobre reload v2.",
        "",
        "## Archivos",
        "",
        "- `reports/FASE_5J_RELOAD_V2.md`",
        "- `reports/FASE_5J_RELOAD_V2.pdf`",
        "- `reports/comparacion_actual_vs_reload_v2.csv`",
        "- `reports/pipeline_category_rejections.csv`",
        "- `reports/reload_v2/`",
        "",
    ])
    REPORT_MD.write_text("\n".join(lines), encoding="utf-8")
    markdown_to_pdf(REPORT_MD, REPORT_PDF, "Fase 5J - Reload V2")


def ejecutar() -> dict:
    csv_info = generar_csv_reload_v2()
    db_info = crear_bd_reload_v2()
    actual = medir_bd(CURRENT_DB, generar_reportes_reload=False)
    reload = medir_bd(RELOAD_V2_DB, generar_reportes_reload=False)
    filas_comparacion = escribir_comparacion(actual, reload, COMPARACION_CSV)
    rechazos = analizar_rechazos()
    escribir_reporte(actual, reload, rechazos, csv_info, db_info, filas_comparacion)
    return {
        "actual": actual,
        "reload": reload,
        "rechazos": rechazos,
        "csv_info": csv_info,
        "db_info": db_info,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Ejecuta reload v2 post-hardening sobre BD paralela.")
    parser.parse_args()
    resultado = ejecutar()
    actual = resultado["actual"]
    reload = resultado["reload"]
    rechazos = resultado["rechazos"]
    print("Reload V2 Fase 5J completada.")
    print(f"productos_actual: {actual['productos']}")
    print(f"productos_reload_v2: {reload['productos']}")
    print(f"hallazgos_actual: {actual['hallazgos_clasificacion_masiva']}")
    print(f"hallazgos_reload_v2: {reload['hallazgos_clasificacion_masiva']}")
    print(f"rechazos_validator: {rechazos['total']}")
    print(f"pdf: {REPORT_PDF}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
