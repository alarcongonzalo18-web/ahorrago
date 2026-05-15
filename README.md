# AhorraGo 🛒

Comparador de precios de supermercados chilenos en tiempo real. Busca productos y compara precios entre **Líder**, **Jumbo** y **Unimarc**, arma listas de compras y encuentra la combinación más económica por tienda.

---

## Características

- Búsqueda de productos con comparación de precios entre los 3 supermercados
- Lista de compras con cálculo de compra óptima por tienda
- Detección automática de ofertas y precios de referencia ($/L, $/kg)
- Base de datos con más de 50 categorías de productos
- Actualización automática de precios programable (4 veces al día)
- API REST documentada con FastAPI

---

## Requisitos previos

| Herramienta | Versión mínima | Descarga |
|---|---|---|
| Python | 3.10+ | [python.org](https://www.python.org/downloads/) |
| Google Chrome | Última versión | [google.com/chrome](https://www.google.com/chrome/) |
| ChromeDriver | Igual a tu versión de Chrome | [chromedriver.chromium.org](https://chromedriver.chromium.org/downloads) |
| Git | Cualquiera | [git-scm.com](https://git-scm.com/) |

> **ChromeDriver** debe estar en tu PATH o en la misma carpeta del proyecto. Verifica que su versión coincida exactamente con la de tu Chrome instalado.

---

## Instalación

### 1. Clonar el repositorio

```bash
git clone https://github.com/alarcongonzalo18-web/ahorrago.git
cd ahorrago
```

### 2. Crear y activar entorno virtual

```bash
# Crear entorno
python -m venv venv

# Activar en Windows
venv\Scripts\activate

# Activar en macOS/Linux
source venv/bin/activate
```

### 3. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 4. Cargar datos iniciales

Ejecuta la actualización de productos para poblar la base de datos por primera vez:

```bash
actualizar-productos.bat
```

> Este proceso puede tomar entre 20 y 60 minutos dependiendo de tu conexión, ya que descarga productos de los 3 supermercados.

---

## Correr el proyecto

### Opción A — Script automático (recomendado)

Inicia backend y frontend con un solo doble clic:

```
iniciar-servidores.bat
```

Esto levanta:
- **Backend** en `http://localhost:8001`
- **Frontend** en `http://localhost:5500`
- Abre el navegador automáticamente

---

### Opción B — Manual

#### Backend (FastAPI)

```bash
# Con el entorno virtual activado
uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload
```

La documentación interactiva de la API queda disponible en:
- Swagger UI: `http://localhost:8001/docs`
- ReDoc: `http://localhost:8001/redoc`

#### Frontend

```bash
# Desde la raíz del proyecto
python -m http.server 5500 --directory frontend
```

Luego abre `http://localhost:5500` en tu navegador.

---

## Actualización de productos

### Manual (ejecutar ahora)

```bash
actualizar-productos.bat
```

### Automática (4 veces al día: 06:00, 12:00, 18:00, 00:00)

Para activar la tarea programada en Windows:

```powershell
.\programar-actualizacion-productos.ps1
```

Para pausarla:

```powershell
.\pausar-actualizacion-productos.ps1
```

> La tarea programada requiere que el computador esté encendido. Si estaba apagado a la hora programada, Windows ejecutará la tarea en cuanto se encienda.

---

## Endpoints de la API

| Método | Endpoint | Descripción |
|---|---|---|
| `GET` | `/` | Health check |
| `GET` | `/productos/buscar/{texto}` | Busca productos y compara precios |
| `GET` | `/buscar/{texto}` | Búsqueda rápida de opciones |
| `POST` | `/comparar` | Compara lista de compras por supermercado |
| `GET` | `/categorias` | Lista todas las categorías |
| `GET` | `/subcategorias/{id}` | Lista subcategorías de una categoría |
| `GET` | `/estado-datos` | Estado actual de la base de datos |
| `GET` | `/diagnostico/calidad` | Reporte de calidad de los datos |

### Ejemplo: comparar lista de compras

```bash
curl -X POST http://localhost:8001/comparar \
  -H "Content-Type: application/json" \
  -d '{
    "productos": [
      {"nombre": "leche", "cantidad": 2},
      {"nombre": "arroz", "cantidad": 1},
      {"nombre": "aceite", "cantidad": 1}
    ]
  }'
```

---

## Estructura de carpetas

```
ahorrago/
│
├── app/                          # Backend (FastAPI)
│   ├── main.py                   # Endpoints y lógica principal
│   ├── models.py                 # Modelos SQLAlchemy (tablas)
│   ├── database.py               # Conexión a SQLite
│   ├── schemas.py                # Schemas Pydantic (validación)
│   ├── services.py               # Lógica de negocio y comparación
│   │
│   ├── scraper_lider.py          # Scraper Líder (urllib, sin navegador)
│   ├── scraper_jumbo_real.py     # Scraper Jumbo (Selenium)
│   ├── scraper_unimarc.py        # Scraper Unimarc (Selenium)
│   │
│   ├── actualizar_productos.py   # Orquestador del pipeline completo
│   ├── combinar_supermercados.py # Une los 3 CSVs en uno solo
│   ├── reconstruir_base.py       # Reconstruye la BD desde CSV
│   ├── importar_csv.py           # Importa CSV a SQLite
│   ├── convertir_lider.py        # Normaliza datos de Líder
│   ├── convertir_jumbo.py        # Normaliza datos de Jumbo
│   ├── convertir_unimarc.py      # Normaliza datos de Unimarc
│   ├── generar_catalogo.py       # Genera catálogo de productos
│   ├── validar_csv.py            # Valida integridad de los datos
│   └── seed.py                   # Datos iniciales de supermercados
│
├── frontend/
│   └── index.html                # SPA (HTML + CSS + JS vanilla)
│
├── data/                         # Datos generados por los scrapers
│   ├── lider_real.csv
│   ├── jumbo_real.csv
│   ├── unimarc_real.csv
│   └── productos_supermercados.csv
│
├── logs/                         # Logs de cada actualización
├── backups/                      # Backups automáticos de la BD
│
├── supercheck.db                 # Base de datos SQLite
├── requirements.txt              # Dependencias Python
│
├── iniciar-servidores.bat        # Inicia backend + frontend
├── actualizar-productos.bat      # Actualiza productos manualmente
├── programar-actualizacion-productos.ps1   # Activa tarea automática
└── pausar-actualizacion-productos.ps1      # Pausa tarea automática
```

---

## Pipeline de actualización de datos

```
scraper_lider.py   ──┐
scraper_jumbo.py   ──┼──► combinar_supermercados.py ──► reconstruir_base.py ──► supercheck.db
scraper_unimarc.py ──┘
```

Cada scraper genera su propio CSV. El combinador los une en `productos_supermercados.csv`, y finalmente se reconstruye la base de datos SQLite.

---

## Supermercados cubiertos

| Supermercado | Método de scraping | Categorías |
|---|---|---|
| Líder | urllib + JSON-LD | 52 |
| Jumbo | Selenium + ChromeDriver | 52 |
| Unimarc | Selenium + ChromeDriver | 52 |

---

## Solución de problemas

**ChromeDriver no encontrado**
```
Asegúrate de que chromedriver.exe esté en tu PATH.
Descarga la versión que coincida con tu Chrome en: chromedriver.chromium.org
```

**Error de CORS al abrir el frontend**
```
Verifica que el backend esté corriendo en el puerto 8001.
El frontend debe abrirse desde http://localhost:5500, no desde el sistema de archivos.
```

**La base de datos está vacía**
```
Ejecuta actualizar-productos.bat para poblar la base de datos.
```

**Selenium no puede abrir Chrome**
```
Verifica que Google Chrome esté instalado y que ChromeDriver tenga la misma versión.
```

---

## Licencia

MIT
