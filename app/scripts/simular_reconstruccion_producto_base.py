from __future__ import annotations

import csv
from collections import defaultdict
from pathlib import Path

from app import models
from app.database import SessionLocal
from app.matching import matching_score
from app.matching_diagnostics import REPORTS_DIR, proponer_producto_base


def _riesgo_grupo(productos: list[models.Producto]) -> str:
    if len(productos) <= 1:
        return "sin_equivalencia"
    scores = []
    for index, producto in enumerate(productos[:6]):
        for candidato in productos[index + 1:6]:
            scores.append(matching_score(producto, candidato))
    if not scores:
        return "bajo"
    minimo = min(scores)
    if minimo >= 80:
        return "bajo"
    if minimo >= 68:
        return "medio"
    return "alto_falso_positivo"


def simular(db) -> tuple[list[dict], dict]:
    productos = db.query(models.Producto).all()
    filas = []
    grupos_propuestos = defaultdict(list)

    for producto in productos:
        propuesto = proponer_producto_base(producto)
        grupos_propuestos[propuesto].append(producto)
        filas.append({
            "producto_id": producto.id,
            "nombre": producto.nombre,
            "marca": producto.marca or "",
            "formato": producto.formato or "",
            "producto_base_actual": producto.producto_base or "",
            "producto_base_propuesto": propuesto,
            "cambia": "si" if (producto.producto_base or "") != propuesto else "no",
        })

    riesgo_por_base = {base: _riesgo_grupo(items) for base, items in grupos_propuestos.items()}
    for fila in filas:
        fila["riesgo"] = riesgo_por_base[fila["producto_base_propuesto"]]

    total = len(filas)
    cambios = sum(1 for fila in filas if fila["cambia"] == "si")
    grupos_equivalentes = sum(1 for items in grupos_propuestos.values() if len(items) > 1)
    riesgos = defaultdict(int)
    for fila in filas:
        riesgos[fila["riesgo"]] += 1

    resumen = {
        "productos_evaluados": total,
        "producto_base_cambiaria": cambios,
        "porcentaje_cambio": round((cambios / total) * 100, 2) if total else 0,
        "grupos_propuestos": len(grupos_propuestos),
        "grupos_con_equivalencia_propuestos": grupos_equivalentes,
        "riesgo_bajo": riesgos["bajo"],
        "riesgo_medio": riesgos["medio"],
        "riesgo_alto_falso_positivo": riesgos["alto_falso_positivo"],
        "sin_equivalencia": riesgos["sin_equivalencia"],
    }
    return filas, resumen


def escribir_reportes(filas: list[dict], resumen: dict, reports_dir: Path = REPORTS_DIR) -> None:
    reports_dir.mkdir(parents=True, exist_ok=True)
    csv_path = reports_dir / "simulacion_producto_base.csv"
    with csv_path.open("w", newline="", encoding="utf-8-sig") as archivo:
        writer = csv.DictWriter(archivo, fieldnames=list(filas[0].keys()) if filas else [])
        if filas:
            writer.writeheader()
            writer.writerows(filas)

    lines = [
        "# Simulacion Producto Base - AhorraGo",
        "",
        "Modo: **DRY RUN**. No se modificaron datos reales.",
        "",
        "## Resumen",
        "",
    ]
    for clave, valor in resumen.items():
        lines.append(f"- {clave}: {valor}")
    lines.extend([
        "",
        "## Interpretacion",
        "",
        "- riesgo_bajo: grupos propuestos con scores consistentes.",
        "- riesgo_medio: requiere revision manual antes de aplicar.",
        "- riesgo_alto_falso_positivo: no aplicar automaticamente.",
        "- sin_equivalencia: producto seguiria sin agrupacion real.",
        "",
        "## Archivo CSV",
        "",
        "- reports/simulacion_producto_base.csv",
    ])
    (reports_dir / "simulacion_producto_base.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    db = SessionLocal()
    try:
        filas, resumen = simular(db)
        escribir_reportes(filas, resumen)
    finally:
        db.close()
    print("Simulacion de producto_base generada en reports/")
    print(f"Productos evaluados: {resumen['productos_evaluados']}")
    print(f"Producto_base cambiaria: {resumen['producto_base_cambiaria']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
