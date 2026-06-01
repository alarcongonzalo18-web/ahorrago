# Cambios Fase 5B - AhorraGo

Fecha: 2026-05-31

## Objetivo

Aplicar de forma real y controlada mejoras de matching únicamente para:

- Mascotas
- Limpieza

No se modificaron Bebidas, Bebé, Higiene Personal, Frutas y Verduras, Congelados, Panadería ni Carnes y Pescados.

## Seguridad

Se creó backup completo y validado antes de aplicar cambios:

- `backups/supercheck_pre_fase5b_20260531_215846.db`

También existe rollback:

- `app/scripts/rollback_fase5b.py`

El rollback usa `reports/fase5b_cambios.csv` para restaurar el `producto_base` anterior de cada producto modificado.

## Cambios Aplicados

- Productos modificados: 502
- Categorías afectadas:
  - Limpieza: 306 productos
  - Mascotas: 196 productos
- Archivo de trazabilidad:
  - `reports/fase5b_cambios.csv`

Cada fila registra:

- `producto_id`
- `producto_original`
- `producto_base_anterior`
- `producto_base_nuevo`
- `categoria`
- `score_matching`

## Métricas Antes y Después

Métricas para Mascotas y Limpieza:

- Equivalencias: 698 -> 924
- Conflictos: 234 -> 163

Detalle:

- Limpieza:
  - Equivalencias: 451 -> 632
  - Conflictos: 166 -> 133
- Mascotas:
  - Equivalencias: 247 -> 292
  - Conflictos: 68 -> 30

## Archivos Creados

- `app/fase5b_apply.py`
- `app/scripts/aplicar_matching_fase5b.py`
- `app/scripts/rollback_fase5b.py`
- `tests/test_fase5b_apply.py`
- `reports/fase5b_cambios.csv`
- `reports/fase5b_validacion.md`
- `reports/FASE_5B_REPORTE.md`
- `reports/FASE_5B_REPORTE.pdf`
- `CAMBIOS_FASE_5B.md`

## Archivos Modificados

- `app/matching_diagnostics.py`
- `app/scripts/aplicar_matching_fase5b.py`

## Tests

Se agregaron tests para:

- Categorías permitidas.
- Categorías bloqueadas.
- Selección segura.
- Exclusión de grupos riesgosos.
- Aplicación por lote.
- Métricas antes/después.
- Rollback lógico.
- Idempotencia.

Resultado:

- `40 passed`

## Riesgos Pendientes

- La mejora se aplicó solo a grupos seguros. Quedan grupos de Mascotas/Limpieza que requieren revisión manual.
- El rollback existe, pero debe ejecutarse manualmente si se quiere revertir.
- Las categorías no incluidas en Fase 5B siguen pendientes.

## Recomendación Fase 5C

Continuar con aplicación controlada para Bebidas, pero con reglas más estrictas para zero/normal, retornable/no retornable, sabores y packs. Antes de aplicar, generar lista blanca y validar manualmente los grupos con mayor impacto.
