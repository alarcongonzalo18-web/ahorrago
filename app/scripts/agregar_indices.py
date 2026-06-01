"""
Agrega índices a la BD SQLite existente sin regenerarla.
Uso: python -m app.scripts.agregar_indices
"""
from pathlib import Path
from sqlalchemy import text
from app.database import engine

INDICES = [
    ("ix_productos_nombre",    "CREATE INDEX IF NOT EXISTS ix_productos_nombre    ON productos (nombre)"),
    ("ix_productos_producto_base", "CREATE INDEX IF NOT EXISTS ix_productos_producto_base ON productos (producto_base)"),
    ("ix_precios_producto_id", "CREATE INDEX IF NOT EXISTS ix_precios_producto_id ON precios (producto_id)"),
    ("ix_precios_supermercado_id", "CREATE INDEX IF NOT EXISTS ix_precios_supermercado_id ON precios (supermercado_id)"),
]

def main():
    db_path = Path(__file__).resolve().parents[2] / "supercheck.db"
    if not db_path.exists():
        print(f"No se encontró la BD en {db_path}")
        return

    with engine.connect() as conn:
        for nombre, sql in INDICES:
            conn.execute(text(sql))
            print(f"  OK {nombre}")
        conn.commit()

    with engine.connect() as conn:
        indices = conn.execute(
            text("SELECT name FROM sqlite_master WHERE type='index' AND tbl_name IN ('productos','precios')")
        ).fetchall()

    print("\nÍndices en productos y precios:")
    for (idx,) in sorted(indices):
        print(f"  - {idx}")

if __name__ == "__main__":
    main()
