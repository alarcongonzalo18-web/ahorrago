# Fase 5B Reporte - AhorraGo

## Resumen Ejecutivo

La Fase 5B aplicó mejoras reales y controladas de matching únicamente en Mascotas y Limpieza. Se creó backup validado, se generó CSV de trazabilidad y se dejó rollback disponible.

Resultado principal: se actualizaron 502 productos, aumentando equivalencias en categorías objetivo de 698 a 924 y reduciendo conflictos de 234 a 163.

## Cambios Aplicados

- Productos modificados: 502
- Limpieza: 306 productos
- Mascotas: 196 productos
- Categorías bloqueadas respetadas.
- Base real modificada solo después de backup validado.

## Métricas Antes/Después

- Equivalencias: 698 -> 924
- Conflictos: 234 -> 163

Por categoría:

- Limpieza: equivalencias 451 -> 632, conflictos 166 -> 133.
- Mascotas: equivalencias 247 -> 292, conflictos 68 -> 30.

## Producto_base Actualizados

Los cambios están en:

- `reports/fase5b_cambios.csv`

Cada cambio incluye producto, producto_base anterior, producto_base nuevo, categoría y score.

## Rollback

Rollback disponible:

```powershell
python -m app.scripts.rollback_fase5b
```

Backup pre-aplicación:

- `backups/supercheck_pre_fase5b_20260531_215846.db`

## Riesgos

- Quedan grupos no aplicados por seguridad.
- Bebidas, Bebé e Higiene Personal no se aplicaron en esta fase.
- Se recomienda revisar manualmente cambios de alto impacto antes de continuar con más categorías.

## Recomendaciones

1. Monitorear resultados de Mascotas y Limpieza en `/diagnostico/matching`.
2. Preparar Fase 5C para Bebidas con lista blanca.
3. Mantener rollback y backups antes de cada aplicación real.
4. No aplicar categorías de alto riesgo hasta tener reglas específicas.

## Comandos Ejecutados

```powershell
python -m app.scripts.aplicar_matching_fase5b
python -m pytest -q
python -m compileall app tests
python -c "from app.main import app; print(app.title)"
```

## Resultado de Tests

- `40 passed`
- `compileall OK`
- `FastAPI`
