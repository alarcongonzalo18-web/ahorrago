from pathlib import Path

from app.database import SessionLocal
from app.fase5b_apply import PROJECT_ROOT, crear_backup_pre_fase5b, leer_cambios
from app import models


def rollback_por_csv() -> int:
    cambios = leer_cambios()
    if not cambios:
        print("No hay reports/fase5b_cambios.csv para revertir")
        return 1

    backup = crear_backup_pre_fase5b()
    db = SessionLocal()
    revertidos = 0
    try:
        for cambio in cambios:
            producto = db.get(models.Producto, int(cambio["producto_id"]))
            if not producto:
                continue
            producto.producto_base = cambio["producto_base_anterior"]
            revertidos += 1
        db.commit()
    finally:
        db.close()

    print(f"Rollback Fase 5B aplicado. Productos revertidos: {revertidos}")
    print(f"Backup previo al rollback: {backup}")
    return 0


def main() -> int:
    return rollback_por_csv()


if __name__ == "__main__":
    raise SystemExit(main())
