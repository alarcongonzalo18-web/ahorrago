from app.database import SessionLocal
from app.matching_diagnostics import diagnosticar_matching


def main() -> int:
    db = SessionLocal()
    try:
        resumen = diagnosticar_matching(db)
    finally:
        db.close()
    print("Diagnostico de matching generado en reports/")
    print(f"Producto_base conflictivos: {resumen['producto_base_conflictivos']}")
    print(f"Porcentaje sin equivalencia: {resumen['porcentaje_sin_equivalencia']}%")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
