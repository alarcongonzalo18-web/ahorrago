from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base
from app.models import Categoria, Producto, Subcategoria
from app.scripts.auditoria_clasificacion_masiva import auditar


def crear_db_fase5f():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    db = Session()

    bebe = Categoria(nombre="Bebe")
    carnes = Categoria(nombre="Carnes y Pescados")
    desayuno = Categoria(nombre="Desayuno y Snacks")
    higiene = Categoria(nombre="Higiene Personal")
    mascotas = Categoria(nombre="Mascotas")
    limpieza = Categoria(nombre="Limpieza")
    sub_bebe = Subcategoria(nombre="Alimentos Bebe", categoria=bebe)
    sub_carnes = Subcategoria(nombre="Carnes", categoria=carnes)
    sub_snacks = Subcategoria(nombre="Snacks", categoria=desayuno)
    sub_shampoo = Subcategoria(nombre="Shampoo", categoria=higiene)
    sub_perros = Subcategoria(nombre="Alimento Perros", categoria=mascotas)
    sub_limpieza = Subcategoria(nombre="Limpiadores", categoria=limpieza)
    db.add_all([bebe, carnes, desayuno, higiene, mascotas, limpieza])
    db.add_all([sub_bebe, sub_carnes, sub_snacks, sub_shampoo, sub_perros, sub_limpieza])
    db.flush()

    productos = [
        Producto(id=1, nombre="Bebida Coca-Cola Original 591 ml", categoria=bebe, subcategoria=sub_bebe),
        Producto(id=2, nombre="Agua Mineral Sin Gas 1.6 L Vital", categoria=bebe, subcategoria=sub_bebe),
        Producto(id=3, nombre="Maní Salado 400 g Lider", categoria=bebe, subcategoria=sub_bebe),
        Producto(id=4, nombre="Detergente Líquido Hipoalergénico Bebé 3 L Popeye", categoria=bebe, subcategoria=sub_bebe),
        Producto(id=5, nombre="Snack Perro Pet's Fun Fémur de Vacuno 1.75 kg", categoria=carnes, subcategoria=sub_carnes),
        Producto(id=6, nombre="Alimento Seco Perro Adulto 15 kg", categoria=desayuno, subcategoria=sub_snacks),
        Producto(id=7, nombre="Shampoo Hair Food Aguacate 300 ml", categoria=higiene, subcategoria=sub_shampoo),
        Producto(id=8, nombre="Alimento Húmedo Perro Trocitos Jugosos 85 g", categoria=mascotas, subcategoria=sub_perros),
        Producto(id=9, nombre="Pasta Limpiadora The Pink Stuff 500 g", categoria=limpieza, subcategoria=sub_limpieza),
    ]
    db.add_all(productos)
    db.commit()
    return db


def test_fase5f_detecta_bebidas_snacks_y_detergentes_en_bebe():
    db = crear_db_fase5f()
    try:
        hallazgos = auditar(db)
    finally:
        db.close()
    por_id = {item["producto_id"]: item for item in hallazgos}

    assert por_id[1]["categoria_sugerida"] == "Bebidas"
    assert por_id[2]["categoria_sugerida"] == "Bebidas"
    assert por_id[3]["categoria_sugerida"] == "Desayuno y Snacks"
    assert por_id[4]["categoria_sugerida"] == "Limpieza"


def test_fase5f_detecta_mascotas_fuera_de_mascotas():
    db = crear_db_fase5f()
    try:
        hallazgos = auditar(db)
    finally:
        db.close()
    por_id = {item["producto_id"]: item for item in hallazgos}

    assert por_id[5]["categoria_sugerida"] == "Mascotas"
    assert por_id[6]["categoria_sugerida"] == "Mascotas"


def test_fase5f_no_marca_falsos_positivos_conocidos():
    db = crear_db_fase5f()
    try:
        hallazgos = auditar(db)
    finally:
        db.close()
    ids = {item["producto_id"] for item in hallazgos}

    assert 7 not in ids
    assert 8 not in ids
    assert 9 not in ids
