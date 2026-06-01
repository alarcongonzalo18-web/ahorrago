"""
Auditoria read-only de calidad de datos.

Uso:
    python -m app.scripts.auditoria_datos

Genera reportes en reports/ sin modificar la base.
"""
from __future__ import annotations

import csv
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path

from sqlalchemy import func
from sqlalchemy.orm import Session

from app import models
from app.database import SessionLocal
from app.normalizacion import extraer_atributos, normalizar_formato, normalizar_texto


ROOT = Path(__file__).resolve().parents[2]
REPORTS_DIR = ROOT / "reports"
PRECIO_ALTO = 500_000
GRUPO_SOSPECHOSO_MINIMO = 12


@dataclass
class AuditoriaResultado:
    resumen: dict
    metricas: dict
    productos_duplicados: list[dict]
    productos_sospechosos: list[dict]
    producto_base_conflictivos: list[dict]


def _texto(valor) -> str:
    return str(valor or "").strip()


def _precio_efectivo(precio: models.Precio) -> float | None:
    if precio.precio_oferta and precio.precio_oferta > 0:
        return precio.precio_oferta
    return precio.precio_normal


def _fila_producto(producto: models.Producto, motivo: str, detalle: str = "") -> dict:
    return {
        "producto_id": producto.id,
        "nombre": producto.nombre,
        "marca": producto.marca or "",
        "formato": producto.formato or "",
        "producto_base": producto.producto_base or "",
        "motivo": motivo,
        "detalle": detalle,
    }


def _producto_dict(producto: models.Producto) -> dict:
    return {
        "producto_id": producto.id,
        "nombre": producto.nombre,
        "marca": producto.marca or "",
        "formato": producto.formato or "",
        "producto_base": producto.producto_base or "",
    }


def _detectar_duplicados(productos: list[models.Producto]) -> list[dict]:
    grupos = defaultdict(list)
    for producto in productos:
        clave = (
            normalizar_texto(producto.nombre),
            normalizar_texto(producto.marca),
            normalizar_formato(producto.formato),
        )
        grupos[clave].append(producto)

    duplicados = []
    for items in grupos.values():
        if len(items) <= 1:
            continue
        ids = ";".join(str(item.id) for item in items)
        supermercados = sorted({
            precio.supermercado.nombre
            for item in items
            for precio in item_precios(item)
            if precio.supermercado
        })
        for producto in items:
            fila = _producto_dict(producto)
            fila["duplicado_con_ids"] = ids
            fila["supermercados"] = ";".join(supermercados)
            duplicados.append(fila)
    return duplicados


def item_precios(producto: models.Producto) -> list[models.Precio]:
    return list(getattr(producto, "precios", []) or [])


def _producto_base_sospechoso(producto_base: str) -> str:
    base = _texto(producto_base)
    if not base:
        return "producto_base faltante"
    if len(base) < 4:
        return "producto_base demasiado corto"
    if base in {"general", "producto", "sin_marca", "varios"}:
        return "producto_base generico"
    if not any(caracter.isalpha() for caracter in base):
        return "producto_base sin texto"
    return ""


def _detectar_conflictos_producto_base(productos: list[models.Producto]) -> list[dict]:
    grupos = defaultdict(list)
    for producto in productos:
        if producto.producto_base:
            grupos[producto.producto_base].append(producto)

    conflictos = []
    for producto_base, items in grupos.items():
        if len(items) <= 1:
            continue

        marcas = sorted({normalizar_texto(item.marca) for item in items if normalizar_texto(item.marca)})
        formatos = sorted({normalizar_formato(item.formato) for item in items if normalizar_formato(item.formato)})
        categorias = sorted({extraer_atributos(item.nombre).get("categoria") or "" for item in items})
        volumenes = sorted({extraer_atributos(f"{item.nombre} {item.formato}").get("volumen") for item in items
                            if extraer_atributos(f"{item.nombre} {item.formato}").get("volumen")})
        pesos = sorted({extraer_atributos(f"{item.nombre} {item.formato}").get("peso") for item in items
                        if extraer_atributos(f"{item.nombre} {item.formato}").get("peso")})

        motivos = []
        if len(marcas) > 1:
            motivos.append("marcas distintas")
        if len(formatos) > 1 and (len(volumenes) > 1 or len(pesos) > 1):
            motivos.append("formatos incompatibles")
        if len(items) >= GRUPO_SOSPECHOSO_MINIMO:
            motivos.append("grupo demasiado grande")
        if len([categoria for categoria in categorias if categoria]) > 1:
            motivos.append("categorias distintas")

        if motivos:
            conflictos.append({
                "producto_base": producto_base,
                "cantidad_productos": len(items),
                "motivos": "; ".join(motivos),
                "marcas": ";".join(marcas),
                "formatos": ";".join(formatos),
                "productos_ids": ";".join(str(item.id) for item in items[:30]),
                "muestra_nombres": " | ".join(item.nombre for item in items[:5]),
            })
    return conflictos


def ejecutar_auditoria(db: Session) -> AuditoriaResultado:
    productos = db.query(models.Producto).all()
    precios = db.query(models.Precio).all()

    total_productos = len(productos)
    total_precios = len(precios)
    productos_con_precio = {precio.producto_id for precio in precios if precio.producto_id}
    productos_agrupados = [p for p in productos if _texto(p.producto_base)]
    grupos_producto_base = defaultdict(list)
    supermercados_con_precio = set()

    for producto in productos:
        if producto.producto_base:
            grupos_producto_base[producto.producto_base].append(producto)

    for precio in precios:
        if precio.supermercado:
            supermercados_con_precio.add(precio.supermercado.nombre)

    sospechosos = []

    for producto in productos:
        nombre = _texto(producto.nombre)
        if producto.id not in productos_con_precio:
            sospechosos.append(_fila_producto(producto, "producto sin precio"))
        if not nombre:
            sospechosos.append(_fila_producto(producto, "nombre vacio"))
        elif len(nombre) < 4:
            sospechosos.append(_fila_producto(producto, "nombre demasiado corto", f"largo={len(nombre)}"))
        if not producto.categoria_id:
            sospechosos.append(_fila_producto(producto, "categoria vacia"))

        motivo_base = _producto_base_sospechoso(producto.producto_base or "")
        if motivo_base:
            sospechosos.append(_fila_producto(producto, motivo_base))

    precio_por_producto = defaultdict(list)
    for precio in precios:
        precio_por_producto[precio.producto_id].append(precio)
        producto = precio.producto
        if not producto:
            continue

        valor = _precio_efectivo(precio)
        if valor is None or valor == 0:
            sospechosos.append(_fila_producto(producto, "precio en cero", f"precio_id={precio.id}"))
        elif valor < 0:
            sospechosos.append(_fila_producto(producto, "precio negativo", f"precio_id={precio.id}; valor={valor}"))
        elif valor > PRECIO_ALTO:
            sospechosos.append(_fila_producto(producto, "precio extremadamente alto", f"precio_id={precio.id}; valor={valor}"))

        if not precio.supermercado_id or not precio.supermercado:
            sospechosos.append(_fila_producto(producto, "producto sin supermercado asociado", f"precio_id={precio.id}"))

    duplicados = _detectar_duplicados(productos)
    conflictos = _detectar_conflictos_producto_base(productos)

    grupos_con_equivalencia = [items for items in grupos_producto_base.values() if len(items) > 1]
    productos_con_equivalencia = sum(len(items) for items in grupos_con_equivalencia)
    promedio_equivalencias = (
        sum(len(items) for items in grupos_producto_base.values()) / len(grupos_producto_base)
        if grupos_producto_base else 0
    )

    resumen = {
        "productos_totales": total_productos,
        "precios_totales": total_precios,
        "supermercados": db.query(models.Supermercado).count(),
        "categorias": db.query(models.Categoria).count(),
        "subcategorias": db.query(models.Subcategoria).count(),
        "productos_sin_precio": total_productos - len(productos_con_precio),
        "productos_duplicados": len(duplicados),
        "productos_sospechosos": len(sospechosos),
        "producto_base_conflictivos": len(conflictos),
    }

    metricas = {
        "porcentaje_productos_agrupados": round((len(productos_agrupados) / total_productos) * 100, 2) if total_productos else 0,
        "porcentaje_sin_equivalencia": round(((total_productos - productos_con_equivalencia) / total_productos) * 100, 2) if total_productos else 0,
        "cantidad_promedio_equivalencias_por_producto_base": round(promedio_equivalencias, 2),
        "supermercados_cubiertos": len(supermercados_con_precio),
        "supermercados_con_precio": ", ".join(sorted(supermercados_con_precio)),
        "grupos_producto_base": len(grupos_producto_base),
        "grupos_con_equivalencia": len(grupos_con_equivalencia),
    }

    return AuditoriaResultado(
        resumen=resumen,
        metricas=metricas,
        productos_duplicados=duplicados,
        productos_sospechosos=sospechosos,
        producto_base_conflictivos=conflictos,
    )


def _escribir_csv(path: Path, filas: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    campos = sorted({campo for fila in filas for campo in fila.keys()})
    with path.open("w", newline="", encoding="utf-8-sig") as archivo:
        writer = csv.DictWriter(archivo, fieldnames=campos)
        writer.writeheader()
        writer.writerows(filas)


def _calidad_estimada(resultado: AuditoriaResultado) -> str:
    total = resultado.resumen["productos_totales"] or 1
    tasa_sospechosos = resultado.resumen["productos_sospechosos"] / total
    conflictos = resultado.resumen["producto_base_conflictivos"]

    if tasa_sospechosos < 0.03 and conflictos < 20:
        return "Alta"
    if tasa_sospechosos < 0.10 and conflictos < 100:
        return "Media"
    return "Baja"


def _markdown(resultado: AuditoriaResultado) -> str:
    calidad = _calidad_estimada(resultado)
    lines = [
        "# Auditoria de Datos - AhorraGo",
        "",
        "## Resumen Ejecutivo",
        "",
        f"- Calidad estimada de datos: **{calidad}**.",
        f"- Productos totales: {resultado.resumen['productos_totales']}.",
        f"- Precios totales: {resultado.resumen['precios_totales']}.",
        f"- Productos sospechosos detectados: {resultado.resumen['productos_sospechosos']}.",
        f"- Producto_base conflictivos: {resultado.resumen['producto_base_conflictivos']}.",
        "",
        "## Conteos Base",
        "",
    ]

    for clave, valor in resultado.resumen.items():
        lines.append(f"- {clave}: {valor}")

    lines.extend(["", "## Metricas de Matching", ""])
    for clave, valor in resultado.metricas.items():
        lines.append(f"- {clave}: {valor}")

    motivos = Counter(item["motivo"] for item in resultado.productos_sospechosos)
    lines.extend(["", "## Riesgos Encontrados", ""])
    if motivos:
        for motivo, cantidad in motivos.most_common():
            lines.append(f"- {motivo}: {cantidad}")
    else:
        lines.append("- No se detectaron riesgos críticos en las reglas auditadas.")

    lines.extend([
        "",
        "## Archivos Generados",
        "",
        "- reports/auditoria_datos.md",
        "- reports/productos_duplicados.csv",
        "- reports/productos_sospechosos.csv",
        "- reports/producto_base_conflictivos.csv",
        "",
        "## Recomendaciones",
        "",
        "- Revisar primero `producto_base_conflictivos.csv`, porque afecta directamente la precision del comparador.",
        "- Corregir productos sin precio o sin supermercado antes de agregar funcionalidades de usuarios.",
        "- Validar manualmente grupos grandes de `producto_base` antes de usarlos para recomendaciones.",
        "- Mantener esta auditoria como paso obligatorio antes de cambios grandes en datos.",
        "",
        "## Nota",
        "",
        "Esta auditoria no modifica datos. Solo lee la base y genera reportes.",
        "",
    ])
    return "\n".join(lines)


def escribir_reportes(resultado: AuditoriaResultado, output_dir: Path = REPORTS_DIR) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "auditoria_datos.md").write_text(_markdown(resultado), encoding="utf-8")
    _escribir_csv(output_dir / "productos_duplicados.csv", resultado.productos_duplicados)
    _escribir_csv(output_dir / "productos_sospechosos.csv", resultado.productos_sospechosos)
    _escribir_csv(output_dir / "producto_base_conflictivos.csv", resultado.producto_base_conflictivos)


def main() -> int:
    db = SessionLocal()
    try:
        resultado = ejecutar_auditoria(db)
        escribir_reportes(resultado)
    finally:
        db.close()

    print(f"Auditoria completada. Reportes en {REPORTS_DIR}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
