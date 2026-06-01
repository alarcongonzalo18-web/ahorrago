from __future__ import annotations

import csv
import shutil
import sqlite3
from collections import defaultdict
from datetime import datetime
from pathlib import Path

from sqlalchemy.orm import Session

from app import models
from app.fase5a_rules import compatible_fase5a, key_fase5a
from app.matching import matching_score


PROJECT_ROOT = Path(__file__).resolve().parents[1]
REPORTS = PROJECT_ROOT / "reports"
BACKUPS = PROJECT_ROOT / "backups"
DB_PATH = PROJECT_ROOT / "supercheck.db"
CATEGORIAS_PERMITIDAS = {"Mascotas", "Limpieza"}
CATEGORIAS_BLOQUEADAS = {
    "Bebidas",
    "Bebe",
    "Higiene Personal",
    "Frutas y Verduras",
    "Congelados",
    "Panaderia",
    "Carnes y Pescados",
}


def crear_backup_pre_fase5b() -> Path:
    BACKUPS.mkdir(exist_ok=True)
    destino = BACKUPS / f"supercheck_pre_fase5b_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
    shutil.copy2(DB_PATH, destino)
    validar_backup(destino)
    return destino


def validar_backup(path: Path) -> bool:
    conn = sqlite3.connect(path)
    try:
        resultado = conn.execute("PRAGMA quick_check").fetchone()[0]
    finally:
        conn.close()
    if resultado != "ok":
        raise RuntimeError(f"Backup invalido: {path} -> {resultado}")
    return True


def cargar_grupos_riesgosos(path: Path = REPORTS / "fase5a_falsos_positivos.csv") -> set[tuple[str, str]]:
    if not path.exists():
        return set()
    riesgos = set()
    with path.open(newline="", encoding="utf-8-sig") as archivo:
        for row in csv.DictReader(archivo):
            categoria = row.get("categoria") or ""
            key = row.get("producto_base_propuesto") or ""
            if categoria and key:
                riesgos.add((categoria, key))
    return riesgos


def _productos_por_categoria(db: Session, categorias: set[str]):
    return db.query(
        models.Producto,
        models.Categoria.nombre.label("categoria"),
    ).join(
        models.Categoria,
        models.Producto.categoria_id == models.Categoria.id,
    ).filter(
        models.Categoria.nombre.in_(categorias)
    ).all()


def _grupo_seguro(grupo: list[models.Producto], categoria: str) -> tuple[bool, float]:
    scores = []
    for index, producto in enumerate(grupo):
        for candidato in grupo[index + 1:]:
            if not compatible_fase5a(producto, candidato, categoria):
                return False, 0
            scores.append(matching_score(producto, candidato))
    score = round(sum(scores) / len(scores), 2) if scores else 100
    return True, score


def metricas_fase5b(db: Session, categorias: set[str] = CATEGORIAS_PERMITIDAS) -> dict:
    rows = _productos_por_categoria(db, categorias)
    por_categoria = defaultdict(lambda: {"productos": 0, "bases": defaultdict(int), "conflictos": 0})
    for producto, categoria in rows:
        data = por_categoria[categoria]
        data["productos"] += 1
        if producto.producto_base:
            data["bases"][producto.producto_base] += 1

    resultado = {}
    total_equivalentes = 0
    total_grupos = 0
    total_conflictos = 0
    for categoria, data in por_categoria.items():
        bases = data["bases"]
        grupos_equivalencia = {base: count for base, count in bases.items() if count > 1}
        productos_equivalentes = sum(grupos_equivalencia.values())
        conflictos = 0
        for base in grupos_equivalencia:
            productos = [
                producto
                for producto, cat in rows
                if cat == categoria and producto.producto_base == base
            ][:8]
            seguro, _ = _grupo_seguro(productos, categoria)
            if not seguro:
                conflictos += 1
        resultado[categoria] = {
            "productos": data["productos"],
            "grupos_equivalencia": len(grupos_equivalencia),
            "productos_equivalentes": productos_equivalentes,
            "conflictos": conflictos,
        }
        total_equivalentes += productos_equivalentes
        total_grupos += len(grupos_equivalencia)
        total_conflictos += conflictos

    resultado["TOTAL"] = {
        "productos": sum(item["productos"] for item in resultado.values()),
        "grupos_equivalencia": total_grupos,
        "productos_equivalentes": total_equivalentes,
        "conflictos": total_conflictos,
    }
    return resultado


def seleccionar_cambios(db: Session, riesgos: set[tuple[str, str]] | None = None) -> list[dict]:
    riesgos = riesgos if riesgos is not None else cargar_grupos_riesgosos()
    rows = _productos_por_categoria(db, CATEGORIAS_PERMITIDAS)
    grupos = defaultdict(list)
    for producto, categoria in rows:
        if categoria in CATEGORIAS_BLOQUEADAS:
            continue
        key = key_fase5a(producto, categoria)
        if (categoria, key) in riesgos:
            continue
        grupos[(categoria, key)].append(producto)

    cambios = []
    for (categoria, key), grupo in sorted(grupos.items()):
        if len(grupo) <= 1:
            continue
        seguro, score = _grupo_seguro(grupo[:12], categoria)
        if not seguro:
            continue
        bases_actuales = {producto.producto_base or "" for producto in grupo}
        if len(bases_actuales) <= 1 and next(iter(bases_actuales)) == key:
            continue
        for producto in grupo:
            if (producto.producto_base or "") == key:
                continue
            cambios.append({
                "producto_id": producto.id,
                "producto_original": producto.nombre,
                "producto_base_anterior": producto.producto_base or "",
                "producto_base_nuevo": key,
                "categoria": categoria,
                "score_matching": score,
            })
    return cambios


def escribir_cambios(cambios: list[dict], path: Path = REPORTS / "fase5b_cambios.csv") -> None:
    REPORTS.mkdir(exist_ok=True)
    campos = [
        "producto_id",
        "producto_original",
        "producto_base_anterior",
        "producto_base_nuevo",
        "categoria",
        "score_matching",
    ]
    with path.open("w", newline="", encoding="utf-8-sig") as archivo:
        writer = csv.DictWriter(archivo, fieldnames=campos)
        writer.writeheader()
        writer.writerows(cambios)


def aplicar_cambios(db: Session, cambios: list[dict], batch_size: int = 100) -> int:
    aplicados = 0
    for index in range(0, len(cambios), batch_size):
        lote = cambios[index:index + batch_size]
        for cambio in lote:
            producto = db.get(models.Producto, int(cambio["producto_id"]))
            if not producto:
                continue
            producto.producto_base = cambio["producto_base_nuevo"]
            aplicados += 1
        db.commit()
    return aplicados


def escribir_validacion(antes: dict, despues: dict, cambios: list[dict], backup: Path | None) -> None:
    lines = [
        "# Validacion Fase 5B - AhorraGo",
        "",
        "## Seguridad",
        "",
        f"- Backup: {backup if backup else 'backup previo existente/no creado por esta ejecucion'}",
        f"- Cambios aplicados: {len(cambios)}",
        "- Categorias permitidas: Mascotas, Limpieza",
        "",
        "## Antes",
        "",
        f"- Equivalencias: {antes['TOTAL']['productos_equivalentes']}",
        f"- Conflictos: {antes['TOTAL']['conflictos']}",
        "",
        "## Despues",
        "",
        f"- Equivalencias: {despues['TOTAL']['productos_equivalentes']}",
        f"- Conflictos: {despues['TOTAL']['conflictos']}",
        "",
        "## Detalle por Categoria",
        "",
    ]
    for categoria in sorted(CATEGORIAS_PERMITIDAS):
        lines.append(
            f"- {categoria}: equivalencias {antes.get(categoria, {}).get('productos_equivalentes', 0)} -> "
            f"{despues.get(categoria, {}).get('productos_equivalentes', 0)}, conflictos "
            f"{antes.get(categoria, {}).get('conflictos', 0)} -> {despues.get(categoria, {}).get('conflictos', 0)}"
        )
    (REPORTS / "fase5b_validacion.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def leer_cambios(path: Path = REPORTS / "fase5b_cambios.csv") -> list[dict]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8-sig") as archivo:
        return list(csv.DictReader(archivo))
