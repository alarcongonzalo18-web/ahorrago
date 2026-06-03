from __future__ import annotations

import argparse
from pathlib import Path

from app.database import Base
from app.importar_csv import crear_session_local_para_db, importar_productos
from app.scripts.agregar_indices import agregar_indices


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DB = ROOT / "supercheck_reload_test.db"
CURRENT_DB = ROOT / "supercheck.db"
DEFAULT_CSV = ROOT / "data" / "productos_supermercados.csv"


def _resolver(path: Path) -> Path:
    return path if path.is_absolute() else ROOT / path


def crear_bd_reload_test(db_path: Path = DEFAULT_DB, csv_path: Path = DEFAULT_CSV) -> dict:
    db_path = _resolver(db_path)
    csv_path = _resolver(csv_path)
    actual = CURRENT_DB.resolve()
    destino = db_path.resolve()

    if destino == actual:
        raise ValueError("La BD reload no puede apuntar a supercheck.db.")
    if not csv_path.exists():
        raise FileNotFoundError(f"No existe el CSV local requerido: {csv_path}")

    db_path.parent.mkdir(parents=True, exist_ok=True)
    if db_path.exists():
        db_path.unlink()

    session_factory, target_engine = crear_session_local_para_db(db_path)
    Base.metadata.create_all(bind=target_engine)
    filas = importar_productos(csv_path=csv_path, session_factory=session_factory, target_engine=target_engine)
    indices = agregar_indices(db_path)

    return {
        "db_path": str(db_path),
        "csv_path": str(csv_path),
        "filas_csv_procesadas": filas,
        "bytes": db_path.stat().st_size if db_path.exists() else 0,
        "indices": len(indices),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Crea una BD paralela de reload test para AhorraGo.")
    parser.add_argument("--db", default=str(DEFAULT_DB), help="Ruta de BD reload destino.")
    parser.add_argument("--csv", default=str(DEFAULT_CSV), help="CSV local a importar.")
    args = parser.parse_args()

    resultado = crear_bd_reload_test(Path(args.db), Path(args.csv))
    print("BD reload creada correctamente.")
    for clave, valor in resultado.items():
        print(f"{clave}: {valor}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
