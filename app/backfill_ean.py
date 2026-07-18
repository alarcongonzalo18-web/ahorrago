"""Puebla la caché `slug -> EAN` de Jumbo y Unimarc desde sus BFF.

Lee los slugs de los CSV por-cadena (`data/<cadena>_real.csv`), consulta el EAN
sólo de los que **no estén ya en la caché**, y guarda en `data/ean_cache.json`.
Después `combinar_supermercados` enriquece cada fila desde ahí, así los scrapers
pueden reescribir los CSV sin destruir el trabajo (ver `app/ean_cache.py`).

Pensado para correr pausado, por el rate-limit de los retailers:
- **Incremental**: salta los slugs ya consultados → una re-corrida sólo pide los nuevos.
- **Checkpoints**: guarda la caché cada N productos (no se pierde avance si se corta).
- **Anti-bloqueo**: ante BloqueoError seguidos pausa fuerte y, si persiste, guarda y aborta.

Uso:
    python -m app.backfill_ean jumbo
    python -m app.backfill_ean unimarc --pausa 0.8 --limite 500
    python -m app.backfill_ean all
"""

import csv
import sys
import time
from pathlib import Path

from app import ean_cache
from app.ean_fetch import (
    BloqueoError,
    fetch_ean_jumbo,
    fetch_ean_unimarc,
    slug_jumbo,
    slug_unimarc,
)

FUENTES = {
    "jumbo": {
        "cadena": "Jumbo",
        "path": Path("data/jumbo_real.csv"),
        "slug": slug_jumbo,
        "fetch": fetch_ean_jumbo,
    },
    "unimarc": {
        "cadena": "Unimarc",
        "path": Path("data/unimarc_real.csv"),
        "slug": slug_unimarc,
        "fetch": fetch_ean_unimarc,
    },
}

CHECKPOINT_CADA = 100
MAX_BLOQUEOS_SEGUIDOS = 5


def slugs_del_csv(path, extraer_slug):
    """Slugs únicos presentes en el CSV, en orden de aparición."""
    if not path.exists():
        return []
    vistos, slugs = set(), []
    with open(path, newline="", encoding="utf-8-sig") as f:
        for fila in csv.DictReader(f):
            slug = extraer_slug(fila.get("url", ""))
            if slug and slug not in vistos:
                vistos.add(slug)
                slugs.append(slug)
    return slugs


def backfill(clave, pausa=0.5, limite=None, cache=None, cache_path=ean_cache.RUTA):
    cfg = FUENTES[clave]
    cadena = cfg["cadena"]
    propia = cache is None
    if propia:
        cache = ean_cache.cargar(cache_path)

    slugs = slugs_del_csv(cfg["path"], cfg["slug"])
    if not slugs:
        print(f"[{cadena}] no hay slugs en {cfg['path']}, se omite.")
        return cache

    pendientes = [s for s in slugs if not ean_cache.tiene(cache, cadena, s)]
    print(
        f"[{cadena}] {len(slugs)} slugs en el CSV, {len(slugs) - len(pendientes)} ya en caché. "
        f"Pendientes: {len(pendientes)}",
        flush=True,
    )

    procesados = con_ean = bloqueos_seguidos = 0

    for slug in pendientes:
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
        # se cachea incluso el "" (sin EAN) para no volver a preguntarlo nunca
        ean_cache.poner(cache, cadena, slug, ean)
        if ean:
            con_ean += 1
        procesados += 1

        if procesados % CHECKPOINT_CADA == 0:
            ean_cache.guardar(cache, cache_path)
            print(f"  checkpoint: {procesados}/{len(pendientes)}, {con_ean} con EAN", flush=True)

        if limite and procesados >= limite:
            print(f"  límite {limite} alcanzado.")
            break

        time.sleep(pausa)

    ean_cache.guardar(cache, cache_path)
    entradas, total_con_ean = ean_cache.total(cache)
    print(
        f"[{cadena}] listo. Esta corrida: {procesados} consultados, {con_ean} con EAN. "
        f"Caché total: {entradas} slugs, {total_con_ean} con EAN.",
        flush=True,
    )
    return cache


def _parse_args(argv):
    if not argv or argv[0] not in (*FUENTES, "all"):
        print("Uso: python -m app.backfill_ean <jumbo|unimarc|all> [--pausa S] [--limite N]")
        raise SystemExit(1)
    claves = list(FUENTES) if argv[0] == "all" else [argv[0]]
    pausa, limite = 0.5, None
    i = 1
    while i < len(argv):
        if argv[i] == "--pausa" and i + 1 < len(argv):
            pausa = float(argv[i + 1]); i += 2
        elif argv[i] == "--limite" and i + 1 < len(argv):
            limite = int(argv[i + 1]); i += 2
        else:
            i += 1
    return claves, pausa, limite


def main(argv=None):
    claves, pausa, limite = _parse_args(argv if argv is not None else sys.argv[1:])
    cache = ean_cache.cargar()
    for clave in claves:
        cache = backfill(clave, pausa=pausa, limite=limite, cache=cache)


if __name__ == "__main__":
    main()
