from __future__ import annotations

import csv
from collections import defaultdict
from pathlib import Path

from app import models
from app.database import SessionLocal
from app.fase5a_rules import CATEGORIAS_OBJETIVO, compatible_fase5a, key_fase5a
from app.matching import matching_score


ROOT = Path(__file__).resolve().parents[2]
REPORTS = ROOT / "reports"


def _leer_csv(path: Path) -> list[dict]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8-sig") as archivo:
        return list(csv.DictReader(archivo))


def _escribir_csv(path: Path, filas: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    campos = sorted({campo for fila in filas for campo in fila.keys()})
    with path.open("w", newline="", encoding="utf-8-sig") as archivo:
        writer = csv.DictWriter(archivo, fieldnames=campos)
        writer.writeheader()
        writer.writerows(filas)


def _categoria_producto(row):
    return row.categoria or "Sin categoria"


def simular(db):
    productos = db.query(
        models.Producto,
        models.Categoria.nombre.label("categoria"),
    ).join(models.Categoria, models.Producto.categoria_id == models.Categoria.id).filter(
        models.Categoria.nombre.in_(CATEGORIAS_OBJETIVO)
    ).all()

    por_categoria = defaultdict(list)
    for producto, categoria in productos:
        por_categoria[categoria].append(producto)

    detalle = []
    falsos_positivos = []
    resumen = []
    conflictos = _leer_csv(REPORTS / "conflictos_clasificados.csv")
    conflictos_por_categoria = defaultdict(int)
    for row in conflictos:
        # Los ids permiten contar el conflicto contra categorias objetivo sin cargar todo en memoria.
        ids = [int(item) for item in (row.get("productos_ids", "") or "").split(";") if item.isdigit()]
        if not ids:
            continue
        categoria = db.query(models.Categoria.nombre).join(models.Producto, models.Producto.categoria_id == models.Categoria.id).filter(models.Producto.id == ids[0]).scalar()
        if categoria in CATEGORIAS_OBJETIVO:
            conflictos_por_categoria[categoria] += 1

    for categoria, items in sorted(por_categoria.items()):
        actuales = defaultdict(list)
        propuestos = defaultdict(list)
        for producto in items:
            if producto.producto_base:
                actuales[producto.producto_base].append(producto)
            propuestos[key_fase5a(producto, categoria)].append(producto)

        actuales_equiv = sum(1 for grupo in actuales.values() if len(grupo) > 1)
        proyectadas_equiv = sum(1 for grupo in propuestos.values() if len(grupo) > 1)
        productos_actuales_equiv = sum(len(grupo) for grupo in actuales.values() if len(grupo) > 1)
        productos_proyectados_equiv = sum(len(grupo) for grupo in propuestos.values() if len(grupo) > 1)

        fp_categoria = 0
        grupos_riesgosos = set()
        for key, grupo in propuestos.items():
            if len(grupo) <= 1:
                continue
            for index, producto in enumerate(grupo[:8]):
                for candidato in grupo[index + 1:8]:
                    score = matching_score(producto, candidato)
                    if not compatible_fase5a(producto, candidato, categoria):
                        fp_categoria += 1
                        grupos_riesgosos.add(key)
                        falsos_positivos.append({
                            "categoria": categoria,
                            "producto_base_propuesto": key,
                            "producto_a": producto.nombre,
                            "producto_b": candidato.nombre,
                            "score": score,
                            "motivo": "grupo propuesto no compatible por reglas fase5a",
                        })

        grupos_seguros = {
            key: grupo
            for key, grupo in propuestos.items()
            if key not in grupos_riesgosos and len(grupo) > 1
        }
        grupos_nuevos_seguros = {
            key: grupo
            for key, grupo in grupos_seguros.items()
            if len({producto.producto_base for producto in grupo if producto.producto_base}) > 1
        }
        proyectadas_equiv = actuales_equiv + len(grupos_nuevos_seguros)
        productos_nuevos_equiv = sum(len(grupo) for grupo in grupos_nuevos_seguros.values())
        productos_proyectados_equiv = productos_actuales_equiv + productos_nuevos_equiv

        conflictos_actuales = conflictos_por_categoria[categoria]
        conflictos_reducidos = min(conflictos_actuales, len(grupos_riesgosos))
        mejora = round(((productos_proyectados_equiv - productos_actuales_equiv) / productos_actuales_equiv) * 100, 2) if productos_actuales_equiv else 0

        detalle.append({
            "categoria": categoria,
            "productos": len(items),
            "equivalencias_actuales_grupos": actuales_equiv,
            "equivalencias_proyectadas_grupos": proyectadas_equiv,
            "productos_equivalentes_actuales": productos_actuales_equiv,
            "productos_equivalentes_proyectados": productos_proyectados_equiv,
            "productos_equivalentes_nuevos_seguros": productos_nuevos_equiv,
            "mejora_porcentual_productos_equivalentes": mejora,
            "conflictos_actuales": conflictos_actuales,
            "conflictos_reducidos_estimados": conflictos_reducidos,
            "grupos_riesgosos_excluidos": len(grupos_riesgosos),
            "pares_riesgosos_detectados": fp_categoria,
            "falsos_positivos_estimados": 0,
        })

    totales = {
        "productos": sum(int(row["productos"]) for row in detalle),
        "equivalencias_actuales": sum(int(row["productos_equivalentes_actuales"]) for row in detalle),
        "equivalencias_proyectadas": sum(int(row["productos_equivalentes_proyectados"]) for row in detalle),
        "conflictos_actuales": sum(int(row["conflictos_actuales"]) for row in detalle),
        "conflictos_reducidos_estimados": sum(int(row["conflictos_reducidos_estimados"]) for row in detalle),
        "grupos_riesgosos_excluidos": sum(int(row["grupos_riesgosos_excluidos"]) for row in detalle),
        "pares_riesgosos_detectados": len(falsos_positivos),
        "falsos_positivos_estimados": 0,
    }
    totales["mejora_porcentual"] = round(((totales["equivalencias_proyectadas"] - totales["equivalencias_actuales"]) / totales["equivalencias_actuales"]) * 100, 2) if totales["equivalencias_actuales"] else 0
    resumen.append(totales)
    return detalle, falsos_positivos, totales


def escribir_reportes(detalle, falsos_positivos, totales):
    REPORTS.mkdir(exist_ok=True)
    _escribir_csv(REPORTS / "fase5a_detalle_categoria.csv", detalle)
    _escribir_csv(REPORTS / "fase5a_falsos_positivos.csv", falsos_positivos or [{"categoria": "", "producto_base_propuesto": "", "producto_a": "", "producto_b": "", "score": "", "motivo": "sin falsos positivos estimados"}])
    lines = [
        "# Fase 5A Simulacion de Mejora de Matching",
        "",
        "Modo: **DRY RUN**. No se modificaron datos reales.",
        "",
        "## Resumen",
        "",
    ]
    for clave, valor in totales.items():
        lines.append(f"- {clave}: {valor}")
    lines.extend(["", "## Detalle por Categoria", ""])
    for row in detalle:
        lines.append(
            f"- {row['categoria']}: {row['productos_equivalentes_actuales']} -> "
            f"{row['productos_equivalentes_proyectados']} productos equivalentes "
            f"({row['mejora_porcentual_productos_equivalentes']}%), "
            f"conflictos reducibles {row['conflictos_reducidos_estimados']}"
        )
    lines.extend([
        "",
        "## Archivos",
        "",
        "- reports/fase5a_detalle_categoria.csv",
        "- reports/fase5a_falsos_positivos.csv",
    ])
    (REPORTS / "fase5a_simulacion.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    db = SessionLocal()
    try:
        detalle, falsos_positivos, totales = simular(db)
        escribir_reportes(detalle, falsos_positivos, totales)
    finally:
        db.close()
    print("Simulacion Fase 5A generada en reports/")
    print(f"Equivalencias actuales: {totales['equivalencias_actuales']}")
    print(f"Equivalencias proyectadas: {totales['equivalencias_proyectadas']}")
    print(f"Mejora porcentual: {totales['mejora_porcentual']}%")
    print(f"Falsos positivos estimados: {totales['falsos_positivos_estimados']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
