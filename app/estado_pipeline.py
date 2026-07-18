"""Registro de salud del pipeline: que corrio, cuando y si salio bien.

Por que existe: las corridas son automaticas y de madrugada. Si algo falla, hoy
nadie se entera hasta abrir el log a mano — y ya paso (dos caidas del backfill en
un mismo dia, en silencio). Este modulo deja un estado legible que la API expone
y la app muestra, asi el fallo se ve solo.

Guarda `data/estado_pipeline.json` con una entrada por tarea (cada cadena, el
backfill de EAN, etc). No usa la base a proposito: tiene que poder registrar
justamente cuando la reconstruccion de la base fallo.
"""

import json
from datetime import datetime, timedelta
from pathlib import Path

RUTA = Path("data/estado_pipeline.json")

# Tras cuantas horas sin corrida exitosa se considera atrasada una tarea diaria.
HORAS_PARA_ATRASO = 30


def cargar(path=RUTA):
    path = Path(path)
    if not path.exists():
        return {}
    try:
        datos = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}
    return datos if isinstance(datos, dict) else {}


def _guardar(estado, path=RUTA):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(estado, ensure_ascii=False, indent=1, sort_keys=True), encoding="utf-8")
    tmp.replace(path)


def registrar(tarea, ok, detalle="", duracion_min=None, ahora=None, path=RUTA):
    """Anota el resultado de una tarea. Conserva la ultima corrida OK aparte.

    Guardar `ultimo_ok` separado del ultimo intento permite responder la pregunta
    que importa: "hace cuanto que esto no funciona", no solo "fallo recien".
    """
    ahora = (ahora or datetime.now()).replace(microsecond=0)
    estado = cargar(path)
    previo = estado.get(tarea, {})

    entrada = {
        "ok": bool(ok),
        "fecha": ahora.isoformat(timespec="seconds"),
        "detalle": (detalle or "")[:400],
        "ultimo_ok": ahora.isoformat(timespec="seconds") if ok else previo.get("ultimo_ok"),
    }
    if duracion_min is not None:
        entrada["duracion_min"] = round(float(duracion_min), 1)

    estado[tarea] = entrada
    _guardar(estado, path)
    return entrada


def _parsear(valor):
    try:
        return datetime.fromisoformat(valor) if valor else None
    except (TypeError, ValueError):
        return None


def diagnostico(estado=None, ahora=None, path=RUTA):
    """Resume la salud: {ok, problemas[], tareas{}}.

    Una tarea esta mal si su ultimo intento fallo, o si hace demasiado que no
    tiene una corrida exitosa (aunque nunca haya tirado error: un scheduler que
    no dispara no deja rastro de fallo).
    """
    estado = cargar(path) if estado is None else estado
    ahora = ahora or datetime.now()
    problemas = []

    for tarea, datos in sorted(estado.items()):
        if not datos.get("ok"):
            problemas.append(f"{tarea}: ultimo intento fallo ({datos.get('detalle') or 'sin detalle'})")
            continue
        ultimo_ok = _parsear(datos.get("ultimo_ok"))
        if ultimo_ok and ahora - ultimo_ok > timedelta(hours=HORAS_PARA_ATRASO):
            horas = int((ahora - ultimo_ok).total_seconds() // 3600)
            problemas.append(f"{tarea}: sin corrida exitosa hace {horas} h")

    return {"ok": not problemas, "problemas": problemas, "tareas": estado}


def main():
    """`python -m app.estado_pipeline` -> resumen legible. Sale 1 si hay problemas."""
    d = diagnostico()
    if not d["tareas"]:
        print("Sin registros todavia: el pipeline no corrio desde que existe el monitoreo.")
        return 0

    for tarea, datos in sorted(d["tareas"].items()):
        marca = "OK  " if datos.get("ok") else "FALLA"
        dur = f" ({datos['duracion_min']} min)" if datos.get("duracion_min") is not None else ""
        print(f"{marca} {tarea:28} {datos.get('fecha','')}{dur}")
        if not datos.get("ok"):
            print(f"      ultimo OK: {datos.get('ultimo_ok') or 'nunca'}")
            if datos.get("detalle"):
                print(f"      {datos['detalle'][:160]}")

    print()
    if d["ok"]:
        print("Todo en orden.")
        return 0
    print("PROBLEMAS:")
    for p in d["problemas"]:
        print(f"  - {p}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
