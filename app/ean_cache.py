"""Caché persistente `slug -> EAN` por cadena.

Por qué existe: los scrapers reescriben los CSV por-cadena en cada corrida con
`ean=""`. Si el backfill escribiera el EAN en el CSV, la primera actualización
automática lo borraría (y son ~33k requests). La caché vive aparte, sobrevive a
los re-scrapes, y `combinar_supermercados` enriquece desde acá.

El EAN de un producto **no cambia nunca**, así que una entrada vale para siempre
y el backfill sólo consulta slugs nuevos (incremental).

Formato: `{"Jumbo": {"<slug>": "<ean>"}, "Unimarc": {...}}`.
Un valor `""` significa "ya se consultó y ese producto no tiene EAN" — se guarda
igual para no volver a pedirlo en cada corrida.
"""

import json
from pathlib import Path


RUTA = Path("data/ean_cache.json")


def cargar(path=RUTA):
    """Lee la caché. Devuelve {} si no existe o está corrupta (no revienta)."""
    path = Path(path)
    if not path.exists():
        return {}
    try:
        datos = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}
    return datos if isinstance(datos, dict) else {}


def guardar(cache, path=RUTA):
    """Escribe la caché de forma atómica (tmp + replace)."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(
        json.dumps(cache, ensure_ascii=False, sort_keys=True, indent=0),
        encoding="utf-8",
    )
    tmp.replace(path)


def tiene(cache, cadena, slug):
    """True si el slug ya fue consultado (aunque haya dado sin EAN)."""
    return slug in (cache.get(cadena) or {})


def obtener(cache, cadena, slug):
    """EAN cacheado, o "" si no está o si se sabe que no tiene."""
    return (cache.get(cadena) or {}).get(slug, "")


def poner(cache, cadena, slug, ean):
    cache.setdefault(cadena, {})[slug] = ean or ""


def total(cache):
    """(entradas, con_ean) — para reportar avance."""
    entradas = sum(len(v) for v in cache.values())
    con_ean = sum(1 for v in cache.values() for e in v.values() if e)
    return entradas, con_ean
