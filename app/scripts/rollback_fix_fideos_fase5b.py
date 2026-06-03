from __future__ import annotations

import csv
from pathlib import Path

from sqlalchemy.orm import Session

from app import models
from app.database import SessionLocal
from app.scripts.fix_fideos_limpieza_fase5b import EXPECTED_IDS, TRACE_CSV


def _categoria_subcategoria(db: Session, categoria: str, subcategoria: str) -> tuple[models.Categoria, models.Subcategoria]:
    categoria_obj = db.query(models.Categoria).filter(models.Categoria.nombre == categoria).one()
    subcategoria_obj = db.query(models.Subcategoria).filter(
        models.Subcategoria.categoria_id == categoria_obj.id,
        models.Subcategoria.nombre == subcategoria,
    ).one()
    return categoria_obj, subcategoria_obj


def cargar_trace(path: Path = TRACE_CSV) -> dict[int, dict]:
    if not path.exists():
        raise RuntimeError(f"No existe CSV de trazabilidad: {path}")
    with path.open(newline="", encoding="utf-8-sig") as archivo:
        rows = {int(row["producto_id"]): row for row in csv.DictReader(archivo)}
    if set(rows) != EXPECTED_IDS:
        raise RuntimeError("El CSV de trazabilidad no coincide con los 25 IDs esperados")
    return rows


def aplicar_rollback(db: Session, trace_path: Path = TRACE_CSV) -> int:
    trace = cargar_trace(trace_path)
    revertidos = 0

    for producto_id in sorted(EXPECTED_IDS):
        row = trace[producto_id]
        categoria, subcategoria = _categoria_subcategoria(
            db,
            row["categoria_anterior"],
            row["subcategoria_anterior"],
        )
        producto = db.get(models.Producto, producto_id)
        if not producto:
            continue
        ya_revertido = (
            producto.categoria_id == categoria.id
            and producto.subcategoria_id == subcategoria.id
            and (producto.producto_base or "") == row["producto_base_anterior"]
        )
        if not ya_revertido:
            producto.categoria_id = categoria.id
            producto.subcategoria_id = subcategoria.id
            producto.producto_base = row["producto_base_anterior"]
            revertidos += 1

    db.commit()
    return revertidos


def main() -> int:
    db = SessionLocal()
    try:
        revertidos = aplicar_rollback(db)
    finally:
        db.close()
    print("Rollback FASE 5B-FIX completado")
    print(f"Productos revertidos: {revertidos}")
    print(f"Trazabilidad actualizada: {TRACE_CSV}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
