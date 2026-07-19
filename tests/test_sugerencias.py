from app.sugerencias import MINIMO_APARICIONES, construir_terminos


def _nombres(termino, cantidad, plantilla="Producto {t} {i}"):
    return [plantilla.format(t=termino, i=i) for i in range(cantidad)]


def test_termino_frecuente_entra_y_raro_no():
    nombres = _nombres("Trencito", MINIMO_APARICIONES) + _nombres("Rarisimo", 2)
    terminos = [x["t"] for x in construir_terminos(nombres)]
    assert "trencito" in terminos
    assert "rarisimo" not in terminos


def test_ordena_por_frecuencia():
    nombres = _nombres("Leche", 30) + _nombres("Queso", 20)
    terminos = [x["t"] for x in construir_terminos(nombres)]
    assert terminos.index("leche") < terminos.index("queso")


def test_no_sugiere_envases_ni_numeros():
    nombres = _nombres("Bolsa 500", MINIMO_APARICIONES)
    terminos = [x["t"] for x in construir_terminos(nombres)]
    assert "bolsa" not in terminos
    assert "500" not in terminos


def test_repetido_en_un_nombre_cuenta_una_vez():
    nombres = ["Leche Leche Leche"] * (MINIMO_APARICIONES - 1)
    assert "leche" not in [x["t"] for x in construir_terminos(nombres)]


def test_marca_multipalabra_como_frase():
    nombres = _nombres("Juan Valdez", MINIMO_APARICIONES)
    assert "juan valdez" in [x["t"] for x in construir_terminos(nombres)]
