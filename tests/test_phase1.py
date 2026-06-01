from urllib.parse import parse_qs, urlsplit

from app.importar_csv import generar_producto_base
from app.main import normalizar_formato, normalizar_texto
from app.services import calcular_ahorro, normalizar_paginacion
from app.url_utils import generar_url_busqueda


def test_normalizar_texto_quita_tildes_y_mantiene_ene():
    assert normalizar_texto("Azúcar Ñuble 1 lt") == "azucar nuble 1 l"


def test_producto_base_equivale_1l_y_1000ml():
    base_1l = generar_producto_base("Leche Soprole 1L", "Soprole", "general", "1 L")
    base_1000ml = generar_producto_base("Leche Soprole 1000ml", "Soprole", "general", "1000 ml")

    assert base_1l == base_1000ml
    assert normalizar_formato("1000ml") == normalizar_formato("1L")


def test_generar_url_busqueda_escapa_espanol():
    url = generar_url_busqueda("https://www.jumbo.cl/busqueda", "ft", "azúcar ñuble 1L")
    query = parse_qs(urlsplit(url).query)

    assert query["ft"] == ["azúcar ñuble 1L"]
    assert "%C3%B1" in url
    assert "%C3%BA" in url


def test_normalizar_paginacion_limita_maximo_y_offset():
    assert normalizar_paginacion(500, -20) == (100, 0)
    assert normalizar_paginacion(None, None) == (50, 0)


def test_calcular_ahorro_basico():
    assert calcular_ahorro(12500, 10000) == 2500
    assert calcular_ahorro(9000, 10000) == 0
