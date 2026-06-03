# Fase 5I - Pipeline Hardening

Fecha: 2026-06-01

## Objetivo

Corregir scrapers e importadores para impedir categorias imposibles antes de llegar a la BD.

## Modo

- No se modifico la BD existente.
- No se recargo la base.
- No se ejecuto scraping masivo.
- No se corrigieron productos existentes.
- No se recalculo `producto_base`.
- No se toco frontend.

## Cambios Implementados

Se creo `app/category_validator.py` como barrera semantica compartida para el pipeline.

El validador:

- Detecta incompatibilidades semanticas entre nombre, categoria y subcategoria.
- Rechaza categorias imposibles.
- Sugiere categoria/subcategoria esperada.
- Registra rechazos en `reports/pipeline_category_rejections.csv` cuando el pipeline se ejecuta.
- Evita falsos positivos conocidos como Hair Food/Aguacate, Trocitos Jugosos en Mascotas y Pasta Limpiadora en Limpieza.

## Integracion en Pipeline

- `app/scraper_lider.py`: filtra productos antes de guardarlos en `lider_real.csv`.
- `app/scraper_jumbo_real.py`: filtra productos antes de guardarlos en `jumbo_real.csv`.
- `app/scraper_unimarc.py`: filtra productos antes de guardarlos en `unimarc_real.csv`.
- `app/combinar_supermercados.py`: filtra filas fuente antes de consolidar `productos_supermercados.csv`.
- `app/importar_csv.py`: ultima barrera antes de crear/actualizar productos en SQLite.

## Reglas Cubiertas

- Bebidas en `Bebe`.
- Snacks/frutos secos en `Bebe`.
- Limpieza en `Bebe`.
- Mascotas fuera de `Mascotas`.
- Higiene Personal fuera de `Higiene Personal`.
- Limpieza fuera de `Limpieza`.
- Bebidas fuera de `Bebidas`.

## Tests de Regresion

Se agregaron pruebas para:

- NotMilk.
- Coca-Cola.
- Yogu Yogu.
- Master Dog.
- Champion Dog.
- Pedigree.
- Nivea.
- Rexona.
- Dove.

Tambien se validan falsos positivos:

- Hair Food/Aguacate.
- Trocitos Jugosos en Mascotas.
- Pasta Limpiadora/Pink Stuff en Limpieza.

## Estimacion Read Only

Sobre `reports/fase5f_clasificacion_masiva.csv`:

- Hallazgos Fase 5F: 1986.
- Hallazgos que bloquearia el validador: 1934.
- Remanente estimado post-hardening: 52.
- Objetivo solicitado: menos de 300 hallazgos.
- Resultado esperado: cumple el objetivo.

Sobre `data/productos_supermercados.csv`:

- Filas actuales: 34481.
- Filas que el validador rechazaria: 2949.
- Filas aceptadas estimadas: 31532.

## Causa Raiz Atacada

Fase 5H identifico `scraper_categoria_por_busqueda_amplia`.

Fase 5I reduce ese riesgo colocando la barrera en cinco puntos:

1. Scraper Lider.
2. Scraper Jumbo.
3. Scraper Unimarc.
4. Combinador de CSV.
5. Importador a SQLite.

## Riesgos

- Puede rechazar productos validos con nombres ambiguos si coinciden con marcas o palabras fuertes.
- El umbral de 52 hallazgos es estimado sobre reportes actuales; debe confirmarse con una recarga paralela posterior.
- Los rechazos reducen cantidad de productos cargados si no se reemplazan por una categoria corregida.
- Antes de produccion conviene revisar `reports/pipeline_category_rejections.csv` luego de una corrida real del pipeline.

## Recomendacion

Ejecutar Fase 5J como reload test post-hardening:

- No reemplazar todavia `supercheck.db`.
- Crear una nueva BD paralela.
- Ejecutar pipeline local con validadores activos.
- Confirmar que los hallazgos bajan de 300.
- Revisar rechazos antes de decidir si se corrige o descarta cada fila.

## Validacion Ejecutada

- `python -m pytest tests/test_fase5i_category_validator.py -q`: OK.
- Medicion read-only sobre reportes y CSV actuales: OK.

## Archivos

- `app/category_validator.py`
- `tests/test_fase5i_category_validator.py`
- `reports/FASE_5I_PIPELINE_HARDENING.md`
- `reports/FASE_5I_PIPELINE_HARDENING.pdf`
