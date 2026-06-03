from __future__ import annotations

import csv
from pathlib import Path

from sqlalchemy.orm import Session

from app import models
from app.database import SessionLocal
from app.scripts.aplicar_fix_categorias_fase5d import TRACE_CSV


def _categoria_subcategoria(db: Session, categoria: str, subcategoria: str) -> tuple[models.Categoria, models.Subcategoria]:
    categoria_obj = db.query(models.Categoria).filter(models.Categoria.nombre == categoria).one()
    subcategoria_obj = db.query(models.Subcategoria).filter(
        models.Subcategoria.categoria_id == categoria_obj.id,
        models.Subcategoria.nombre == subcategoria,
    ).one()
    return categoria_obj, subcategoria_obj


def cargar_trace(path: Path = TRACE_CSV) -> list[dict]:
    if not path.exists():
        raise RuntimeError(f"No existe CSV de trazabilidad: {path}")
    with path.open(newline="", encoding="utf-8-sig") as archivo:
        return list(csv.DictReader(archivo))


def aplicar_rollback(db: Session, trace_path: Path = TRACE_CSV) -> int:
    rows = cargar_trace(trace_path)
    revertidos = 0
    for row in rows:
        producto = db.get(models.Producto, int(row["producto_id"]))
        if not producto:
            continue
        categoria_obj, subcategoria_obj = _categoria_subcategoria(
            db,
            row["categoria_anterior"],
            row["subcategoria_anterior"],
        )
        ya_revertido = producto.categoria_id == categoria_obj.id and producto.subcategoria_id == subcategoria_obj.id
        if ya_revertido:
            continue
        producto.categoria_id = categoria_obj.id
        producto.subcategoria_id = subcategoria_obj.id
        revertidos += 1
    db.commit()
    return revertidos


def main() -> int:
    db = SessionLocal()
    try:
        revertidos = aplicar_rollback(db)
    finally:
        db.close()
    print("Rollback FASE 5D-FIX completado")
    print(f"Productos revertidos: {revertidos}")
    print(f"Trazabilidad usada: {TRACE_CSV}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
