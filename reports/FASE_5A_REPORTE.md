# Fase 5A Reporte - AhorraGo

## Resumen Ejecutivo

La Fase 5A simuló mejoras de matching en categorías de mejor retorno y menor riesgo: Bebidas, Limpieza, Higiene Personal, Bebé y Mascotas. La simulación se ejecutó en DRY RUN y no modificó la base real.

Resultado principal: se proyecta aumentar productos equivalentes de 2.918 a 4.477, una mejora de 53,43%, manteniendo falsos positivos aplicables en 0 porque los grupos riesgosos se excluyen.

## Métricas Antes

- Productos evaluados en categorías objetivo: 10.656
- Productos equivalentes actuales: 2.918
- Conflictos actuales: 715

## Métricas Después Proyectadas

- Productos equivalentes proyectados: 4.477
- Mejora porcentual: 53,43%
- Conflictos reducibles estimados: 540
- Grupos riesgosos excluidos: 639
- Pares riesgosos detectados: 5.480
- Falsos positivos estimados aplicables: 0

## Categorías Mejoradas

- Bebé: 360 -> 573 productos equivalentes (+59,17%)
- Bebidas: 1.197 -> 1.683 productos equivalentes (+40,60%)
- Higiene Personal: 663 -> 1.055 productos equivalentes (+59,13%)
- Limpieza: 451 -> 738 productos equivalentes (+63,64%)
- Mascotas: 247 -> 428 productos equivalentes (+73,28%)

## Conflictos Encontrados

Los principales conflictos siguen relacionados con:

- Formatos incompatibles.
- Volúmenes distintos.
- Pesos distintos.
- Variantes como zero/normal.
- Aromas y sabores distintos.
- Etapas/tallas en bebé y mascotas.

## Riesgos

- No aplicar automáticamente los grupos riesgosos.
- Las categorías excluidas siguen con baja calidad de matching.
- Las reglas deben validarse con revisión humana antes de modificar datos reales.

## Recomendaciones

1. Priorizar aplicación controlada en Mascotas y Limpieza.
2. Mantener DRY RUN obligatorio para cualquier cambio de `producto_base`.
3. Revisar manualmente `fase5a_falsos_positivos.csv`.
4. Crear una lista blanca de grupos seguros para aplicación real.
5. Dejar Frutas/Verduras, Carnes, Panadería y Congelados para otra fase.

## Comandos Ejecutados

```powershell
python -m app.scripts.simular_mejora_matching_fase5a
python -m pytest -q
python -m compileall app tests
python -c "from app.main import app; print(app.title)"
```

## Resultado de Tests

- `32 passed`
- `compileall OK`
- `FastAPI`
