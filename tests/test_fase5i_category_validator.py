from pathlib import Path

from app.category_validator import is_valid_row, validate_category


def test_bebidas_no_entran_en_bebe():
    ejemplos = [
        "Bebida Vegetal NotMilk Protein 750 ml NotCo",
        "Bebida Sin Azucar Pack Lata 6 Un Coca-Cola",
        "Bebida Leche Lactea Yogu Yogu Mora Caja",
    ]

    for nombre in ejemplos:
        resultado = validate_category(nombre, "Bebe", "Alimentos Bebe")
        assert not resultado.accepted
        assert resultado.reason == "bebida_en_bebe"
        assert resultado.suggested_category == "Bebidas"


def test_productos_mascota_no_entran_en_carnes_desayuno_o_lacteos():
    ejemplos = [
        ("Galletas Cachorro Raza Grande Sabor Leche 500 g Master Dog", "Desayuno y Snacks", "Snacks"),
        ("Alimento Seco Perro Adulto Carne 3 Kg Champion Dog", "Carnes y Pescados", "Carnes"),
        ("Alimento Humedo Cachorro Sabor Carne Pouch 85 g Pedigree", "Lacteos, Huevos y Congelados", "Leche"),
    ]

    for nombre, categoria, subcategoria in ejemplos:
        resultado = validate_category(nombre, categoria, subcategoria)
        assert not resultado.accepted
        assert resultado.reason == "mascota_fuera_de_mascotas"
        assert resultado.suggested_category == "Mascotas"


def test_higiene_no_entra_en_lacteos_despensa_o_bebe():
    ejemplos = [
        ("Tonico Rose Care Leche y Tonico Micelar 200 ml Nivea", "Lacteos, Huevos y Congelados"),
        ("Desodorante Rexona Clinical Mujer 48 h", "Despensa"),
        ("Jabon Dove Original Barra 90 g", "Bebe"),
    ]

    for nombre, categoria in ejemplos:
        resultado = validate_category(nombre, categoria, "Leche")
        assert not resultado.accepted
        assert resultado.reason == "higiene_fuera_de_higiene"
        assert resultado.suggested_category == "Higiene Personal"


def test_falsos_positivos_se_mantienen_validos():
    assert validate_category("Hair Food Aguacate 350 ml Garnier", "Higiene Personal", "Acondicionador").accepted
    assert validate_category("Trocitos Jugosos Carne Pouch 100 g Master Dog", "Mascotas", "Alimento Perros").accepted
    assert validate_category("Pasta Limpiadora Pink Stuff 850 g", "Limpieza", "Limpiadores").accepted


def test_logging_de_rechazos(tmp_path):
    row = {
        "nombre": "Bebida Sin Azucar Pack Lata 6 Un Coca-Cola",
        "categoria": "Bebe",
        "subcategoria": "Alimentos Bebe",
    }
    log_path = tmp_path / "rechazos.csv"

    assert not is_valid_row(row, "test", log_path)

    contenido = log_path.read_text(encoding="utf-8-sig")
    assert "bebida_en_bebe" in contenido
    assert "Coca-Cola" in contenido
