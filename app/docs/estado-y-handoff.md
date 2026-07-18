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
| Jumbo | 23.726 | frescos ✅ | 0% ⏳ |
| Líder | 8.260 | frescos ✅ | 100% ✅ |
| Unimarc | 9.231 | frescos ✅ | 0% ⏳ |
| **Total** | **41.201** productos / 41.245 precios | | |

**Grupos comparables (≥2 cadenas): 1.645** ← *la métrica del negocio*. Sube fuerte cuando se
haga el backfill de EAN de Jumbo/Unimarc.

## Automatización (ACTIVA)

Tarea programada de Windows **"AhorraGo - Actualizar productos"**, 2×/día a las **06:00 y 18:00**.
Corre `actualizar-productos.bat` → `python -m app.actualizar_productos`, que hace:
scrape Líder+Jumbo+Unimarc → validar → combinar → reconstruir base → validar.

Trae de fábrica: lock anti-concurrencia, backups previos, validaciones por cadena, **restauración
automática si falla**, y log con timestamp (que alimenta el badge de frescura de la app).

```powershell
.\programar-actualizacion-productos.ps1   # activar / reprogramar
.\pausar-actualizacion-productos.ps1      # pausar
.\actualizar-productos.bat                # correr a mano ahora
```

## 🔴 Lo más importante pendiente

### 1. Caché de EAN antes del backfill (BLOQUEANTE)
`app/backfill_ean.py` escribe el `ean` en los CSV por-cadena, **pero los scrapers los reescriben
con `ean=""` en cada corrida** → la automatización destruiría el backfill (33k requests tirados).

**Antes de correr el backfill hay que**: persistir una caché `slug -> ean` (ej. `data/ean_cache.json`)
que sobreviva a los re-scrapes, hacer que el backfill solo consulte slugs nuevos (incremental), y
enriquecer desde la caché en `combinar_supermercados` (o como paso del pipeline post-scrape).
El EAN de un producto no cambia nunca → la caché es válida para siempre.

*(Líder no tiene este problema: su EAN se reconstruye de la URL en cada `combinar`.)*

### 2. Backfill de EAN de Jumbo + Unimarc
Una vez exista la caché: `python -m app.backfill_ean all` (pausado, resumible, ~33k requests).
Es lo que hace saltar la comparabilidad. Contratos ya resueltos y verificados en
[ean-jumbo.md](ean-jumbo.md) y [ean-unimarc.md](ean-unimarc.md).

### 3. Profundidad de Líder en 9 categorías
`/v/salsas`, `/v/aceites`, `/v/pescados`, `/v/congelados`, `/v/mermeladas`, `/v/detergentes`,
`/v/condimentos`, `/v/alimentos-bebe`, `/v/vinos` topan en 48 productos: el parámetro
`?pagenumber=` **se ignora** ahí (devuelve la misma página). Hay que encontrar el endpoint
paginado real de Líder — misma técnica que se usó con Jumbo/Unimarc: abrir el sitio en el
navegador, interceptar `fetch`/XHR y mirar qué API hidrata el listado.

### 4. Historial de precios
`Precio` no tiene fecha ni histórico → sin esto **las alertas por media son imposibles**
(ver [roadmap-producto.md](roadmap-producto.md)) y no se puede medir deriva de precios.

### 5. Agregar Tottus (4ª cadena)
Sumar **Tottus** (tottus.falabella.com) al comparador. Cada cadena nueva sube la comparabilidad
y la credibilidad del "dónde comprar más barato" — hoy solo se comparan 3.

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
