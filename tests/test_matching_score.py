from types import SimpleNamespace

from app.matching import candidato_compatible, matching_score
from app.normalizacion import extraer_atributos, normalizar_formato


def producto(nombre, marca="", tipo="general", formato="", producto_base=None, id=1):
    return SimpleNamespace(
        id=id,
        nombre=nombre,
        marca=marca,
        tipo=tipo,
        formato=formato,
        producto_base=producto_base,
    )


def test_extraer_atributos_leche_soprole_1l():
    atributos = extraer_atributos("Leche Soprole Entera 1L")

    assert atributos["marca"] == "soprole"
    assert atributos["volumen"] == 1000
    assert atributos["unidad"] == "ml"
    assert atributos["categoria"] == "leche"


def test_leche_soprole_1l_vs_1000ml_tiene_score_alto():
    a = producto("Leche Soprole Entera 1L", marca="Soprole", formato="1 L", producto_base="leche_soprole_entera_1l")
    b = producto("Leche Soprole Entera 1000ml", marca="Soprole", formato="1000 ml", producto_base="leche_soprole_entera_1l", id=2)

    assert normalizar_formato("1L") == normalizar_formato("1000ml")
    assert matching_score(a, b) >= 85
    assert candidato_compatible(a, b)


def test_coca_cola_1_5l_vs_1500ml_tiene_score_alto():
    a = producto("Bebida Coca Cola Original 1.5L", marca="Coca Cola", formato="1.5 L")
    b = producto("Coca-Cola Bebida Original 1500ml", marca="Coca-Cola", formato="1500 ml", id=2)

    assert normalizar_formato("1.5L") == normalizar_formato("1500ml")
    assert matching_score(a, b) >= 80
    assert candidato_compatible(a, b)


def test_arroz_tucapel_1kg_vs_1000g_tiene_score_alto():
    a = producto("Arroz Tucapel Grado 1 1kg", marca="Tucapel", formato="1 kg")
    b = producto("Arroz Tucapel Grado 1 1000g", marca="Tucapel", formato="1000 g", id=2)

    assert normalizar_formato("1kg") == normalizar_formato("1000g")
    assert matching_score(a, b) >= 80
    assert candidato_compatible(a, b)


def test_pack_6_coca_cola_vs_coca_cola_x6_tiene_score_alto():
    a = producto("Pack 6 Bebida Coca Cola 350ml", marca="Coca Cola", formato="pack 6")
    b = producto("Bebida Coca-Cola x6 350 ml", marca="Coca-Cola", formato="x6", id=2)

    assert normalizar_formato("pack 6") == normalizar_formato("x6")
    assert matching_score(a, b) >= 80
    assert candidato_compatible(a, b)


def test_yogurt_distintos_sabores_no_deben_coincidir():
    a = producto("Yogurt Soprole Frutilla 1kg", marca="Soprole", formato="1 kg")
    b = producto("Yogurt Soprole Vainilla 1kg", marca="Soprole", formato="1 kg", id=2)

    assert matching_score(a, b) >= 70
    assert not candidato_compatible(a, b)
