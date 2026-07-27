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

## ✅ AKAMAI VENCIDO (26-07-2026): undetected-chromedriver

El camino 1 de la lista de abajo **funciona**. `pip install undetected-chromedriver`
(+ `setuptools<81`: uc importa `distutils`, que Python 3.14 ya no trae) y:

```python
driver = uc.Chrome(options=opts, use_subprocess=True, version_main=150)
```

- **`version_main` es obligatorio**: uc baja el driver de la última versión de Chrome y
  si no coincide con el instalado tira `SessionNotCreatedException`.
- **No usar headless**: es una de las señales que mira el anti-bot.
- Verificado contra `/browse/higiene-y-cuidado-personal/jabones`: **`count=143`,
  `maxPage=4`, sin challenge** — contra los ~10 que devuelve `/v/jabones`.

Transporte en `app/scraper_lider_browse.py` (`crear_driver` / `bajar_categoria`).

### Formato de precios del SPA (distinto al endpoint viejo)

`priceInfo` los entrega **formateados como string**, no numéricos:

```json
{"itemPrice": "$14.690", "linePrice": "$11.690", "wasPrice": "$14.690",
 "savings": "Ahorra $3.000", "savingsAmt": 3000}
```

`itemPrice`/`wasPrice` = precio de lista · `linePrice` = **lo que se paga**.
`_a_entero()` los normaliza a int, como en las otras 3 cadenas.

### ⛔ EL TECHO: `maxPage=4` → 192 productos por categoría (26-07-2026)

Medido corriendo las 92 subcategorías nivel-2: **`paginationV2.maxPage` es 4 en todas**,
o sea 48 × 4 = **192 productos como máximo por categoría**, sin importar su `count` real.

Eso invierte el resultado según el tamaño de la categoría:

| Categoría | Productos reales | Endpoint viejo `/v/` | `/browse` nivel-2 |
|---|---:|---:|---:|
| Jabones | 143 | 10 | **136** ✅ |
| Leche | 318+ | **318** | 171 🔴 |
| Verduras | ~400 | 350+ | 199 🔴 |
| Quesos | 400+ | — | 244 🔴 |

Por eso la corrida completa dio **+220% en higiene/limpieza/mascotas** (categorías chicas,
que el endpoint viejo servía mal) y **−60% en alimentos** (categorías grandes, que topan).
El total sube (8.646 → 11.880 únicos, 100% EAN) pero el catálogo queda deformado: para un
comparador de supermercados, perder dos tercios de lácteos y carnes es peor que no migrar.
**Por eso no se publicó** (`data/lider_browse_nuevo.csv` quedó aparte, sin tocar el CSV bueno).

**Solución: bajar a nivel 3 donde el nivel 2 tope.** El árbol tiene sub-subcategorías
(`/browse/<rubro>/<sub>/<sub-sub>/<id_id_id>`) y cada una tiene su propio techo de 192.
En vez de pedir "Leche" (318 → se corta), pedir sus hijas por separado. Criterio de corte:
si una categoría nivel-2 llega a `maxPage=4`, reemplazarla por sus hijas nivel-3.

### El árbol de categorías (resuelto)

El sitio **no expone los paths `/browse/<rubro>/<sub>/<ids>`** por ninguna vía accesible:

| Intento | Resultado |
|---|---|
| Links `/browse` en el HTML del home | **0** |
| `sitemap.xml` / `sitemap_index.xml` | vacíos |
| Clic en el botón "Categorías" y releer el DOM | **0** links nuevos |
| `emptyCartNavMenuLinks` del `bootstrapData` | trajo el menú **una vez**, vacío en la corrida siguiente (A/B) |

Los ids existen (Jabones es `72387472_38253071`) pero el menú se hidrata por estado
interno de JS sin dejar `href`. **Próximo intento**: capturar el tráfico de red del SPA
(performance log de Chrome / CDP) al abrir el menú, para ver qué endpoint devuelve la
taxonomía. Alternativa: navegar el menú a mano una vez y anotar los ~90 paths.

## Caminos para migrar (el 1 ya está resuelto)

1. ~~**undetected-chromedriver**~~ — **FUNCIONA**, ver arriba.
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
