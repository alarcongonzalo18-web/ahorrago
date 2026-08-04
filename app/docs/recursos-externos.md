# Recursos externos evaluados (bóveda de tododeia)

> Revisión 31-07-2026 de la bóveda comunitaria de [tododeia.com/community](https://www.tododeia.com/community)
> (399 recursos), filtrada por lo que le sirve a AhorraGo. El disparador fue el artículo
> [Trifecta Perfecta](https://www.tododeia.com/community/trifecta-perfecta).

## 🟢 Para usar ya: los tres comandos que Claude Code trae de fábrica

**Nada que instalar, oficial de Anthropic.** Verificado disponible en la sesión.

| Comando | Qué hace | Dónde aplica en AhorraGo |
|---|---|---|
| `/security-review` | detector de vulnerabilidades sobre los cambios de la rama | **el endurecimiento de la API** (token admin, rate limiting, CORS) — commit `ba6a182` |
| `/code-review` | caza bugs en el diff antes del push | scrapers nuevos, cambios de matching |
| `/verify` | comprueba que el cambio funciona en su superficie real | pipeline y frontend |

Además existe [`anthropics/claude-code-security-review`](https://github.com/anthropics/claude-code-security-review):
el mismo análisis como GitHub Action sobre cada PR. Útil cuando el repo tenga PRs.

**PENDIENTE 31-07**: correr `/security-review` sobre el endurecimiento de la API.

## 🟡 La Trifecta Perfecta (terceros, MIT, autor Hainrixz)

| Herramienta | Qué hace | Veredicto para AhorraGo |
|---|---|---|
| **The Architect** | entrevista la idea y genera `BLUEPRINT.md` de 16 secciones | **No aplica**: el proyecto ya está construido y documentado |
| **Cyber Neo** | auditoría con 5 subagentes, 11 dominios, reporte por gravedad | Se solapa con `/security-review`, que ya está instalado. Evaluar solo si el oficial se queda corto |
| **All Deploy** | detecta stack, elige Vercel/Railway, preview y promueve a producción con rollback | **La única con valor directo**: es exactamente la Fase 2 del plan maestro |

> ⚠️ Instalar una skill de terceros = ejecutar su código con acceso al proyecto. Son MIT y de
> una comunidad con nombre, pero conviene leer qué hacen antes. Prioridad: primero lo oficial,
> y **All Deploy** solo si el despliegue manual se complica.

## 🟡 Para el problema del pipeline siempre encendido

- **Agente 24/7 en VPS controlado por Telegram** (usa Browser Harness). Ataca el mismo dolor que
  tenemos: el pipeline depende de una máquina prendida.
  **Pero ojo**: nuestro scraping necesita **IP residencial** (los retailers bloquean datacenter),
  así que un VPS sirve para *servir* la web, no para scrapear. Ver [camino-a-produccion.md](camino-a-produccion.md).

## ⚪ Descartado (bajo valor para este proyecto)

- **ScrapeGraphAI** (26k ⭐) y **Apify MCP**: scraping genérico con LLM. Nuestros 4 scrapers
  ya recorren categorías reales y extraen EAN; un scraper genérico sería menos preciso y más caro.
- **Agent Webkit / landing pages**, **n8n**, **Obsidian sync**: no tocan nuestro problema.
- Guías de orquestación, CLAUDE.md y system prompt: útiles en general, no para lo que falta ahora.

Relacionado: [plan-maestro.md](plan-maestro.md) · [camino-a-produccion.md](camino-a-produccion.md)
