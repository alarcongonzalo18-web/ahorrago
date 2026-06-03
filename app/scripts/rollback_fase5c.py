from __future__ import annotations

from app import models
from app.database import SessionLocal
from app.scripts.aplicar_matching_fase5c import crear_backup_pre_fase5c, leer_cambios


def rollback_por_csv() -> int:
    cambios = leer_cambios()
    if not cambios:
        print("No hay reports/fase5c_cambios.csv para revertir")
        return 1

    backup = crear_backup_pre_fase5c()
    db = SessionLocal()
    revertidos = 0
    try:
        for cambio in cambios:
            producto = db.get(models.Producto, int(cambio["producto_id"]))
            if not producto:
                continue
            if (producto.producto_base or "") == (cambio["producto_base_anterior"] or ""):
                continue
            producto.producto_base = cambio["producto_base_anterior"]
            revertidos += 1
        db.commit()
    finally:
        db.close()

    print(f"Rollback Fase 5C aplicado. Productos revertidos: {revertidos}")
    print(f"Backup previo al rollback: {backup}")
    return 0


def main() -> int:
    return rollback_por_csv()


if __name__ == "__main__":
    raise SystemExit(main())
