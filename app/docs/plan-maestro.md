# Plan maestro — mejoras, correcciones y nuevas implementaciones

> Consolidado el 23-07-2026, tras completar la migración de las 3 cadenas a categorías
> reales. Ordena TODO lo pendiente por fases con criterio de dependencia: primero validar
> lo construido, después corregir, después salir a internet, después producto, y la
> monetización AL FINAL (regla de Gonzalo). Detalle fino en los docs enlazados.

## Fase 0 — Validar lo recién construido (esta semana, BLOQUEA todo lo demás)

La migración a categorías está en GitHub pero solo probada con smokes de 2 categorías.
Nada de lo que sigue tiene sentido sin datos validados.

1. **Reactivar el pipeline** en el equipo actualizador + `git pull` (trae las 3 migraciones).
2. **Registrar el baseline del KPI antes de la primera corrida**: grupos comparables ≥2
   cadenas en la base del actualizador (~4.7-4.9k al 19-07).
3. **Primera corrida nocturna migrada** (la prueba de fuego): revisar
   `python -m app.estado_pipeline`, duraciones por paso, guards (que ninguna cadena haya
   dejado `.nuevo`), `reports/pipeline_category_rejections.csv` y `_quarantine.csv`.
4. **Iterar mapeos 1-2 noches**: si un nivel-2 concentra rechazos → remapear en la
   constante `CATEGORIAS` del scraper. Medir KPI después vs baseline.
5. **Vigilar el drenaje de EAN**: Unimarc nace con EAN; Jumbo (~344/noche de cuota) y
   Tottus van por backfill. Con el catálogo multiplicado, evaluar si la ventana de las
   03:00 alcanza o se amplía.

**Éxito = catálogo multiplicado + comparables subiendo + 3 noches estables.**

## Fase 1 — Corrección de errores conocidos (en paralelo con Fase 0)

| # | Problema | Acción | Ref |
|---|---|---|---|
| 1.1 | **Líder degradándose**: endpoint viejo `/v/` es legacy (Jabón 54→10, 9 categorías capadas en 48). El endpoint bueno está detrás de Akamai. | Decidir e implementar el camino anti-bot: (a) undetected-chromedriver, (b) perfil Chrome persistente con cookie `_abck`, (c) proxy residencial. El PoC del parser ya existe (`scraper_lider_browse.py`). | [lider-endpoint-nuevo.md](lider-endpoint-nuevo.md) |
| 1.2 | **Unimarc EAN 403** desde el actualizador (urllib bloqueado por WAF). Impacto menor (caché 98%) y ahora casi nulo: el scraper nuevo trae EAN directo. | Migrar `fetch_ean_unimarc` a Selenium **solo si** aparecen slugs sin EAN tras la migración; si no, cerrar como resuelto-por-diseño. | [estado-y-handoff.md](estado-y-handoff.md) |
| 1.3 | **Matching con catálogo multiplicado**: más productos = más riesgo de grupos difusos malos (ya pasó: Whiskas+Cat Chow). | Tras 2-3 noches, muestreo de los grupos difusos más grandes (script ya usado el 18-07); afinar `MARCADORES_VARIANTE`/vocabularios si aparecen mezclas nuevas. | tests `test_fase5a_marca.py` |
| 1.4 | **Categorías internas quizás quedaron chicas**: "Desayuno y Snacks" ahora recibe café+té+cereales+chocolates+galletas de 3 cadenas. | Si el matching se ve fragmentado o la UI queda desbalanceada, evaluar subdividir (requiere tocar `TODAS_LAS_CATEGORIAS` + frontend con cuidado). No antes de la Fase 0. | — |

## Fase 2 — Salir a internet (el proyecto grande; 1-2 semanas)

Hoy AhorraGo solo existe en las máquinas de Gonzalo. Esto es lo único que separa
"proyecto" de "producto". Detalle completo en [camino-a-produccion.md](camino-a-produccion.md).

1. **Sync casa→nube**: paso final del pipeline nocturno que sube `supercheck.db` al
   servidor con swap atómico (el scraping se queda en casa: IP residencial irreemplazable).
2. **Infra**: VPS chico (~USD 5/mes alcanza para FastAPI+SQLite), dominio, HTTPS.
3. **Endurecimiento**: CORS, cerrar `/diagnostico/*`, rate limiting, backups remotos.
4. **Beta real**: 2-3 usuarios (el beta tester de nuevo) usando la URL pública.
5. **Operación mínima**: uptime monitor + revisión semanal de logs.

## Fase 3 — Producto para usuarios reales

En orden de dependencias (detalle en [roadmap-producto.md](roadmap-producto.md)):

1. **Geolocalización**: qué supermercados hay cerca (hace accionable la comparación).
2. **Cuentas de usuario**: listas/historial/alertas dejan de vivir en localStorage.
3. **Alertas de precio por media histórica**: el historial ya acumula desde el 18-07
   justamente para esto (~50k puntos/día).
4. **Plan de compra**: carro óptimo multi-supermercado.
5. **Identidad**: nombre nuevo + colores ANTES de difundir públicamente (decisión
   pendiente de Gonzalo; no bloquea nada técnico).

## Fase 4 — Monetización (LO ÚLTIMO, regla explícita)

Freemium + prueba de 15 días + pasarela chilena (Webpay/MercadoPago/Flow).
**No se construye hasta que las Fases 0-3 funcionen y haya usuarios reales usándolo.**

## Transversal (siempre)

- Cadencia: cada cambio → commit → push a GitHub (fuente de verdad). El actualizador
  toma cambios solo por `git pull`.
- Tests verdes antes de cada push (hoy: 134).
- Guards anti-regresión intactos: ninguna corrida sospechosa pisa datos buenos.
- Los dos equipos no scrapean en paralelo jamás.

## Estado de tareas al 23-07-2026

- ✅ Migración 3 cadenas a categorías reales (226 subcats, commits `e9f9bff`/`4b9b147`/`9e077a0`)
- ✅ Todo el feedback del beta tester (A-G) resuelto
- ✅ Matching endurecido (marca obligatoria, variantes, combos con `+`)
- ✅ Historial de precios acumulando + herencia de formato vía EAN
- ⏳ Fase 0 esperando reactivación del pipeline
