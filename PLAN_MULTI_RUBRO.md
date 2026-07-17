# AhorraGo: De Supermercados a Súper-App de Comparación

Tu visión es transformar AhorraGo en el **"Google de las cotizaciones"**: un ecosistema donde el usuario selecciona un rubro (Supermercado, Tecnología, Mascotas, Vuelos, Hoteles) y el motor compara todo el mercado específico de ese rubro.

Este es un **cambio arquitectónico masivo**, ya que el sistema actual fue diseñado exclusivamente para productos de supermercado (con variables como "formato en litros/kilos", "ahorro por unidad", etc.). 

## Estrategia Arquitectónica

Para soportar múltiples verticales (rubros) sin colapsar el sistema, debemos rediseñar la base de datos y la interfaz gráfica. 

### 1. Reestructuración de la Base de Datos (`app/models.py`)
Actualmente todo asume que existe un `Supermercado`. Cambiaremos esto a un modelo genérico de `Proveedor` o `Tienda`, agrupados por **Vertical**.

- **Nueva Tabla `Verticales`:** 
  - ID 1: Supermercados
  - ID 2: Tecnología (SPDigital, PCFactory, Aufbau, etc.)
  - ID 3: Mascotas (SuperZoo, PetHappy, etc.)
  - ID 4: Vuelos (Despegar, Latam, Sky)
  - ID 5: Hoteles
- **Renombrar `Supermercado` a `Proveedor`:** Cada proveedor pertenecerá a una `Vertical`.
- **Flexibilidad en `Producto`:** Un computador (Tecnología) tiene *RAM, Procesador y Almacenamiento*. Una bolsa de comida de perro (Mascotas) tiene *Kilos y Etapa (Cachorro/Adulto)*. Un Vuelo tiene *Origen, Destino, Fechas*. 
  Tendremos que crear tablas específicas para servicios (ej. `Vuelos`, `Hoteles`) o usar un campo genérico tipo `JSON` (Metadata) en la tabla productos para guardar los detalles técnicos de cada rubro.

### 2. Rediseño del Frontend (Interfaz)
- **Nueva Pantalla de Inicio (Landing Page):** 
  El usuario ya no entrará directo a los productos. Entrará a una pantalla principal estilo "Mundo AhorraGo" con tarjetas grandes preguntando: *¿Qué quieres comparar hoy?* 🛒 **Supermercados** | 💻 **Tecnología** | ✈️ **Viajes**.
- **Motores de Búsqueda Dedicados:** Si eliges "Vuelos", el buscador debe cambiar (pedir origen, destino y fecha, en vez de una barra de texto simple). Si eliges "Supermercado", se mantiene el buscador actual.

### 3. Pipeline de Scraping Dinámico
Actualmente el pipeline (`actualizar_productos.py`) corre los 3 supermercados al mismo tiempo. Necesitaremos un orquestador que ejecute módulos independientes:
- `scrapers/supermercados/...`
- `scrapers/tecnologia/...` (PCFactory, SPDigital)
- `scrapers/vuelos/...` (vía APIs de vuelos comerciales)

## Fases de Implementación Sugeridas

Como esto es hacer 4 aplicaciones en 1, te sugiero implementarlo de manera **escalonada**:

1. **Fase 1: Preparación Estructural.** Modificar la base de datos para crear la categoría `Verticales` y renombrar `Supermercados` a `Proveedores`. Ajustar el Frontend para tener la página de bienvenida (Landing) con los rubros, pero dejando solo "Supermercado" activo por ahora.
2. **Fase 2: Expansión a Productos Similares (Tecnología y Mascotas).** Crear los scrapers para PCFactory y SuperZoo. Como venden "productos tangibles", podemos usar la misma tabla de base de datos actual.
3. **Fase 3: Expansión a Servicios (Vuelos y Hoteles).** Crear un sistema completamente nuevo dentro de AhorraGo exclusivo para buscar pasajes y reservas (ya que requieren fechas y ciudades, lo cual rompe la lógica de un producto normal).

## Open Questions

> [!IMPORTANT]
> **Definición de Alcance Inicial**
> Empezar a programar Vuelos, Tecnología y Mascotas al mismo tiempo tomará muchas semanas de desarrollo. ¿Estás de acuerdo con el **plan de 3 Fases** que propongo arriba? Así podemos crear la "Carcasa" multi-rubro de inmediato (Fase 1) y luego ir conectando cada nuevo rubro uno por uno (Fase 2 y 3).
