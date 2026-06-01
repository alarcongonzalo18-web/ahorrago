# Cambios Fase 5A - AhorraGo

Fecha: 2026-05-31

## Objetivo

Mejorar equivalencias únicamente en categorías de mejor retorno y menor riesgo:

- Bebidas
- Limpieza
- Higiene Personal
- Bebé
- Mascotas

No se modificaron categorías de alto riesgo como Frutas y Verduras, Carnes y Pescados, Panadería o Congelados.

## Modo de Trabajo

La fase se ejecutó completa en **DRY RUN**:

- No se modificó la base real.
- No se ejecutó scraping.
- No se modificó frontend.
- No se crearon usuarios.

## Reglas Implementadas

### Bebidas

- Normalización de `1L`, `1000ml`, `1.5L`, `1500ml`, `2L`, `2000ml`.
- Packs `pack 6`, `x6`, `pack 12`, `x12`.
- Diferenciación de retornable/no retornable.
- Diferenciación de zero/sin azúcar/light vs normal.
- Protección contra sabores distintos.

### Limpieza

- Normalización de ml, litros, gramos y kilogramos.
- Detección de aroma.
- Detección de concentrado, diluido, antibacterial y tradicional.
- Protección contra Lavanda vs Limón y Antibacterial vs Tradicional.

### Higiene Personal

- Detección de shampoo, acondicionador, jabón, desodorante, pasta dental y crema.
- Detección de aroma.
- Detección de género/formato: hombre, mujer, infantil, adulto.
- Protección contra hombre vs mujer e infantil vs adulto.

### Bebé

- Detección de etapa.
- Detección de talla.
- Detección de cantidad.
- Protección contra Talla M vs Talla G y Etapa 1 vs Etapa 2.

### Mascotas

- Detección de perro/gato.
- Detección de peso.
- Detección de etapa: cachorro, adulto, senior.
- Protección contra cachorro vs adulto y gato vs perro.

## Métricas Actuales vs Proyectadas

- Productos evaluados: 10.656
- Productos equivalentes actuales: 2.918
- Productos equivalentes proyectados: 4.477
- Mejora proyectada: 53,43%
- Conflictos actuales en categorías objetivo: 715
- Conflictos reducibles estimados: 540
- Grupos riesgosos excluidos: 639
- Pares riesgosos detectados y no aplicados: 5.480
- Falsos positivos estimados aplicables: 0

## Categorías Más Beneficiadas

- Mascotas: +73,28%
- Limpieza: +63,64%
- Bebé: +59,17%
- Higiene Personal: +59,13%
- Bebidas: +40,60%

## Archivos Creados

- `app/fase5a_rules.py`
- `app/scripts/simular_mejora_matching_fase5a.py`
- `tests/test_fase5a_rules.py`
- `tests/test_fase5a_simulacion.py`
- `reports/fase5a_simulacion.md`
- `reports/fase5a_detalle_categoria.csv`
- `reports/fase5a_falsos_positivos.csv`
- `reports/FASE_5A_REPORTE.md`
- `reports/FASE_5A_REPORTE.pdf`
- `CAMBIOS_FASE_5A.md`

## Archivos Modificados

- `app/normalizacion.py`
- `tests/fixtures/productos_reales.json`

## Tests

Se agregaron pruebas positivas, negativas y casos límite para:

- Bebidas
- Limpieza
- Higiene Personal
- Bebé
- Mascotas
- Simulación DRY RUN

Resultado final:

- `32 passed`

## Riesgos Pendientes

- La simulación excluye 639 grupos riesgosos; esos grupos requieren revisión manual.
- Los 5.480 pares riesgosos detectados no deben aplicarse automáticamente.
- La mejora proyectada depende de aplicar solo grupos seguros.
- Las categorías excluidas siguen pendientes para fases posteriores.

## Recomendación Fase 5B

Ejecutar limpieza controlada por categoría, empezando por Mascotas y Limpieza porque muestran mejor retorno y reglas más claras. Mantener DRY RUN, respaldo automático y aplicación real solo para grupos con riesgo bajo y tests específicos.
