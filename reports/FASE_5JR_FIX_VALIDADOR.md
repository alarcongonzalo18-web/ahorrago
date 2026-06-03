# Fase 5J-R — Fix del Validador de Categorías (pre-reload)

**Fecha:** 2026-06-02
**Autor:** Principal Engineer + Data Architect
**Modo:** Prototipo validado sobre datos reales en disco. Sin scraping. Sin escritura a BD productiva.

## Objetivo

Corregir `app/category_validator.py` **antes** de cualquier reload, porque el reload
convierte cada rechazo del validador en un borrado permanente. Se detectaron falsos
positivos por coincidencia de substring que provocaban pérdida de productos válidos.

## Causa raíz de los falsos positivos (v1)

1. **Coincidencia por substring crudo.** `keyword in texto` hacía que `jugo` matcheara
   `jugoso`, `caju` matcheara `cajun`, etc.
2. **Palabras legítimas que contienen un keyword.** "Vinagre de **Vino**", "Carne al
   **Vino**", "**Bebida Láctea**" caían en la regla de bebidas.
3. **Sin vía de cuarentena.** Confianza Media eliminaba el producto igual que Alta:
   un falso positivo = pérdida de dato, silenciosa.
4. **Comparación de categoría sensible a acentos.** `cat == "Bebe"` fallaba con `"Bebé"`;
   convivían `"Lácteos…"` y `"Lacteos…"` como categorías distintas.

## Cambios aplicados (v2)

- Coincidencia por **palabra completa** (regex `\b…\b`).
- **Exclusiones** para la regla de bebidas: `vinagre`, `en vino`, `al vino`,
  `bebida lactea`, `saborizante`, `polvo`, `salsa`.
- **Política de cuarentena:** confianza **Alta → reject** (se quita del load);
  confianza **Media → review** (se **conserva** y se registra en
  `pipeline_category_quarantine.csv` para revisión humana). Nunca se pierde un producto
  por confianza media.
- **Categoría insensible a acentos** (`normalize` aplicado a `categoria`).

## Resultado medido (33.267 productos reales: Líder 7.536, Jumbo 23.794, Unimarc 1.937)

| Métrica | v1 (substring) | v2 (word-boundary + cuarentena) |
|---|---:|---:|
| Productos borrados a la fuerza | 1.440 | **999** (solo Alta) |
| Conservados y marcados (cuarentena) | 0 | **287** |
| Falsos positivos eliminados (ya ni se marcan) | — | **154** |
| **Productos rescatados de borrado** | — | **441** |

### Verificación dirigida

Falsos positivos que v1 borraba y v2 conserva: `Vinagre de Vino Blanco`,
`Base Maggi Jugoso`, `Carne Asada en Vino Tinto`, `Bebida Láctea Soprole Kéfir`.

Aciertos reales (bug 5H) que v2 sigue rechazando con Alta: `Pedigree` en Carnes,
`Crema Nivea` en Crema, `Limpiador Cif` en Crema, `Whiskas Gato` en Crema.

## Tests

`tests/test_category_validator.py` — **16/16 PASSED**. Cubre: regresión de falsos
positivos, word-boundary (`jugoso`, `cajun`), aciertos del bug 5H, insensibilidad a
acentos, y la política de cuarentena (Media se conserva, sólo Alta devuelve `False`).

## Rollback

El archivo nuevo reemplaza `app/category_validator.py` en la rama `fase-5j-hardening`.
Rollback = `git checkout fase-5j-hardening -- app/category_validator.py` desde el commit
anterior, o `git revert` del commit del fix. La versión v1 queda en el historial.

## Pendiente (siguiente paso, no incluido en este fix)

- Modo *reprocess-only* en `reload_v3_fase5jr.py` (stages 2→5 sobre CSV en disco, sin
  `run_scrapers`) para producir `supercheck_reload_v3.db` real y medir el remanente.
- Normalizar acentos de `categoria` en `importar_csv.py` / `combinar_supermercados.py`
  para evitar categorías duplicadas en la BD.
- Fix del checkpoint de scrapers (marca "complete" aún con errores).
