# Auditoría completa + Plan de desarrollo — AhorraGo

> Revisión de código y producto del 17-07-2026 (post limpieza frontend y fix scraper).
> Alcance: frontend (`frontend/index.html`), backend (`app/*.py`), datos y estado de features.
> Severidad: 🔴 Alta · 🟡 Media · 🟢 Baja.

## Resumen ejecutivo

El backend es sólido: la calculadora de compra óptima (`calcular_resumen_compra` en
`app/main.py:502`) maneja equivalencia por `producto_base` + EAN, cobertura por proveedor y
umbrales de recomendación (una tienda / dividir). El bot de WhatsApp ya usa la calculadora
oficial vía `services.comparar_lista`.

**El problema #1 no es de código sino de producto: comparabilidad.** Solo el ~4,9% del catálogo
es comparable entre cadenas (1.562 grupos de 37.883 productos). Sin subir esa métrica, la
propuesta de valor ("te digo dónde comprar más barato") no se cumple para la mayoría del catálogo.

**El problema #2 es de coherencia:** el frontend **no usa** la calculadora oficial del backend —
recalcula la compra óptima en JS (`actualizarDashboard`, `renderCompraOptima`) con lógica más
pobre (sin agrupar por `producto_base`, sin los umbrales de recomendación). Web y bot pueden dar
respuestas distintas para la misma lista.

---

## Auditoría por área

### 1. Arquitectura / coherencia 🔴
- **El frontend solo consume 2 endpoints**: `/productos/buscar/{texto}` y `/estado-datos`
  (`frontend/index.html:2809, 3477`). **Nunca llama a `/productos/resumen-compra`.**
- La "compra óptima" y el total se calculan en el cliente (`actualizarDashboard`
  `frontend/index.html:2745`, `renderCompraOptima` `:3137`, `calcularTotalesSupermercado` `:3196`).
  Esa lógica no agrupa equivalentes por `producto_base` ni aplica los mensajes/umbrales de
  recomendación → **diverge de la calculadora oficial**. Contradice el principio propio
  "Backend = calculadora oficial. Frontend solo renderiza".
- **Dos calculadoras de óptimo en el backend**: `services.comparar_lista` (usada por `/comparar`
  y el bot, entrada = lista de texto) y `calcular_resumen_compra` (usada por
  `/productos/resumen-compra`, entrada = ids de carrito). Riesgo de que evolucionen distinto.

### 2. Datos y cobertura 🔴 (la métrica del negocio)
- 37.883 productos, **solo 4,9% comparables**; 173 en las 3 cadenas. Medir siempre con
  `python -m app.reporte_cobertura`.
- **Líder es el proveedor más delgado** (6.383 vs 22.324 Jumbo) siendo la cadena más grande.
  El fix de scraping + profundidad ya está en código (commit `8a063c0`); falta la corrida real.
- **EAN solo en Líder.** Matchear por código de barras es la palanca de comparabilidad; falta
  capturarlo en una 2ª cadena (Jumbo/Unimarc) — requiere hallar su API interna vía devtools.

### 3. Backend 🟡
- `/productos/buscar` pagina en la BD (`.offset().limit()` en `main.py:351`) **antes** de aplicar
  el filtro de familia y el de "azucar" (`:352-357`) → una página puede devolver menos de `limit`
  resultados y la paginación se vuelve inconsistente con los filtros.
- Sin autenticación ni rate limiting (OK para local; bloqueante para producción pública).
- Mensaje raíz con mojibake: `"SuperCheck funcionando ðŸš€"` (`main.py:47`) — cosmético.

### 4. Frontend / UX 🟡 (bugs de `FEEDBACK.md`, beta tester 15-05)
- **A**: búsqueda en móvil sin feedback visual (sin loader ni scroll a resultados) → parece que
  el botón no responde.
- **C**: vista tabla sin "ver producto" (solo "agregar").
- **B**: sin autocomplete/sugerencias de marcas.
- **E**: categorías sin agrupar (Lácteos madre → leches/quesos/yogurt).
- **F**: panel "Estado de datos" visible al usuario final (debería ser admin) — sigue en
  `frontend/index.html:2225`.
- **D** (contadores desactualizados): mitigado al eliminar la `.summary-grid` hoy.

### 5. Features "fantasma" (UI sin backend) 🟡
- **Alertas** (`crearAlerta*`, `renderAlertas`) y **Historial** (`guardarHistorial`,
  `renderHistorial`) son **solo localStorage**. No hay backend ni datos que los respalden.
- **Causa raíz**: el modelo `Precio` (`app/models.py:65`) **no tiene timestamp/fecha** → no existe
  historial de precios, así que "te aviso cuando baje" es imposible hoy.
- **Listas guardadas** (`guardarListaOptima`, `renderListas`) también localStorage — se pierden
  entre dispositivos.
- **Verticales** Tecnología / Mascotas / Vuelos son placeholders "Próximamente"
  (`frontend/index.html:2007-2025`); el modelo `Vertical` existe pero sin datos.

### 6. Deploy / infra 🔴 (bloquea el North Star)
- La app corre solo en localhost. El bot de WhatsApp necesita webhook público → sin deploy no hay
  usuarios. Decidir hosting (Railway/Fly/VPS). SQLite aguanta esta escala. El scraping seguramente
  deba seguir corriendo local (retailers bloquean IPs de datacenter) y subir el CSV/base.

### 7. Testing / entorno 🟢
- 48 tests (pytest). Este PC no tiene el entorno (faltan fastapi, sqlalchemy, etc.) → la suite se
  corre en el venv de Gonzalo. Recomendado: `python -m venv .venv && pip install -r requirements.txt`
  documentado en README para reproducibilidad.

---

## Plan de desarrollo (orden por palanca)

### Fase A — Comparabilidad real (la métrica) 🔴
El producto no vale sin esto. Objetivo: subir el % comparable muy por encima del 4,9%.
1. Correr el scraper de Líder arreglado en **una sola pasada pausada** → `combinar` →
   `reconstruir` → `reporte_cobertura`. (Requiere a Gonzalo; el guard ya evita regresiones.)
2. **EAN en una 2ª cadena**: hallar la API interna de Jumbo o Unimarc (devtools en un PDP) y
   capturar el código de barras. Unir por EAN dispara la comparabilidad.
3. Dirigir el esfuerzo a las peores categorías (`reporte_cobertura`): Carnes 1,2%, Bebé, Congelados.

### Fase B — Una sola calculadora (coherencia) 🔴
Que web y bot den siempre la misma respuesta.
1. El frontend deja de calcular el óptimo en JS y **consume `/productos/resumen-compra`**
   (implementa los pendientes #4 sticky bottom bar y #5 panel "Ver plan" con el resultado real
   del endpoint: `recomendacion`, `mensaje`, `distribucion`, `ahorro`).
2. Evaluar unificar `services.comparar_lista` y `calcular_resumen_compra` en un único núcleo
   (una por texto, otra por id, pero compartiendo el motor de óptimo).

### Fase C — Deploy + bot en producción (North Star) 🔴
1. Elegir hosting y desplegar (app + base). Scraping queda local subiendo el CSV.
2. Túnel/HTTPS + sandbox de Twilio apuntando `/webhook/whatsapp` → probar desde el teléfono.
3. Número dedicado de AhorraGo en Meta (no el de Reikobyte).

### Fase D — Historial de precios (habilita Alertas/Historial) 🟡
1. Agregar `fecha`/timestamp a `Precio` (o tabla `historial_precios`) — poblado en cada corrida.
2. Endpoints de historial y de alertas persistidas → conectar los botones que hoy son localStorage.

### Fase E — Pulido UX y limpieza 🟢
1. Bugs `FEEDBACK.md`: loader + scroll a resultados en móvil (A), "ver producto" en tabla (C),
   autocomplete de marcas (B), ocultar "Estado de datos" del usuario final (F), header móvil (G).
2. Fix de paginación de `/productos/buscar` (filtrar antes de paginar).
3. Quitar CSS huérfano `summary-*`; corregir mojibake del mensaje raíz.
4. Verticales nuevas: **congeladas** hasta que el canal funcione con supermercados (decisión propia).

---

## Quick wins (bajo costo, se pueden hacer ya, sin la app corriendo)
- Fix de paginación de `/productos/buscar` (backend puro, testeable con pytest).
- Timestamp en `Precio` + migración (backend, testeable) — desbloquea Fase D.
- Ocultar el panel "Estado de datos" del usuario final (frontend, 1 bloque).
- Corregir mojibake `main.py:47` y limpiar CSS `summary-*`.

## Cómo verificar cada fase
- **A**: `reporte_cobertura` antes/después; el % comparable sube.
- **B**: misma lista en web y bot → mismo total y misma recomendación; tests de
  `calcular_resumen_compra` cubriendo carrito con equivalentes.
- **C**: mensaje real de WhatsApp desde el teléfono devuelve comparación.
- **D**: alerta creada persiste y dispara cuando el histórico baja del objetivo.
- **E**: recorrido móvil (390px) sin errores de consola; bugs de FEEDBACK cerrados uno a uno.
