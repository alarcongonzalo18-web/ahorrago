# Estado del proyecto y handoff — AhorraGo

> Corte al 17-07-2026 (fin de sesión larga). Este doc es el punto de entrada para retomar.
> Índice: [auditoria-2026-07-17.md](auditoria-2026-07-17.md) (qué está mal y el plan por fases) ·
> [roadmap-producto.md](roadmap-producto.md) (features nuevas) ·
> [ean-jumbo.md](ean-jumbo.md) / [ean-unimarc.md](ean-unimarc.md) (contratos de EAN) ·
> [ahorrago-contexto.md](ahorrago-contexto.md) (histórico detallado).

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

## Estado de los datos (17-07-2026, tras la actualización)

| Cadena | Productos | Precios | EAN |
|---|---|---|---|
| Jumbo | 23.726 | frescos ✅ | 1% ⏳ (backlog ~23.800) |
| Líder | 8.260 | frescos ✅ | 100% ✅ |
| Unimarc | 9.231 | frescos ✅ | 98% ✅ |
| Tottus | 8.768 | frescos ✅ | 0% ⏳ (recién sumado) |
| **Total** | **49.833** productos / 50.058 precios | | |

**Grupos comparables (≥2 cadenas): 4.968** ← *la métrica del negocio*.
Evolución: 1.562 (matching por texto) → 1.645 (fix EAN Líder) → 4.333 (EAN Unimarc) →
**4.968** (Tottus sumado). Sigue subiendo a medida que la tarea nocturna de EAN drena el
backlog de Jumbo y llena Tottus.

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

### 4. Historial de precios
`Precio` no tiene fecha ni histórico → sin esto **las alertas por media son imposibles**
(ver [roadmap-producto.md](roadmap-producto.md)) y no se puede medir deriva de precios.

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
