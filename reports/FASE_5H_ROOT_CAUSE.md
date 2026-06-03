# Fase 5H - Root Cause de Clasificacion Masiva

Modo READ ONLY / AUDITORIA. No modifica base de datos ni producto_base.

## Estado General

- Hallazgos Fase 5F: 1986
- Hallazgos alta confianza: 1639
- Productos trazados: 51

## Causa Raiz Principal

La causa raiz mas probable es que los scrapers asignan la categoria/subcategoria configurada para una busqueda o URL amplia a todos los productos capturados, sin validar semanticamente cada resultado.

Ejemplos: busquedas o secciones como `alimento bebe`, `leche`, `carne`, `galleta`, `snack` o `crema facial` pueden devolver bebidas, productos de mascotas, cosmeticos o limpieza. Esos productos entran al CSV fuente con la categoria erronea y luego `combinar_supermercados.py` e `importar_csv.py` la preservan.

## Resumen de Causas

| Causa | Cantidad | % | Script afectado | Riesgo |
|---|---:|---:|---|---|
| scraper_categoria_por_busqueda_amplia | 51 | 100.0 | app/scraper_lider.py (48); app/scraper_jumbo_real.py (3) | alto |

## Hipotesis A-H

| Hipotesis | Resultado | Evidencia |
|---|---|---|
| A: Supermercado entrega categoria incorrecta | No concluyente | No concluyente: los CSV locales no conservan taxonomia real del sitio, solo la categoria asignada por scraper. |
| B: Scraper captura mal la categoria | Confirmada parcialmente | Confirmada parcialmente: el scraper asigna categoria configurada a resultados de busquedas amplias. |
| C: convertir_jumbo.py introduce el error | No confirmada para la muestra | No confirmada para la muestra: el error ya esta en jumbo_real.csv o scraper. |
| D: convertir_lider.py introduce el error | No confirmada para la muestra | No confirmada para la muestra: el error ya esta en lider_real.csv o scraper. |
| E: convertir_unimarc.py introduce el error | No confirmada para la muestra | No confirmada para la muestra: el error ya esta en unimarc_real.csv o scraper. |
| F: importar_csv.py asigna categoria incorrecta | Riesgo secundario | Riesgo secundario: importa lo que recibe y puede actualizar categoria por nombre compartido. |
| G: Mapeo de categorias generico o errado | Confirmada | Confirmada: 51 trazas apuntan a busquedas/mapeos amplios. |
| H: producto_base influye en categoria | Descartada en esta fase | Descartada en esta fase: producto_base se calcula despues y no participa en categoria/subcategoria. |

## Analisis de Scripts

| Script | Categorias hardcodeadas | Categoria por busqueda | Riesgo |
|---|---|---|---|
| app/scraper_lider.py | si | si | alto: asigna la categoria configurada a todos los productos extraidos desde una URL de categoria. |
| app/scraper_jumbo_real.py | si | si | alto: asigna la categoria del termino de busqueda, no una taxonomia validada del producto. |
| app/scraper_unimarc.py | si | si | alto: asigna la categoria del termino de busqueda y puede capturar resultados cruzados. |
| app/combinar_supermercados.py | no | no | medio: preserva la categoria fuente sin validar incompatibilidades. |
| app/importar_csv.py | no | no | medio: si el mismo nombre existe en varias filas, actualiza categoria por nombre. |

## Ejemplos Trazados

| ID | Producto | Supermercado | BD | Fuente | Causa |
|---:|---|---|---|---|---|
| 199 | Bebida Vegetal Notmilk Protein Con 7gr Proteína 750 ml NotCo | Líder | Bebe > Alimentos Bebe | Bebe > Alimentos Bebe | scraper_categoria_por_busqueda_amplia |
| 56 | Bebida Leche Láctea Yogu Yogu Chirimoya Caja | Líder | Bebe > Alimentos Bebe | Bebe > Alimentos Bebe | scraper_categoria_por_busqueda_amplia |
| 213 | Bebida Láctea Sin Lactosa Chocolate 200 ml Milo | Líder | Bebe > Alimentos Bebe | Bebe > Alimentos Bebe | scraper_categoria_por_busqueda_amplia |
| 3365 | Bebida Sin Azúcar Pack Lata 6 Un Coca-Cola | Líder | Bebe > Alimentos Bebe | Bebe > Alimentos Bebe | scraper_categoria_por_busqueda_amplia |
| 286 | Galletas Cachorro Raza Grande Sabor Leche Bolsa 500 g Master Dog | Líder | Desayuno y Snacks > Snacks | Desayuno y Snacks > Snacks | scraper_categoria_por_busqueda_amplia |
| 310 | Galleta Perro Cachoro Leche g g Pet Food | Líder | Desayuno y Snacks > Snacks | Desayuno y Snacks > Snacks | scraper_categoria_por_busqueda_amplia |
| 339 | Tónico Rose Care Leche & Tonico Micelar 2 En 1 200 ml Nivea | Líder | Lacteos, Huevos y Congelados > Leche | Lacteos, Huevos y Congelados > Leche | scraper_categoria_por_busqueda_amplia |
| 1127 | Acondicionador Ballerina Micelar Botella - Bajo Poo | Líder | Lacteos, Huevos y Congelados > Quesos | Lacteos, Huevos y Congelados > Quesos | scraper_categoria_por_busqueda_amplia |
| 509 | Desodorante Spray Nivea Black&white Original Masculino Xl Hombre | Líder | Lacteos, Huevos y Congelados > Huevos | Lacteos, Huevos y Congelados > Huevos | scraper_categoria_por_busqueda_amplia |
| 132 | Bebida Leche Láctea Yogu Yogu Mora Caja | Líder | Bebe > Alimentos Bebe | Bebe > Alimentos Bebe | scraper_categoria_por_busqueda_amplia |
| 148 | Bebida Leche Láctea Yogu Yogu Damasco Caja | Líder | Bebe > Alimentos Bebe | Bebe > Alimentos Bebe | scraper_categoria_por_busqueda_amplia |
| 149 | Bebida Leche Láctea Yogu Yogu Frutilla Caja | Líder | Bebe > Alimentos Bebe | Bebe > Alimentos Bebe | scraper_categoria_por_busqueda_amplia |
| 150 | Bebida Leche Láctea Yogu Yogu Piña Caja | Líder | Bebe > Alimentos Bebe | Bebe > Alimentos Bebe | scraper_categoria_por_busqueda_amplia |
| 151 | Bebida Leche Láctea Trencito Chocolate Caja | Líder | Bebe > Alimentos Bebe | Bebe > Alimentos Bebe | scraper_categoria_por_busqueda_amplia |
| 217 | Bebida Vegetal Notmilk Chocolate Tetra Pak 200 ml NotCo | Líder | Bebe > Alimentos Bebe | Bebe > Alimentos Bebe | scraper_categoria_por_busqueda_amplia |
| 218 | Bebida Vegetal Notmilk Original 1 L NotCo | Líder | Bebe > Alimentos Bebe | Bebe > Alimentos Bebe | scraper_categoria_por_busqueda_amplia |
| 220 | Bebida Láctea Sabor Frutilla 200 ml Surlat | Líder | Bebe > Alimentos Bebe | Bebe > Alimentos Bebe | scraper_categoria_por_busqueda_amplia |
| 246 | Chocolate Lenguas De Gato Leche 120 g Costa | Líder | Lacteos, Huevos y Congelados > Leche | Lacteos, Huevos y Congelados > Leche | scraper_categoria_por_busqueda_amplia |
| 300 | Alimento Seco Cachorro Raza Pequeña Carne Y Leche Bolsa 3 Kg Master Do | Líder | Carnes y Pescados > Carnes | Carnes y Pescados > Carnes | scraper_categoria_por_busqueda_amplia |
| 306 | Alimento Seco Cachorro Raza Mediana/grande Sabor Carne Y Leche Bolsa 3 | Líder | Carnes y Pescados > Carnes | Carnes y Pescados > Carnes | scraper_categoria_por_busqueda_amplia |
| 1878 | Alimento Seco Cachorro Carne Y Cereales Bolsa 3 Kg Cannes | Líder | Carnes y Pescados > Carnes | Carnes y Pescados > Carnes | scraper_categoria_por_busqueda_amplia |
| 1886 | Alimento Húmedo Cachorro Sabor Carne Pouch 85 g Pedigree | Líder | Carnes y Pescados > Carnes | Carnes y Pescados > Carnes | scraper_categoria_por_busqueda_amplia |
| 1890 | Alimento Seco Cachorro Pollo Y Carne Bolsa 2 Kg Purina One | Líder | Carnes y Pescados > Carnes | Carnes y Pescados > Carnes | scraper_categoria_por_busqueda_amplia |
| 1891 | Galletas Perro Adulto Sabor Carne Bolsa 500 g Master Dog | Líder | Desayuno y Snacks > Snacks | Desayuno y Snacks > Snacks | scraper_categoria_por_busqueda_amplia |
| 1895 | Alimento Seco Cachorro Raza Mediana/grande Carne Bolsa 3 Kg Champion D | Líder | Carnes y Pescados > Carnes | Carnes y Pescados > Carnes | scraper_categoria_por_busqueda_amplia |
| 1896 | Alimento Seco Cachorro Raza Pequeña Carne Bolsa 3 Kg Champion Dog | Líder | Carnes y Pescados > Carnes | Carnes y Pescados > Carnes | scraper_categoria_por_busqueda_amplia |
| 1897 | Galletas Perro Adulto Sabor Carne Bolsa 500 g Champion Dog | Líder | Desayuno y Snacks > Snacks | Desayuno y Snacks > Snacks | scraper_categoria_por_busqueda_amplia |
| 1912 | Snack Perro Beef Stick Carne g Vitakraft | Líder | Desayuno y Snacks > Snacks | Desayuno y Snacks > Snacks | scraper_categoria_por_busqueda_amplia |
| 1932 | Alimento Seco Cachorro Carne Bolsa 3 Kg Pedigree | Líder | Carnes y Pescados > Carnes | Carnes y Pescados > Carnes | scraper_categoria_por_busqueda_amplia |
| 1105 | Jabón Crema Ballerina Triple Humectación Piel Sensible Hipoalergénico | Líder | Lacteos, Huevos y Congelados > Quesos | Lacteos, Huevos y Congelados > Quesos | scraper_categoria_por_busqueda_amplia |

## Correcciones Propuestas

1. Agregar validador semantico antes de escribir cada CSV fuente.
2. Reemplazar busquedas ambiguas por URLs/taxonomias mas especificas cuando existan.
3. Bloquear categorias imposibles antes de combinar e importar.
4. En `importar_csv.py`, evitar overwrite de categoria por nombre cuando supermercados distintos traen categorias incompatibles.
5. Agregar tests de regresion para NotMilk, Yogu Yogu, Coca-Cola, Master Dog, Pet Food, Nivea Micelar y Desodorante Nivea.
6. Ejecutar recarga limpia solo despues de corregir scrapers/importadores y validar 0 bloqueos criticos.

## Archivos Generados

- reports/fase5h_trazabilidad_productos.csv
- reports/fase5h_causa_raiz_resumen.csv
- reports/FASE_5H_ROOT_CAUSE.md
- reports/FASE_5H_ROOT_CAUSE.pdf
