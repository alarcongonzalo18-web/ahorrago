# Competencia — comparadores de precios de supermercado en Chile

> Research 18-07-2026. Objetivo doble: entender **cómo resuelven el mismo problema** y definir
> **en qué NO queremos parecernos**. Relacionado: [roadmap-producto.md](roadmap-producto.md) ·
> [auditoria-2026-07-17.md](auditoria-2026-07-17.md)

## Quiénes están

| Sitio | Cadenas | Modelo | Notas |
|---|---|---|---|
| **Carriapp** (carriapp.cl) | Líder, Jumbo, Unimarc, **Tottus** | Gratis | El competidor real. Lanzó nov-2025, +9.000 usuarios, 58.000 productos, solo RM |
| **AhorraPo** (ahorrapo.cl) | 6 cadenas + farmacias + suplementos + licores | Gratis, con **sponsors** | Ad-heavy; slots de sponsor vacíos a la vista |
| **AhorraMax** (ahorramax.cl) | 5 cadenas | Gratis | Detrás de challenge anti-bot de Cloudflare |
| **Pmatch** (pmatch.cl) | 4 cadenas | Gratis | Más antiguo (2023) |
| **SERNAC** | Canasta básica | Estatal | Referencia de autoridad, no competidor directo |

## Cómo funcionan (lo técnico)

- **Todos mantienen su propia base de datos.** Ninguno consulta las cadenas en vivo por
  búsqueda — confirma la decisión de arquitectura de AhorraGo (ver `estado-y-handoff.md`).
- **Carriapp** es el más sofisticado: carrito, y **dos modos de optimización** — máximo ahorro
  (que puede dividir la compra entre las 4 cadenas) vs. lo más barato dentro de **una sola**
  cadena. Incorpora **costos de despacho y membresías** en el cálculo. Dice usar IA y algoritmos
  de optimización. Promete ~20% de ahorro promedio.
- **AhorraMax** protege su sitio con Cloudflare anti-bot: se defienden de que les scrapeen los
  datos que ellos mismos scrapean.

## 🔴 Hallazgos incómodos que hay que enfrentar

### 1. Colisión de nombre
**"AhorraGo" vs "AhorraPo" vs "AhorraMax".** El espacio `Ahorra*` está saturado y AhorraPo es
casi idéntico fonética y visualmente. Si el objetivo explícito es *no parecernos a ninguno*,
el nombre actual va en contra desde el primer segundo. **Vale la pena evaluar un renombre**
antes de invertir en marca, dominio y marketing.

### 2. El mercado es gratis
Carriapp, AhorraPo, AhorraMax y Pmatch son **todos gratuitos**. Carriapp además ofrece **más**
que nosotros hoy (4 cadenas, 58k productos, optimización con despacho y membresías) sin cobrar.
Cobrar una membresía contra eso es muy difícil. Refuerza la regla ya escrita: **la membresía va
al final**, y probablemente el modelo deba ser otro (sponsors, afiliados, datos agregados).

### 3. Carriapp nos lleva ventaja
Hoy tienen más cadenas (incluye Tottus), más productos y features que no tenemos (despacho,
membresías, dos modos de optimización). Copiarlos nos deja siempre atrás. Hay que **elegir un eje
propio**, no correr su misma carrera.

## En qué NO parecernos

- **Nada de slots de sponsor vacíos** ni rieles de publicidad como AhorraPo: grita "sitio sin
  tracción" y ensucia la comparación, que es justo lo que el usuario vino a hacer.
- **Nada de claims sin respaldo**: "COMPARADOR #1 EN CHILE", "Precios actualizados" (sin fecha),
  "Miles de productos". Son promesas verificables que nadie verifica.
- **Nada de gradientes morado/rosa de landing genérica** — es el look por defecto del rubro.
- **Nada de descuidos visibles**: AhorraPo tiene su página 404 en inglés sin traducir.
- **No cobrar por lo que la competencia regala.**

## Dónde sí podemos ser distintos (ejes propios)

1. **Honestidad del dato.** Ninguno muestra **cuándo** se actualizó el precio. Nosotros ya
   tenemos el badge "Precios actualizados hace X días" — y nació justo del problema real de
   mostrar $590 cuando la tienda cobraba $680. Es un diferenciador honesto y difícil de copiar
   sin exponer la propia desactualización.
2. **Matching por EAN.** Si la competencia empareja por texto, arrastra el mismo techo de
   comparabilidad que nosotros teníamos (~5%). Nuestro índice por código de barras es un moat
   técnico real: une productos con nombres totalmente distintos entre cadenas.
3. **Geolocalización de tiendas cercanas.** Carriapp es solo RM y está centrado en despacho.
   "Qué supermercado tenés cerca y si vale la pena ir" es un eje libre — y hace accionable la
   recomendación de dividir la compra.
4. **Cobertura fuera de la RM.** Carriapp solo opera en Región Metropolitana. Regiones está
   desatendido.

## Decisiones tomadas sobre este research (18-07-2026)

- **Nombre y colores: hay que cambiarlos, pero NO ahora.** Gonzalo lo da por aceptado (el nombre
  choca con AhorraPo/AhorraMax y la paleta es la genérica del rubro), pero la prioridad actual es
  **que todo funcione bien y esté controlado**. No abrir el tema de marca hasta que los datos y
  el pipeline estén sólidos. No renombrar por iniciativa propia.
- **Horario del pipeline movido a las 03:00** (era 06:00/18:00). 18:00 es hora punta del
  e-commerce de supermercado: sumaba carga cuando los retailers están más ocupados y es cuando
  más probable es que throttleen. Ver `programar-actualizacion-productos.ps1`.

## Consecuencias para el roadmap

- **Tottus deja de ser opcional**: la competencia ya lo tiene. (Ya anotado como pendiente.)
- **Repensar la monetización** antes de construirla: el mercado es gratis y el competidor fuerte
  también. Sponsors/afiliados/datos agregados son más realistas que una membresía.
- **Evaluar el nombre** antes de gastar en marca.
- **Doblar la apuesta en EAN y frescura**, que es donde tenemos ventaja técnica real y donde
  ellos son débiles.

## Fuentes

- [Carriapp](https://carriapp.cl/) · [nota en Chócale](https://chocale.cl/2026/04/carriapp-la-plataforma-para-comparar-precios-en-supermercados/) · [nota en Sabes.cl](https://sabes.cl/2026/03/22/conoce-la-start-up-chilena-que-compara-precios-de-supermercados-y-te-ayuda-a-ahorrar-dinero/)
- [AhorraPo](https://ahorrapo.cl/) · [AhorraMax](https://ahorramax.cl/) · [Pmatch (Chócale)](https://chocale.cl/2023/09/pmatch-plataforma-compara-los-precios-en-supermercados/)
- [SERNAC — comparador de canasta](https://www.sernac.cl/portal/604/w3-article-63379.html)
