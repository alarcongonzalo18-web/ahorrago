# Tottus — cómo funciona (4ª cadena)

> Research 18-07-2026. **Conclusión: es la más fácil de las cuatro.** Sin Selenium, sin apiKey,
> sin reconstruir dígito verificador. Todo sale de HTML + `__NEXT_DATA__` con `urllib` puro.
> Relacionado: [ean-jumbo.md](ean-jumbo.md) · [ean-unimarc.md](ean-unimarc.md) · [estado-y-handoff.md](estado-y-handoff.md)

## El stack

Tottus (grupo Falabella) corre un frontend **Next.js**: cada página trae todos sus datos
embebidos en `<script id="__NEXT_DATA__">`. No hace falta navegador ni ejecutar JS: se pide el
HTML y se parsea ese JSON. Sólo requiere un **User-Agent de navegador**.

## 1. Listado / búsqueda (productos + precios)

```
GET https://www.tottus.cl/tottus-cl/buscar?Ntt=<termino>&page=<N>
```

De `__NEXT_DATA__`:
- **`props.pageProps.results`** → array de productos (**48 por página**)
- **`props.pageProps.pagination`** → `{count, perPage, totalPerPage, currentPage}`

`count` es el **total real de resultados**, así que se sabe de antemano cuántas páginas pedir
(`ceil(count / perPage)`). Es mejor que Líder, donde había que avanzar a ciegas hasta que una
página viniera vacía.

Campos útiles de cada producto:

| Campo | Ejemplo |
|---|---|
| `displayName` | `Leche Entera Natural Colun 1 L` |
| `productId` / `skuId` | `112737597` / `112737598` |
| `url` | `https://www.tottus.cl/tottus-cl/articulo/112737597/leche-natural-colun-st-1-lt` |
| `brand` | `COLUN` |
| `prices[0].price[0]` | `"1.390"` (string con separador de miles) |
| `prices[0].pum` | precio por unidad: `{label:"LT", price:["1.390"]}` |
| `measurements.format` | `1 LT` |
| `availability`, `promotions`, `badges` | stock y promos |

Trae marca, formato y precio por unidad ya calculados — más completo que otras cadenas.

## 2. EAN (ficha de producto)

```
GET <url del producto>
```

De `__NEXT_DATA__`:

```
props.pageProps.productData.variants[0].okayToShopBarcodes[0]   ->  EAN-13
```

**Verificado**: la Leche Entera Natural Colun 1 L da `7802920777542`, **el mismo EAN** que ya
tenemos para ese producto en Líder, Jumbo y Unimarc. Es decir, entra directo al matching
existente sin normalización especial.

> El nombre del campo (`okayToShopBarcodes`) no menciona "ean" ni "gtin", por eso no aparece
> buscando esas palabras. Es un array: puede traer más de un código.

## Comparación con las otras cadenas

| | Listado | EAN | Dificultad |
|---|---|---|---|
| **Tottus** | HTML + `__NEXT_DATA__` | ficha, `okayToShopBarcodes` | 🟢 la más simple |
| **Jumbo** | API Constructor.io (necesita `key`) | `POST bff/catalog/pdp` con `apiKey`, **cuota dura ~344** | 🔴 la más dura |
| **Unimarc** | Selenium + BeautifulSoup | `GET bff .../by-slug` (sin auth) | 🟡 lenta (navegador) |
| **Líder** | HTML + JSON-LD | de la URL, **reconstruyendo dígito verificador** | 🟡 paginación irregular |

## Qué falta para integrarla

1. **`app/scraper_tottus.py`** siguiendo el patrón de los otros: mismas columnas de CSV
   (`categoria, subcategoria, nombre, precio, precio_normal, precio_oferta, precio_referencia,
   promocion, url, imagen_url, ean`), `is_valid_row`, backoff y guard anti-regresión.
   Ventaja: con `pagination.count` el guard puede ser más preciso.
2. **Lista de categorías**: definir los términos de búsqueda (`Ntt=`) equivalentes a los de las
   otras cadenas, para que las subcategorías casen.
3. **EAN**: agregar `slug_tottus` + `fetch_ean_tottus` a `app/ean_fetch.py` y sumar Tottus a
   `FUENTES` en `app/backfill_ean.py` (la caché ya es por cadena, no hay que cambiarla) y a
   `SLUG_POR_CADENA` en `combinar_supermercados.py`.
   Ojo: el identificador para la ficha es la **URL completa**, no un slug corto.
4. **Pipeline**: sumar a `RAW_FILES` y `STEPS` en `actualizar_productos.py` (y a `SCRAPERS`
   para que funcione `--solo tottus`), más una tarea programada propia en el escalonado nocturno.
5. **Frontend**: sumar Tottus al filtro de supermercados.

**Falta medir**: cuántos requests aguanta antes de throttlear (Jumbo corta a los ~344). Conviene
empezar pausado y ver.
