# Cambios Fase 1 - AhorraGo

Fecha: 2026-05-31

## Objetivo

Corregir problemas críticos y de alto impacto inicial sin romper el MVP actual, evitando refactor masivo, cambios de arquitectura o migraciones de base de datos.

## Cambios Aplicados

### 1. Seguridad: API Key de Jumbo

- Se eliminó la API key hardcodeada de los scrapers de Jumbo.
- Los scrapers ahora leen `JUMBO_API_KEY` desde variables de entorno.
- Si falta la variable, el scraper falla con un mensaje claro sin exponer secretos.
- Se creó `.env.example` con la variable requerida.
- Se actualizó `.gitignore` para excluir `.env` y `.env.*`, manteniendo `.env.example` versionable.

Archivos:
- `app/scraper_jumbo_real.py`
- `app/scraper_jumbo_api.py`
- `.env.example`
- `.gitignore`

### 2. Búsquedas con LIMIT y OFFSET

- Se agregaron parámetros `limit` y `offset` a endpoints de búsqueda.
- Default: `limit=50`.
- Máximo permitido: `limit=100`.
- Se evitó carga ilimitada en las búsquedas principales de productos.
- El frontend ahora consulta con `limit=50&offset=0`.

Archivos:
- `app/main.py`
- `app/services.py`
- `frontend/index.html`

### 3. URLs Correctamente Escapadas

- Se creó helper centralizado para generar URLs de búsqueda con `urllib.parse.urlencode`.
- Se reemplazaron URLs generadas con `replace(" ", "%20")`.
- Las URLs ahora soportan tildes, `ñ` y caracteres especiales.

Archivos:
- `app/url_utils.py`
- `app/convertir_lider.py`
- `app/convertir_jumbo.py`
- `app/convertir_unimarc.py`
- `app/generar_catalogo.py`
- `app/services.py`

### 4. Índices Básicos en SQLite

- Se reforzó el script idempotente de índices.
- Se agregaron índices seguros para:
  - `productos.nombre`
  - `productos.producto_base`
  - `precios.producto_id`
  - `precios.supermercado_id`
- El script usa `CREATE INDEX IF NOT EXISTS`, por lo que no borra ni reconstruye datos.

Archivo:
- `app/scripts/agregar_indices.py`

### 5. Lock Real para Actualización de Productos

- Se reemplazó el lock manual por `filelock`.
- Se evita que dos ejecuciones del pipeline corran al mismo tiempo.
- Si ya existe una actualización en curso, el proceso sale con mensaje claro.

Archivos:
- `app/actualizar_productos.py`
- `requirements.txt`

### 6. Tests Iniciales

Se creó el primer set mínimo de tests para:

- Normalización de texto.
- Equivalencia entre `Leche Soprole 1L` y `Leche Soprole 1000ml`.
- URLs con tildes y `ñ`.
- Límites de búsqueda.
- Cálculo básico de ahorro.

Archivo:
- `tests/test_phase1.py`

### 7. Documento para Agentes

Se creó `AGENTS.md` con:

- Stack detectado.
- Reglas de trabajo para Codex.
- Comandos de ejecución.
- Comandos de testing.
- Reglas de seguridad.
- Definición de terminado.

Archivo:
- `AGENTS.md`

## Dependencias Agregadas

En `requirements.txt`:

```txt
filelock>=3.13.0
pytest>=8.0.0
```

## Verificación Ejecutada

Comandos ejecutados:

```powershell
venv\Scripts\python.exe -m pytest tests/test_phase1.py -q
venv\Scripts\python.exe -m compileall app tests
venv\Scripts\python.exe -m app.scripts.agregar_indices
venv\Scripts\python.exe -c "from app.main import app; print(app.title)"
```

Resultados:

- Tests: `5 passed`.
- Compilación Python: OK.
- Import de FastAPI app: OK.
- Índices SQLite aplicados correctamente.
- Verificación de `JUMBO_API_KEY` faltante: muestra error claro.

## Archivos Modificados o Creados

Modificados:

- `.gitignore`
- `app/actualizar_productos.py`
- `app/convertir_jumbo.py`
- `app/convertir_lider.py`
- `app/convertir_unimarc.py`
- `app/generar_catalogo.py`
- `app/importar_csv.py`
- `app/main.py`
- `app/scraper_jumbo_api.py`
- `app/scraper_jumbo_real.py`
- `app/scripts/agregar_indices.py`
- `app/services.py`
- `frontend/index.html`
- `requirements.txt`

Creados:

- `.env.example`
- `AGENTS.md`
- `app/url_utils.py`
- `tests/test_phase1.py`
- `CAMBIOS_FASE_1.md`

## Riesgos Pendientes

- Aún existen `.all()` en endpoints de diagnóstico, estado de datos y lógica interna no crítica. No se tocaron para evitar ampliar demasiado esta fase.
- El pipeline completo de scrapers no fue ejecutado para evitar scraping externo y cambios masivos de datos.
- Hay un warning de Pydantic por uso de `@validator`; conviene migrarlo a `@field_validator` en una fase posterior.
- SQLite se mantiene como base actual, según la restricción de no migrar todavía.

## Siguiente Fase Recomendada

1. Optimizar endpoints pesados como `/diagnostico/calidad` y `/estado-datos`.
2. Agregar tests de integración con SQLite temporal.
3. Migrar validadores Pydantic a estilo v2.
4. Revisar límites y paginación en comparador y diagnósticos.
5. Revisar manejo de configuración con carga explícita de `.env` si el flujo local lo necesita.
