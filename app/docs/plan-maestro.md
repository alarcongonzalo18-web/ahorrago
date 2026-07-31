# Plan maestro — mejoras, correcciones y nuevas implementaciones

> Creado el 23-07-2026, **revisado el 27-07-2026** tras completar la migración de las 4
> cadenas a categorías reales. Ordena lo pendiente por dependencia: primero validar,
> después corregir, después salir a internet, después producto, y la monetización AL
> FINAL (regla de Gonzalo). Detalle fino en los docs enlazados.

## Estado al 27-07-2026

| | |
|---|---:|
| **Comparables (KPI)** | **11.346** (11.181 por EAN) |
| Productos | 65.914 · **74% con EAN** |
| Precios | 66.194 · 4 cadenas |
| Historial | 9 días, 509.588 puntos |
| Tests | 144 |

Evolución del KPI: 6.967 (baseline 23-07) → 7.119 (Tottus) → 10.479 (Jumbo+VTEX) →
**11.346** (Líder fusionado). **+63% en cuatro días.**

## ✅ Fase 0 — Validar lo construido: COMPLETA

Se hizo **desde el equipo de trabajo**, no desde el actualizador (estaba apagado; la base
autoritativa viajó por pendrive). Las 4 cadenas corren por categorías reales:

| Cadena | Endpoint | Subcats | EAN |
|---|---|---:|---|
| Jumbo | Constructor.io `/browse/group_id` | 89 | VTEX por lotes (1% → 50%) |
| Tottus | `/lista/CATG` + `__NEXT_DATA__` | 71 | backfill |
| Unimarc | Selenium por `/category` | 66 | directo del listado |
| Líder | `/v/` **+** SPA `/browse` fusionados por EAN | 93 + 94 | directo, 100% |

Hallazgos que quedaron documentados: [ean-jumbo.md](ean-jumbo.md) (VTEX reemplaza al BFF),
[lider-endpoint-nuevo.md](lider-endpoint-nuevo.md) (Akamai vencido con
undetected-chromedriver), y el bug del guard que confundía migración con regresión.

## ✅ Fase 1 — Corrección de errores: COMPLETA

| # | Problema | Cómo se resolvió |
|---|---|---|
| 1.1 | Líder degradándose (endpoint legacy) | `undetected-chromedriver` pasa Akamai. Pero el diagnóstico intermedio ("techo de 192 productos") **era erróneo**: `maxPage` varía. El problema real era el **EAN sin dígito verificador** (12 dígitos → cero coincidencias). Arreglado, y los dos endpoints se **fusionan por EAN**: 8.646 → 13.481 productos. |
| 1.2 | Unimarc EAN 403 desde el actualizador | **Resuelto por diseño**: el scraper nuevo trae EAN del listado, no usa el BFF. |
| 1.3 | Matching con catálogo multiplicado | ⏳ **PENDIENTE**: con 65.914 productos hay que re-auditar los grupos difusos (hoy solo 165 de 11.346, pero conviene revisar los más grandes). |
| 1.4 | Categorías internas quizá chicas | ⏳ **PENDIENTE, opcional**: "Desayuno y Snacks" recibe café+té+cereales+chocolates de 4 cadenas. Evaluar solo si molesta en la UI. |

## 🔴 Fase 1.5 — Pendientes operativos (NUEVOS, bloquean la automatización)

Aparecieron al trabajar desde este equipo. **Son lo más urgente.**

1. **Devolver la posta al equipo actualizador.** Está apagado, con datos del 23-07 y sus
   tareas nocturnas **activas**. Si se enciende así, scrapea con base vieja y bifurca el
   historial. Orden correcto: copiarle `supercheck.db` del pendrive → `git pull` →
   recién ahí reactivar tareas. Ver [migracion-equipo.md](migracion-equipo.md).
2. **Automatizar el scraper nuevo de Líder.** Necesita **Chrome visible** (headless es una
   señal que Akamai detecta), y las tareas corren de madrugada. Decidir: sesión
   desbloqueada, u horario en que haya alguien. Hoy `scraper_lider_browse` no está en
   `SCRAPERS` de `actualizar_productos.py` — corre a mano.
3. **Windows Task Scheduler + Chrome visible**: verificar que una tarea programada pueda
   levantar Chrome no-headless con la sesión bloqueada. Si no puede, Líder `/browse` queda
   como corrida manual semanal (el `/v/` sigue automático y cubre alimentos).

## Fase 2 — Salir a internet (el proyecto grande)

Hoy AhorraGo solo existe en dos máquinas. Es lo único que separa "proyecto" de "producto".
Detalle en [camino-a-produccion.md](camino-a-produccion.md).

1. **Sync casa→nube**: paso final del pipeline que sube `supercheck.db` con swap atómico
   (el scraping se queda en casa: la IP residencial es irreemplazable).
2. **Infra**: VPS chico (~USD 5/mes para FastAPI+SQLite), dominio, HTTPS.
3. **Endurecimiento**: CORS, cerrar `/diagnostico/*`, rate limiting, backups remotos.
4. **Beta real**: 2-3 usuarios con la URL pública.

## Fase 3 — Producto

En orden de dependencias (detalle en [roadmap-producto.md](roadmap-producto.md)):
geolocalización → cuentas de usuario → alertas por media histórica (el historial ya
acumula 9 días para esto) → plan de compra → nombre y colores nuevos antes de difundir.

## Fase 4 — Monetización (LO ÚLTIMO)

Freemium + prueba de 15 días + pasarela chilena. No se construye hasta que las Fases 2-3
funcionen y haya usuarios reales.

## Transversal

- Cadencia: cada cambio → commit → push a GitHub → sincronizar pendrive.
- Tests verdes antes de cada push (hoy 144).
- Los dos equipos **nunca** scrapean en paralelo.
- **Lección del 26/27-07**: dos diagnósticos resultaron errados por medir mal (comparar
  filas con duplicados contra filas sin duplicados; asumir un techo fijo sin verificarlo).
  Antes de decidir sobre un número, confirmar qué está contando.
