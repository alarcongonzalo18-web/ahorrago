# EAN de Jumbo — fuente encontrada (2ª cadena)

> ## ⚠️ ACTUALIZACIÓN 26-07-2026: usar el catálogo VTEX, no el BFF
>
> El BFF descrito abajo **ya no sirve para volumen**: hoy bloquea en la **3ª consulta**
> seguida (el texto original hablaba de ~344/noche; eso ya no se sostiene). Con el catálogo
> por categorías reales Jumbo trae ~34.000 fichas, así que de a una nunca terminaría.
>
> **La fuente buena es el catalog_system público de VTEX**:
>
> ```
> GET https://jumbochile.vtexcommercestable.com.br/api/catalog_system/pub/products/search
>     ?fq=productId:6797&fq=productId:6782&...&_from=0&_to=49
> ```
>
> - Devuelve `items[0].ean` (EAN-13 real, verificado).
> - **Acepta 50 productos por request**, responde en ~2 s, sin cuota observada
>   (3 ráfagas seguidas: 0.0-1.9 s).
> - El `ProductId` ya viene en el listado de Constructor.io → el EAN se resuelve
>   **durante el scrape** (`_resolver_eans` en `app/scraper_jumbo_real.py`), sin backfill.
> - **El truco que costó encontrar**: `www.jumbo.cl/api/catalog_system/...` devuelve **HTML**
>   (por eso el intento previo se leyó como "410 / no es VTEX"). Hay que pegarle al host
>   interno `jumbochile.vtexcommercestable.com.br`. `jumbo.vtexcommercestable...` también
>   responde; `cencosud` devuelve `[]` y `cencosudjumbo` da 404.
>
> **Rendimiento real** (corrida del 26-07): 682 lotes, **17.051 de 34.085 productos con EAN
> (50%)**, contra los 349 que tenía la caché. En categorías populares el hit rate es ~90%;
> las de nicho tienen productos que VTEX no indexa (el fallback por `alternateIds_RefId`
> devuelve vacío, no hay ganancia ahí). Impacto: KPI de comparables **6.967 → 10.302**.
>
> El BFF de abajo sigue siendo útil para consultas sueltas (`fetch_ean_jumbo`), y la
> documentación se conserva porque describe bien el contrato del PDP.

> Hallazgo 17-07-2026 explorando jumbo.cl con el navegador + devtools. Destraba la Fase A
> (comparabilidad): Líder ya expone EAN; con Jumbo por EAN el matching exacto entre cadenas
> deja de depender del texto. Ver [auditoria-2026-07-17.md](auditoria-2026-07-17.md) y
> [ahorrago-contexto.md](ahorrago-contexto.md).

## Contexto

Jumbo.cl NO es VTEX clásico: es un frontend propio de Cencosud (SPA, bundle
`_cencosud_cencommerce_sm_web_front`) contra un BFF en `bff.jumbo.cl`. Por eso fallaron los
intentos previos (Constructor.io da `RefId` interno, la VTEX API pública da 410). El EAN **sí**
existe, en el endpoint que hidrata la ficha (PDP).

## El endpoint

```
POST https://bff.jumbo.cl/catalog/pdp
```

**Headers** (todos estáticos salvo x-trace-id, que es un UUID cualquiera):

| Header | Valor |
|---|---|
| `Content-Type` | `application/json` |
| `Accept` | `application/json, text/plain, */*` |
| `apiKey` | `be-reg-groceries-jumbo-catalog-w54byfvkmju5` |
| `x-client-platform` | `web` |
| `x-client-version` | `3.3.98` |
| `x-trace-id` | cualquier UUID v4 |

> El `apiKey` es una clave pública del cliente web (no credencial de usuario; se capturó sin
> sesión iniciada). Puede rotar/versionarse: si un día da 401, recapturarla desde devtools →
> Network → cualquier request a `/catalog/pdp` → headers. Igual que `x-client-version`.

**Body**:
```json
{"slug": "<slug-del-producto>", "store": "jumboclj512"}
```
El `slug` es el segmento de la URL del producto: `https://www.jumbo.cl/<slug>/p`. El `store`
`jumboclj512` es la tienda por defecto observada.

**Respuesta** (JSON): el EAN está en `items[].ean` (GTIN-13). También trae `reference` (código
interno), `productId`, `slug`, precios, specifications, etc.

## Verificado (reproducible, sin sesión)

| slug | producto | EAN (`items[0].ean`) |
|---|---|---|
| `m-ideal-bco-xl-750` | Pan Molde Ideal Blanco XL 750 g | `7803473002662` |
| `leche-descremada-colun-1-l-2` | Leche Colun Descremada 1 L | `7802920000084` |

## Cómo integrarlo al scraper

1. El scraper de Jumbo ya obtiene productos (vía Constructor.io) con su URL → **de la URL se saca
   el `slug`** (`.../<slug>/p`). Para el catálogo ya scrapeado, el slug sale del CSV existente.
2. Por cada producto: `POST /catalog/pdp` con el slug → leer `items[0].ean`.
3. Guardar el EAN en la columna `ean` (misma que Líder). El matching por EAN ya está implementado
   (`unificar_producto_base_por_ean` en `app/importar_csv.py`, `producto_base = "ean:<código>"`).
4. **Normalización**: Líder guarda el EAN sin ceros a la izquierda (`extraer_ean_lider` en
   `app/url_utils.py`). Jumbo devuelve GTIN-13 tal cual (ej. `7802920000084`). Aplicar el mismo
   `lstrip("0")` para que casen (Chile suele usar prefijo `780`, sin ceros líderes, así que en la
   práctica ya coinciden — validar con un par de productos que existan en ambas).

## Precauciones

- **Rate-limiting**: es un POST por producto (~22k en Jumbo). Correr pausado y por tandas, con
  backoff (mismo criterio que el fix de Líder, [ahorrago-contexto.md](ahorrago-contexto.md)).
  Idealmente cachear y solo refrescar EAN cuando cambie el catálogo (el EAN no cambia).
- Correr desde IP residencial (no datacenter), como el resto del scraping.
- El `apiKey`/`x-client-version` pueden cambiar con deploys de Jumbo → si empieza a dar 401,
  recapturar (una línea en devtools).

## Pendiente

- **Unimarc** (3ª cadena, VTEX): repetir la exploración (abrir un PDP, mirar la request que
  hidrata la ficha, buscar `ean`/`gtin`). Con Jumbo+Líder por EAN ya sube la comparabilidad;
  Unimarc la completa.
- Backfill de EAN en el catálogo Jumbo existente y re-`reconstruir` → medir con
  `reporte_cobertura` cuánto sube el % comparable.
