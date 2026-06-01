import json
from pathlib import Path
from types import SimpleNamespace

from app.matching import candidato_compatible, matching_score


def producto(data, id):
    return SimpleNamespace(
        id=id,
        nombre=data["nombre"],
        marca=data["marca"],
        tipo="general",
        formato=data["formato"],
        producto_base=data["producto_base"],
    )


def cargar_fixture():
    path = Path(__file__).parent / "fixtures" / "productos_reales.json"
    return json.loads(path.read_text(encoding="utf-8"))


def test_fixtures_reales_equivalencias_positivas():
    items = cargar_fixture()
    pares = [(0, 1), (2, 3), (4, 5), (6, 7)]

    for left, right in pares:
        a = producto(items[left], left)
        b = producto(items[right], right)
        assert matching_score(a, b) >= 80
        assert candidato_compatible(a, b)


def test_fixtures_reales_yogurt_sabores_distintos_no_coinciden():
    items = cargar_fixture()
    a = producto(items[8], 8)
    b = producto(items[9], 9)

    assert not candidato_compatible(a, b)
