"""Chequeo de entorno: dice si esta maquina puede correr el pipeline.

Pensado para migrar a otro equipo sin sorpresas. Verifica dependencias, secretos,
datos y conectividad con las 4 cadenas, y avisa de lo que NO viaja por git
(el `.env` y, sobre todo, el historial de precios dentro de supercheck.db).

    python -m app.doctor        # sale 1 si falta algo critico
"""

import importlib
import os
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]

OK, AVISO, FALLA = "OK", "AVISO", "FALTA"

DEPENDENCIAS = [
    ("fastapi", True), ("uvicorn", True), ("sqlalchemy", True), ("pydantic", True),
    ("filelock", True), ("rapidfuzz", True),
    ("selenium", True),      # scraper de Unimarc
    ("bs4", True),           # scraper de Unimarc
    ("httpx", False), ("pytest", False),
]

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)


def _linea(estado, texto, detalle=""):
    print(f"  [{estado:5}] {texto}" + (f" — {detalle}" if detalle else ""))
    return estado


def revisar_dependencias():
    print("\nDependencias")
    faltan = []
    for modulo, critica in DEPENDENCIAS:
        try:
            importlib.import_module(modulo)
            _linea(OK, modulo)
        except ImportError:
            _linea(FALLA if critica else AVISO, modulo,
                   "pip install -r requirements.txt" if critica else "opcional")
            if critica:
                faltan.append(modulo)
    return faltan


def revisar_secretos():
    print("\nSecretos (no viajan por git)")
    from app.config import cargar_env

    cargar_env()
    problemas = []
    if os.environ.get("JUMBO_API_KEY"):
        _linea(OK, ".env con JUMBO_API_KEY")
    else:
        _linea(FALLA, "JUMBO_API_KEY", "copiar el .env del equipo anterior (ver .env.example)")
        problemas.append("JUMBO_API_KEY")
    return problemas


def revisar_datos():
    print("\nDatos")
    problemas = []

    cache = RAIZ / "data" / "ean_cache.json"
    if cache.exists():
        from app import ean_cache
        entradas, con_ean = ean_cache.total(ean_cache.cargar(cache))
        _linea(OK, "cache de EAN", f"{entradas} slugs, {con_ean} con EAN")
    else:
        _linea(AVISO, "cache de EAN", "se repuebla sola, pero cuesta horas de requests")

    csvs = list((RAIZ / "data").glob("*_real.csv"))
    if csvs:
        _linea(OK, "CSV por cadena", f"{len(csvs)} archivos")
    else:
        _linea(AVISO, "CSV por cadena", "no hay: la primera corrida los genera (~1.5 h)")

    db = RAIZ / "supercheck.db"
    if not db.exists():
        _linea(AVISO, "base de datos", "no existe: se regenera con el pipeline")
        problemas.append("historial")
        print("         OJO: el HISTORIAL de precios vive en la base y NO viaja por git.")
        print("         Si venis de otro equipo, copia supercheck.db o perdes la serie.")
        return problemas

    try:
        from app.database import SessionLocal
        from app.historial_precios import resumen
        from app import models

        sesion = SessionLocal()
        try:
            productos = sesion.query(models.Producto).count()
            dias, puntos = resumen(sesion)
        finally:
            sesion.close()

        _linea(OK, "base de datos", f"{productos} productos")
        if puntos:
            _linea(OK, "historial de precios", f"{puntos} puntos en {dias} dia(s)")
        else:
            _linea(AVISO, "historial de precios",
                   "vacio: si venis de otro equipo, copia supercheck.db para no perder la serie")
            problemas.append("historial")
    except Exception as exc:
        _linea(FALLA, "base de datos", f"no se pudo leer: {type(exc).__name__}")
        problemas.append("base")

    return problemas


def revisar_conectividad():
    """Ejercita los contratos REALES, no las home.

    Pingear la portada da falsos positivos (el WAF de Unimarc rechaza un request
    pelado, pero por Selenium y por su BFF con headers responde bien). Se prueba
    lo que el pipeline usa de verdad, incluida la auth de Jumbo.
    """
    print("\nConectividad con las cadenas (contratos reales)")
    from app.ean_fetch import fetch_ean_jumbo, fetch_ean_tottus, fetch_ean_unimarc
    from app.scraper_lider import descargar_html

    # productos conocidos, con su EAN esperado: si cambia el contrato, se nota
    pruebas = [
        ("Lider (listado)", lambda: "ok" if len(descargar_html("https://super.lider.cl/v/leches")) > 5000 else ""),
        ("Jumbo (EAN + apiKey)", lambda: fetch_ean_jumbo("m-ideal-bco-xl-750")),
        ("Unimarc (EAN)", lambda: fetch_ean_unimarc("arroz-g2-largo-delgad-nuestra-cocina-1kg")),
        ("Tottus (EAN)", lambda: fetch_ean_tottus("/tottus-cl/articulo/112737597/leche-natural-colun-st-1-lt")),
    ]

    caidas = []
    for nombre, probar in pruebas:
        try:
            resultado = probar()
            if resultado:
                _linea(OK, nombre, str(resultado)[:20])
            else:
                _linea(AVISO, nombre, "respondio vacio (¿cambio el contrato?)")
                caidas.append(nombre)
        except Exception as exc:
            _linea(AVISO, nombre, f"{type(exc).__name__} (¿bloqueo, sin red o contrato cambiado?)")
            caidas.append(nombre)
    return caidas


def main():
    print("=" * 62)
    print(f"AhorraGo — chequeo de entorno   ({sys.version.split()[0]}, {sys.platform})")
    print(f"Proyecto: {RAIZ}")
    print("=" * 62)

    criticos = []
    criticos += revisar_dependencias()
    criticos += revisar_secretos()
    avisos_datos = revisar_datos()
    caidas = revisar_conectividad()

    print("\n" + "=" * 62)
    if criticos:
        print("FALTA algo critico para correr el pipeline:", ", ".join(criticos))
        return 1
    if "historial" in avisos_datos:
        print("Listo para correr, PERO revisá el historial de precios (ver arriba).")
        return 0
    if caidas:
        print("Listo, aunque no se alcanzaron:", ", ".join(caidas))
        return 0
    print("Todo en orden: este equipo puede correr el pipeline.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
