# Feedback de usuarios reales

## Sesión 1 — 15/05/2026, primer beta tester

### Bugs prioritarios (críticos)
- [x] **A. Sin feedback visual al buscar en móvil** — RESUELTO. `buscar()` muestra
  "Buscando mejores precios..." y hace `scrollIntoView` a los resultados.
- [x] **C. Vista tabla sin link a producto** — RESUELTO. `renderFilaTabla` incluye el
  botón "Ver" cuando el producto tiene URL.
- [x] **D. Estado UI inconsistente** — RESUELTO 17-07-2026 eliminando la grilla de stats
  de la home (era la que no se actualizaba). El total y la recomendación ahora salen de
  la calculadora oficial del backend.

### Mejoras UX (medio)
- [x] **B. Sin autocomplete/sugerencias** — RESUELTO 19-07-2026. Endpoint `/sugerencias` (2.214 términos minados del catálogo: marcas y palabras frecuentes, "trencito" incluido) + `datalist` nativo en el input. Verificado en navegador.
- [x] **E. Categorías sin agrupar** — RESUELTO 19-07-2026. La vista Categorías agrupa
  las 13 tarjetas bajo 5 rubros madre (Lácteos y frescos / Despensa / Bebidas /
  Panadería / Limpieza y hogar). Verificado en navegador.

### Diseño (baja)
- [x] **F. "Estado de datos" visible al usuario final** — RESUELTO 18-07-2026. El panel
  queda oculto y se abre con `?admin=1` (se recuerda en localStorage). Ahí vive también
  el aviso de salud del pipeline, que es información de operador, no de usuario.
- [x] **G. Layout header móvil** — RESUELTO 19-07-2026. Patrón Jumbo: una sola fila
  (marca + acciones + hamburguesa) con menú desplegable, en vez del `<select>` que
  sumaba una fila al header. Verificado en 390px y en desktop.

### Cosas que SÍ funcionaron bien
- Cálculo de "Tu ahorro estimado" muestra valores reales ($7.810)
- "Mejor supermercado" se calcula correctamente
- Búsqueda devuelve resultados (24 comparables para "yogurt")
- Vista de comparación entre 3 supermercados es clara

## Búsquedas reales del primer beta tester
Capturadas en los logs de uvicorn (IP 192.168.100.69)

### Lo que buscó:
- Categorías típicas: leche, yogurt, queso
- Marcas reconocidas: Trencito (×2), Chocolate, Coca-Cola

### Patrones identificados:
- **El usuario buscó por MARCA**, no solo por categoría genérica
- **"Trencito" se buscó 2 veces** → posiblemente los primeros resultados no fueron satisfactorios
- **La app maneja correctamente nombres con espacios** (Coca cola → %20)

### Implicaciones para próximas iteraciones:
- Considerar autocomplete con marcas populares
- Investigar resultados de "Trencito" — ¿la búsqueda no agrupa bien las galletas Trencito?
- Confirmar que tildes y caracteres especiales se manejen bien


## Estado al 18-07-2026

**Todo el feedback de la sesión 1 está resuelto** (A-G, 19-07-2026). El autocomplete
además usa desplegable propio (el nativo del navegador se dibujaba donde quería).

Nota: A y C ya estaban arreglados en el código pero seguían figurando como abiertos acá.
Un archivo de feedback desactualizado hace perder tiempo revisando bugs que no existen;
conviene marcarlos al resolverlos.
