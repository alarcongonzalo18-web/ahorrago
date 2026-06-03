# Informe de Continuidad — AhorraGo
**Generado:** 2026-06-02  
**Modo:** Solo auditoría. Sin modificaciones.

---

## 1. Estado Git

| Campo | Valor |
|---|---|
| Rama actual | `main` |
| Sincronización | Up to date con `origin/main` |
| Archivos modificados sin commit | 9 (ver abajo) |
| Archivos nuevos sin trackear | ~60 |

### Archivos modificados (sin commit)

```
app/combinar_supermercados.py
app/importar_csv.py
app/main.py
app/matching_diagnostics.py
app/normalizacion.py
app/scraper_jumbo_real.py
app/scraper_lider.py
app/scraper_unimarc.py
app/scripts/agregar_indices.py
data/lider_real.csv
reports/AHORRAGO_MASTER_REPORT.md
reports/AHORRAGO_MASTER_REPORT.pdf
```

### Archivos nuevos sin trackear (selección relevante)

```
app/category_validator.py              ← Fase 5I
app/scripts/reload_v2_fase5j.py        ← Fase 5J
app/scripts/reload_v3_fase5jr.py       ← Fase 5J-R
app/scripts/auditoria_root_cause_fase5h.py
app/scripts/comparar_bd_actual_vs_reload.py
app/scripts/crear_bd_reload_test.py
tests/test_fase5i_category_validator.py
reports/pipeline_category_rejections_v3.csv  ← Artefacto 5J-R
```

### Últimos 10 commits

```
41d20ef  feat: Completa fases 1-5B con matching avanzado, tests y auditoría técnica
079b749  Actualiza base de productos a 34.481 items y agrega docs de contexto
030082a  Corrige bugs de seguridad y calidad encontrados en revision de codigo
8f14641  Revert "Agrega documento de contexto para continuidad entre sesiones"
b79d486  Agrega documento de contexto para continuidad entre sesiones
e59f48a  Agrega manejo de cantidades por producto en carrito
4a57d14  Agrega endpoint /productos/resumen-compra con calculo de ahorro
64a2f92  Agrega link Ver producto en vista tabla
9b2b487  Unifica breakpoint movil a 1024px y oculta contenido innecesario
5ba6748  Compacta header en vista movil
```

**Nota:** Todo el trabajo de Fase 5C hasta 5J-R fue realizado en `main` sin commits intermedios. Existe una brecha importante entre el último commit y el estado real del proyecto.

---

## 2. Estado de Fases

| Fase | Estado | Evidencia |
|---|---|---|
| Fase 1 | ✅ Completa | Commit `030082a`, `AHORRAGO_MASTER_REPORT.md` |
| Fase 2 | ✅ Completa | Incluida en `AHORRAGO_MASTER_REPORT.md` |
| Fase 3 | ✅ Completa | Incluida en `AHORRAGO_MASTER_REPORT.md` |
| Fase 4 | ✅ Completa | `reports/FASE_4_REPORTE.md` + PDF (31-05-2026) |
| Fase 5A | ✅ Completa | `reports/FASE_5A_REPORTE.md` + PDF (31-05-2026) |
| Fase 5B | ✅ Completa | `reports/FASE_5B_REPORTE.md` + commit `41d20ef` |
| Fase 5B-FIX | ✅ Completa | `reports/FASE_5B_FIX_REPORTE.md` + PDF (01-06-2026 20:20) |
| Fase 5C | ✅ Completa | `reports/FASE_5C_REPORTE.md` + PDF (01-06-2026 21:28) |
| Fase 5D-FIX | ✅ Completa | `reports/FASE_5D_FIX_REPORTE.md` + PDF (01-06-2026 20:31) |
| Fase 5E | ✅ Completa | `reports/FASE_5E_AUDITORIA_GLOBAL.md` + PDF (01-06-2026 21:41) |
| Fase 5F | ✅ Completa | `reports/FASE_5F_REPORTE.md` + PDF (01-06-2026 21:51) |
| Fase 5G | ✅ Completa | `reports/FASE_5G_RELOAD_TEST.md` + PDF (01-06-2026 22:07) |
| Fase 5H | ✅ Completa | `reports/FASE_5H_ROOT_CAUSE.md` + PDF (01-06-2026 22:17) |
| Fase 5I | ✅ Completa | `reports/FASE_5I_PIPELINE_HARDENING.md` + PDF (01-06-2026 22:22) |
| Fase 5J | ⚠️ Parcial | Script `reload_v2_fase5j.py` creado. `reports/reload_v2/` vacía. Sin DB resultante. |
| Fase 5J-R | ❌ No completada | Script `reload_v3_fase5jr.py` existe. Generó `pipeline_category_rejections_v3.csv` (23:24) pero sin DB, sin checkpoints, sin directorio `reload_v3/`. |

---

## 3. Bases de Datos

| BD | Estado | Productos | Precios | Categorías | Subcategorías | Tamaño | Fecha Mod |
|---|---|---|---|---|---|---|---|
| `supercheck.db` | ✅ **VÁLIDA — PRODUCCIÓN** | 31.124 | 31.139 | 13 | 54 | 14,9 MB | 01-06-2026 21:28 |
| `supercheck_reload_test.db` | ✅ Referencia (Fase 5G) | 31.124 | 31.155 | 13 | 54 | 15,2 MB | 01-06-2026 22:06 |
| `supercheck_reload_v2.db` | ❌ No existe | — | — | — | — | — | — |
| `supercheck_reload_v3.db` | ❌ No existe | — | — | — | — | — | — |

**BD válida actualmente:** `supercheck.db` con **31.124 productos** de Líder, Jumbo y Unimarc.  
No existe diferencia significativa entre la BD principal y el reload_test (mismo producto count, 16 precios extra en test).

---

## 4. Reportes

### Reportes completos con PDF

| Reporte | Fecha | Fase |
|---|---|---|
| `AHORRAGO_MASTER_REPORT.md` | 01-06-2026 22:22 | Acumulado |
| `FASE_5I_PIPELINE_HARDENING.md` | 01-06-2026 22:22 | 5I |
| `FASE_5H_ROOT_CAUSE.md` | 01-06-2026 22:17 | 5H |
| `FASE_5G_RELOAD_TEST.md` | 01-06-2026 22:07 | 5G |
| `FASE_5F_REPORTE.md` | 01-06-2026 21:51 | 5F |
| `FASE_5E_AUDITORIA_GLOBAL.md` | 01-06-2026 21:41 | 5E |
| `FASE_5D_FIX_REPORTE.md` | 01-06-2026 20:31 | 5D-FIX |
| `FASE_5C_REPORTE.md` | 01-06-2026 21:28 | 5C |
| `FASE_5B_FIX_REPORTE.md` | 01-06-2026 20:20 | 5B-FIX |

### Reportes sin PDF (incompletos o solo MD)

| Archivo | Observación |
|---|---|
| `FASE_5D_ANALISIS.md` | Sin PDF (solo análisis previo) |
| `CAMBIOS_FASE_5F.md` | Sin PDF |
| `auditoria_categorias.md` | Sin PDF |

### Reportes de Fase 5J / 5J-R

| Archivo | Estado |
|---|---|
| `reports/FASE_5J_*.md` | **NO EXISTE** |
| `reports/FASE_5JR_RELOAD_V3.md` | **NO EXISTE** |
| `pipeline_category_rejections_v3.csv` | Existe — 2.559 rechazos, 23:24:38 del 01-06 |

**Último reporte válido:** `FASE_5I_PIPELINE_HARDENING.md` (22:22 del 01-06-2026).

---

## 5. Estado Fase 5J-R (Detalle)

| Indicador | Estado |
|---|---|
| Script `reload_v3_fase5jr.py` | Existe (creado 22:37) |
| Proceso activo | No (ningún proceso Python corriendo) |
| Checkpoints (`reports/reload_v3_checkpoints/`) | **No existen** |
| Directorio `reports/reload_v3/` | **No existe** |
| CSV intermedio `productos_supermercados_v3.csv` | **No existe** |
| `supercheck_reload_v3.db` | **No existe** |
| `pipeline_category_rejections_v3.csv` | Existe — 2.559 filas — timestamp 23:24:38 |
| Archivos corruptos | Ninguno detectado |

### Interpretación

El script `reload_v3_fase5jr.py` fue ejecutado al menos parcialmente la noche del 01-06-2026 a las 23:24. Generó el log de rechazos del validador (2.559 productos rechazados) pero **se interrumpió antes de crear el CSV consolidado y la nueva base de datos**. No quedan checkpoints recuperables. La Fase 5J-R debe iniciarse desde cero.

---

## 6. Hallazgos Críticos

### Causa Raíz (Fase 5H)

**`scraper_categoria_por_busqueda_amplia`**: Los tres scrapers asignan la categoría configurada en el script a todos los productos devueltos por una búsqueda o URL de sección, sin validar semánticamente cada resultado. Una búsqueda como `"leche"` o `"alimento bebe"` puede traer bebidas energéticas, comida de mascotas o cosméticos, todos con categoría `Bebe > Alimentos Bebe`. Esto afecta Líder (48 casos trazados) y Jumbo (3 casos trazados) en la muestra.

Ejemplos confirmados:
- Coca-Cola → Bebe > Alimentos Bebe
- NotMilk → Bebe > Alimentos Bebe
- Master Dog (galletas perro) → Desayuno y Snacks > Snacks
- Desodorante Nivea → Lacteos, Huevos y Congelados > Huevos

### Cambios Aplicados (Fase 5I)

Se creó `app/category_validator.py` con barrera semántica en **5 puntos del pipeline**:

1. `scraper_lider.py` — filtra antes de escribir CSV
2. `scraper_jumbo_real.py` — filtra antes de escribir CSV
3. `scraper_unimarc.py` — filtra antes de escribir CSV
4. `combinar_supermercados.py` — filtra al consolidar
5. `importar_csv.py` — última barrera antes de SQLite

**Estimación read-only (Fase 5I):**
- Hallazgos previos (5F): 1.986
- Bloqueados por validador: 1.934 (97,4%)
- Remanente estimado: 52 (objetivo era <300 ✅)
- Productos rechazados del CSV fuente: 2.949 de 34.481

**Ejecución real (5J-R parcial):**
- Rechazos efectivos registrados: 2.559 (más conservador que la estimación)

### Estado del `category_validator.py`

- Archivo: `app/category_validator.py` (untracked, sin commit)
- Tests: `tests/test_fase5i_category_validator.py` (untracked)
- Tests ejecutados en Fase 5I: `pytest` → OK
- Integrado en los 5 puntos del pipeline
- Rechazos se loguean en `reports/pipeline_category_rejections_v3.csv`

### Estado del Pipeline

El pipeline está **hardened pero no validado end-to-end** con una recarga completa. La BD actual (`supercheck.db`) contiene datos del pipeline anterior a los validadores. La Fase 5J-R es el primer reload real con pipeline endurecido.

---

## 7. Próximo Paso Recomendado

### Opción recomendada: **B — Reiniciar Fase 5J-R desde cero**

**Justificación técnica:**

1. **No hay nada recuperable.** No existen checkpoints, ni CSV intermedio, ni BD parcial. El único artefacto es el log de rechazos (2.559 filas), que el script regenerará automáticamente.

2. **El script tiene checkpoint logic.** `reload_v3_fase5jr.py` implementa checkpoints en `reports/reload_v3_checkpoints/`. Al reiniciarlo, las etapas completadas se saltan. Si se interrumpe nuevamente, sí habrá algo que retomar.

3. **La BD actual está íntegra.** `supercheck.db` no fue tocada. El script crea `supercheck_reload_v3.db` como BD paralela y solo promueve a producción si todo es exitoso. No hay riesgo de pérdida de datos.

4. **La Fase 5J (v2) falló antes.** `reports/reload_v2/` está vacía, lo que indica que el script `reload_v2_fase5j.py` también se interrumpió prematuramente. Esto sugiere un problema de ejecución (timeout, crash, interrupción manual) no un bug en la lógica.

5. **El objetivo de Fase 5J-R es crítico.** Sin una recarga limpia con validadores activos, la BD de producción sigue conteniendo las ~1.986 clasificaciones incorrectas detectadas en Fase 5F. El hardening de Fase 5I no tiene efecto sobre datos ya cargados.

**Secuencia recomendada para hoy:**

```
1. Verificar que no hay procesos Python activos
2. Ejecutar: python -m app.scripts.reload_v3_fase5jr
3. Monitorear checkpoints en reports/reload_v3_checkpoints/
4. Revisar reports/pipeline_category_rejections_v3.csv al terminar
5. Revisar reports/FASE_5JR_RELOAD_V3.md generado
6. Decidir si promover supercheck_reload_v3.db a producción
7. Commit de todo el trabajo de Fases 5C–5J-R
```

---

## Riesgos Actuales

| Riesgo | Severidad | Descripción |
|---|---|---|
| 31.124 productos mal clasificados en producción | Alto | BD actual tiene clasificaciones previas al hardening de Fase 5I |
| ~60 archivos sin commit | Alto | Todo el trabajo de Fases 5C-5J-R puede perderse sin respaldo en GitHub |
| Pipeline 5J-R falló 2 veces (v2 y v3 parcial) | Medio | Causa de interrupción no identificada; puede repetirse |
| `category_validator.py` sin commit | Medio | Archivo crítico no versionado en GitHub |
| Falsos positivos del validador | Bajo | 52 productos válidos podrían ser rechazados incorrectamente |
| Encoding en supercheck.db | Bajo | Nombres de supermercados con `?` sugieren problema de charset |

---

*Informe generado el 2026-06-02 en modo auditoría. Sin modificaciones a código ni base de datos.*
