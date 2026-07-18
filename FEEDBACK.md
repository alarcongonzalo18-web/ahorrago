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
- [ ] **B. Sin autocomplete/sugerencias** al escribir en el buscador
- [ ] **E. Categorías sin agrupar:** Lácteos debería ser categoría madre 
  con subcategorías: leches, quesos, yogurts, etc.

### Diseño (baja)
- [x] **F. "Estado de datos" visible al usuario final** — RESUELTO 18-07-2026. El panel
  queda oculto y se abre con `?admin=1` (se recuerda en localStorage). Ahí vive también
  el aviso de salud del pipeline, que es información de operador, no de usuario.
- [ ] **G. Layout header móvil:** Considerar formato similar a Jumbo (marca 
  + selector menú)

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

Resueltos: **A, C, D, F**. Pendientes: **B** (autocomplete de marcas), **E** (agrupar
categorías en madre/subcategorías) y **G** (layout del header móvil).

Nota: A y C ya estaban arreglados en el código pero seguían figurando como abiertos acá.
Un archivo de feedback desactualizado hace perder tiempo revisando bugs que no existen;
conviene marcarlos al resolverlos.
