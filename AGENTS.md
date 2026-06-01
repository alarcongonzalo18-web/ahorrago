# AGENTS.md - AhorraGo

## Stack detectado
- Backend: FastAPI, SQLAlchemy, SQLite.
- Frontend: HTML, CSS y JavaScript vanilla en `frontend/index.html`.
- Scraping/datos: scripts Python en `app/` y CSVs en `data/`.

## Reglas para Codex
- Hacer cambios pequenos, testeables y compatibles con el MVP.
- No eliminar codigo funcional ni reestructurar carpetas sin una fase dedicada.
- No migrar SQLite a PostgreSQL hasta que sea una decision explicita.
- Proteger cambios del usuario y revisar `git status` antes de cerrar.

## Comandos de ejecucion
- Backend: `uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload`
- Frontend: `python -m http.server 5500 --directory frontend`
- Pipeline productos: `python -m app.actualizar_productos`
- Indices SQLite: `python -m app.scripts.agregar_indices`

## Comandos de testing
- Tests: `pytest`
- Tests de fase 1: `pytest tests/test_phase1.py`

## Reglas de seguridad
- No hardcodear API keys, tokens ni secretos.
- Usar `.env` local para secretos y mantenerlo fuera de Git.
- Documentar variables requeridas en `.env.example`.
- Escapar URLs con `urllib.parse.quote`, `urlencode` o helpers equivalentes.
- Limitar endpoints de busqueda con `limit` y `offset`.

## Definicion de terminado
- La app sigue levantando backend y frontend.
- No quedan secretos hardcodeados en codigo fuente.
- Las busquedas tienen limites por defecto y maximos razonables.
- Las URLs soportan tildes, ene y caracteres especiales.
- Los cambios tienen tests minimos y comandos claros para verificarlos.
- La base SQLite existente no se borra ni se reconstruye salvo instruccion explicita.
- Cada fase debe cerrar con un documento `CAMBIOS_FASE_N.md` y su PDF equivalente `CAMBIOS_FASE_N.pdf`.
- Cada fase tambien debe actualizar `reports/AHORRAGO_MASTER_REPORT.md` y `reports/AHORRAGO_MASTER_REPORT.pdf` con el resumen acumulado.
