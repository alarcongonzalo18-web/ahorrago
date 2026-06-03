"""
Agrega indices a una BD SQLite existente sin regenerarla.

Uso:
    python -m app.scripts.agregar_indices
    python -m app.scripts.agregar_indices --db supercheck_reload_test.db
"""
from __future__ import annotations

import argparse
from pathlib import Path

from sqlalchemy import create_engine, text


ROOT = Path(__file__).resolve().parents[2]

INDICES = [
    ("ix_productos_nombre", "CREATE INDEX IF NOT EXISTS ix_productos_nombre ON productos (nombre)"),
    (
        "ix_productos_producto_base",
        "CREATE INDEX IF NOT EXISTS ix_productos_producto_base ON productos (producto_base)",
    ),
    ("ix_precios_producto_id", "CREATE INDEX IF NOT EXISTS ix_precios_producto_id ON precios (producto_id)"),
    (
        "ix_precios_supermercado_id",
        "CREATE INDEX IF NOT EXISTS ix_precios_supermercado_id ON precios (supermercado_id)",
    ),
]


def agregar_indices(db_path: Path) -> list[str]:
    if not db_path.exists():
        raise FileNotFoundError(f"No se encontro la BD en {db_path}")

    target_engine = create_engine(f"sqlite:///{db_path}", connect_args={"check_same_thread": False})
    with target_engine.connect() as conn:
        for nombre, sql in INDICES:
            conn.execute(text(sql))
            print(f"  OK {nombre}")
        conn.commit()

    with target_engine.connect() as conn:
        rows = conn.execute(
            text("SELECT name FROM sqlite_master WHERE type='index' AND tbl_name IN ('productos','precios')")
        ).fetchall()

    return sorted(idx for (idx,) in rows)


def main() -> int:
    parser = argparse.ArgumentParser(description="Agrega indices SQLite usados por AhorraGo.")
    parser.add_argument("--db", default=str(ROOT / "supercheck.db"))
    args = parser.parse_args()

    indices = agregar_indices(Path(args.db))
    print("\nIndices en productos y precios:")
    for idx in indices:
        print(f"  - {idx}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
