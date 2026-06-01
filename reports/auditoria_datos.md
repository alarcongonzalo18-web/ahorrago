# Auditoria de Datos - AhorraGo

## Resumen Ejecutivo

- Calidad estimada de datos: **Baja**.
- Productos totales: 31124.
- Precios totales: 31139.
- Productos sospechosos detectados: 3.
- Producto_base conflictivos: 1601.

## Conteos Base

- productos_totales: 31124
- precios_totales: 31139
- supermercados: 3
- categorias: 13
- subcategorias: 54
- productos_sin_precio: 0
- productos_duplicados: 244
- productos_sospechosos: 3
- producto_base_conflictivos: 1601

## Metricas de Matching

- porcentaje_productos_agrupados: 100.0
- porcentaje_sin_equivalencia: 79.94
- cantidad_promedio_equivalencias_por_producto_base: 1.14
- supermercados_cubiertos: 3
- supermercados_con_precio: Jumbo, Líder, Unimarc
- grupos_producto_base: 27418
- grupos_con_equivalencia: 2538

## Riesgos Encontrados

- precio extremadamente alto: 3

## Archivos Generados

- reports/auditoria_datos.md
- reports/productos_duplicados.csv
- reports/productos_sospechosos.csv
- reports/producto_base_conflictivos.csv

## Recomendaciones

- Revisar primero `producto_base_conflictivos.csv`, porque afecta directamente la precision del comparador.
- Corregir productos sin precio o sin supermercado antes de agregar funcionalidades de usuarios.
- Validar manualmente grupos grandes de `producto_base` antes de usarlos para recomendaciones.
- Mantener esta auditoria como paso obligatorio antes de cambios grandes en datos.

## Nota

Esta auditoria no modifica datos. Solo lee la base y genera reportes.
