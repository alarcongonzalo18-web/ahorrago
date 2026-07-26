# Estado del proyecto y handoff — AhorraGo

> Corte al 17-07-2026 (fin de sesión larga). Este doc es el punto de entrada para retomar.
> Índice: [migracion-equipo.md](migracion-equipo.md) (pasar a otro equipo) ·
> [camino-a-produccion.md](camino-a-produccion.md) (qué falta para salir) ·
> [auditoria-2026-07-17.md](auditoria-2026-07-17.md) (qué está mal y el plan por fases) ·
> [roadmap-producto.md](roadmap-producto.md) (features nuevas) ·
> [ean-jumbo.md](ean-jumbo.md) / [ean-unimarc.md](ean-unimarc.md) (contratos de EAN) ·
> [ahorrago-contexto.md](ahorrago-contexto.md) (histórico detallado).

## Migración a categorías reales — LAS 3 CADENAS, 23-07-2026

Jumbo, Unimarc y Tottus dejaron de buscar por ~50 keywords y ahora **recorren el árbol de
categorías real** de cada sitio (de ~150 keywords sueltas a **226 subcategorías nivel-2**,
solo rubros de consumo). Multiplica el catálogo y, con él, los grupos comparables (el KPI).

| Cadena | Transporte nuevo | Subcats | EAN en listado | Commit |
|---|---|---|---|---|
| **Unimarc** | Selenium por `/category/<slug>?page=N`, parsea `__NEXT_DATA__` | 66 | **SÍ, directo** | `e9f9bff` |
| **Jumbo** | `ac.cnstrc.com/browse/group_id/<id>` (misma key del `.env`) | 89 | no (backfill, igual que antes) | `4b9b147` |
| **Tottus** | `/tottus-cl/lista/CATG<id>/…?page=N`, urllib sin WAF | 71 | no (backfill) | `9e077a0` |

- **Por qué Unimarc quedó en Selenium** (no BFF, contra el plan inicial): el BFF capa a 50
  productos/categoría y no pagina; el HTML y `_next/data` dan **403 (WAF Akamai)** desde
  urllib — el WAF fingerprintea el cliente TLS, no basta la cookie. Selenium (ya dependencia)
  es la única vía; optimizado con `page_load_strategy=eager` + sin imágenes, ~2.5 s/página.
  Bonus: el listado trae EAN → los productos de Unimarc **nacen comparables**, sin backfill.
- **Guards reforzados** en las 3: filtro de baseline (`solo_subcategorias`, para que el
  renombre de taxonomía no dispare falsas caídas) + carry-forward por subcategoría + red de
  seguridad de totales (si el total baja tras migrar, deja `.nuevo` y no pisa).
- **Mapeos curados** a las 12 categorías internas (excluidos Electrohogar/Ferretería/
  Librería/Farmacia). El árbol de cada cadena se reproduce con
  `python -m app.descubrir_taxonomia <unimarc|jumbo|tottus>`.
- **134 tests** (baseline 116 → +18). Cada cadena con smoke real de 2 categorías verificado.

### Validación real de Tottus (25/26-07-2026) — LA MIGRACIÓN FUNCIONA

Corrida completa de Tottus con las 71 categorías reales, hecha **desde el equipo de
trabajo** (el actualizador estaba apagado; se trajo la base autoritativa por pendrive).

| | Baseline | Post-migración |
|---|---:|---:|
| **Comparables (KPI)** | 6.967 | **7.119 (+152)** |
| Precios Tottus | 8.904 | 10.046 (+13%) |
| Subcategorías Tottus | 49 | 71 |
| Cobertura EAN | 52% | 53% |

**El KPI baja antes de subir**: los productos nuevos llegan sin EAN (el catálogo llega
antes que su identidad) y recién al drenar el backfill se vuelven comparables. Secuencia
medida: 6.967 → 6.589 (tras el scrape) → **7.119** (tras backfill de 2.403 slugs).
Al planificar las otras cadenas, contar esa fase intermedia como normal.

### 🐛 Bug encontrado por la corrida real: el guard confundía migración con regresión

`solo_subcategorias` filtra por NOMBRE, y eso no alcanzaba. 8 de las 49 subcategorías
viejas de Tottus sobrevivieron con el mismo nombre pero **otro significado**: la vieja
"Bebidas" eran los 826 resultados de buscar la keyword `bebida` (de cualquier rubro) y la
nueva son los 180 de la categoría real. El guard leyó `826 → 180` como regresión, hizo
carry-forward de las filas viejas y dejó **1.674 productos duplicados y mal categorizados**
(papilla de bebé archivada dentro de "Verduras").

**Fix** (commit `52cf575`): `es_migracion_de_taxonomia()` — si menos de la mitad de las
subcategorías previas sobrevive (acá: 8/49 = 16%), la corrida es una migración, no hay
contra qué comparar y el guard se aparta; vuelve solo en la corrida siguiente. Aplicado a
las 3 cadenas. Tras el fix: 10.931 filas limpias, duplicados 1.674 → 420 (y esos 420 son
legítimos: el sitio lista el mismo pañal de adulto en dos categorías).

### ⚠️ Pendiente: primera corrida nocturna migrada (la prueba de fuego)

Los smokes fueron de 2 categorías/cadena. **La primera corrida nocturna completa es la
validación real** — ahí se ve el catálogo multiplicado. Al reactivar el pipeline:
`git pull` en este equipo (trae las 3 migraciones) y revisar tras la primera noche:
`python -m app.estado_pipeline`, duraciones por paso, `reports/pipeline_category_rejections.csv`
(si un nivel-2 concentra rechazos → remapear en la constante `CATEGORIAS` del scraper), y
**grupos comparables antes/después**. Los guards protegen: una cadena que falle deja `.nuevo`
sin pisar los datos buenos.

## Migración de equipo — COMPLETADA 19-07-2026

**Este equipo es el dueño oficial de los datos desde hoy.** Se migró el pipeline siguiendo
[migracion-equipo.md](migracion-equipo.md) y quedó verificado:

- `supercheck.db`, `.env` y los `data/*_real.csv` se copiaron del paquete de migración a la
  raíz; el `supercheck.db` se validó por SHA256 contra el origen (idéntico). El historial
  llegó intacto: **101.573 puntos en 2 días** al momento de migrar.
- `python -m app.doctor`: todo verde salvo el aviso de Unimarc (ver abajo).
- Prueba corta real `--solo tottus`: OK (12.917 productos, historial +87 puntos).
- Las **5 tareas nocturnas** quedaron programadas y en `Ready` (Tottus 21:00, Unimarc 22:30,
  Jumbo 00:00, Líder 02:00, EAN 03:00).
- **El equipo viejo quedó con sus tareas deshabilitadas** (`pausar-actualizacion-productos.ps1`),
  para no scrapear los dos en paralelo. Nunca copiar su `supercheck.db` sobre la de este equipo.

### ⚠️ Hallazgo: Unimarc EAN (urllib) bloqueado desde este equipo (403)

El chequeo de conectividad de `app.doctor` marca **`[AVISO] Unimarc (EAN) — BloqueoError`**: el
BFF (`bff-unimarc-ecommerce.unimarc.cl`) responde **403 Access Denied** al cliente `urllib` de
`app.ean_fetch.fetch_ean_unimarc`. Desde un navegador real el mismo endpoint responde 200 (con
headers `source: WEB` + `version`), o sea **el contrato no cambió**: es un bloqueo de borde
(Akamai) contra el fingerprint/IP del cliente Python, no un bug de código.

- **Precios de Unimarc: OK** — el scraper usa Selenium (Chrome real), que el WAF no bloquea. La
  tarea nocturna de Unimarc (22:30) no se ve afectada por esto.
- **EAN de Unimarc por urllib: bloqueado** — sólo afecta el backfill incremental de EAN. Impacto
  **menor**: la caché de Unimarc ya está al **98%**, así que casi no quedan slugs por consultar.
- Si en algún momento hace falta recuperar ese 2% restante: verificar IP residencial del equipo,
  o migrar `fetch_ean_unimarc` a Selenium como los precios.

## Dónde está todo

| Qué | Dónde |
|---|---|
| Repo (fuente de verdad) | GitHub: `alarcongonzalo18-web/ahorrago`, rama `main` |
| Working copy | `E:\ahorrago` |
| Copia espejo local | `E:\ahorrago-main` (clon git completo, se refresca con robocopy) |
| Entorno Python | `E:\ahorrago\.venv` (deps de `requirements.txt` + selenium/bs4) |
| Base de datos | `E:\ahorrago\supercheck.db` (SQLite, **no versionada**, se regenera) |
| CSV de datos | `data/*_real.csv`, `data/productos_supermercados.csv` (**no versionados**) |
| Backups automáticos | `backups/productos_<timestamp>/` (DB + 4 CSV, antes de cada corrida) |
| Logs del pipeline | `logs/actualizacion_productos_<timestamp>.log` |
| Secretos | `.env` (gitignoreado) — hoy solo `JUMBO_API_KEY` |

## Estado de los datos (18-07-2026, tras el fix de matching)

| Cadena | Precios | Frescura | EAN |
|---|---|---|---|
| Jumbo | 23.734 | frescos ✅ | 1% ⏳ (backlog ~23.800, drena a las 03:00) |
| Unimarc | 9.231 | frescos ✅ | 98% ✅ |
| Tottus | 8.818 | frescos ✅ | 0% ⏳ (backfill arranca solo 03:00) |
| Líder | 8.280 | frescos ✅ | 100% ✅ |
| **Total** | **49.850** productos / 50.063 precios | | |

**Grupos comparables (≥2 cadenas): 4.345** ← *la métrica del negocio*.
De esos, **3.528 por EAN** (identidad exacta, confiables) y 817 difusos.

Evolución: 1.562 (texto) → 1.645 (fix EAN Líder) → 4.333 (EAN Unimarc) → 4.968 (Tottus) →
**4.345 (18-07: limpieza de matching)**. La baja fue deliberada: los grupos "en 4 cadenas"
eran falsos positivos (Whiskas agrupado con Cat Chow; vino de 750 cc con el de 375; café
descafeinado con el normal). Se endureció el matching difuso — exigir marca en ambos lados,
no recortar el tamaño de la clave, marcadores de variante simétricos, cerrar el escape
`or score >= 82` — y cayeron 623 comparaciones incorrectas. **Los grupos por EAN no se
tocaron**: 3.528 antes y después. El grupo difuso más grande pasó de 35 productos a 5.
Sigue subiendo a medida que la tarea nocturna de EAN drena Jumbo y llena Tottus.

## Automatización (ACTIVA)

**Tres tareas programadas de Windows, una por cadena, escalonadas de noche:**

| Tarea | Qué hace | Hora |
|---|---|---|
| `AhorraGo - Actualizar Tottus` | scrape Tottus + publicar | **21:00** |
| `AhorraGo - Actualizar Unimarc` | scrape Unimarc + publicar | **22:30** |
| `AhorraGo - Actualizar Jumbo` | scrape Jumbo + publicar | **00:00** |
| `AhorraGo - Actualizar Lider` | scrape Líder + publicar | **02:00** |
| `AhorraGo - EAN` | backfill de EAN (las 3 cadenas con caché) + publicar | **03:00** |

La tarea de **EAN va última, después de los scrapes**, para trabajar sobre los CSV recién
actualizados y capturar también los productos nuevos de la noche. Es **incremental**: consulta
sólo los slugs que falten, drena lo que la cuota de Jumbo permita (~344 por ventana) y retoma
donde quedó. Así el backlog de Jumbo (~23.800) se agota solo en varias noches y después queda
como mantenimiento de productos nuevos. Corre `backfill-ean.bat all`, que hace backfill y luego
publica con `--sin-scrape` (sin pedirle nada extra a los retailers).

Cada una corre `actualizar-productos.bat --solo <cadena>` → scrape de esa cadena + combinar +
reconstruir, así la base queda publicada después de cada una (no hay que esperar a las tres).

**Por qué escalonado** (antes era una corrida única de ~1.5 h): reparte la carga sobre los
retailers, evita que una cadena caída arrastre a las otras, y con corridas más cortas se topa
menos la cuota (Jumbo corta a los ~344 requests). **Por qué estos horarios**: Líder y Jumbo son
los de más público, así que van en la ventana más profunda de bajo tráfico; Unimarc tiene menos
público y tolera el horario más temprano.

> El espaciado de 1.5 h es **conservador** hasta tener duraciones reales. El log ahora mide cada
> paso (`-- Scraper X: N min --`); con esos números se puede ajustar. Si una corrida se pasa de
> su ventana, la siguiente se saltea por el lock y se recupera con `StartWhenAvailable`.

Cada corrida trae de fábrica: lock anti-concurrencia, backups previos, validaciones por cadena,
**restauración automática si falla**, y log con timestamp (que alimenta el badge de frescura).

```powershell
.\programar-actualizacion-productos.ps1   # activar / reprogramar
.\pausar-actualizacion-productos.ps1      # pausar
.\actualizar-productos.bat                # correr a mano ahora (todo)
```

### Actualizaciones individuales

No hace falta re-scrapear las 3 cadenas (~1.5 h) para arreglar una. El orquestador
acepta corridas parciales **conservando toda la maquinaria de seguridad** (lock,
backups, validaciones, restauración automática):

```bash
python -m app.actualizar_productos                     # todo (lo que corre la tarea)
python -m app.actualizar_productos --solo lider        # una sola cadena
python -m app.actualizar_productos --solo jumbo,unimarc
python -m app.actualizar_productos --sin-scrape        # solo combinar + reconstruir
```

- **`--solo <cadena>`**: cuando una cadena falló, cambió su sitio, o se le tocó el scraper.
  Las otras conservan sus datos en disco (la validación igual exige que las 3 tengan datos).
- **`--sin-scrape`**: publica a la base datos que ya están en disco, sin pedirle nada a los
  retailers. Es el caso después de `app.backfill_ean` (que solo toca la caché de EAN) o tras
  editar un CSV a mano.

Combinar y reconstruir corren **siempre**: son rápidos y son los que publican el cambio.

> No usar los scrapers sueltos (`python -m app.scraper_lider`) salvo para depurar: saltean el
> lock, los backups y las validaciones, y dejan la base sin actualizar.

### ⚠️ Dependencia del equipo encendido

La tarea programada **sólo corre si el PC está prendido**. Mitigaciones ya configuradas:

- **`WakeToRun`**: despierta el equipo si está **suspendido o hibernando** (el equipo soporta
  S3 e hibernación). Requiere que el plan de energía permita *temporizadores de reactivación*:
  Panel de control → Opciones de energía → Cambiar la configuración del plan → Cambiar la
  configuración avanzada → Suspender → **Permitir temporizadores de reactivación → Habilitar**.
- **`StartWhenAvailable`**: si el equipo estaba **apagado del todo**, la corrida se ejecuta
  apenas se prende, para no quedarse un día entero sin actualizar.

**Lo que NO resuelve**: nada puede despertar un equipo apagado por completo. Y si se prende
a las 10:00, el scrape de ~1.5 h corre en horario de alto tráfico — justo lo que se quiso evitar
al mover la tarea a las 03:00.

**Solución real (pendiente de decidir): mover el pipeline a algo siempre encendido.**

| Opción | Costo | Pros / contras |
|---|---|---|
| **Mini PC / Raspberry Pi / notebook viejo en casa** | ~$50-100 una vez, ~5 W | ✅ **Mantiene la IP residencial**, que es lo crítico. Es la solución clásica para este problema. El pipeline es Python portable; Selenium corre con chromium |
| **VPS / nube** | ~$5/mes | ❌ **IP de datacenter**: los retailers bloquean mucho más fácil (Jumbo ya nos throttleó desde IP residencial). Necesitaría proxies residenciales = más costo y fragilidad |
| **Dejar el PC suspendido** | $0 | Funciona con lo ya configurado, pero depende del hábito de no apagarlo |

**Cuando se despliegue la app**, el patrón correcto es el split: la **app** (backend + frontend)
en la nube, y el **scraper en casa** desde IP residencial, subiendo los datos. No mover el
scraping a la nube.

## 🔴 Lo más importante pendiente

### ~~1. Caché de EAN~~ — HECHO 17-07-2026
`app/ean_cache.py` guarda `data/ean_cache.json` (`{cadena: {slug: ean}}`), que **sobrevive a los
re-scrapes**. `app/backfill_ean.py` la puebla consultando sólo slugs nuevos (incremental), y
`combinar_supermercados` enriquece cada fila desde ahí. Un valor `""` significa "ya se consultó y
no tiene EAN", para no volver a pedirlo nunca.

Verificado end-to-end con datos reales: la misma leche Colun quedó unificada bajo
`producto_base = 'ean:7802920777542'` en las 3 cadenas, con nombres que el matching textual jamás
habría unido ("Leche Entera Natural Caja 1 L 1 L Colun" / "Leche Colun Entera 1 L" /
"Leche entera natural colun sin tapa 1 l").

### 2. Backfill de EAN de Jumbo + Unimarc ← SIGUIENTE
Ya está desbloqueado: `python -m app.backfill_ean all` (pausado, resumible, incremental).
Faltan ~33k slugs (24.139 Jumbo + 9.247 Unimarc); a ~0.5 s cada uno son varias horas, pero se
puede cortar y retomar cuando sea (la caché se guarda cada 100). Es **lo que hace saltar la
comparabilidad**. Contratos en [ean-jumbo.md](ean-jumbo.md) y [ean-unimarc.md](ean-unimarc.md).

> Nota: conviene correrlo cuando la tarea programada no esté por dispararse (06:00 / 18:00),
> para no competir por ancho de banda ni sumar carga a los retailers al mismo tiempo.

### 3. Profundidad de Líder en 9 categorías
`/v/salsas`, `/v/aceites`, `/v/pescados`, `/v/congelados`, `/v/mermeladas`, `/v/detergentes`,
`/v/condimentos`, `/v/alimentos-bebe`, `/v/vinos` topan en 48 productos: el parámetro
`?pagenumber=` **se ignora** ahí (devuelve la misma página). Hay que encontrar el endpoint
paginado real de Líder — misma técnica que se usó con Jumbo/Unimarc: abrir el sitio en el
navegador, interceptar `fetch`/XHR y mirar qué API hidrata el listado.

### ~~4. Historial de precios~~ — HECHO 17-07-2026
`app/historial_precios.py` + tabla `historial_precios` con `clave` estable (EAN o nombre
normalizado, NO ids que cambian en cada reconstrucción). Snapshot diario idempotente desde el
pipeline. Al 18-07: 50.050 puntos, 1 día — la serie crece sola cada noche.

### ~~6. Matching difuso: packs vs unidad~~ — HECHO 19-07-2026
Tras las dos rondas de endurecimiento del 18-07 (exigir marca, no recortar tamaño, marcadores
de variante simétricos, cerrar el escape `or score >= 82`, tokens propios por lado), el caso
que queda: `Pack Coca-Cola 3L + Fanta` se agrupa con `Coca-Cola 3L` sola, porque `pack` está
en `RELLENO` (`app/matching.py`) — se puso ahí para que "Pack 6 un" vs "6 un" no separara
productos iguales. Fix propuesto: tratar `pack` como marcador de variante **solo cuando el
nombre trae un `+`** (combo de productos distintos), no cuando es multipack del mismo.
Bajo volumen; los grupos difusos hoy topan en 5 productos.

### ~~5. Agregar Tottus~~ — HECHO 18-07-2026
Integrado: `app/scraper_tottus.py` (urllib puro, sin navegador ni API key), EAN vía
`okayToShopBarcodes`, y enganchado a backfill, combinar, pipeline (`--solo tottus`) y a la
agenda nocturna (21:00). Contrato en [tottus.md](tottus.md). **Falta**: sumarlo al filtro de
supermercados del frontend, y que la tarea de EAN llene su caché (arranca sola a las 03:00).

Requiere lo mismo que ya se resolvió para las otras: (a) encontrar de dónde salen los productos
y precios (abrir el sitio, interceptar `fetch`/XHR y ver qué API hidrata el listado — así se
resolvieron Jumbo y Unimarc), (b) **encontrar su fuente de EAN**, que es lo que la hace
comparable de verdad, (c) escribir `app/scraper_tottus.py` siguiendo el patrón de los otros
(mismas columnas de CSV, `is_valid_row`, backoff y guard anti-regresión), y (d) sumarla a
`FUENTES` en `combinar_supermercados.py`, a `RAW_FILES`/`STEPS` en `actualizar_productos.py`,
y al filtro de supermercados del frontend.

Ojo: Tottus es del grupo Falabella, así que su stack probablemente no se parezca ni al de
Cencosud (Jumbo) ni al de SMU (Unimarc) — hay que investigarlo de cero.

## Arquitectura: por qué hay BD y no consulta 100% en vivo

Se evaluó consultar las cadenas en vivo por búsqueda (técnicamente posible: sus BFF responden).
Se descartó como modelo único porque: (a) el rate-limiting escala con los usuarios y desde IP de
datacenter bloquean rápido; (b) **el problema difícil es el matching**, no el fetch — saber que el
mismo producto es el mismo entre cadenas requiere el índice EAN/`producto_base` guardado;
(c) sin datos guardados no hay historial → no hay alertas; (d) si una cadena cambia su API, se
rompe en vivo frente al usuario.

**Rumbo recomendado: híbrido** — BD local como *índice de identidad* (refrescado por el pipeline)
+ *precio en vivo bajo demanda* solo para los pocos productos que el usuario compara, con caché
corto. `app/ean_fetch.py` ya le pega producto-por-producto a los BFF: extenderlo para traer precio
en vivo es un paso chico.

## Convenciones de trabajo (mantener)

- **Cadencia**: cada cambio → commit → `git push origin main` → refrescar `E:\ahorrago-main`
  (robocopy /MIR excluyendo `__pycache__ .pytest_cache venv .venv logs backups *.pyc *.db .env`).
- **Antes de tocar código**: mostrar el plan y esperar aprobación. Commits chicos y validables.
- **Verificar de verdad**: correr los tests (hoy 70, `python -m pytest`), y cuando sea UI probar en
  el navegador. No declarar algo funcionando sin haberlo ejercitado.
- **Reportar honesto**: si algo quedó a medias o no se pudo verificar, decirlo.
- **Scraping**: pausado, con backoff, desde IP residencial. Nunca pisar datos buenos con una
  corrida sospechosa (para eso está el guard anti-regresión de `scraper_lider`).
- **Métrica que manda**: grupos comparables (≥2 cadenas), no el total de productos.
