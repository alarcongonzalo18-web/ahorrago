# EAN de Unimarc — fuente encontrada (3ª cadena)

> Hallazgo 17-07-2026 explorando unimarc.cl con el navegador + devtools. Completa la base de EAN
> de las 3 cadenas (Líder ✓, Jumbo ✓ [ean-jumbo.md](ean-jumbo.md), Unimarc ✓). Con esto el
> matching exacto por código de barras cubre todo el catálogo comparable.

## El endpoint (limpio, sin auth)

```
GET https://bff-unimarc-ecommerce.unimarc.cl/catalog/product/search/by-slug/<slug>
```

**Headers** (todos estáticos; **no requiere sesión ni token**):

| Header | Valor |
|---|---|
| `Accept` | `application/json, text/plain, */*` |
| `channel` | `UNIMARC` |
| `source` | `web` |
| `version` | `1.0.0` |

> Sin el header `channel: UNIMARC` responde **422**. Con los 4 headers de arriba da **200 sin
> sesión** (más simple que Jumbo, que sí pide un `apiKey`).

El `<slug>` es el segmento de la URL del producto: `https://www.unimarc.cl/product/<slug>`.

**Respuesta** (JSON): el EAN está en `products[0].item.ean` (GTIN-13). El objeto `item` trae
además nombre, marca, formato, precios, etc.

## Verificado (reproducible, sin sesión)

| slug | producto | EAN (`products[0].item.ean`) |
|---|---|---|
| `arroz-g2-largo-delgad-nuestra-cocina-1kg` | Arroz G2 Nuestra Cocina 1 kg | `7848004940150` |
| `leche-entera-natural-colun-sin-tapa-1-l-2` | Leche Entera Colun 1 L | `7802920777542` |

## Otros endpoints con EAN (por si sirven)

- `POST https://bff-unimarc-ecommerce.unimarc.cl/catalog/product/search` — búsqueda **batch**;
  cada producto trae `ean`. Más eficiente (muchos por llamada) pero su contrato de body es más
  complejo; el by-slug alcanza para el backfill.
- `GET .../catalog/product/nutritional-data/<ean>` — datos nutricionales **keyeados por EAN**
  (confirma que el EAN es el identificador canónico interno).
- `/_next/data/<buildId>/search.json?q=...` — resultados de búsqueda con `ean`, pero el `buildId`
  cambia en cada deploy de Unimarc (hay que scrapearlo de la página); menos estable que el BFF.

## Integración al scraper (igual que Jumbo)

1. El scraper de Unimarc ya tiene la URL de cada producto → sacar el `<slug>` (`/product/<slug>`).
2. `GET /catalog/product/search/by-slug/<slug>` con los 4 headers → `products[0].item.ean`.
3. Guardar en la columna `ean` (normalizar con `lstrip("0")` para casar con Líder; ver
   [ean-jumbo.md](ean-jumbo.md)). El matching por EAN ya está en `app/importar_csv.py`.

## Precauciones

- Rate-limiting: un GET por producto → correr pausado, por tandas, con backoff (mismo criterio
  que Líder). El EAN no cambia → cachear y solo refrescar en catálogo nuevo.
- IP residencial.
- Si un día empieza a dar 4xx, recapturar los headers desde devtools (Network → by-slug).
