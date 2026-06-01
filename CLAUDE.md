# CLAUDE.md - AhorraGo Project

## 📋 Descripción del Proyecto

**AhorraGo** es un comparador de precios de supermercados chilenos que permite a usuarios buscar productos en múltiples cadenas (Líder, Jumbo, Unimarc) y obtener recomendaciones de compra óptima basadas en precios y disponibilidad.

**GitHub**: alarcongonzalo18-web/ahorrago

## 🎯 Objetivo de Negocio

- Ayudar a usuarios a ahorrar dinero comparando precios de supermercados
- Proporcionar lista de compras con plan de compra óptimo
- Expandir a modelo freemium con sistemas de usuarios, favoritos, alertas y WhatsApp bot

## 🏗️ Arquitectura

```
AhorraGo
├── Backend (FastAPI + SQLAlchemy)
│   ├── Endpoints REST
│   ├── Scrapers (Selenium + Constructor.io API)
│   ├── Lógica de negocio (resumen de compra, recomendaciones)
│   └── Base de datos (SQLite 3.x)
├── Frontend (HTML + CSS + Vanilla JS)
│   ├── Búsqueda de productos
│   ├── Gestión de carrito
│   ├── Dashboard de lista de compra
│   └── Responsive design (móvil + desktop)
└── Scripts (actualización de datos, mantenimiento)
```

## 🛠️ Tecnologías Detectadas

### Backend
- **Framework**: FastAPI 0.110.0+
- **Server**: Uvicorn 0.27.0+
- **ORM**: SQLAlchemy 2.0.0+
- **Validación**: Pydantic 2.0.0+
- **Base de datos**: SQLite 3.x

### Scraping
- **Selenium**: 4.18.0+ (navegador automatizado)
- **Constructor.io API**: Para Jumbo (search + catálogo)
- **Métodos**: Selenium para Líder/Unimarc, API para Jumbo

### Frontend
- **HTML5 + CSS3 + JavaScript vanilla**
- **Bootstrap 5 CDN** (inferido de estructura)
- **Responsive**: Mobile-first, breakpoint 1024px

### Desarrollo
- **Python**: 3.10+
- **Servidor dev**: `python -m http.server 5500` (frontend)
- **Servidor API**: `uvicorn app.main:app --reload --port 8001`

## 📊 Base de Datos

### Modelos principales
- **Product**: producto con ID, nombre, precio, URL, imagen
- **Categoria**: clasificación de productos
- **Supermercado**: Líder, Jumbo, Unimarc con URLs base
- **UserCart**: carrito del usuario con cantidades por producto

### Índices críticos
- `product_name_idx`: búsqueda rápida por nombre
- `supermarket_id_idx`: filtrado por supermercado
- `category_id_idx`: navegación por categoría

### Estado actual
- **52 categorías** scrapeadas por supermercado
- **23,749 productos Jumbo** (migración a Constructor.io API)
- **Índices**: Aplicados para optimizar N+1 queries

## 📝 Convenciones de Código

### Python Backend
```python
# Nombres
- Variables: snake_case
- Clases: PascalCase
- Constantes: UPPER_SNAKE_CASE
- Funciones privadas: _private_function

# Estructura
- Imports: stdlib → third-party → local
- Máximo 100 caracteres por línea
- Type hints: Obligatorios en funciones públicas
- Docstrings: Google-style en clases públicas
```

### JavaScript Frontend
```javascript
// Nombres
- Variables: camelCase
- Constantes: UPPER_SNAKE_CASE
- Funciones: camelCase
- Clases: PascalCase

// Estructura
- Async/await preferido sobre .then()
- Manejo de errores con try/catch
- Eventos: addEventListener() preferido
- DOM: Validar existencia antes de manipular
```

### SQL
```sql
-- Nombres
- Tablas: plural_snake_case
- Columnas: snake_case
- Índices: {tabla}_{columna}_idx
- Constraints: {tabla}_{constraint_type}

-- Queries
- EXPLAIN ANALYZE antes de optimizar
- índices en WHERE, JOIN, ORDER BY
```

## 🔀 Convenciones de Git

### Ramas
- `main`: producción, protegida
- `develop`: staging, base para features
- `feature/{nombre}`: nuevas funcionalidades
- `bugfix/{nombre}`: correcciones
- `hotfix/{nombre}`: urgencias en main

### Formato de ramas
```
feature/carrito-cantidades
bugfix/busqueda-stopwords
hotfix/crash-resumen-compra
```

## 📝 Convenciones de Commits

### Formato
```
<tipo>(<scope>): <descripción breve>

<descripción detallada si es necesario>

<footer>
```

### Tipos
- `feat`: nueva característica
- `fix`: corrección de bug
- `perf`: mejora de performance
- `refactor`: cambio de estructura sin cambiar comportamiento
- `docs`: cambios de documentación
- `test`: agregar/actualizar tests
- `chore`: tareas de mantenimiento
- `style`: formato de código (sin cambios funcionales)

### Ejemplos
```
feat(carrito): agregar selector de cantidad por producto

fix(busqueda): resolver bug de stopwords devolviendo BD completa

perf(api): agregar índices para mejorar queries de búsqueda
```

## 🧪 Convenciones de Testing

### Estructura
```
tests/
├── unit/
│   ├── test_models.py
│   ├── test_schemas.py
│   └── test_services.py
├── integration/
│   ├── test_endpoints.py
│   └── test_database.py
└── conftest.py
```

### Estándares
- **Cobertura mínima**: 80% en lógica crítica
- **Framework**: pytest (recomendado)
- **Fixtures**: conftest.py centralizado
- **Mocking**: unittest.mock para dependencias externas
- **Test DB**: SQLite en memoria para tests

### Nombre de tests
```python
def test_{feature}_{scenario}_{expected_result}():
    pass

# Ejemplos
test_busqueda_con_stopwords_devuelve_lista_vacia()
test_carrito_agregar_producto_incrementa_cantidad()
test_resumen_compra_con_empate_elige_menor_total()
```

## 📚 Convenciones de Documentación

### Docstrings
```python
def buscar_productos(query: str, limite: int = 10) -> list[ProductoSchema]:
    """Busca productos por nombre en todas las categorías.
    
    Args:
        query: Término de búsqueda (mínimo 2 caracteres)
        limite: Máximo de resultados (default 10, máx 100)
        
    Returns:
        Lista de productos encontrados ordenados por relevancia
        
    Raises:
        ValueError: Si query tiene menos de 2 caracteres
    """
```

### README
- Descripción clara del proyecto
- Instrucciones de setup
- Estructura de carpetas
- Endpoints principales
- Roadmap técnico

## 🔒 Estándares de Seguridad

### Backend
- ✅ CORS habilitado solo para red local (192.168.x.x, 10.x.x.x)
- ✅ Input validation con Pydantic
- ✅ SQL Injection: SQLAlchemy ORM (NO raw SQL)
- ✅ CSRF: N/A (API stateless)
- ⚠️ Autenticación: No implementada (TODO para Fase 1)
- ⚠️ Rate limiting: No implementado (TODO)
- ⚠️ HTTPS: No en desarrollo, requerido en producción

### Frontend
- ✅ XSS prevention: textContent en lugar de innerHTML
- ✅ CSRF tokens: N/A (API sin sesiones)
- ⚠️ Local storage: No guardar datos sensibles (TODO)

### Base de Datos
- ✅ SQLite con permisos 0600 (solo lectura para app)
- ✅ Backups automáticos en `/backups/`
- ⚠️ Encriptación: No implementada

## ⚡ Estándares de Rendimiento

### Objetivos
- **API response time**: < 200ms (p95)
- **Frontend load time**: < 2s (3G)
- **DB query time**: < 50ms (p95)
- **Búsqueda**: < 100ms incluso con 50K+ productos

### Optimizaciones aplicadas
- ✅ Índices de base de datos
- ✅ Eliminación de N+1 queries
- ✅ Paginación en endpoints
- ✅ Caching de categorías en frontend
- ⚠️ Redis caching: No implementado (TODO)
- ⚠️ Compression: No implementado

### Monitoreo
- Logs en `/logs/` con timestamp
- EXPLAIN ANALYZE para queries lentas
- DevTools: Network tab en navegador

## 📋 Reglas para Claude Code

### Workflow recomendado
1. Leer CLAUDE.md + skills relevantes
2. Ejecutar pre-commit checklist
3. Usar skills especializadas para cada tarea
4. Crear PR con descripción clara
5. Ejecutar pre-deployment checklist

### Prohibiciones
- ❌ NO modificar main directamente
- ❌ NO eliminar índices de BD sin análisis
- ❌ NO hacer commits a main sin review
- ❌ NO pushear con tests fallando
- ❌ NO cambiar esquema de BD sin migration

### Permisos
- ✅ Crear branches feature/
- ✅ Hacer commits en develop
- ✅ Refactorizar código sin cambiar comportamiento
- ✅ Agregar tests
- ✅ Mejorar documentación

## 🚀 Flujo de Trabajo Recomendado

### Feature Development
```bash
1. git checkout develop
2. git pull origin develop
3. git checkout -b feature/{nombre}
4. [Desarrollar + Tests]
5. Pre-commit checklist
6. git push origin feature/{nombre}
7. Crear PR a develop
8. Code review + merge
```

### Hotfix (Producción)
```bash
1. git checkout main
2. git pull origin main
3. git checkout -b hotfix/{nombre}
4. [Fix + Tests]
5. Pre-deployment checklist
6. Push + PR a main
7. Tag release
```

## ✅ Checklist Pre-Commit

- [ ] Tests pasan localmente
- [ ] No hay errores de tipo (mypy si aplica)
- [ ] Código formateado (black/pylint)
- [ ] Docstrings añadidos/actualizados
- [ ] No hay print() ni console.log() en prod
- [ ] No hay secrets en el código
- [ ] Commit message sigue formato
- [ ] No modificar código no relacionado

## ✅ Checklist Pre-Deployment

- [ ] Todos los tests pasan
- [ ] Code review aprobado
- [ ] Performance acceptable (< 200ms p95)
- [ ] Security check completado
- [ ] Documentación actualizada
- [ ] Backups de BD realizados
- [ ] Plan de rollback disponible
- [ ] Monitoreo configurado
- [ ] Changelog actualizado

## 🔗 Links Importantes

- **Repo**: https://github.com/alarcongonzalo18-web/ahorrago
- **Roadmap**: FEEDBACK.md + memoria de sesiones
- **Dependencias**: requirements.txt
- **Logs**: `/logs/` (development)
- **Backups BD**: `/backups/` (diarios)

## 📚 Recursos por Skill

- **Backend**: `.claude/skills/fastapi-builder/`
- **BD**: `.claude/skills/database-architect/`
- **Scraping**: `.claude/skills/scraper-engineer/`
- **Frontend**: `.claude/skills/frontend-reviewer/`
- **QA**: `.claude/skills/qa-reviewer/`
- **Seguridad**: `.claude/skills/security-engineer/`
