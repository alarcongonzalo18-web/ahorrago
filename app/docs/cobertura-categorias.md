# Cobertura de categorías por cadena — análisis 23-07-2026

> Comparación entre lo que scrapeamos hoy y la taxonomía real de cada supermercado,
> para decidir cargar todas las categorías existentes.

## Hallazgo principal

**3 de las 4 cadenas NO usan el árbol de categorías real: buscan por palabra clave.**
Jumbo, Unimarc y Tottus arman su lista con ~50 términos de búsqueda elegidos a mano
("leche", "huevos", "arroz"…). Todo lo que no matchea uno de esos términos queda afuera,
y cada búsqueda topa en el techo de resultados del buscador. Solo **Líder** recorre
categorías reales.

## Cobertura actual vs. taxonomía real

| Cadena | Hoy scrapeamos | Método actual | Árbol real del sitio | Cobertura aprox. |
|---|---|---|---|---|
| **Jumbo** | 51 términos | búsqueda por keyword | **16 rubros / 117 subcategorías** | ~44% de las subcategorías |
| **Unimarc** | 51 términos | búsqueda por keyword | **15 rubros / 79 subcategorías** | ~65% |
| **Tottus** | 49 términos | búsqueda por keyword | **19 rubros / 116 subcat. / 395 nivel-3** | ~42% (nivel 2) |
| **Líder** | 93 subcategorías | **categorías reales** (`/v/`) | árbol Walmart `/browse` (mayor, ver nota) | la más completa |

> El % es orientativo: aun dentro de un rubro cubierto, la búsqueda por keyword se pierde
> productos cuyo nombre no contiene el término, y no baja el catálogo completo de la categoría.

## Rubros enteros que hoy quedan afuera

- **Jumbo**: Farmacia, Hogar/Juguetería/Librería, Catering, Experiencias Jumbo, parte de Mascotas.
- **Unimarc**: Hogar (Electrohogar, Ferretería, Cocina y mesa…), Perfumería/Farmacia completa,
  Veganos y vegetarianos, Frutos secos, Cocina internacional, Productos naturales.
- **Tottus**: Electrohogar y TV, Hogar y Librería, Aire Libre y Entretención, Cuidado Personal
  (a nivel 3 son 395 hojas), Mundo Bebé ampliado.

## Cómo cargar TODAS las categorías (endpoints encontrados)

Cada sitio expone su taxonomía y permite navegar por categoría, no solo buscar:

- **Jumbo** — Constructor.io. Árbol: `GET https://ac.cnstrc.com/browse/group_id/{id}?key=...`
  (devuelve `response.groups[0].children`). Productos por categoría: mismo endpoint `browse`
  con paginado. **Sin auth nueva** (misma key del `.env`). Dificultad: **baja**.
- **Unimarc** — BFF. Árbol: `GET /catalog/categories` (79 hojas con `slug`, ej.
  `despensa/conservas`). Productos por categoría vía el BFF con headers `source: WEB` +
  `version`. Dificultad: **baja**.
- **Tottus** — taxonomía embebida en el `__NEXT_DATA__` de cualquier página:
  `props.pageProps.serverData.headerData.taxonomy.entry.all_accesses.categories`
  (19 rubros → 116 → 395, con `gcategory_id` e `item_url`). Falta confirmar el endpoint de
  listado por categoría y su paginado. Dificultad: **media**.
- **Líder** — ya es por categoría (`/v/`). Migrar al `/browse` de Walmart (más completo)
  es el proyecto anti-Akamai aparte; ver [lider-endpoint-nuevo.md](lider-endpoint-nuevo.md).

## Decisiones antes de implementar

1. **Granularidad**: ¿nivel 2 (~80-120 categorías por cadena) o nivel 3 (Tottus solo tiene
   395)? Nivel 2 ya multiplica varias veces el catálogo; nivel 3 es exhaustivo pero pesado.
2. **Alcance de rubros**: ¿sumamos Hogar / Electrohogar / Librería / Farmacia, o nos quedamos
   en alimentos + limpieza + cuidado personal (el foco actual del comparador)?
3. **Presupuesto de scraping**: más categorías = más requests y más minutos por noche. Hoy
   Líder ya tarda ~50 min; Jumbo y Unimarc crecerían proporcional. Habría que revisar los
   horarios escalonados y el pacing.
4. **Impacto en matching**: más productos = más grupos comparables, pero también más ruido a
   emparejar. La métrica del negocio es grupos comparables (≥2 cadenas), no el total.

## Recomendación

Migrar de "búsqueda por keyword" a "recorrido por categoría real", **empezando por Jumbo y
Unimarc** (endpoints fáciles, sin nuevo anti-bot), a **nivel 2**, acotado a los rubros de
consumo (alimentos, bebidas, limpieza, cuidado personal, mascotas, bebé). Tottus después
(falta confirmar su endpoint de listado). Líder queda como está hasta resolver Akamai.
