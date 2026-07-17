# AhorraGo — Contexto para continuidad entre sesiones

## Mi rol
Soy Gonzalo, fundador de AhorraGo (app comparadora de precios de 
supermercados chilenos: Líder, Jumbo, Unimarc).

## Stack
- FastAPI + SQLAlchemy + SQLite
- Frontend vanilla HTML/CSS/JS
- Mobile-first (iPhone 17 Pro Max es dispositivo de testing)
- Repo: https://github.com/alarcongonzalo18-web/ahorrago

## North Star del producto
"AhorraGo te dice si vale la pena dividir tu compra."
No es solo comparar precios — recomienda una acción concreta.

## Workflow de 3 capas
1. Claude (chat) → estrategia, decisiones de producto
2. Claude Code (VS Code) → implementación, commits
3. Codex (ChatGPT) → code review profundo

## Estado actual (último commit: e59f48a)

### YA HECHO:
- Backend endpoint POST /productos/resumen-compra (commit 4a57d14)
- Carrito con cantidades (commit e59f48a):
  - agregarACompra incrementa si existe
  - Controles +/− con trash en cantidad=1
  - Límite máximo 99
  - Migración de carritos viejos en localStorage

### BUG CRÍTICO producto_base (detectado por Codex) — ARREGLADO (17-07-2026):
El endpoint /productos/resumen-compra solo buscaba por producto_id
exacto, pero la app agrupa productos por producto_base para comparar
entre supermercados. Consecuencia: productos comparables se marcaban
como "sin comparación" y el total usaba el precio del proveedor
equivocado.

Solución aplicada: nueva helper `equivalentes_por_item()` en app/main.py
que replica el patrón de /productos/buscar (agrupa por producto_base y
filtra con candidato_compatible). Cubierto por
test_resumen_compra_con_equivalente_en_otro_proveedor_elige_precio_menor.

### Secuelas del rename Multi-Rubro (Supermercado → Proveedor), arregladas 17-07-2026:
El commit 3686a58 dejó el rename a medio hacer y nadie lo validó:
- `/productos/buscar` tiraba **HTTP 500** (NameError: 'supermercado' no
  definido en app/main.py). El buscador entero estaba caído en main.
- `/diagnostico/matching` tiraba AttributeError (models.Supermercado ya
  no existe) desde app/matching_diagnostics.py.
- `/estado-datos` pasó a devolver la clave "proveedores", pero el
  frontend seguía leyendo `estado.supermercados` → panel vacío en silencio.
- tests/test_integration.py importaba Supermercado y no cargaba.

### Tests huérfanos — RESUELTO (17-07-2026):
test_auditoria_datos.py eliminado (probaba solo código borrado de
app/scripts/). test_fase4_diagnostico.py rescatado (3 de 4 tests probaban
código vivo). La suite completa corre sin exclusiones: 48 tests verdes.

## Visión y rumbo (decidido 17-07-2026)

North Star ampliado: comparador multi-rubro consultable por WhatsApp —
el usuario manda su lista por chat y recibe la comparación y la compra
óptima en el mismo chat.

Decisiones de rumbo:
1. **Rubros nuevos congelados** hasta que el bot esté en producción con
   supermercados. Un canal funcionando con 1 rubro > 3 rubros sin usuarios.
2. **El bot se construye desacoplado del canal** (app/chat.py). Twilio,
   Meta Cloud API o Telegram son solo transportes.
3. Cada vertical futura tendrá su propia estrategia de matching
   (tecnología = modelo/SKU exacto, no texto difuso). No intentar un
   motor universal.

### Bot WhatsApp — estado
- **Hecho (17-07-2026)**: núcleo conversacional (app/chat.py) + webhook
  POST /webhook/whatsapp estilo Twilio (form-urlencoded → TwiML), con 7
  tests. Verificado contra servidor real: "2 leches" → comparación
  completa con compra óptima.
- **Siguiente (requiere al dueño)**: cuenta Twilio (sandbox WhatsApp
  gratis) apuntando el webhook a la app → probar desde el teléfono. Para
  eso la app debe estar accesible: túnel (ngrok/cloudflared) para probar,
  o el deploy definitivo.
- **Bloqueador estructural**: la app no está desplegada (corre en
  localhost). Sin servidor público no hay webhook ni usuarios. Decidir
  hosting (PaaS tipo Railway/Fly o VPS). SQLite aguanta esta escala.
  Ojo scraping: probablemente deba seguir corriendo en PC local y subir
  el CSV/base al servidor (retailers bloquean IPs de datacenter).
- **Después**: número dedicado para AhorraGo en Meta (NO el +56 9 6222
  9771, que es de Reikobyte), y más adelante un LLM barato que traduzca
  lenguaje natural a llamadas API (la v1 usa comandos simples).

### Cobertura del catálogo — diagnóstico (17-07-2026)

Medido con `python -m app.reporte_cobertura` sobre los datos reales:
- **37.883 productos pero solo 1.562 grupos comparables (4,9%)**; apenas
  173 existen en los 3 supermercados. El comparador solo puede comparar
  ~5% de su catálogo — esta es LA métrica a subir, no el total de productos.
- **Líder es el proveedor más delgado** (6.383 vs 22.324 de Jumbo) siendo
  la cadena más grande de Chile. Causa probable: su scraper usa listas
  curadas `/v/` mientras Jumbo/Unimarc usan búsquedas amplias.
- **Ningún scraper captura EAN (código de barras)**. Jumbo y Unimarc
  corren sobre VTEX (la API expone `ean` por SKU) y Líder sobre stack
  Walmart (UPC en el JSON). Matchear por EAN primero y texto después es
  la vía correcta para disparar la comparabilidad — es lo que hacen los
  comparadores serios.
- Los 3 scrapers cubren las mismas ~50 subcategorías (canasta completa);
  el problema no son categorías faltantes sino profundidad y matching.

Plan de datos (orden de palanca):
1. ~~Infraestructura EAN~~ — **hecho 17-07-2026** (commit `a1bb4bb`):
   columna `Producto.ean`, extracción desde URLs de Líder (99% cobertura,
   retroactivo — el GTIN-14 viene en la URL `/ip/<slug>/00780...`),
   unificación de producto_base como `ean:<código>` cuando 2+ productos
   comparten EAN, fase5b no pisa grupos EAN, resumen-compra matchea por
   EAN aunque el texto difiera. **Pendiente para que pague**: EAN de una
   segunda cadena. Sondeado 17-07: Jumbo no lo expone en Constructor.io
   (RefId = código interno) ni VTEX API pública (410) ni PDP (shell JS);
   Unimarc VTEX API responde 404/500. Vía: abrir devtools en un PDP de
   Jumbo/Unimarc desde casa y encontrar la API interna que hidrata la
   página (ahí está el EAN seguro).
2. **Profundizar Líder** (más subcategorías `/v/` o su API de búsqueda)
   hasta paridad ~20k. Cada producto nuevo de Líder suma comparables
   directo porque Jumbo ya tiene el catálogo contra el cual matchear —
   y ahora cada producto de Líder llega con EAN.
3. Correr `reporte_cobertura` después de cada actualización y dirigir el
   esfuerzo a las categorías con peor % (hoy: Carnes 1,2%, Bebé 2,2%,
   Congelados 2,4%).
4. **BD**: `Precio` no tiene fecha — agregar timestamp + tabla de
   historial de precios (los botones "Historial" y "Alertas" del frontend
   lo necesitan; sin historial no hay "te aviso cuando baje").
5. Recién después: rubros/pasillos nuevos (licores, farmacia, hogar).

## Plan próximos commits (orden estricto)
1. ~~Fix backend producto_base~~ — hecho 17-07-2026.
2. ~~Bot: núcleo + webhook~~ — hecho 17-07-2026.
3. Limpieza:
   - Eliminar .summary-grid en desktop (ya está oculto en móvil)
   - Badge carrito: usar sum(p.cantidad) en vez de carritoCompra.length
4. Sticky bottom bar consumiendo el endpoint arreglado
5. Panel detallado "Ver plan" con compra inteligente

## Decisiones de producto tomadas
- Modelo B: controles +/− SOLO en carrito (no duplicar en cards)
- Eliminar stats vacías de home
- Métrica de ahorro: mejor_super_unico - compra_optimizada
- Microcopy: "Tu compra inteligente"
- Umbrales chilenos: <$1k / <$7k / <$15k para recomendación
- Backend = calculadora oficial. Frontend solo renderiza.

## Servidores locales
- Backend: http://localhost:8001 (uvicorn)
- Frontend: http://localhost:5500/frontend/ (python -m http.server)
- App en red local: http://192.168.100.92:5500/frontend/

## Estilo de comunicación que prefiero
- Directo, con recomendaciones claras
- Validar visualmente con screenshots cuando sea posible
- Antes de tocar código, mostrar plan + esperar aprobación
- Commits pequeños y validables