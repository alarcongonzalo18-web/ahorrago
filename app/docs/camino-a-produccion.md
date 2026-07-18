# Camino a producción — evaluación honesta

> Corte 18-07-2026. Qué está listo, qué falta y en qué orden. Relacionado:
> [estado-y-handoff.md](estado-y-handoff.md) · [auditoria-2026-07-17.md](auditoria-2026-07-17.md) ·
> [competencia.md](competencia.md)

## Resumen en una línea

**Los datos ya están en forma; el producto no está desplegado.** La parte difícil de un
comparador (pipeline confiable + matching por EAN) está resuelta. Lo que falta es
infraestructura, y hay **una pieza arquitectónica sin construir** que es el verdadero bloqueante.

## ✅ Lo que ya está listo

| Área | Estado |
|---|---|
| Pipeline de datos | Automático, 4 cadenas, nocturno y escalonado |
| Auto-recuperación | Lock, backups previos, validaciones, restauración si falla, guard anti-regresión |
| Catálogo | 49.833 productos / 50.058 precios, precios frescos |
| Matching | Índice EAN (Líder 100%, Unimarc 98%, Jumbo y Tottus en curso) |
| Comparabilidad | 4.968 grupos ≥2 cadenas (era 1.562) |
| Calculadora | Backend oficial, y el frontend la consume |
| Honestidad del dato | Badge de frescura real (nadie en la competencia lo tiene) |
| Tests | 77 |

## 🔴 El bloqueante real: sincronizar datos casa → nube

Esto **no está construido** y condiciona todo lo demás.

El scraping **tiene que correr desde IP residencial** (los retailers bloquean datacenter; Jumbo
ya throttleó desde casa). Pero la app **tiene que estar en la nube** para que la use gente. O sea
el dato nace en un PC en Providencia y tiene que llegar a un servidor, todas las noches.

Hoy la base pesa **26 MB** (CSV combinado 21 MB). Opciones:

| Opción | Cómo | Nota |
|---|---|---|
| **Subir la BD entera** | tras el pipeline, `scp`/rclone/S3 del `supercheck.db` | Simple y suficiente a esta escala (26 MB/noche). **La recomendada para empezar** |
| Subir el CSV y reconstruir en el server | subir 21 MB y correr `reconstruir` allá | Más CPU en el server, sin ventaja clara |
| Base gestionada (Postgres) | el pipeline escribe directo a la nube | Lo correcto a futuro; hoy es sobre-ingeniería |

**Sin resolver esto no hay producción**, por más que el resto esté listo.

## 🟡 Endurecimiento antes de abrir al público

1. **CORS**: hoy sólo acepta `localhost`/red local. Hay que sumar el dominio real.
2. **Endpoints internos expuestos**: `/diagnostico/calidad`, `/diagnostico/matching` y
   `/estado-datos` son públicos y muestran interioridades (conteos, calidad, rutas). Cerrarlos o
   dejarlos tras token.
3. **Sin rate limiting ni auth**: cualquiera puede raspar toda la base. Ironía: es exactamente lo
   que nosotros le hacemos a los retailers, y por eso AhorraMax se protege con Cloudflare.
4. **Panel "Estado de datos" visible al usuario** (FEEDBACK item F): es vista de admin.
5. **SQLite**: alcanza de sobra para lectura, pero el archivo se reemplaza cada noche → hay que
   hacer el swap atómico para no servir una base a medio copiar.

## 🟡 Producto: qué falta para que valga la pena mostrarlo

- **Comparabilidad**: 4.968 grupos sobre ~50k productos. Sube solo cada noche (backfill de EAN de
  Jumbo y Tottus). **Es el número que decide si el producto sirve**; conviene lanzar con esto más
  alto.
- Bugs de UX de [FEEDBACK.md](../../FEEDBACK.md): búsqueda en móvil sin feedback, vista tabla sin
  "ver producto", sin autocomplete.
- ~~**Historial de precios**~~ — **HECHO 18-07-2026**: tabla `historial_precios` acumulando desde
  hoy (49.925 puntos en el primer snapshot). Ya se puede calcular media y "bajó de precio";
  falta que pasen días para tener serie, y construir las alertas encima.

## ⚪ Operación

- **Monitoreo**: hoy si el pipeline falla de noche, nadie se entera hasta mirar el log. Hace falta
  al menos un aviso (mail/WhatsApp) ante fallo. Hoy mismo hubo dos caídas del backfill.
- **Dependencia del PC encendido**: ver [estado-y-handoff.md](estado-y-handoff.md). Un mini PC
  siempre encendido resuelve scraping y sincronización de una.

## ⚠️ Legal / ToS

Scrapear y republicar precios es zona gris. La competencia lo hace (Carriapp, AhorraPo, AhorraMax)
y el propio SERNAC publica comparativas, así que hay precedente. Aun así, antes de un lanzamiento
público con marca conviene: no republicar imágenes con logo cuando se pueda evitar, citar la
fuente y respetar un ritmo de scraping razonable (ya se hace). **No es bloqueante técnico, pero sí
una decisión consciente a tomar.**

## Orden sugerido

1. **Terminar los datos** (nocturno drenando EAN de Jumbo y Tottus) → comparabilidad arriba.
2. ~~**Historial de precios**~~ — hecho 18-07-2026, ya acumula todas las noches.
3. **Decidir el "siempre encendido"** (mini PC) → resuelve scraping y sincronización.
4. **Construir la sincronización casa → nube** ← el bloqueante.
5. **Desplegar** app + dominio + HTTPS, con CORS al dominio y los endpoints internos cerrados.
6. **Monitoreo básico** (aviso si el pipeline falla).
7. Recién ahí: cuentas, geolocalización, y **al final** membresía (ver
   [roadmap-producto.md](roadmap-producto.md)).

> La membresía va última por decisión explícita: el mercado es gratis y no se cobra hasta que el
> producto funcione bien.
