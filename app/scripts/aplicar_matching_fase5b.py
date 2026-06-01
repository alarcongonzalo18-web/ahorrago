from app.database import SessionLocal
from app.fase5b_apply import (
    REPORTS,
    aplicar_cambios,
    crear_backup_pre_fase5b,
    escribir_cambios,
    escribir_validacion,
    metricas_fase5b,
    seleccionar_cambios,
)


def main() -> int:
    db = SessionLocal()
    backup = None
    try:
        antes = metricas_fase5b(db)
        cambios = seleccionar_cambios(db)
        if not cambios and (REPORTS / "fase5b_cambios.csv").exists():
            despues = antes
            print("Aplicacion Fase 5B sin cambios pendientes; se conservan reportes existentes")
            print("Cambios aplicados: 0")
            print(f"Equivalencias: {antes['TOTAL']['productos_equivalentes']} -> {despues['TOTAL']['productos_equivalentes']}")
            print(f"Conflictos: {antes['TOTAL']['conflictos']} -> {despues['TOTAL']['conflictos']}")
            return 0
        escribir_cambios(cambios)
        if cambios:
            backup = crear_backup_pre_fase5b()
            aplicar_cambios(db, cambios)
        despues = metricas_fase5b(db)
        escribir_validacion(antes, despues, cambios, backup)
    finally:
        db.close()

    print("Aplicacion Fase 5B completada")
    print(f"Cambios aplicados: {len(cambios)}")
    print(f"Equivalencias: {antes['TOTAL']['productos_equivalentes']} -> {despues['TOTAL']['productos_equivalentes']}")
    print(f"Conflictos: {antes['TOTAL']['conflictos']} -> {despues['TOTAL']['conflictos']}")
    if backup:
        print(f"Backup: {backup}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
