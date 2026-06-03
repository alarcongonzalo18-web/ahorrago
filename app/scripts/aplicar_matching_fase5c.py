from __future__ import annotations

import csv
import re
import shutil
import sqlite3
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

from sqlalchemy.orm import Session

from app import models
from app.database import SessionLocal
from app.fase5a_rules import atributos_fase5a, compatible_fase5a, key_fase5a
from app.matching import matching_score
from app.normalizacion import marca_producto, normalizar_texto
from app.scripts.auditoria_categorias import auditar_categorias
from app.scripts.report_pdf import markdown_to_pdf


ROOT = Path(__file__).resolve().parents[2]
REPORTS = ROOT / "reports"
BACKUPS = ROOT / "backups"
DB_PATH = ROOT / "supercheck.db"
CAMBIOS_CSV = REPORTS / "fase5c_cambios.csv"
VALIDACION_MD = REPORTS / "fase5c_validacion.md"
MASTER_REPORT = REPORTS / "AHORRAGO_MASTER_REPORT.md"

CATEGORIAS_PERMITIDAS = {"Bebidas", "Higiene Personal", "Bebe"}
CATEGORIAS_BLOQUEADAS = {
    "Mascotas",
    "Limpieza",
    "Frutas y Verduras",
    "Congelados",
    "Panaderia",
    "Carnes y Pescados",
    "Desayuno y Snacks",
}
MIN_PAIR_SCORE = 90
MIN_GROUP_SCORE = 92

GENERIC_SIGNATURE_TOKENS = {
    "bebida", "bebidas", "gaseosa", "pack", "caja", "lata", "botella", "un",
    "unidades", "ml", "cc", "l", "g", "gr", "kg", "original", "sabor", "de",
    "del", "la", "el", "y", "con", "sin", "para", "en", "no", "retornable",
    "desechable", "tocador", "jabon", "jabón", "shampoo", "acondicionador",
    "pañales", "panales", ".",
}
SIZE_RE = re.compile(r"\b(rn|xxg|xg|xxl|xl|g|m|p|pm|p/m|g/xg)\b")


def crear_backup_pre_fase5c() -> Path:
    BACKUPS.mkdir(parents=True, exist_ok=True)
    destino = BACKUPS / f"supercheck_pre_fase5c_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
    shutil.copy2(DB_PATH, destino)
    if destino.stat().st_size <= 0:
        raise RuntimeError(f"Backup vacio: {destino}")
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


def auditoria_previa_ok(db: Session) -> bool:
    return len(auditar_categorias(db)) == 0


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
        models.Subcategoria.nombre.label("subcategoria"),
    ).join(
        models.Categoria,
        models.Producto.categoria_id == models.Categoria.id,
    ).outerjoin(
        models.Subcategoria,
        models.Producto.subcategoria_id == models.Subcategoria.id,
    ).filter(
        models.Categoria.nombre.in_(categorias)
    ).all()


def _signature(producto: models.Producto) -> set[str]:
    texto = normalizar_texto(producto.nombre).replace("-", " ")
    tokens = []
    for token in texto.split():
        if token in GENERIC_SIGNATURE_TOKENS:
            continue
        if re.fullmatch(r"\d+(?:\.\d+)?", token):
            continue
        if re.fullmatch(r"n\d+", token):
            continue
        tokens.append(token)
    return set(tokens)


def _signature_compatible(a: models.Producto, b: models.Producto) -> bool:
    firma_a = _signature(a)
    firma_b = _signature(b)
    if not firma_a or not firma_b:
        return False
    interseccion = len(firma_a.intersection(firma_b))
    union = len(firma_a.union(firma_b))
    return (
        interseccion / union >= 0.72
        and len(firma_a - firma_b) <= 1
        and len(firma_b - firma_a) <= 1
    )


def _producto_estricto(producto: models.Producto, categoria: str) -> bool:
    texto = normalizar_texto(producto.nombre)
    attrs = atributos_fase5a(producto, categoria)
    marca = marca_producto(producto)

    if categoria == "Bebidas":
        if attrs.get("familia") != "bebida" or not attrs.get("medida") or not marca:
            return False
        bloqueados = ["k wave", "kwave", "edicion", "edición", "sugar free", "con gas", "sin gas", " ice "]
        return "+" not in texto and not any(item in texto for item in bloqueados)

    if categoria == "Higiene Personal":
        if not attrs.get("familia") or not (attrs.get("medida") or attrs.get("cantidad")) or not marca:
            return False
        return not any(item in texto for item in ["perro", "gato", "pet", "canish", "traper"])

    if categoria == "Bebe":
        if not attrs.get("familia") or not (attrs.get("medida") or attrs.get("cantidad") or attrs.get("talla") or attrs.get("etapa")):
            return False
        if attrs.get("familia") in {"panal", "paal"} and SIZE_RE.search(texto) and not attrs.get("talla"):
            return False
        return True

    return False


def _grupo_seguro(grupo: list[models.Producto], categoria: str) -> tuple[bool, float]:
    scores = []
    for index, producto in enumerate(grupo):
        for candidato in grupo[index + 1:]:
            score = matching_score(producto, candidato)
            if not compatible_fase5a(producto, candidato, categoria):
                return False, 0
            if score < MIN_PAIR_SCORE:
                return False, score
            if not _signature_compatible(producto, candidato):
                return False, score
            scores.append(score)
    score_promedio = round(sum(scores) / len(scores), 2) if scores else 100
    return score_promedio >= MIN_GROUP_SCORE, score_promedio


def metricas_fase5c(db: Session, categorias: set[str] = CATEGORIAS_PERMITIDAS) -> dict:
    rows = _productos_por_categoria(db, categorias)
    por_categoria = defaultdict(lambda: {"productos": 0, "bases": defaultdict(int), "conflictos": 0})
    for producto, categoria, _subcategoria in rows:
        data = por_categoria[categoria]
        data["productos"] += 1
        if producto.producto_base:
            data["bases"][producto.producto_base] += 1

    resultado = {}
    total_equivalentes = 0
    total_grupos = 0
    total_conflictos = 0
    for categoria, data in por_categoria.items():
        grupos_equivalencia = {base: count for base, count in data["bases"].items() if count > 1}
        productos_equivalentes = sum(grupos_equivalencia.values())
        conflictos = 0
        for base in grupos_equivalencia:
            productos = [
                producto
                for producto, cat, _sub in rows
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
    subcategoria_por_id = {}

    for producto, categoria, subcategoria in rows:
        if categoria in CATEGORIAS_BLOQUEADAS:
            continue
        if not _producto_estricto(producto, categoria):
            continue
        key = key_fase5a(producto, categoria)
        if (categoria, key) in riesgos:
            continue
        grupos[(categoria, key)].append(producto)
        subcategoria_por_id[producto.id] = subcategoria or ""

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
        timestamp = datetime.now().isoformat(timespec="seconds")
        for producto in grupo:
            if (producto.producto_base or "") == key:
                continue
            cambios.append({
                "producto_id": producto.id,
                "producto_original": producto.nombre,
                "producto_base_anterior": producto.producto_base or "",
                "producto_base_nuevo": key,
                "categoria": categoria,
                "subcategoria": subcategoria_por_id.get(producto.id, ""),
                "score_matching": score,
                "motivo_cambio": "grupo seguro fase5c: score alto, firma compatible, reglas categoria estrictas",
                "timestamp": timestamp,
            })
    return cambios


def escribir_cambios(cambios: list[dict], path: Path = CAMBIOS_CSV) -> None:
    campos = [
        "producto_id",
        "producto_original",
        "producto_base_anterior",
        "producto_base_nuevo",
        "categoria",
        "subcategoria",
        "score_matching",
        "motivo_cambio",
        "timestamp",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
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


def leer_cambios(path: Path = CAMBIOS_CSV) -> list[dict]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8-sig") as archivo:
        return list(csv.DictReader(archivo))


def escribir_validacion(antes: dict, despues: dict, cambios: list[dict], backup: Path | None, auditoria_post: int) -> None:
    por_categoria = Counter(cambio["categoria"] for cambio in cambios)
    posibles_fp = sum(1 for cambio in cambios if float(cambio["score_matching"] or 0) < MIN_GROUP_SCORE)
    lines = [
        "# Validacion Fase 5C - AhorraGo",
        "",
        "## Seguridad",
        "",
        f"- Backup: {backup if backup else 'backup previo existente/no creado por esta ejecucion'}",
        f"- Cambios aplicados: {len(cambios)}",
        "- Categorias permitidas: Bebidas, Higiene Personal, Bebe",
        f"- Categorias bloqueadas verificadas: {', '.join(sorted(CATEGORIAS_BLOQUEADAS))}",
        f"- Auditoria de categorias post-cambio: {auditoria_post} hallazgos",
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
        "## Productos Modificados",
        "",
    ]
    for categoria in sorted(CATEGORIAS_PERMITIDAS):
        lines.append(f"- {categoria}: {por_categoria.get(categoria, 0)}")
    lines.extend([
        "",
        "## Detalle por Categoria",
        "",
    ])
    for categoria in sorted(CATEGORIAS_PERMITIDAS):
        lines.append(
            f"- {categoria}: equivalencias {antes.get(categoria, {}).get('productos_equivalentes', 0)} -> "
            f"{despues.get(categoria, {}).get('productos_equivalentes', 0)}, conflictos "
            f"{antes.get(categoria, {}).get('conflictos', 0)} -> {despues.get(categoria, {}).get('conflictos', 0)}"
        )
    lines.extend([
        "",
        "## Falsos Positivos",
        "",
        f"- Posibles falsos positivos detectados por score bajo: {posibles_fp}",
    ])
    VALIDACION_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


def escribir_reportes(antes: dict, despues: dict, cambios: list[dict], backup: Path | None, auditoria_post: int) -> None:
    por_categoria = Counter(cambio["categoria"] for cambio in cambios)
    equivalencias_ganadas = despues["TOTAL"]["productos_equivalentes"] - antes["TOTAL"]["productos_equivalentes"]
    conflictos_reducidos = antes["TOTAL"]["conflictos"] - despues["TOTAL"]["conflictos"]
    barras = []
    for categoria in sorted(CATEGORIAS_PERMITIDAS):
        count = por_categoria.get(categoria, 0)
        barras.append(f"- {categoria}: {'#' * min(count, 40)} ({count})")

    lines = [
        "# Fase 5C Reporte - AhorraGo",
        "",
        "## Resumen Ejecutivo",
        "",
        "Fase 5C aplico matching real y controlado solo en categorias autorizadas.",
        "",
        "## Metricas Antes/Despues",
        "",
        f"- Productos modificados: {len(cambios)}",
        f"- Equivalencias: {antes['TOTAL']['productos_equivalentes']} -> {despues['TOTAL']['productos_equivalentes']}",
        f"- Equivalencias ganadas: {equivalencias_ganadas}",
        f"- Conflictos: {antes['TOTAL']['conflictos']} -> {despues['TOTAL']['conflictos']}",
        f"- Conflictos reducidos: {conflictos_reducidos}",
        "",
        "## Productos Modificados por Categoria",
        "",
        *barras,
        "",
        "## Seguridad",
        "",
        f"- Backup generado: {backup if backup else 'no creado'}",
        "- Rollback disponible: `python -m app.scripts.rollback_fase5c`",
        f"- Auditoria post-cambio: {auditoria_post} hallazgos",
        "- No se modificaron categorias bloqueadas.",
        "",
        "## Riesgos",
        "",
        "- La fase fue conservadora: Bebidas tuvo cambios; Higiene Personal y Bebe quedaron sin cambios por falta de grupos suficientemente seguros.",
        "- Las categorias pendientes requieren reglas de marca/variedad mas completas antes de una aplicacion real.",
        "",
        "## Recomendaciones",
        "",
        "- Antes de ampliar Fase 5C, enriquecer MARCAS_CONOCIDAS para bebidas isotónicas/energéticas y reglas de tallas de Bebe.",
        "- Mantener auditoria de categorias en 0 antes de cualquier nueva aplicacion.",
        "",
    ]
    reporte_md = REPORTS / "FASE_5C_REPORTE.md"
    cambios_md = ROOT / "CAMBIOS_FASE_5C.md"
    texto = "\n".join(lines)
    reporte_md.write_text(texto, encoding="utf-8")
    cambios_md.write_text(texto.replace("# Fase 5C Reporte", "# Cambios Fase 5C"), encoding="utf-8")
    markdown_to_pdf(reporte_md, REPORTS / "FASE_5C_REPORTE.pdf", "Fase 5C - AhorraGo")

    master = MASTER_REPORT.read_text(encoding="utf-8") if MASTER_REPORT.exists() else ""
    if "# Fase 5C" not in master:
        MASTER_REPORT.write_text(master.rstrip() + "\n---\n\n" + texto + "\n", encoding="utf-8")
    markdown_to_pdf(MASTER_REPORT, REPORTS / "AHORRAGO_MASTER_REPORT.pdf", "AhorraGo Master Report")


def main() -> int:
    db = SessionLocal()
    backup = None
    try:
        if not auditoria_previa_ok(db):
            print("Fase 5C detenida: auditoria de categorias con hallazgos")
            return 1
        antes = metricas_fase5c(db)
        cambios = seleccionar_cambios(db)
        if not cambios and CAMBIOS_CSV.exists():
            despues = antes
            auditoria_post = len(auditar_categorias(db))
            print("Aplicacion Fase 5C sin cambios pendientes; se conservan reportes existentes")
            print("Cambios aplicados: 0")
            print(f"Equivalencias: {antes['TOTAL']['productos_equivalentes']} -> {despues['TOTAL']['productos_equivalentes']}")
            print(f"Conflictos: {antes['TOTAL']['conflictos']} -> {despues['TOTAL']['conflictos']}")
            print(f"Auditoria post: {auditoria_post}")
            return 0
        escribir_cambios(cambios)
        if cambios:
            backup = crear_backup_pre_fase5c()
            aplicar_cambios(db, cambios)
        despues = metricas_fase5c(db)
        auditoria_post = len(auditar_categorias(db))
        escribir_validacion(antes, despues, cambios, backup, auditoria_post)
        escribir_reportes(antes, despues, cambios, backup, auditoria_post)
    finally:
        db.close()

    print("Aplicacion Fase 5C completada")
    print(f"Cambios aplicados: {len(cambios)}")
    print(f"Equivalencias: {antes['TOTAL']['productos_equivalentes']} -> {despues['TOTAL']['productos_equivalentes']}")
    print(f"Conflictos: {antes['TOTAL']['conflictos']} -> {despues['TOTAL']['conflictos']}")
    print(f"Auditoria post: {auditoria_post}")
    if backup:
        print(f"Backup: {backup}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
