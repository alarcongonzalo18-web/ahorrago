# Cambios Fase 5H - Root Cause Clasificacion Masiva

Fecha: 2026-06-01

## Objetivo

Identificar la causa raiz de los errores masivos de clasificacion detectados en Fase 5F y confirmados por Fase 5G.

## Modo

- READ ONLY / AUDITORIA.
- No se modifico `supercheck.db`.
- No se corrigieron productos.
- No se recalculo `producto_base`.
- No se ejecuto scraping masivo.
- No se toco frontend.
- No se crearon usuarios.

## Cambios Realizados

- Se creo `app/scripts/auditoria_root_cause_fase5h.py`.
- Se genero trazabilidad de 51 productos de alta confianza.
- Se genero resumen de causa raiz.
- Se agregaron tests read-only para validar hipotesis y ejemplos criticos.

## Causa Raiz

La causa raiz principal es `scraper_categoria_por_busqueda_amplia`.

Los scrapers asignan a cada resultado la categoria/subcategoria configurada para la busqueda o URL recorrida, sin validar semanticamente si el producto pertenece realmente a esa categoria.

## Evidencia

- NotMilk, Yogu Yogu, Milo y Coca-Cola aparecen en `Bebe > Alimentos Bebe`.
- Master Dog y Pet Food aparecen en `Carnes`, `Desayuno y Snacks` o `Lacteos`.
- Nivea micelar y desodorantes aparecen en `Lacteos`.
- La categoria erronea ya existe en CSV fuente para los productos trazados.

## Scripts Afectados

- `app/scraper_lider.py`: alto impacto.
- `app/scraper_jumbo_real.py`: impacto presente.
- `app/scraper_unimarc.py`: riesgo estructural equivalente.
- `app/combinar_supermercados.py`: preserva errores sin validar.
- `app/importar_csv.py`: importa errores y puede sobrescribir categoria por nombre.

## Archivos Generados

- `reports/FASE_5H_ROOT_CAUSE.md`
- `reports/FASE_5H_ROOT_CAUSE.pdf`
- `reports/fase5h_trazabilidad_productos.csv`
- `reports/fase5h_causa_raiz_resumen.csv`

## Recomendacion

Antes de una nueva recarga limpia, conviene ejecutar Fase 5I para corregir importadores/scrapers y agregar validadores pre-import. Despues de eso, repetir reload test.
