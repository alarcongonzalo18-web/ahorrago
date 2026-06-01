from types import SimpleNamespace

from app.fase5a_rules import atributos_fase5a, compatible_fase5a, key_fase5a
from app.normalizacion import normalizar_formato


def producto(nombre, marca="", formato="", tipo="general", producto_base=""):
    return SimpleNamespace(
        id=1,
        nombre=nombre,
        marca=marca,
        formato=formato,
        tipo=tipo,
        producto_base=producto_base,
    )


def test_bebidas_positivos_y_negativos():
    assert normalizar_formato("1.5L") == normalizar_formato("1500ml")
    assert normalizar_formato("pack 6") == normalizar_formato("x6")
    coca = producto("Bebida Coca Cola Original 1.5 L", "Coca Cola", "1.5 L")
    coca_ml = producto("Coca-Cola Bebida Original 1500 ml", "Coca-Cola", "1500 ml")
    zero = producto("Bebida Coca Cola Zero 1.5 L", "Coca Cola", "1.5 L")
    assert compatible_fase5a(coca, coca_ml, "Bebidas")
    assert not compatible_fase5a(coca, zero, "Bebidas")


def test_limpieza_aroma_y_variedad():
    lavanda = producto("Detergente Liquido Omo Lavanda 3 L", "Omo", "3 L")
    lavanda_ml = producto("Detergente Líquido Omo Lavanda 3000 ml", "Omo", "3000 ml")
    limon = producto("Detergente Liquido Omo Limon 3 L", "Omo", "3 L")
    antibacterial = producto("Limpiador Antibacterial Limon 900 ml", "Omo", "900 ml")
    tradicional = producto("Limpiador Tradicional Limon 900 ml", "Omo", "900 ml")
    assert compatible_fase5a(lavanda, lavanda_ml, "Limpieza")
    assert not compatible_fase5a(lavanda, limon, "Limpieza")
    assert not compatible_fase5a(antibacterial, tradicional, "Limpieza")


def test_higiene_genero_e_infantil():
    hombre = producto("Desodorante Dove Hombre 150 ml", "Dove", "150 ml")
    hombre_ml = producto("Dove Desodorante Men Hombre 0.15 L", "Dove", "0.15 L")
    mujer = producto("Desodorante Dove Mujer 150 ml", "Dove", "150 ml")
    infantil = producto("Shampoo Infantil Manzanilla 750 ml", "Simonds", "750 ml")
    adulto = producto("Shampoo Adulto Manzanilla 750 ml", "Simonds", "750 ml")
    assert compatible_fase5a(hombre, hombre_ml, "Higiene Personal")
    assert not compatible_fase5a(hombre, mujer, "Higiene Personal")
    assert not compatible_fase5a(infantil, adulto, "Higiene Personal")


def test_bebe_talla_etapa_cantidad():
    talla_m = producto("Pañal Pampers Talla M 48 un", "Pampers", "48 un")
    talla_m_pack = producto("Panal Pampers Talla M Pack 48", "Pampers", "pack 48")
    talla_g = producto("Pañal Pampers Talla G 48 un", "Pampers", "48 un")
    etapa1 = producto("Formula Infantil Etapa 1 800 g", "Nido", "800 g")
    etapa2 = producto("Formula Infantil Etapa 2 800 g", "Nido", "800 g")
    assert compatible_fase5a(talla_m, talla_m_pack, "Bebe")
    assert not compatible_fase5a(talla_m, talla_g, "Bebe")
    assert not compatible_fase5a(etapa1, etapa2, "Bebe")


def test_mascotas_perro_gato_cachorro_adulto():
    perro = producto("Alimento Perro Adulto Master Dog 15 kg", "Master Dog", "15 kg")
    perro_g = producto("Alimento para Perro Adulto Master Dog 15000 g", "Master Dog", "15000 g")
    cachorro = producto("Alimento Perro Cachorro Master Dog 15 kg", "Master Dog", "15 kg")
    gato = producto("Alimento Gato Adulto Master Cat 15 kg", "Master Cat", "15 kg")
    attrs = atributos_fase5a(perro, "Mascotas")
    assert attrs["animal"] == "perro"
    assert compatible_fase5a(perro, perro_g, "Mascotas")
    assert not compatible_fase5a(perro, cachorro, "Mascotas")
    assert not compatible_fase5a(perro, gato, "Mascotas")
    assert key_fase5a(perro, "Mascotas") == key_fase5a(perro_g, "Mascotas")
