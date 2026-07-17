from __future__ import annotations

import csv
from collections import defaultdict
from pathlib import Path

from sqlalchemy import distinct, func
from sqlalchemy.orm import Session

from app import models
from app.matching import matching_score
from app.normalizacion import extraer_atributos, generar_producto_base, normalizar_formato, normalizar_texto


ROOT = Path(__file__).resolve().parents[1]
REPORTS_DIR = ROOT / "reports"


def clasificar_conflicto(row: dict) -> list[str]:
    motivos = normalizar_texto(row.get("motivos", ""))
    marcas = [item for item in (row.get("marcas", "") or "").split(";") if item]
    formatos = [item for item in (row.get("formatos", "") or "").split(";") if item]
    nombres = normalizar_texto(row.get("muestra_nombres", ""))
    clases = []

    if "marcas distintas" in motivos or len(set(marcas)) > 1:
        clases.append("marca distinta")
    if "formatos incompatibles" in motivos or len(set(formatos)) > 1:
        clases.append("formato distinto")

    volumenes = set()
    pesos = set()
    cantidades = set()
    sabores = set()
    categorias = set()
    for nombre in (row.get("muestra_nombres", "") or "").split("|"):
        attrs = extraer_atributos(nombre)
        if attrs.get("volumen"):
            volumenes.add(attrs["volumen"])
        if attrs.get("peso"):
            pesos.add(attrs["peso"])
        if attrs.get("cantidad"):
            cantidades.add(attrs["cantidad"])
        sabores.update(attrs.get("sabores") or [])
        if attrs.get("categoria"):
            categorias.add(attrs["categoria"])

    if len(volumenes) > 1:
        clases.append("volumen distinto")
    if len(pesos) > 1:
        clases.append("peso distinto")
    if len(cantidades) > 1:
        clases.append("cantidad distinta")
    if len(sabores) > 1:
        clases.append("sabor distinto")
    if len(categorias) > 1 or "categorias distintas" in motivos:
        clases.append("categoria incorrecta")

    cantidad = int(row.get("cantidad_productos") or 0)
    if cantidad >= 12:
        clases.append("nombre demasiado generico")
    if "formato distinto" in clases and ("_1" in (row.get("producto_base", "") or "") or "general" in nombres):
        clases.append("error de normalizacion")
    if clases:
        clases.append("error de producto_base")
        clases.append("posible falso positivo")
    else:
        clases.extend(["posible falso negativo"])

    return sorted(set(clases))


def _leer_csv(path: Path) -> list[dict]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8-sig") as archivo:
        return list(csv.DictReader(archivo))


def _escribir_csv(path: Path, filas: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    campos = sorted({campo for fila in filas for campo in fila.keys()})
    with path.open("w", newline="", encoding="utf-8-sig") as archivo:
        writer = csv.DictWriter(archivo, fieldnames=campos)
        writer.writeheader()
        writer.writerows(filas)


def metricas_por_categoria(db: Session, conflictos: list[dict] | None = None) -> list[dict]:
    conflictos = conflictos or []
    conflictos_por_producto = defaultdict(int)
    for row in conflictos:
        for raw_id in (row.get("productos_ids", "") or "").split(";"):
            if raw_id.isdigit():
                conflictos_por_producto[int(raw_id)] += 1

    productos = db.query(
        models.Producto.id,
        models.Producto.producto_base,
        models.Categoria.nombre.label("categoria"),
    ).outerjoin(models.Categoria, models.Producto.categoria_id == models.Categoria.id).all()

    por_categoria = defaultdict(lambda: {
        "productos_totales": 0,
        "bases": defaultdict(int),
        "supermercados": set(),
        "conflictos_detectados": 0,
    })
    filas_proveedor = db.query(
        models.Producto.id,
        models.Categoria.nombre.label("categoria"),
        models.Proveedor.nombre.label("proveedor"),
    ).join(models.Precio, models.Precio.producto_id == models.Producto.id).join(
        models.Proveedor, models.Precio.proveedor_id == models.Proveedor.id
    ).outerjoin(models.Categoria, models.Producto.categoria_id == models.Categoria.id).all()

    for producto in productos:
        categoria = producto.categoria or "Sin categoria"
        data = por_categoria[categoria]
        data["productos_totales"] += 1
        if producto.producto_base:
            data["bases"][producto.producto_base] += 1
        data["conflictos_detectados"] += conflictos_por_producto.get(producto.id, 0)

    for row in filas_proveedor:
        por_categoria[row.categoria or "Sin categoria"]["supermercados"].add(row.proveedor)

    resultado = []
    for categoria, data in por_categoria.items():
        total = data["productos_totales"]
        bases = data["bases"]
        grupos_con_equivalencia = sum(1 for count in bases.values() if count > 1)
        productos_con_equivalencia = sum(count for count in bases.values() if count > 1)
        porcentaje_equivalencia = round((productos_con_equivalencia / total) * 100, 2) if total else 0
        resultado.append({
            "categoria": categoria,
            "productos_totales": total,
            "producto_base_unicos": len(bases),
            "grupos_con_equivalencia": grupos_con_equivalencia,
            "porcentaje_equivalencia": porcentaje_equivalencia,
            "porcentaje_sin_equivalencia": round(100 - porcentaje_equivalencia, 2),
            "supermercados_cubiertos": len(data["supermercados"]),
            "conflictos_detectados": data["conflictos_detectados"],
        })

    return sorted(resultado, key=lambda item: (item["porcentaje_equivalencia"], -item["conflictos_detectados"]))


def resumen_matching(db: Session, conflictos: list[dict] | None = None) -> dict:
    conflictos = conflictos if conflictos is not None else _leer_csv(REPORTS_DIR / "producto_base_conflictivos.csv")
    total_productos = db.query(models.Producto).count()
    producto_base_unicos = db.query(func.count(distinct(models.Producto.producto_base))).scalar() or 0
    grupos_con_equivalencia = db.query(models.Producto.producto_base).filter(
        models.Producto.producto_base.isnot(None),
        models.Producto.producto_base != "",
    ).group_by(models.Producto.producto_base).having(func.count(models.Producto.id) > 1).count()

    categorias = metricas_por_categoria(db, conflictos)
    sin_equivalencia = round(100 - (
        sum(item["productos_totales"] * item["porcentaje_equivalencia"] / 100 for item in categorias) / total_productos * 100
        if total_productos else 0
    ), 2)

    score_muestras = []
    limite_muestra = min(500, grupos_con_equivalencia)
    grupos = db.query(models.Producto.producto_base).filter(
        models.Producto.producto_base.isnot(None),
        models.Producto.producto_base != "",
    ).group_by(models.Producto.producto_base).having(func.count(models.Producto.id) > 1).limit(limite_muestra).all()
    for (base,) in grupos:
        productos = db.query(models.Producto).filter(models.Producto.producto_base == base).limit(3).all()
        if len(productos) >= 2:
            score_muestras.append(matching_score(productos[0], productos[1]))

    score_promedio = round(sum(score_muestras) / len(score_muestras), 2) if score_muestras else 0
    cambios_path = REPORTS_DIR / "fase5b_cambios.csv"
    cambios_aplicados = 0
    fecha_ultima_actualizacion = None
    if cambios_path.exists():
        cambios_aplicados = max(0, len(_leer_csv(cambios_path)))
        fecha_ultima_actualizacion = cambios_path.stat().st_mtime
    fases_csv = {
        "fase5b": REPORTS_DIR / "fase5b_cambios.csv",
        "fase5b_fix": REPORTS_DIR / "fix_fideos_fase5b.csv",
        "fase5d_fix": REPORTS_DIR / "fase5d_fix_cambios.csv",
        "fase5c": REPORTS_DIR / "fase5c_cambios.csv",
    }
    cambios_por_fase = {}
    fechas = []
    for fase, path in fases_csv.items():
        if path.exists():
            cambios_por_fase[fase] = len(_leer_csv(path))
            fechas.append(path.stat().st_mtime)
        else:
            cambios_por_fase[fase] = 0
    if fechas:
        fecha_ultima_actualizacion = max(fechas)
    categorias_aplicadas = ["Limpieza", "Mascotas"]
    if cambios_por_fase.get("fase5c"):
        categorias_aplicadas.extend(["Bebidas", "Higiene Personal", "Bebe"])
    categorias_pendientes = [
        categoria for categoria in [
            "Frutas y Verduras",
            "Congelados",
            "Panaderia",
            "Carnes y Pescados",
            "Desayuno y Snacks",
        ] if categoria not in categorias_aplicadas
    ]
    return {
        "total_productos": total_productos,
        "producto_base_unicos": producto_base_unicos,
        "grupos_con_equivalencia": grupos_con_equivalencia,
        "equivalencias_actuales": sum(item["productos_totales"] * item["porcentaje_equivalencia"] / 100 for item in categorias),
        "equivalencias_por_categoria": categorias,
        "porcentaje_sin_equivalencia": sin_equivalencia,
        "producto_base_conflictivos": len(conflictos),
        "categorias_peor_matching": categorias[:5],
        "categorias_mejor_matching": sorted(categorias, key=lambda item: item["porcentaje_equivalencia"], reverse=True)[:5],
        "score_promedio": score_promedio,
        "cambios_aplicados": cambios_aplicados,
        "cambios_por_fase": cambios_por_fase,
        "fecha_ultima_actualizacion": fecha_ultima_actualizacion,
        "categorias_aplicadas": sorted(set(categorias_aplicadas)),
        "categorias_pendientes": categorias_pendientes,
        "recomendaciones": [
            "Revisar producto_base conflictivos por formato y marca antes de crear usuarios.",
            "Priorizar categorias con menor porcentaje de equivalencia.",
            "Validar manualmente grupos grandes antes de aplicar reconstruccion real.",
        ],
    }


def diagnosticar_matching(db: Session, reports_dir: Path = REPORTS_DIR) -> dict:
    conflictos = _leer_csv(reports_dir / "producto_base_conflictivos.csv")
    clasificados = []
    for row in conflictos:
        item = dict(row)
        item["clasificacion"] = "; ".join(clasificar_conflicto(row))
        clasificados.append(item)

    categorias = metricas_por_categoria(db, clasificados)
    grupos_sospechosos = sorted(
        clasificados,
        key=lambda item: int(item.get("cantidad_productos") or 0),
        reverse=True,
    )[:300]

    _escribir_csv(reports_dir / "conflictos_clasificados.csv", clasificados)
    _escribir_csv(reports_dir / "equivalencias_por_categoria.csv", categorias)
    _escribir_csv(reports_dir / "grupos_sospechosos.csv", grupos_sospechosos)

    resumen = resumen_matching(db, clasificados)
    lines = [
        "# Diagnostico de Matching - AhorraGo",
        "",
        "## Resumen",
        "",
        f"- Total productos: {resumen['total_productos']}",
        f"- Producto_base unicos: {resumen['producto_base_unicos']}",
        f"- Grupos con equivalencia: {resumen['grupos_con_equivalencia']}",
        f"- Porcentaje sin equivalencia: {resumen['porcentaje_sin_equivalencia']}%",
        f"- Producto_base conflictivos: {resumen['producto_base_conflictivos']}",
        f"- Score promedio muestreado: {resumen['score_promedio']}",
        "",
        "## Peor Matching",
        "",
    ]
    for item in resumen["categorias_peor_matching"]:
        lines.append(f"- {item['categoria']}: {item['porcentaje_equivalencia']}% equivalencia, {item['conflictos_detectados']} conflictos")
    lines.extend(["", "## Mejor Matching", ""])
    for item in resumen["categorias_mejor_matching"]:
        lines.append(f"- {item['categoria']}: {item['porcentaje_equivalencia']}% equivalencia, {item['conflictos_detectados']} conflictos")
    lines.extend(["", "## Archivos", "", "- conflictos_clasificados.csv", "- equivalencias_por_categoria.csv", "- grupos_sospechosos.csv"])
    (reports_dir / "diagnostico_matching.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return resumen


def proponer_producto_base(producto: models.Producto) -> str:
    attrs = extraer_atributos(f"{producto.nombre} {producto.formato}")
    base = generar_producto_base(producto.nombre, producto.marca or attrs.get("marca") or "", producto.tipo or "general", producto.formato or "")
    partes = [attrs.get("categoria") or "", attrs.get("marca") or "", base]
    if attrs.get("volumen"):
        partes.append(f"{attrs['volumen']}ml")
    if attrs.get("peso"):
        partes.append(f"{attrs['peso']}g")
    if attrs.get("cantidad"):
        partes.append(f"{attrs['cantidad']}un")
    limpio = "_".join(part for part in partes if part)
    return normalizar_texto(limpio).replace(" ", "_").replace("-", "_")
