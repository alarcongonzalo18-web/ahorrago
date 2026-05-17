# AhorraGo — Contexto para próxima sesión

## Mi rol
Soy Gonzalo, fundador de AhorraGo (app comparadora de precios de 
supermercados chilenos: Líder, Jumbo, Unimarc). Vengo trabajando con 
Claude en estrategia y código.

## Stack y repo
- FastAPI + SQLAlchemy + SQLite + frontend vanilla HTML/CSS/JS
- Repo público: https://github.com/alarcongonzalo18-web/ahorrago
- Mobile-first (iPhone 17 Pro Max es mi dispositivo de testing)

## North Star del producto
"AhorraGo te dice si vale la pena dividir tu compra."
No es solo comparar precios — recomienda una acción.

## Workflow de 3 capas
1. Claude (este chat) → estrategia, decisiones de producto
2. Claude Code (VS Code) → implementación, commits
3. Codex (ChatGPT) → code review profundo

## Estado actual (último commit: `e59f48a`)

### YA HECHO:
- ✅ Backend endpoint POST /productos/resumen-compra (commit 4a57d14)
- ✅ Carrito con cantidades (commit e59f48a)
  * agregarACompra incrementa si existe
  * Controles +/− con trash en cantidad=1
  * Límite máximo 99
  * Migración de carritos viejos en localStorage

### 🔴 BUG CRÍTICO PENDIENTE (detectado por Codex):
El endpoint /productos/resumen-compra solo busca por producto_id 
exacto, pero la app agrupa productos por producto_base para comparar 
entre supermercados.

Consecuencia: productos comparables se marcan como "sin comparación".

Solución: replicar el patrón que YA usa /productos/buscar para 
agrupar por producto_base. Buscar TODOS los productos con el mismo 
producto_base para calcular ahorros reales.

## Plan próximos commits (en orden estricto):
1. 🔴 Fix backend producto_base (CRÍTICO antes de cualquier feature visual)
2. 🟡 Limpieza:
   - Eliminar .summary-grid en desktop (ya está oculto en móvil)
   - Badge carrito: usar sum(p.cantidad) en vez de carritoCompra.length
3. 🟢 Sticky bottom bar consumiendo el endpoint arreglado
4. 🟢 Panel detallado "Ver plan" con compra inteligente

## Decisiones de producto tomadas
- Modelo B: controles +/− SOLO en carrito (no duplicar en cards)
- Eliminar stats vacías de home (cards "Tu ahorro $0" etc)
- Métrica de ahorro: mejor_super_unico - compra_optimizada
- Microcopy: "Tu compra inteligente"
- Umbrales chilenos: <$1k/<$7k/<$15k para recomendación
- Backend = calculadora oficial. Frontend solo renderiza.

## Servidores locales
- Backend: http://localhost:8001 (uvicorn)
- Frontend: http://localhost:5500/frontend/ (python -m http.server)
- App en red local: http://192.168.100.92:5500/frontend/

## Estilo de comunicación que prefiero
- Directo, con recomendaciones claras (no enumeres todas las opciones sin priorizar)
- Validar visualmente con screenshots cuando sea posible
- Antes de tocar código, mostrar plan + esperar aprobación
- Commits pequeños y validables, no megacommits
