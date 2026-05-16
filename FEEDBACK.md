# Feedback de usuarios reales

## Sesión 1 — 15/05/2026, primer beta tester

### Bugs prioritarios (críticos)
- [ ] **A. Sin feedback visual al buscar en móvil:** El usuario hace click 
  en "Buscar" pero los resultados quedan abajo del fold sin scroll automático 
  ni loader. El usuario cree que el botón no funciona.
- [ ] **C. Vista tabla sin link a producto:** En modo tabla solo aparece 
  "agregar al carro", falta "ver producto" como en vista tarjetas.
- [ ] **D. Estado UI inconsistente:** Los contadores "X productos comparables" 
  y "Tu ahorro estimado" no se actualizan al agregar/borrar productos del 
  carro.

### Mejoras UX (medio)
- [ ] **B. Sin autocomplete/sugerencias** al escribir en el buscador
- [ ] **E. Categorías sin agrupar:** Lácteos debería ser categoría madre 
  con subcategorías: leches, quesos, yogurts, etc.

### Diseño (baja)
- [ ] **F. "Estado de datos" visible al usuario final:** Debería ser solo 
  vista admin
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
