from types import SimpleNamespace

from app.matching import candidato_compatible
from app.normalizacion import normalizar_formato


def producto(nombre, marca="Test", tipo="general", formato="", producto_base=None, id=1):
    return SimpleNamespace(
        id=id,
        nombre=nombre,
        marca=marca,
        tipo=tipo,
        formato=formato,
        producto_base=producto_base,
    )


def test_matching_equivale_1l_y_1000ml():
    assert normalizar_formato("1L") == normalizar_formato("1000ml")
    assert candidato_compatible(
        producto("Leche Test Entera 1L", formato="1 L"),
        producto("Leche Test Entera 1000ml", formato="1000 ml", id=2),
    )


def test_matching_equivale_500g_y_0_5kg():
    assert normalizar_formato("500g") == normalizar_formato("0.5kg")
    assert candidato_compatible(
        producto("Arroz Test 500g", formato="500 g"),
        producto("Arroz Test 0.5kg", formato="0.5 kg", id=2),
    )


def test_matching_equivale_pack_6_y_6_unidades():
    assert normalizar_formato("pack 6") == normalizar_formato("6 unidades")
    assert candidato_compatible(
        producto("Bebida Test Pack 6", formato="pack 6"),
        producto("Bebida Test 6 unidades", formato="6 unidades", id=2),
    )
