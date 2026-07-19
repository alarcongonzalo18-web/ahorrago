"""Casos reales de agrupacion incorrecta detectados el 18-07-2026.

Los grupos "en 4 cadenas" de la base resultaron ser falsos positivos: sin marca
detectada, la clave agrupaba por categoria + tamaño y mezclaba marcas distintas
(Whiskas con Cat Chow) o formatos distintos (papel higienico de 22 m con humedo).
"""

from types import SimpleNamespace

from app.fase5a_rules import compatible_fase5a, key_fase5a
from app.fase5b_apply import MAX_PRODUCTOS_POR_GRUPO, _grupo_seguro


def producto(nombre, marca="", tipo="general", formato=""):
    return SimpleNamespace(id=0, nombre=nombre, marca=marca, tipo=tipo, formato=formato,
                           producto_base="")


def test_sin_marca_no_genera_clave():
    """El bug: sin marca la clave agrupaba todo el gato adulto sabor carne."""
    sin_marca = producto("Alimento Seco Gato Adulto Sabor Carne Bolsa 8 kg")
    assert key_fase5a(sin_marca, "Mascotas") == ""


def test_con_marca_si_genera_clave_y_la_incluye():
    con_marca = producto("Alimento Gato Adulto Cat Chow Carne 8 kg", marca="Cat Chow")
    clave = key_fase5a(con_marca, "Mascotas")
    assert clave
    assert "cat_chow" in clave


def test_marcas_distintas_no_comparten_clave():
    a = producto("Alimento Gato Adulto Cat Chow Carne 8 kg", marca="Cat Chow")
    b = producto("Alimento Gato Adulto Whiskas Carne 8 kg", marca="Whiskas")
    assert key_fase5a(a, "Mascotas") != key_fase5a(b, "Mascotas")


def test_no_son_compatibles_si_falta_la_marca():
    """Antes pasaban: el chequeo solo comparaba campos presentes en ambos."""
    a = producto("Alimento Seco Gato Adulto Sabor Carne Bolsa 8 kg")
    b = producto("Alimento Gato Adulto Carne 8 kg")
    assert not compatible_fase5a(a, b, "Mascotas")


def test_no_son_compatibles_marcas_distintas():
    a = producto("Alimento Gato Adulto Cat Chow Carne 8 kg", marca="Cat Chow")
    b = producto("Alimento Gato Adulto Whiskas Carne 8 kg", marca="Whiskas")
    assert not compatible_fase5a(a, b, "Mascotas")


def test_grupo_demasiado_grande_se_rechaza():
    """35 productos no son "el mismo producto en varias cadenas"."""
    grupo = [producto(f"Pasta Dental Marca{i} 90 g", marca=f"Marca{i}")
             for i in range(MAX_PRODUCTOS_POR_GRUPO + 1)]
    seguro, _ = _grupo_seguro(grupo, "Higiene Personal")
    assert not seguro


def test_grupo_chico_y_coherente_sigue_pasando():
    """La correccion no debe matar los grupos legitimos."""
    grupo = [producto("Alimento Gato Adulto Cat Chow Carne 8 kg", marca="Cat Chow"),
             producto("Alimento para Gatos Adulto Cat Chow Sabor Carne 8 kg", marca="Cat Chow")]
    seguro, _ = _grupo_seguro(grupo, "Mascotas")
    assert seguro


def test_el_tamano_sobrevive_al_recorte_de_la_clave():
    """La clave cortaba a 6 tokens con el formato al final: se perdia primero."""
    from app.normalizacion import generar_producto_base

    de_750 = generar_producto_base(
        "Vino Santa Ema Select Terroir Reserva Carmenere 750 cc", "Santa Ema", "reserva", "750 cc")
    de_375 = generar_producto_base(
        "Vino Santa Ema Select Terroir Reserva Carmenere 375 cc", "Santa Ema", "reserva", "375 cc")
    merlot = generar_producto_base(
        "Vino Santa Ema Select Terroir Reserva Merlot 750 cc", "Santa Ema", "reserva", "750 cc")

    assert de_750 != de_375   # distinto tamaño
    assert de_750 != merlot   # distinta cepa
    assert "0_75l" in de_750
