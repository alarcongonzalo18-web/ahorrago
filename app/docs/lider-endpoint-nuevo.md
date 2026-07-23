# Líder: endpoint nuevo (SPA de Walmart) y por qué el scraper viejo decae

> Hallazgo del 23-07-2026 investigando por qué el guard bloqueaba Líder cada noche.

## Qué pasó

Líder migró su catálogo a la **plataforma de Walmart sobre Next.js** (un SPA, mismo
patrón que Uber Eats y otras apps: el HTML es un cascarón y los productos vienen en
JSON). El scraper actual (`app/scraper_lider.py`) usa el endpoint **viejo `/v/<cat>`**,
que sigue respondiendo pero quedó **legacy y parcial**: algunas categorías ya no se
sirven completas ahí (ej. **Jabón** cayó de ~54 a ~10 y no vuelve; 9 categorías topan
en 48 porque `?pagenumber=` se ignora).

## El endpoint bueno

- **Listado por categoría:** `GET https://super.lider.cl/browse/<rubro>/<categoria>/<ids>?page=N`
- **Búsqueda:** `GET https://super.lider.cl/search?q=<termino>&page=N`
- Los datos están en el `<script id="__NEXT_DATA__">` de la respuesta:
  `props.pageProps.initialData.searchResult.itemStacks[0]`
  - `.count` → total real de la categoría
  - `.items[]` → productos; cada uno con:
    - `usItemId` → **el GTIN/EAN** (14 dígitos, ej. `00780500031555` = EAN `780500031555`)
    - `name`, `brand`, `canonicalUrl` (`/ip/<cat>/<usItemId>`)
    - `priceInfo` → `itemPrice`, `linePrice` (oferta), `wasPrice`, `unitPrice`, `savingsAmt`
    - `imageInfo.thumbnailUrl`
  - `searchResult.paginationV2.maxPage` → **paginación real** (páginas distintas, verificado)

Los IDs de categoría del árbol `/browse/` salen del home (`a[href*="/browse/"]`), ej.
`higiene-y-cuidado-personal/jabones/72387472_38253071`. `count=144-226` para Jabón,
contra los ~10 del endpoint viejo.

## ⚠️ El bloqueo: Akamai Bot Manager

El endpoint nuevo está protegido y **bloquea la automatización**. Probado el 23-07:

| Cliente | Resultado |
|---|---|
| urllib (con y sin headers de navegador completos) | challenge "Robot or human?" |
| Selenium **headless** (`--headless=new`) | bloqueado |
| Selenium **no-headless** + flags anti-automation | bloqueado |
| Navegador real (perfil normal) | **pasa** |

El viejo `/v/` **sí** pasa desde urllib (por eso el scraper actual funciona). O sea el
problema para migrar no es encontrar el endpoint —está acá— sino **vencer el anti-bot**.

## Caminos para migrar (pendiente de decidir)

1. **undetected-chromedriver** — Selenium parcheado para evadir la detección de Akamai.
   Es la vía más directa; nueva dependencia; cat-and-mouse (puede romperse en updates).
2. **Perfil de Chrome real persistente** — resolver el challenge una vez a mano, guardar
   el `user-data-dir` con la cookie `_abck` válida y reusarlo; refrescarla cuando caduque.
3. **Proxy residencial** — ataca el lado IP, no el fingerprint; suma costo y complejidad.

Un PoC del parser (que ya funciona con `__NEXT_DATA__`) quedó en
`app/scraper_lider_browse.py` (no cableado al pipeline); solo le falta un transporte
que pase Akamai.

## Mitigación aplicada mientras tanto (23-07-2026)

En vez del guard todo-o-nada que dejaba la base congelada, `scraper_lider.py` ahora:

- **Exime** las categorías degradadas permanentes (`SUBCATEGORIAS_DEGRADADAS`, hoy `Jabon`)
  para que una categoría muerta no bloquee la corrida.
- **Reintenta** una vez, tras un cooldown largo, las categorías que caen >50% (throttling,
  ej. Cecinas).
- **Carry-forward por categoría** (`fusionar_preservando`): si tras el reintento una
  categoría sigue caída, conserva sus filas **previas** y publica el resto fresco. Así
  Líder siempre publica y ninguna categoría retrocede.
