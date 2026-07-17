# Fase 1: Arquitectura Multi-Rubro (Cimientos)

- `[x]` **Refactor de Base de Datos (`app/models.py`)**
  - Añadir la tabla `Vertical` (Ej: Supermercados, Tecnología, Mascotas).
  - Renombrar o adaptar la tabla `Supermercado` a `Tienda`, y enlazarla con una `Vertical`.
  - Crear script de migración para no perder los datos actuales de Supermercados.
- `[x]` **Adaptación de API (`app/main.py`)**
  - Modificar los endpoints para que acepten búsquedas y consultas por `vertical_id`.
  - Ajustar el motor de cotización y resumen para que respete el rubro.
- `[x]` **Rediseño del Frontend (Landing Page)**
  - Crear una pantalla inicial (`index.html`) que pida al usuario elegir un rubro (Supermercados, Mascotas, etc.).
  - Implementar estado visual donde solo "Supermercados" esté clickeable (próximamente los demás).
  - Ajustar la navegación para que la app recuerde en qué "Mundo" (rubro) está el usuario.
- `[x]` **Testeo del Flujo Base**
  - Confirmar que la búsqueda de Lider, Jumbo y Unimarc siga funcionando intacta bajo el nuevo modelo de "Vertical 1".
