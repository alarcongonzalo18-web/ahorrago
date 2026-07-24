"""Baja el arbol de categorias real de una cadena y lo vuelca a JSON.

Utilitario manual (NO entra al pipeline nocturno). Sirve para curar el mapeo
`(categoria_interna, subcategoria_visible, slug)` de cada scraper cuando la
cadena cambia su taxonomia.

    python -m app.descubrir_taxonomia unimarc
    python -m app.descubrir_taxonomia tottus

Vuelca `data/taxonomia_<cadena>.json` e imprime el arbol nivel-2 para revisar.
El mapeo curado (que subcategorias entran y a que categoria interna van) vive
como constante CATEGORIAS en cada scraper, no aca.
"""

import json
import sys
import urllib.request
from pathlib import Path

from app.ean_fetch import USER_AGENT

RAIZ = Path(__file__).resolve().parents[1]

UNIMARC_CATEGORIES = "https://bff-unimarc-ecommerce.unimarc.cl/catalog/categories"
UNIMARC_HEADERS = {
    "Accept": "application/json, text/plain, */*",
    "User-Agent": USER_AGENT,
    "Origin": "https://www.unimarc.cl",
    "Referer": "https://www.unimarc.cl/",
    "channel": "UNIMARC",
    "source": "web",
    "version": "1.0.0",
}


def _get_json(url, headers):
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8", "replace"))


def descubrir_unimarc():
    """Devuelve [{rubro, slug, id, subcategorias:[{name, slug}]}]."""
    arbol = _get_json(UNIMARC_CATEGORIES, UNIMARC_HEADERS)
    salida = []
    for cat in arbol:
        salida.append({
            "rubro": cat.get("name"),
            "slug": cat.get("slug"),
            "id": cat.get("id"),
            "subcategorias": [
                {"name": s.get("name"), "slug": s.get("slug")}
                for s in (cat.get("subcategories") or [])
            ],
        })
    return salida


JUMBO_BROWSE = "https://ac.cnstrc.com/browse/group_id/{gid}?key={key}&num_results_per_page=1"
# Rubros top de consumo de Jumbo (Constructor.io). Los ids son estables; se
# descubrieron unionando los `groups` de varias busquedas amplias. Excluidos:
# Hogar/Jugueteria (335), Experiencias Jumbo (831), Catering (1025),
# Farmacia (1165), Mi bebe (393).
JUMBO_RUBROS = {
    1: "Lacteos, Huevos y Congelados", 20: "Frutas y Verduras", 27: "Despensa",
    47: "Chocolates, Galletas y Snacks", 75: "Carnes y Pescados",
    86: "Quesos y Fiambres", 157: "Panaderia y Pasteleria",
    204: "Licores, Bebidas y Aguas", 230: "Cuidado Personal y Bebe",
    261: "Limpieza", 400: "Mascotas",
}


def descubrir_jumbo():
    """Devuelve [{rubro, id, subcategorias:[{name, id, count}]}] via Constructor.io."""
    from app.scraper_jumbo_real import obtener_api_key

    key = obtener_api_key()
    salida = []
    for gid, nombre in JUMBO_RUBROS.items():
        resp = _get_json(JUMBO_BROWSE.format(gid=gid, key=key), {"User-Agent": USER_AGENT})
        response = resp.get("response", {})
        grupos = response.get("groups", [])
        hijos = grupos[0].get("children", []) if grupos else []
        salida.append({
            "rubro": nombre,
            "id": gid,
            "total": response.get("total_num_results"),
            "subcategorias": [
                {"name": c.get("display_name"), "id": c.get("group_id"), "count": c.get("count")}
                for c in hijos
            ],
        })
    return salida


DESCUBRIDORES = {
    "unimarc": descubrir_unimarc,
    "jumbo": descubrir_jumbo,
}


def main(argv=None):
    argv = argv if argv is not None else sys.argv[1:]
    if not argv or argv[0] not in DESCUBRIDORES:
        print("uso: python -m app.descubrir_taxonomia <" + "|".join(DESCUBRIDORES) + ">")
        return 1

    cadena = argv[0]
    arbol = DESCUBRIDORES[cadena]()

    destino = RAIZ / "data" / f"taxonomia_{cadena}.json"
    destino.write_text(json.dumps(arbol, ensure_ascii=False, indent=2), encoding="utf-8")

    total_subs = sum(len(c["subcategorias"]) for c in arbol)
    print(f"{cadena}: {len(arbol)} rubros, {total_subs} subcategorias nivel-2")
    for cat in arbol:
        ident = cat.get("slug", cat.get("id"))
        print(f"\n## {cat['rubro']}  ({ident})")
        for s in cat["subcategorias"]:
            ref = s.get("slug", s.get("id"))
            print(f"   - {s['name']}  ->  {ref}")
    print(f"\nVolcado en {destino}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
