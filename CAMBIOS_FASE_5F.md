# Cambios Fase 5F - Auditoria Masiva Read Only

Fecha: 2026-06-01

## Objetivo

Detectar y clasificar errores masivos de categoria/subcategoria antes de usuarios, sin modificar datos.

## Modo

- READ ONLY.
- No se modifico base de datos.
- No se modifico producto_base.
- No se modificaron categorias ni subcategorias.
- No se toco frontend, usuarios ni scraping.

## Resultado

- Hallazgos totales: 1986.
- Alta confianza: 1639.
- Media confianza: 347.
- Baja confianza: 0.
- Falso positivo probable: 0.

## Categorias Mas Afectadas

- Bebe: 627
- Desayuno y Snacks: 407
- Lacteos, Huevos y Congelados: 391
- Carnes y Pescados: 213
- Congelados: 104
- Despensa: 99
- Bebidas: 75
- Mascotas: 44
- Frutas y Verduras: 17
- Limpieza: 3

## Motivos Principales

- Producto de mascotas fuera de Mascotas: 657
- Producto de higiene personal fuera de Higiene Personal: 457
- Bebida detectada dentro de categoria Bebe: 416
- Bebida fuera de Bebidas: 298
- Snack/fruto seco detectado dentro de categoria Bebe: 126
- Producto de limpieza fuera de Limpieza: 27
- Producto de limpieza detectado dentro de categoria Bebe: 5

## Productos Criticos Alta Confianza

| ID | Producto | Actual | Sugerida | Motivo |
|---:|---|---|---|---|
| 56 | Bebida Leche Láctea Yogu Yogu Chirimoya Caja | Bebe > Alimentos Bebe | Bebidas > Bebidas | Bebida detectada dentro de categoria Bebe |
| 132 | Bebida Leche Láctea Yogu Yogu Mora Caja | Bebe > Alimentos Bebe | Bebidas > Bebidas | Bebida detectada dentro de categoria Bebe |
| 148 | Bebida Leche Láctea Yogu Yogu Damasco Caja | Bebe > Alimentos Bebe | Bebidas > Bebidas | Bebida detectada dentro de categoria Bebe |
| 149 | Bebida Leche Láctea Yogu Yogu Frutilla Caja | Bebe > Alimentos Bebe | Bebidas > Bebidas | Bebida detectada dentro de categoria Bebe |
| 150 | Bebida Leche Láctea Yogu Yogu Piña Caja | Bebe > Alimentos Bebe | Bebidas > Bebidas | Bebida detectada dentro de categoria Bebe |
| 151 | Bebida Leche Láctea Trencito Chocolate Caja | Bebe > Alimentos Bebe | Bebidas > Bebidas | Bebida detectada dentro de categoria Bebe |
| 199 | Bebida Vegetal Notmilk Protein Con 7gr Proteína 750 ml NotCo | Bebe > Alimentos Bebe | Bebidas > Bebidas | Bebida detectada dentro de categoria Bebe |
| 213 | Bebida Láctea Sin Lactosa Chocolate 200 ml Milo | Bebe > Alimentos Bebe | Bebidas > Bebidas | Bebida detectada dentro de categoria Bebe |
| 217 | Bebida Vegetal Notmilk Chocolate Tetra Pak 200 ml NotCo | Bebe > Alimentos Bebe | Bebidas > Bebidas | Bebida detectada dentro de categoria Bebe |
| 218 | Bebida Vegetal Notmilk Original 1 L NotCo | Bebe > Alimentos Bebe | Bebidas > Bebidas | Bebida detectada dentro de categoria Bebe |
| 220 | Bebida Láctea Sabor Frutilla 200 ml Surlat | Bebe > Alimentos Bebe | Bebidas > Bebidas | Bebida detectada dentro de categoria Bebe |
| 221 | Bebida Láctea Sabor Chocolate 200 ml Surlat | Bebe > Alimentos Bebe | Bebidas > Bebidas | Bebida detectada dentro de categoria Bebe |
| 222 | Bebida Láctea Sabor Vainilla 200 ml Surlat | Bebe > Alimentos Bebe | Bebidas > Bebidas | Bebida detectada dentro de categoria Bebe |
| 225 | Bebida Vegetal Notmilk Zero 1 L NotCo | Bebe > Alimentos Bebe | Bebidas > Bebidas | Bebida detectada dentro de categoria Bebe |
| 226 | Bebida Vegetal Notmilk Low Fat 1 L NotCo | Bebe > Alimentos Bebe | Bebidas > Bebidas | Bebida detectada dentro de categoria Bebe |
| 228 | Bebida Vegetal Original 1 L Nature's Heart | Bebe > Alimentos Bebe | Bebidas > Bebidas | Bebida detectada dentro de categoria Bebe |
| 246 | Chocolate Lenguas De Gato Leche 120 g Costa | Lacteos, Huevos y Congelados > Leche | Mascotas > Alimento Gatos | Producto de mascotas fuera de Mascotas |
| 286 | Galletas Cachorro Raza Grande Sabor Leche Bolsa 500 g Master Dog | Desayuno y Snacks > Snacks | Mascotas > Alimento Perros | Producto de mascotas fuera de Mascotas |
| 300 | Alimento Seco Cachorro Raza Pequeña Carne Y Leche Bolsa 3 Kg Master Dog | Carnes y Pescados > Carnes | Mascotas > Alimento Perros | Producto de mascotas fuera de Mascotas |
| 306 | Alimento Seco Cachorro Raza Mediana/grande Sabor Carne Y Leche Bolsa 3 Kg Master Dog | Carnes y Pescados > Carnes | Mascotas > Alimento Perros | Producto de mascotas fuera de Mascotas |
| 310 | Galleta Perro Cachoro Leche g g Pet Food | Desayuno y Snacks > Snacks | Mascotas > Alimento Perros | Producto de mascotas fuera de Mascotas |
| 339 | Tónico Rose Care Leche & Tonico Micelar 2 En 1 200 ml Nivea | Lacteos, Huevos y Congelados > Leche | Higiene Personal > Cuidado Facial | Producto de higiene personal fuera de Higiene Personal |
| 429 | Bebida Vegetal Notmilk Chocolate 1 L NotCo | Bebe > Alimentos Bebe | Bebidas > Bebidas | Bebida detectada dentro de categoria Bebe |
| 444 | Bebida Vegetal De Avellana Sabor Chocolate Caja 1 L Vivicosí | Bebe > Alimentos Bebe | Bebidas > Bebidas | Bebida detectada dentro de categoria Bebe |
| 509 | Desodorante Spray Nivea Black&white Original Masculino Xl Hombre | Lacteos, Huevos y Congelados > Huevos | Higiene Personal > Desodorantes | Producto de higiene personal fuera de Higiene Personal |

## Archivos Generados

- reports/fase5f_clasificacion_masiva.csv
- reports/fase5f_clasificacion_masiva.md
- reports/FASE_5F_REPORTE.md
- reports/FASE_5F_REPORTE.pdf
- CAMBIOS_FASE_5F.md

## Recomendacion Fase 5F-FIX

- Crear una fase separada con backup y rollback especifico.
- Aplicar primero solo alta confianza y categorias de destino con subcategoria clara.
- Revisar manualmente hallazgos de media confianza.
- No recalcular producto_base hasta terminar movimientos de categoria.
- Prioridad inicial: Bebidas/Snacks/Limpieza dentro de Bebe y productos de mascotas fuera de Mascotas.
