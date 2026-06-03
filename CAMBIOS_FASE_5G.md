# Cambios Fase 5G - Reload Test Paralelo

Fecha: 2026-06-01

## Objetivo

Crear una BD paralela desde cero y comparar su calidad contra la BD actual sin modificar `supercheck.db`.

## Cambios Realizados

- Se creo `app/scripts/crear_bd_reload_test.py`.
- Se creo `app/scripts/comparar_bd_actual_vs_reload.py`.
- Se parametrizo `app/importar_csv.py` para aceptar `--db`.
- Se parametrizo `app/scripts/agregar_indices.py` para aceptar `--db`.
- Se creo `supercheck_reload_test.db` desde `data/productos_supermercados.csv`.
- Se agregaron tests de seguridad para BD paralela, importacion con destino y comparacion.

## Resultado

- Productos en BD actual: 31124.
- Productos en BD reload: 31124.
- Hallazgos clasificacion masiva actual: 1986.
- Hallazgos clasificacion masiva reload: 1986.
- Hallazgos alta confianza actual: 1639.
- Hallazgos alta confianza reload: 1683.
- Conflictos actual: 1545.
- Conflictos reload: 1605.

## Decision Tecnica

- La reload no mejora la calidad global.
- Los 1986 hallazgos reaparecen.
- El origen probable esta en datos fuente/importadores/reglas de clasificacion, no solo en la BD actual.
- No conviene reemplazar `supercheck.db` por la reload.
- Conviene corregir importadores/datos fuente y seguir con Fase 5F-FIX quirurgica.

## Archivos Generados

- `supercheck_reload_test.db`
- `reports/FASE_5G_RELOAD_TEST.md`
- `reports/FASE_5G_RELOAD_TEST.pdf`
- `reports/comparacion_actual_vs_reload.csv`
- `reports/auditoria_reload_test.md`
- `reports/reload_test/`

## Validacion

- `python -m app.scripts.crear_bd_reload_test`: OK.
- `python -m app.scripts.comparar_bd_actual_vs_reload`: OK.
- `python -m pytest -q`: 58 tests passing.
- `python -m compileall app tests`: OK.
- `python -c "from app.main import app; print(app.title)"`: FastAPI.

## Seguridad

- `supercheck.db` quedo intacta.
- No se ejecuto scraping masivo.
- No se aplicaron fixes sobre la BD actual.
- No se modifico frontend.
- No se crearon usuarios.
