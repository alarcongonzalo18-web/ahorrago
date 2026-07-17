from app.scraper_lider import (
    contar_por_subcategoria,
    guardar_productos,
    leer_conteo_previo,
    validar_anti_regresion,
)


def _producto(subcategoria, nombre):
    return {"subcategoria": subcategoria, "nombre": nombre}


def test_contar_por_subcategoria_agrupa():
    productos = [
        _producto("Leche", "a"),
        _producto("Leche", "b"),
        _producto("Yogurt", "c"),
    ]
    assert contar_por_subcategoria(productos) == {"Leche": 2, "Yogurt": 1}


def test_validar_anti_regresion_detecta_caida_fuerte_y_a_cero():
    previos = {"Leche": 100, "Salsas": 500, "Bebe": 471}
    nuevos = {"Leche": 100, "Salsas": 48, "Bebe": 0}
    caidas = dict((c[0], (c[1], c[2])) for c in validar_anti_regresion(nuevos, previos))
    assert caidas["Salsas"] == (500, 48)   # 90% menos
    assert caidas["Bebe"] == (471, 0)      # a cero
    assert "Leche" not in caidas           # sin cambios


def test_validar_anti_regresion_ignora_subidas_y_categorias_nuevas():
    previos = {"Leche": 50}
    nuevos = {"Leche": 200, "Pisco": 30}   # Leche sube, Pisco es nueva
    assert validar_anti_regresion(nuevos, previos) == []


def test_validar_anti_regresion_respeta_el_borde_del_umbral():
    previos = {"X": 100}
    # exactamente a la mitad NO es regresion (umbral 50%); un producto menos si.
    assert validar_anti_regresion({"X": 50}, previos, umbral=0.5) == []
    assert validar_anti_regresion({"X": 49}, previos, umbral=0.5) == [("X", 100, 49)]


def test_leer_conteo_previo_roundtrip_y_archivo_inexistente(tmp_path):
    destino = tmp_path / "lider.csv"
    assert leer_conteo_previo(destino) == {}   # todavia no existe

    productos = [
        _producto("Leche", "a"),
        _producto("Leche", "b"),
        _producto("Quesos", "c"),
    ]
    guardar_productos(productos, destino)
    assert leer_conteo_previo(destino) == {"Leche": 2, "Quesos": 1}
