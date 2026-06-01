# Cambios Fase 4 - AhorraGo

Fecha: 2026-05-31

## Objetivos

Mejorar la calidad de datos y aumentar equivalencias reales entre supermercados antes de crear usuarios, manteniendo todo en modo seguro:

- Sin usuarios.
- Sin login.
- Sin cambios de frontend.
- Sin migración de base de datos.
- Sin scraping masivo.
- Sin modificar datos reales.
- Con respaldo previo.
- Con simulación por defecto.

## Métricas Iniciales

- Productos: 31.124
- Precios: 31.139
- Producto_base conflictivos: 1.601
- Productos duplicados: 244
- Productos sospechosos: 3
- Equivalencias detectadas: 2.538
- Sin equivalencia: 79,94%

## Métricas Finales

La fase fue de diagnóstico y simulación, por lo que no cambió la base real.

- Total productos analizados: 31.124
- Producto_base únicos: 27.418
- Grupos con equivalencia: 2.538
- Porcentaje sin equivalencia recalculado por diagnóstico: 81,03%
- Producto_base conflictivos clasificados: 1.601
- Score promedio muestreado: 70,91
- Productos evaluados en simulación: 31.124
- Producto_base que cambiarían en simulación: 29.542
- Porcentaje de cambio simulado: 94,92%
- Grupos con equivalencia propuestos: 915
- Riesgo bajo: 2.001 productos
- Riesgo medio: 126 productos
- Riesgo alto de falso positivo: 2 productos

## Conflictos Encontrados

Clasificaciones más frecuentes:

- Formato y peso distinto: 856 grupos.
- Formato y volumen distinto: 659 grupos.
- Marca distinta: 21 grupos.
- Error de normalización con volumen distinto: 21 grupos.
- Sabor distinto con volumen distinto: 7 grupos.

## Categorías con Peor Matching

- Frutas y Verduras: 7,41% equivalencia.
- Congelados: 7,70% equivalencia.
- Panadería: 13,12% equivalencia.
- Desayuno y Snacks: 14,24% equivalencia.
- Carnes y Pescados: 14,90% equivalencia.

## Categorías con Mejor Matching

- Mascotas: 57,18% equivalencia.
- Bebidas: 28,01% equivalencia.
- Limpieza: 27,50% equivalencia.
- Bebé: 24,47% equivalencia.
- Higiene Personal: 23,35% equivalencia.

## Archivos Creados

- `app/matching_diagnostics.py`
- `app/scripts/diagnostico_matching.py`
- `app/scripts/simular_reconstruccion_producto_base.py`
- `tests/test_fase4_diagnostico.py`
- `reports/diagnostico_matching.md`
- `reports/conflictos_clasificados.csv`
- `reports/equivalencias_por_categoria.csv`
- `reports/grupos_sospechosos.csv`
- `reports/simulacion_producto_base.csv`
- `reports/simulacion_producto_base.md`
- `reports/FASE_4_REPORTE.md`
- `reports/FASE_4_REPORTE.pdf`
- `reports/AHORRAGO_MASTER_REPORT.pdf`
- `CAMBIOS_FASE_4.md`

## Archivos Modificados

- `app/main.py`
- `app/normalizacion.py`
- `tests/fixtures/productos_reales.json`
- `tests/test_integration.py`

## Scripts Creados

- `python -m app.scripts.diagnostico_matching`
- `python -m app.scripts.simular_reconstruccion_producto_base`

## Tests Agregados

- Clasificación de conflictos.
- Métricas por categoría.
- Simulación de reconstrucción sin modificar la base.
- Nuevas reglas de normalización.
- Falsos positivos y falsos negativos.
- Endpoint `/diagnostico/matching`.

## Seguridad de Datos

Se creó respaldo automático antes de la fase:

- `backups/supercheck_20260531_213244.db`

La simulación no modificó datos reales.

## Riesgos Pendientes

- El 94,92% de cambios propuestos en simulación indica que no debe aplicarse automáticamente.
- La simulación propone menos grupos con equivalencia que el estado actual; sirve para diagnóstico, no para migración directa.
- El mayor problema actual está en grupos `producto_base` demasiado amplios con formatos/pesos/volúmenes incompatibles.
- Se requiere revisión manual o reglas por categoría antes de cualquier limpieza real.

## Recomendaciones

1. No aplicar reconstrucción automática todavía.
2. Priorizar corrección de `producto_base` en bebidas, limpieza, mascotas y lácteos.
3. Crear una muestra etiquetada manualmente de 300 a 500 productos.
4. Ajustar reglas por categoría con métricas de precisión y recall.
5. Mantener `/diagnostico/matching` como endpoint interno antes de cambios de datos.
