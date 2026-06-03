# Cambios Fase 5I - Pipeline Hardening

Fecha: 2026-06-01

## Resumen

Se agrego una barrera semantica compartida para impedir que categorias imposibles entren al pipeline y lleguen a SQLite en futuras recargas.

## Archivos Modificados

- `app/category_validator.py`
- `app/scraper_lider.py`
- `app/scraper_jumbo_real.py`
- `app/scraper_unimarc.py`
- `app/combinar_supermercados.py`
- `app/importar_csv.py`
- `tests/test_fase5i_category_validator.py`
- `reports/FASE_5I_PIPELINE_HARDENING.md`

## Resultado Estimado

- Hallazgos Fase 5F: 1986.
- Bloqueados por validador: 1934.
- Remanente estimado: 52.
- Objetivo: menos de 300.

## Seguridad

- No se modifico `supercheck.db`.
- No se ejecuto recarga.
- No se ejecuto scraping.
- No se corrigieron datos existentes.

## Siguiente Paso

Fase 5J debe ejecutar reload test post-hardening en una BD paralela y revisar `reports/pipeline_category_rejections.csv`.
