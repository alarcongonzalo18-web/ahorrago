"""Backfill de EAN en los CSV por-cadena de Jumbo y Unimarc.

Recorre `data/<cadena>_real.csv`, saca el slug de cada URL, pide el EAN al BFF
(`app.ean_fetch`) y lo escribe en la columna `ean`. Después basta el flujo normal
`combinar` -> `reconstruir` para que el EAN entre a la base (combinar ya lee la
columna `ean`), y el matching por EAN une productos entre cadenas.

Pensado para correr pausado, por el rate-limit de los retailers:
- **Resumible**: salta las filas que ya tienen `ean`, así una re-corrida continúa.
- **Checkpoints**: guarda el CSV cada N productos (no se pierde avance si se corta).
- **Anti-bloqueo**: si se acumulan BloqueoError seguidos, pausa fuerte y, si
  persiste, guarda y aborta (no quema la IP ni corrompe datos).

Uso:
    python -m app.backfill_ean jumbo
    python -m app.backfill_ean unimarc --pausa 0.8 --limite 500
    python -m app.backfill_ean all
"""

import csv
import sys
import time
from pathlib import Path

from app.ean_fetch import (
    BloqueoError,
    fetch_ean_jumbo,
    fetch_ean_unimarc,
    slug_jumbo,
    slug_unimarc,
)

FUENTES = {
    "jumbo": {
        "path": Path("data/jumbo_real.csv"),
        "slug": slug_jumbo,
        "fetch": fetch_ean_jumbo,
    },
    "unimarc": {
        "path": Path("data/unimarc_real.csv"),
        "slug": slug_unimarc,
        "fetch": fetch_ean_unimarc,
    },
}

CHECKPOINT_CADA = 100
MAX_BLOQUEOS_SEGUIDOS = 5


def _leer(path):
    with open(path, newline="", encoding="utf-8-sig") as f:
        lector = csv.DictReader(f)
        filas = list(lector)
        campos = list(lector.fieldnames or [])
    if "ean" not in campos:
        campos.append("ean")
    for fila in filas:
        fila.setdefault("ean", "")
    return filas, campos


def _guardar(path, filas, campos):
    # escritura atómica: primero a .tmp y luego reemplazo, para no dejar el CSV
    # a medias si el proceso se corta durante el guardado.
    tmp = path.with_suffix(path.suffix + ".tmp")
    with open(tmp, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=campos, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(filas)
    tmp.replace(path)


def backfill(cadena, pausa=0.5, limite=None):
    cfg = FUENTES[cadena]
    path = cfg["path"]
    if not path.exists():
        print(f"No existe {path}, se omite {cadena}.")
        return

    filas, campos = _leer(path)
    total = len(filas)
    ya_tenian = sum(1 for f in filas if (f.get("ean") or "").strip())
    print(f"[{cadena}] {total} filas, {ya_tenian} ya con EAN. Procesando el resto...")

    procesados = con_ean = sin_slug = bloqueos_seguidos = 0

    for fila in filas:
        if (fila.get("ean") or "").strip():
            continue  # resume: ya resuelto en una corrida anterior

        slug = cfg["slug"](fila.get("url", ""))
        if not slug:
            sin_slug += 1
            continue

        try:
            ean = cfg["fetch"](slug)
        except BloqueoError as exc:
            bloqueos_seguidos += 1
            print(f"  bloqueo ({bloqueos_seguidos}/{MAX_BLOQUEOS_SEGUIDOS}): {exc}")
            if bloqueos_seguidos >= MAX_BLOQUEOS_SEGUIDOS:
                print("  demasiados bloqueos seguidos: guardo y aborto. Reintentá más tarde.")
                break
            time.sleep(30)
            continue

        bloqueos_seguidos = 0
        if ean:
            fila["ean"] = ean
            con_ean += 1
        procesados += 1

        if procesados % CHECKPOINT_CADA == 0:
            _guardar(path, filas, campos)
            print(f"  checkpoint: {procesados} procesados, {con_ean} con EAN")

        if limite and procesados >= limite:
            print(f"  límite {limite} alcanzado.")
            break

        time.sleep(pausa)

    _guardar(path, filas, campos)
    total_con_ean = sum(1 for f in filas if (f.get("ean") or "").strip())
    print(
        f"[{cadena}] listo. Esta corrida: {procesados} procesados, {con_ean} EAN nuevos, "
        f"{sin_slug} sin slug. Total con EAN ahora: {total_con_ean}/{total}."
    )


def _parse_args(argv):
    if not argv or argv[0] not in (*FUENTES, "all"):
        print("Uso: python -m app.backfill_ean <jumbo|unimarc|all> [--pausa S] [--limite N]")
        raise SystemExit(1)
    cadenas = list(FUENTES) if argv[0] == "all" else [argv[0]]
    pausa, limite = 0.5, None
    i = 1
    while i < len(argv):
        if argv[i] == "--pausa" and i + 1 < len(argv):
            pausa = float(argv[i + 1]); i += 2
        elif argv[i] == "--limite" and i + 1 < len(argv):
            limite = int(argv[i + 1]); i += 2
        else:
            i += 1
    return cadenas, pausa, limite


def main(argv=None):
    cadenas, pausa, limite = _parse_args(argv if argv is not None else sys.argv[1:])
    for cadena in cadenas:
        backfill(cadena, pausa=pausa, limite=limite)


if __name__ == "__main__":
    main()
