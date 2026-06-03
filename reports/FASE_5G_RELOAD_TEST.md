# Fase 5G - Reload Test Paralelo

Modo: comparacion controlada. No se modifica supercheck.db.

## Resumen Ejecutivo

- Productos en BD actual: 31124
- Productos en BD reload: 31124
- Hallazgos actuales: 1986
- Hallazgos reload: 1986
- Hallazgos alta confianza actual: 1639
- Hallazgos alta confianza reload: 1683
- Diferencia porcentual de hallazgos: 0.0%

## Decision Tecnica

- La BD recargada tiene menos errores que la actual: no
- Los errores reaparecen en la recarga: si
- Origen probable: scripts_datos_fuente
- Conviene reemplazar la BD actual: no
- Conviene arreglar importadores/datos fuente antes: si
- Conviene seguir con Fase 5F-FIX: si

## Comparacion

| Metrica | Actual | Reload | Diferencia | Diferencia % |
|---|---:|---:|---:|---:|
| productos | 31124 | 31124 | 0 | 0.0 |
| precios | 31139 | 31155 | 16 | 0.05 |
| categorias | 13 | 13 | 0 | 0.0 |
| subcategorias | 54 | 54 | 0 | 0.0 |
| producto_base_unicos | 27299 | 27400 | 101 | 0.37 |
| equivalencias | 2626 | 2550 | -76 | -2.89 |
| productos_con_equivalencia | 6451 | 6274 | -177 | -2.74 |
| productos_sin_equivalencia | 24673 | 24850 | 177 | 0.72 |
| conflictos | 1545 | 1605 | 60 | 3.88 |
| hallazgos_categorias | 0 | 89 | 89 | 100.0 |
| hallazgos_clasificacion_masiva | 1986 | 1986 | 0 | 0.0 |
| hallazgos_alta_confianza | 1639 | 1683 | 44 | 2.68 |
| hallazgos_media_confianza | 347 | 303 | -44 | -12.68 |
| productos_sospechosos | 3 | 3 | 0 | 0.0 |
| producto_base_conflictivos | 1545 | 1605 | 60 | 3.88 |

## Categorias Top Actual

- Lacteos, Huevos y Congelados: 5658
- Desayuno y Snacks: 4802
- Bebidas: 4274
- Despensa: 4038
- Higiene Personal: 2800
- Carnes y Pescados: 2060
- Congelados: 1960
- Limpieza: 1595
- Bebe: 1471
- Frutas y Verduras: 998

## Categorias Top Reload

- Lacteos, Huevos y Congelados: 5658
- Desayuno y Snacks: 4802
- Bebidas: 4274
- Despensa: 3998
- Higiene Personal: 2839
- Carnes y Pescados: 2060
- Congelados: 1960
- Limpieza: 1640
- Bebe: 1471
- Frutas y Verduras: 998

## Auditorias Ejecutadas Sobre Reload

- reports/reload_test/auditoria_categorias.md
- reports/reload_test/fase5f_clasificacion_masiva.md
- reports/reload_test/diagnostico_matching.md
- reports/reload_test/auditoria_datos.md

## Recomendacion

- No reemplazar supercheck.db solo por esta prueba si los errores reaparecen.
- Corregir reglas de importacion/clasificacion de datos fuente antes de una recarga productiva.
- Mantener Fase 5F-FIX como siguiente fase quirurgica para datos actuales, con backup y rollback.
