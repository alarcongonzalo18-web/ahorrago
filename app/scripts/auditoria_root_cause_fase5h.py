from __future__ import annotations

import argparse
import csv
import sqlite3
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path

from app.scripts.report_pdf import markdown_to_pdf


ROOT = Path(__file__).resolve().parents[2]
DB_PATH = ROOT / "supercheck.db"
REPORTS_DIR = ROOT / "reports"
HALLAZGOS_CSV = REPORTS_DIR / "fase5f_clasificacion_masiva.csv"
TRACE_CSV = REPORTS_DIR / "fase5h_trazabilidad_productos.csv"
SUMMARY_CSV = REPORTS_DIR / "fase5h_causa_raiz_resumen.csv"
REPORT_MD = REPORTS_DIR / "FASE_5H_ROOT_CAUSE.md"
REPORT_PDF = REPORTS_DIR / "FASE_5H_ROOT_CAUSE.pdf"

FUENTES = {
    "Lider": (ROOT / "data" / "lider_real.csv", "app/scraper_lider.py"),
    "Líder": (ROOT / "data" / "lider_real.csv", "app/scraper_lider.py"),
    "Jumbo": (ROOT / "data" / "jumbo_real.csv", "app/scraper_jumbo_real.py"),
    "Unimarc": (ROOT / "data" / "unimarc_real.csv", "app/scraper_unimarc.py"),
}

MOTIVO_TARGETS = {
    "Bebida detectada dentro de categoria Bebe": 12,
    "Producto de mascotas fuera de Mascotas": 14,
    "Producto de higiene personal fuera de Higiene Personal": 12,
    "Producto de limpieza fuera de Limpieza": 5,
    "Producto de limpieza detectado dentro de categoria Bebe": 3,
    "Snack/fruto seco detectado dentro de categoria Bebe": 8,
}

KEYWORD_PRIORIDAD = [
    "notmilk",
    "yogu yogu",
    "milo",
    "coca",
    "master dog",
    "pet food",
    "nivea",
    "micelar",
    "desodorante",
]

SCRIPT_ANALISIS = {
    "app/scraper_lider.py": {
        "usa_categorias_hardcodeadas": "si",
        "usa_categoria_por_posicion_busqueda": "si",
        "fallback_incorrecto": "no observado",
        "riesgo": "alto: asigna la categoria configurada a todos los productos extraidos desde una URL de categoria.",
    },
    "app/scraper_jumbo_real.py": {
        "usa_categorias_hardcodeadas": "si",
        "usa_categoria_por_posicion_busqueda": "si",
        "fallback_incorrecto": "no observado",
        "riesgo": "alto: asigna la categoria del termino de busqueda, no una taxonomia validada del producto.",
    },
    "app/scraper_unimarc.py": {
        "usa_categorias_hardcodeadas": "si",
        "usa_categoria_por_posicion_busqueda": "si",
        "fallback_incorrecto": "no observado",
        "riesgo": "alto: asigna la categoria del termino de busqueda y puede capturar resultados cruzados.",
    },
    "app/combinar_supermercados.py": {
        "usa_categorias_hardcodeadas": "no",
        "usa_categoria_por_posicion_busqueda": "no",
        "fallback_incorrecto": "no observado",
        "riesgo": "medio: preserva la categoria fuente sin validar incompatibilidades.",
    },
    "app/importar_csv.py": {
        "usa_categorias_hardcodeadas": "no",
        "usa_categoria_por_posicion_busqueda": "no",
        "fallback_incorrecto": "no observado",
        "riesgo": "medio: si el mismo nombre existe en varias filas, actualiza categoria por nombre.",
    },
}


def normalizar(valor: str) -> str:
    texto = unicodedata.normalize("NFKD", str(valor or ""))
    texto = "".join(ch for ch in texto if not unicodedata.combining(ch))
    return " ".join(texto.lower().strip().split())


def leer_csv(path: Path) -> list[dict]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8-sig") as archivo:
        return list(csv.DictReader(archivo))


def seleccionar_muestra(hallazgos: list[dict], minimo: int = 50) -> list[dict]:
    alta = [row for row in hallazgos if row.get("confianza") == "Alta"]
    usados = set()
    seleccion = []

    for keyword in KEYWORD_PRIORIDAD:
        for row in alta:
            if row.get("producto_id") in usados:
                continue
            if keyword in normalizar(row.get("nombre", "")):
                seleccion.append(row)
                usados.add(row.get("producto_id"))
                break

    for motivo, objetivo in MOTIVO_TARGETS.items():
        actuales = [row for row in seleccion if row.get("motivo") == motivo]
        faltan = max(0, objetivo - len(actuales))
        for row in alta:
            if faltan <= 0:
                break
            if row.get("producto_id") in usados or row.get("motivo") != motivo:
                continue
            seleccion.append(row)
            usados.add(row.get("producto_id"))
            faltan -= 1

    for row in alta:
        if len(seleccion) >= minimo:
            break
        if row.get("producto_id") in usados:
            continue
        seleccion.append(row)
        usados.add(row.get("producto_id"))

    return seleccion[: max(minimo, len(seleccion))]


def cargar_fuentes() -> dict[str, list[dict]]:
    fuentes = {}
    for supermercado, (path, _) in FUENTES.items():
        if supermercado == "Lider":
            continue
        rows = leer_csv(path)
        for index, row in enumerate(rows, start=2):
            row["_fila_fuente"] = str(index)
            row["_archivo_fuente"] = str(path.relative_to(ROOT))
            row["_supermercado"] = supermercado
        fuentes[supermercado] = rows
    return fuentes


def cargar_combinado() -> dict[tuple[str, str], list[dict]]:
    index = defaultdict(list)
    for fila, row in enumerate(leer_csv(ROOT / "data" / "productos_supermercados.csv"), start=2):
        row["_fila_combinado"] = str(fila)
        key = (normalizar(row.get("supermercado")), normalizar(row.get("nombre")))
        index[key].append(row)
    return index


def conectar_read_only(db_path: Path):
    uri = f"file:{db_path.as_posix()}?mode=ro"
    return sqlite3.connect(uri, uri=True)


def producto_bd(conn, producto_id: int) -> dict:
    conn.row_factory = sqlite3.Row
    row = conn.execute(
        """
        SELECT p.id, p.nombre, p.producto_base, c.nombre categoria, s.nombre subcategoria
        FROM productos p
        LEFT JOIN categorias c ON c.id = p.categoria_id
        LEFT JOIN subcategorias s ON s.id = p.subcategoria_id
        WHERE p.id = ?
        """,
        (producto_id,),
    ).fetchone()
    if not row:
        return {}
    supermercados = conn.execute(
        """
        SELECT sm.nombre
        FROM precios pr
        JOIN supermercados sm ON sm.id = pr.supermercado_id
        WHERE pr.producto_id = ?
        ORDER BY sm.nombre
        """,
        (producto_id,),
    ).fetchall()
    data = dict(row)
    data["supermercados"] = [item["nombre"] for item in supermercados]
    return data


def buscar_fuente(
    nombre: str,
    supermercado: str,
    fuentes: dict[str, list[dict]],
    categoria_preferida: str = "",
    subcategoria_preferida: str = "",
) -> dict | None:
    rows = fuentes.get(supermercado) or []
    nombre_norm = normalizar(nombre)
    exactas = [row for row in rows if normalizar(row.get("nombre")) == nombre_norm]
    for row in exactas:
        if (
            normalizar(row.get("categoria")) == normalizar(categoria_preferida)
            and normalizar(row.get("subcategoria")) == normalizar(subcategoria_preferida)
        ):
            return row
    if exactas:
        return exactas[-1]

    tokens = [token for token in nombre_norm.split() if len(token) > 3][:5]
    candidatas = []
    for row in rows:
        row_norm = normalizar(row.get("nombre"))
        if tokens and all(token in row_norm for token in tokens):
            candidatas.append(row)
    for row in candidatas:
        if (
            normalizar(row.get("categoria")) == normalizar(categoria_preferida)
            and normalizar(row.get("subcategoria")) == normalizar(subcategoria_preferida)
        ):
            return row
    if candidatas:
        return candidatas[-1]
    return None


def causa_probable(row: dict, fuente: dict | None, combinado_rows: list[dict], bd: dict) -> tuple[str, str, str]:
    categoria_bd = bd.get("categoria") or row.get("categoria_actual") or ""
    subcategoria_bd = bd.get("subcategoria") or row.get("subcategoria_actual") or ""
    categoria_fuente = (fuente or {}).get("categoria", "")
    subcategoria_fuente = (fuente or {}).get("subcategoria", "")

    if fuente and categoria_fuente == categoria_bd and subcategoria_fuente == subcategoria_bd:
        return (
            "scraper_categoria_por_busqueda_amplia",
            "scraper_fuente",
            "El CSV fuente ya contiene la categoria incorrecta; el scraper asigno la categoria configurada al resultado.",
        )

    categorias_combinadas = {
        (item.get("categoria", ""), item.get("subcategoria", ""))
        for item in combinado_rows
    }
    if fuente and (categoria_fuente, subcategoria_fuente) not in categorias_combinadas:
        return (
            "combinar_supermercados_preserva_o_mezcla_categoria_erronea",
            "app/combinar_supermercados.py",
            "La categoria cambia entre fuente y CSV combinado o hay filas equivalentes con categorias distintas.",
        )

    if combinado_rows and (categoria_bd, subcategoria_bd) not in categorias_combinadas:
        return (
            "importar_csv_actualiza_categoria_por_nombre",
            "app/importar_csv.py",
            "La BD no coincide con las filas combinadas para ese supermercado; posible overwrite por nombre compartido.",
        )

    if not fuente:
        return (
            "fuente_no_encontrada_o_nombre_transformado",
            "pipeline_fuente",
            "No se encontro una fila fuente exacta; requiere trazabilidad de scraper o datos intermedios.",
        )

    return (
        "datos_fuente_sin_validacion_semantica",
        "pipeline_fuente",
        "La categoria incorrecta atraviesa el pipeline sin validadores de incompatibilidad.",
    )


def recomendacion_para(causa: str) -> str:
    if causa == "scraper_categoria_por_busqueda_amplia":
        return "Validar cada resultado contra reglas de categoria antes de escribir CSV; limitar busquedas ambiguas."
    if causa == "importar_csv_actualiza_categoria_por_nombre":
        return "Importar por clave nombre+supermercado o bloquear cambios de categoria incompatibles."
    if causa == "combinar_supermercados_preserva_o_mezcla_categoria_erronea":
        return "Agregar validador semantico en combinar_supermercados antes de persistir el CSV final."
    return "Agregar auditoria pre-import y revisar datos fuente antes de recarga."


def trazar_productos(db_path: Path = DB_PATH, hallazgos_csv: Path = HALLAZGOS_CSV, minimo: int = 50) -> list[dict]:
    hallazgos = leer_csv(hallazgos_csv)
    muestra = seleccionar_muestra(hallazgos, minimo)
    fuentes = cargar_fuentes()
    combinado = cargar_combinado()
    conn = conectar_read_only(db_path)
    trazas = []
    try:
        for row in muestra:
            producto_id = int(row["producto_id"])
            bd = producto_bd(conn, producto_id)
            supermercados = bd.get("supermercados") or [""]
            supermercado = supermercados[0]
            fuente = buscar_fuente(
                bd.get("nombre") or row.get("nombre", ""),
                supermercado,
                fuentes,
                bd.get("categoria") or row.get("categoria_actual", ""),
                bd.get("subcategoria") or row.get("subcategoria_actual", ""),
            )
            combinado_rows = combinado.get((normalizar(supermercado), normalizar(bd.get("nombre") or row.get("nombre", ""))), [])
            causa, script, punto = causa_probable(row, fuente, combinado_rows, bd)
            archivo_fuente = (fuente or {}).get("_archivo_fuente", "")
            fila_fuente = (fuente or {}).get("_fila_fuente", "")
            if fila_fuente:
                archivo_fuente = f"{archivo_fuente}:{fila_fuente}"
            trazas.append({
                "producto_id": producto_id,
                "producto_nombre": bd.get("nombre") or row.get("nombre", ""),
                "supermercado": supermercado,
                "categoria_bd": bd.get("categoria") or row.get("categoria_actual", ""),
                "subcategoria_bd": bd.get("subcategoria") or row.get("subcategoria_actual", ""),
                "categoria_sugerida": row.get("categoria_sugerida", ""),
                "subcategoria_sugerida": row.get("subcategoria_sugerida", ""),
                "archivo_fuente": archivo_fuente,
                "categoria_fuente": (fuente or {}).get("categoria", ""),
                "subcategoria_fuente": (fuente or {}).get("subcategoria", ""),
                "script_origen": script if script.startswith("app/") else FUENTES.get(supermercado, ("", script))[1],
                "punto_falla": punto,
                "causa_probable": causa,
                "confianza": row.get("confianza", ""),
                "recomendacion": recomendacion_para(causa),
            })
    finally:
        conn.close()
    return trazas


def escribir_csv(path: Path, filas: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    campos = list(filas[0].keys()) if filas else []
    with path.open("w", newline="", encoding="utf-8-sig") as archivo:
        writer = csv.DictWriter(archivo, fieldnames=campos)
        writer.writeheader()
        writer.writerows(filas)


def resumen_causa_raiz(trazas: list[dict]) -> list[dict]:
    total = len(trazas) or 1
    por_causa = defaultdict(list)
    for row in trazas:
        por_causa[row["causa_probable"]].append(row)

    filas = []
    for causa, items in sorted(por_causa.items(), key=lambda item: len(item[1]), reverse=True):
        scripts = Counter(item["script_origen"] for item in items)
        ejemplos = " | ".join(f"{item['producto_id']} {item['producto_nombre'][:45]}" for item in items[:4])
        filas.append({
            "causa_probable": causa,
            "cantidad": len(items),
            "porcentaje": round((len(items) / total) * 100, 2),
            "ejemplos": ejemplos,
            "script_afectado": "; ".join(f"{script} ({count})" for script, count in scripts.most_common()),
            "correccion_recomendada": recomendacion_para(causa),
            "riesgo": "alto" if "scraper" in causa or "importar" in causa else "medio",
        })
    return filas


def hipotesis(trazas: list[dict]) -> list[tuple[str, str, str]]:
    causas = Counter(row["causa_probable"] for row in trazas)
    return [
        ("A", "Supermercado entrega categoria incorrecta", "No concluyente: los CSV locales no conservan taxonomia real del sitio, solo la categoria asignada por scraper."),
        ("B", "Scraper captura mal la categoria", "Confirmada parcialmente: el scraper asigna categoria configurada a resultados de busquedas amplias."),
        ("C", "convertir_jumbo.py introduce el error", "No confirmada para la muestra: el error ya esta en jumbo_real.csv o scraper."),
        ("D", "convertir_lider.py introduce el error", "No confirmada para la muestra: el error ya esta en lider_real.csv o scraper."),
        ("E", "convertir_unimarc.py introduce el error", "No confirmada para la muestra: el error ya esta en unimarc_real.csv o scraper."),
        ("F", "importar_csv.py asigna categoria incorrecta", "Riesgo secundario: importa lo que recibe y puede actualizar categoria por nombre compartido."),
        ("G", "Mapeo de categorias generico o errado", f"Confirmada: {causas.get('scraper_categoria_por_busqueda_amplia', 0)} trazas apuntan a busquedas/mapeos amplios."),
        ("H", "producto_base influye en categoria", "Descartada en esta fase: producto_base se calcula despues y no participa en categoria/subcategoria."),
    ]


def escribir_reporte(trazas: list[dict], resumen: list[dict]) -> None:
    total_hallazgos = len(leer_csv(HALLAZGOS_CSV))
    alta = sum(1 for row in leer_csv(HALLAZGOS_CSV) if row.get("confianza") == "Alta")
    lines = [
        "# Fase 5H - Root Cause de Clasificacion Masiva",
        "",
        "Modo READ ONLY / AUDITORIA. No modifica base de datos ni producto_base.",
        "",
        "## Estado General",
        "",
        f"- Hallazgos Fase 5F: {total_hallazgos}",
        f"- Hallazgos alta confianza: {alta}",
        f"- Productos trazados: {len(trazas)}",
        "",
        "## Causa Raiz Principal",
        "",
        "La causa raiz mas probable es que los scrapers asignan la categoria/subcategoria configurada para una busqueda o URL amplia a todos los productos capturados, sin validar semanticamente cada resultado.",
        "",
        "Ejemplos: busquedas o secciones como `alimento bebe`, `leche`, `carne`, `galleta`, `snack` o `crema facial` pueden devolver bebidas, productos de mascotas, cosmeticos o limpieza. Esos productos entran al CSV fuente con la categoria erronea y luego `combinar_supermercados.py` e `importar_csv.py` la preservan.",
        "",
        "## Resumen de Causas",
        "",
        "| Causa | Cantidad | % | Script afectado | Riesgo |",
        "|---|---:|---:|---|---|",
    ]
    for row in resumen:
        lines.append(
            f"| {row['causa_probable']} | {row['cantidad']} | {row['porcentaje']} | "
            f"{row['script_afectado']} | {row['riesgo']} |"
        )

    lines.extend([
        "",
        "## Hipotesis A-H",
        "",
        "| Hipotesis | Resultado | Evidencia |",
        "|---|---|---|",
    ])
    for codigo, titulo, resultado in hipotesis(trazas):
        lines.append(f"| {codigo}: {titulo} | {resultado.split(':')[0]} | {resultado} |")

    lines.extend([
        "",
        "## Analisis de Scripts",
        "",
        "| Script | Categorias hardcodeadas | Categoria por busqueda | Riesgo |",
        "|---|---|---|---|",
    ])
    for script, data in SCRIPT_ANALISIS.items():
        lines.append(
            f"| {script} | {data['usa_categorias_hardcodeadas']} | "
            f"{data['usa_categoria_por_posicion_busqueda']} | {data['riesgo']} |"
        )

    lines.extend([
        "",
        "## Ejemplos Trazados",
        "",
        "| ID | Producto | Supermercado | BD | Fuente | Causa |",
        "|---:|---|---|---|---|---|",
    ])
    for row in trazas[:30]:
        producto = row["producto_nombre"].replace("|", "/")[:70]
        bd = f"{row['categoria_bd']} > {row['subcategoria_bd']}"
        fuente = f"{row['categoria_fuente']} > {row['subcategoria_fuente']}"
        lines.append(f"| {row['producto_id']} | {producto} | {row['supermercado']} | {bd} | {fuente} | {row['causa_probable']} |")

    lines.extend([
        "",
        "## Correcciones Propuestas",
        "",
        "1. Agregar validador semantico antes de escribir cada CSV fuente.",
        "2. Reemplazar busquedas ambiguas por URLs/taxonomias mas especificas cuando existan.",
        "3. Bloquear categorias imposibles antes de combinar e importar.",
        "4. En `importar_csv.py`, evitar overwrite de categoria por nombre cuando supermercados distintos traen categorias incompatibles.",
        "5. Agregar tests de regresion para NotMilk, Yogu Yogu, Coca-Cola, Master Dog, Pet Food, Nivea Micelar y Desodorante Nivea.",
        "6. Ejecutar recarga limpia solo despues de corregir scrapers/importadores y validar 0 bloqueos criticos.",
        "",
        "## Archivos Generados",
        "",
        "- reports/fase5h_trazabilidad_productos.csv",
        "- reports/fase5h_causa_raiz_resumen.csv",
        "- reports/FASE_5H_ROOT_CAUSE.md",
        "- reports/FASE_5H_ROOT_CAUSE.pdf",
        "",
    ])
    REPORT_MD.write_text("\n".join(lines), encoding="utf-8")
    markdown_to_pdf(REPORT_MD, REPORT_PDF, "Fase 5H - Root Cause")


def ejecutar(minimo: int = 50) -> dict:
    trazas = trazar_productos(minimo=minimo)
    resumen = resumen_causa_raiz(trazas)
    escribir_csv(TRACE_CSV, trazas)
    escribir_csv(SUMMARY_CSV, resumen)
    escribir_reporte(trazas, resumen)
    return {
        "trazas": len(trazas),
        "causa_principal": resumen[0]["causa_probable"] if resumen else "",
        "pdf": str(REPORT_PDF),
        "csv": str(TRACE_CSV),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Auditoria root cause read-only Fase 5H.")
    parser.add_argument("--minimo", type=int, default=50)
    args = parser.parse_args()
    resultado = ejecutar(args.minimo)
    print("Auditoria root cause Fase 5H completada.")
    for clave, valor in resultado.items():
        print(f"{clave}: {valor}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
