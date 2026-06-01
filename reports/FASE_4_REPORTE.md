# Fase 4 Reporte - AhorraGo

## Resumen Ejecutivo

La Fase 4 auditó y diagnosticó la calidad del matching de productos sin modificar datos reales. Se creó un respaldo de la base, se clasificaron conflictos existentes, se calcularon métricas por categoría, se simuló una posible reconstrucción de `producto_base` y se agregó un endpoint interno de diagnóstico.

Resultado principal: la calidad de datos requiere limpieza controlada antes de crear funcionalidades de usuarios. El mayor riesgo no está en productos sin precio, sino en grupos `producto_base` conflictivos.

## Estado Inicial

- Productos: 31.124
- Precios: 31.139
- Producto_base conflictivos: 1.601
- Productos duplicados: 244
- Productos sospechosos: 3
- Equivalencias detectadas: 2.538
- Sin equivalencia: 79,94%

## Estado Final

No se modificó la base real. El estado final corresponde a reportes y simulación:

- Producto_base únicos: 27.418
- Grupos con equivalencia: 2.538
- Porcentaje sin equivalencia recalculado: 81,03%
- Score promedio muestreado: 70,91
- Producto_base conflictivos clasificados: 1.601
- Productos evaluados en simulación: 31.124
- Producto_base que cambiarían en simulación: 29.542
- Riesgo alto de falso positivo: 2 productos

## Cambios Aplicados

- Se creó diagnóstico avanzado de matching.
- Se clasificaron conflictos por marca, formato, volumen, peso, cantidad, sabor, categoría y normalización.
- Se calcularon métricas por categoría.
- Se creó simulación de reconstrucción de `producto_base` en modo DRY RUN.
- Se agregó endpoint interno `GET /diagnostico/matching`.
- Se ampliaron fixtures reales.
- Se agregaron tests de diagnóstico, simulación y endpoint.

## Auditoría de Datos

La auditoría previa identificó:

- 0 productos sin precio.
- 244 productos duplicados.
- 3 precios extremadamente altos.
- 1.601 grupos conflictivos de `producto_base`.

La Fase 4 profundizó esos conflictos y los clasificó para priorizar limpieza.

## Matching

Peor matching:

- Frutas y Verduras: 7,41%
- Congelados: 7,70%
- Panadería: 13,12%
- Desayuno y Snacks: 14,24%
- Carnes y Pescados: 14,90%

Mejor matching:

- Mascotas: 57,18%
- Bebidas: 28,01%
- Limpieza: 27,50%
- Bebé: 24,47%
- Higiene Personal: 23,35%

## Calidad de Datos

La calidad actual es útil para MVP, pero todavía riesgosa para funcionalidades de usuarios como favoritos, alertas o historial, porque esas funciones dependen de equivalencias estables.

## Base de Datos

No se modificó la base. Se creó respaldo:

- `backups/supercheck_20260531_213244.db`

## Tests

Comandos ejecutados:

```powershell
python -m pytest -q
python -m compileall app tests
python -c "from app.main import app; print(app.title)"
python -m app.scripts.diagnostico_matching
python -m app.scripts.simular_reconstruccion_producto_base
```

Resultado:

- `26 passed`
- `compileall OK`
- `FastAPI`

## Riesgos

- No aplicar la reconstrucción simulada automáticamente.
- Los grupos conflictivos por formato/peso/volumen pueden distorsionar recomendaciones de ahorro.
- Se necesita validación humana por categoría.

## Recomendaciones

1. Crear dataset etiquetado manualmente.
2. Resolver primero grupos con formato incompatible.
3. Diseñar reglas por categoría.
4. Mantener todo cambio de `producto_base` con DRY RUN y respaldo.

## Próximos Pasos

- Fase 5: limpieza controlada de `producto_base` por categoría.
- Priorizar bebidas, limpieza, mascotas y lácteos.
- Crear reportes de precisión/recall por categoría.

## Comandos Ejecutados

```powershell
python -m app.scripts.diagnostico_matching
python -m app.scripts.simular_reconstruccion_producto_base
python -m pytest -q
python -m compileall app tests
python -c "from app.main import app; print(app.title)"
```
