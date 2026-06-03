"""Tests Fase 5J-R para el validador de categorias (v2).
Repo-ready: importa desde app.category_validator; cae al modulo local si no existe.
"""
try:
    from app.category_validator import validate_category, validate_row, decide_action, is_valid_row
except ImportError:
    from category_validator_v2 import validate_category, validate_row, decide_action, is_valid_row


def action(nombre, categoria, subcategoria=""):
    return decide_action(validate_category(nombre, categoria, subcategoria))


# ---- Falsos positivos que v1 borraba y NO deben perderse ----
def test_vinagre_de_vino_se_conserva():
    assert action("Vinagre de Vino Blanco Traverso 1 L", "Despensa", "Condimentos") == "keep"

def test_base_maggi_jugoso_se_conserva():
    assert action("Base Maggi Jugoso Al Horno Pollo 24 g", "Despensa", "Sazonadores") == "keep"

def test_carne_al_vino_se_conserva():
    assert action("Carne Asada en Vino Tinto kg", "Carnes y Pescados", "Carnes") == "keep"

def test_bebida_lactea_se_conserva_en_lacteos():
    assert action("Bebida Lactea Soprole Kefir Berries 1 L", "Lacteos, Huevos y Congelados", "Leche") == "keep"

def test_saborizante_milo_polvo_se_conserva():
    assert action("Saborizante para Leche Milo Polvo Chocolate 700 g", "Lacteos, Huevos y Congelados", "Leche") == "keep"


# ---- Word boundary: substrings que NO deben gatillar ----
def test_jugoso_no_es_jugo():
    assert action("Pechuga Jugosa al Sarten", "Carnes y Pescados", "Carnes") == "keep"

def test_cajun_no_es_caju_snack():
    assert action("Sazonador Cajun en Polvo", "Despensa", "Condimentos") == "keep"

def test_crema_de_leche_no_es_higiene():
    assert action("Crema de Leche Nestle 200 g", "Lacteos, Huevos y Congelados", "Crema") == "keep"


# ---- Aciertos reales (bug 5H): deben rechazarse con Alta ----
def test_pedigree_en_carnes_se_rechaza():
    assert action("Alimento Humedo Perro Adulto Pedigree Carne 100 g", "Carnes y Pescados", "Carnes") == "reject"

def test_nivea_en_crema_se_rechaza():
    assert action("Crema Nivea Milk Nutritiva Piel Extra Seca 100 ml", "Lacteos, Huevos y Congelados", "Crema") == "reject"

def test_cif_limpiador_en_crema_se_rechaza():
    assert action("Limpiador Crema Cif Original 500 ml", "Lacteos, Huevos y Congelados", "Crema") == "reject"

def test_coca_cola_en_bebe_se_rechaza():
    assert action("Coca Cola Original 1.5 L", "Bebe", "Alimentos Bebe") == "reject"

def test_notmilk_en_bebe_se_rechaza():
    assert action("NotMilk Entera 1 L", "Bebe", "Alimentos Bebe") == "reject"


# ---- Insensibilidad a acentos en categoria ----
def test_acentos_categoria_equivalentes():
    con = action("Crema Nivea Soft 200 ml", "Lácteos, Huevos y Congelados", "Crema")
    sin = action("Crema Nivea Soft 200 ml", "Lacteos, Huevos y Congelados", "Crema")
    assert con == sin == "reject"


# ---- Politica de cuarentena ----
def test_media_va_a_cuarentena_y_se_conserva():
    v = validate_category("Bebida Energetica Score Tropical 500 ml", "Despensa", "Otros")
    assert v.confidence == "Media"
    assert decide_action(v) == "review"
    assert is_valid_row({"nombre": "Bebida Energetica Score Tropical 500 ml", "categoria": "Despensa"}) is True

def test_is_valid_row_false_solo_para_alta():
    # Alta -> se quita
    assert is_valid_row({"nombre": "Alimento Perro Pedigree 100 g", "categoria": "Carnes y Pescados"}) is False
    # keep
    assert is_valid_row({"nombre": "Pan Hallulla 6 un", "categoria": "Panaderia"}) is True
