from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base
from app.fase5a_rules import compatible_fase5a
from app.models import Categoria, Producto, Subcategoria
from app.scripts.aplicar_matching_fase5c import (
    CATEGORIAS_BLOQUEADAS,
    CATEGORIAS_PERMITIDAS,
    aplicar_cambios,
    auditoria_previa_ok,
    metricas_fase5c,
    seleccionar_cambios,
)


def crear_db_fase5c():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    db = Session()
    bebidas = Categoria(nombre="Bebidas")
    higiene = Categoria(nombre="Higiene Personal")
    bebe = Categoria(nombre="Bebe")
    limpieza = Categoria(nombre="Limpieza")
    mascotas = Categoria(nombre="Mascotas")
    db.add_all([bebidas, higiene, bebe, limpieza, mascotas])
    db.flush()
    sub_bebidas = Subcategoria(nombre="Bebidas", categoria=bebidas)
    shampoo = Subcategoria(nombre="Shampoo", categoria=higiene)
    panales = Subcategoria(nombre="Panales", categoria=bebe)
    detergentes = Subcategoria(nombre="Detergentes", categoria=limpieza)
    perros = Subcategoria(nombre="Alimento Perros", categoria=mascotas)
    db.add_all([sub_bebidas, shampoo, panales, detergentes, perros])
    db.flush()
    productos = [
        Producto(id=1, nombre="Bebida Coca-Cola Original 1.5 L", marca="Coca Cola", formato="1.5 L", producto_base="old_coke", categoria=bebidas, subcategoria=sub_bebidas),
        Producto(id=2, nombre="Bebida coca cola original 1.5 l", marca="Coca-Cola", formato="1500 ml", producto_base="old_coke", categoria=bebidas, subcategoria=sub_bebidas),
        Producto(id=3, nombre="Bebida Coca-Cola Zero 1.5 L", marca="Coca Cola", formato="1.5 L", producto_base="old_zero", categoria=bebidas, subcategoria=sub_bebidas),
        Producto(id=4, nombre="Bebida Fanta Naranja 1.5 L", marca="Fanta", formato="1.5 L", producto_base="old_fanta_naranja", categoria=bebidas, subcategoria=sub_bebidas),
        Producto(id=5, nombre="Bebida Fanta Limon 1.5 L", marca="Fanta", formato="1.5 L", producto_base="old_fanta_limon", categoria=bebidas, subcategoria=sub_bebidas),
        Producto(id=6, nombre="Detergente Omo 3 L", marca="Omo", formato="3 L", producto_base="old_omo", categoria=limpieza, subcategoria=detergentes),
        Producto(id=7, nombre="Alimento Perro Test 15 kg", marca="Test", formato="15 kg", producto_base="old_dog", categoria=mascotas, subcategoria=perros),
        Producto(id=8, nombre="Shampoo Dove Hombre 400 ml", marca="Dove", formato="400 ml", producto_base="old_hombre", categoria=higiene, subcategoria=shampoo),
        Producto(id=9, nombre="Shampoo Dove Mujer 400 ml", marca="Dove", formato="400 ml", producto_base="old_mujer", categoria=higiene, subcategoria=shampoo),
        Producto(id=10, nombre="Acondicionador Dove Mujer 400 ml", marca="Dove", formato="400 ml", producto_base="old_acond", categoria=higiene, subcategoria=shampoo),
        Producto(id=11, nombre="Pañal Pampers Talla M 48 un", marca="Pampers", formato="48 un", producto_base="old_m", categoria=bebe, subcategoria=panales),
        Producto(id=12, nombre="Pañal Pampers Talla G 48 un", marca="Pampers", formato="48 un", producto_base="old_g", categoria=bebe, subcategoria=panales),
        Producto(id=13, nombre="Formula Infantil Etapa 1 800 g", marca="Nido", formato="800 g", producto_base="old_e1", categoria=bebe, subcategoria=panales),
        Producto(id=14, nombre="Formula Infantil Etapa 2 800 g", marca="Nido", formato="800 g", producto_base="old_e2", categoria=bebe, subcategoria=panales),
    ]
    db.add_all(productos)
    db.commit()
    return db


def test_categorias_permitidas_y_bloqueadas_fase5c():
    assert CATEGORIAS_PERMITIDAS == {"Bebidas", "Higiene Personal", "Bebe"}
    assert "Mascotas" in CATEGORIAS_BLOQUEADAS
    assert "Limpieza" in CATEGORIAS_BLOQUEADAS


def test_seleccionar_cambios_solo_aplica_grupo_seguro_de_bebidas():
    db = crear_db_fase5c()
    try:
        cambios = seleccionar_cambios(db, riesgos=set())
        ids = {int(cambio["producto_id"]) for cambio in cambios}
        assert ids == {1, 2}
        assert {cambio["categoria"] for cambio in cambios} == {"Bebidas"}
        assert all(cambio["producto_base_nuevo"] == "bebidas_bebida_coca_cola_normal_cola_1500_ml" for cambio in cambios)
    finally:
        db.close()


def test_aplicar_cambios_fase5c_es_idempotente():
    db = crear_db_fase5c()
    try:
        cambios = seleccionar_cambios(db, riesgos=set())
        antes = metricas_fase5c(db)
        aplicados = aplicar_cambios(db, cambios, batch_size=1)
        despues = metricas_fase5c(db)
        nuevos = seleccionar_cambios(db, riesgos=set())
        assert aplicados == 2
        assert nuevos == []
        assert despues["TOTAL"]["productos_equivalentes"] >= antes["TOTAL"]["productos_equivalentes"]
    finally:
        db.close()


def test_auditoria_previa_obligatoria_fase5c():
    db = crear_db_fase5c()
    try:
        assert auditoria_previa_ok(db)
    finally:
        db.close()


def test_reglas_negativas_fase5c():
    db = crear_db_fase5c()
    try:
        productos = {producto.id: producto for producto in db.query(Producto).all()}
        assert not compatible_fase5a(productos[1], productos[3], "Bebidas")
        assert not compatible_fase5a(productos[4], productos[5], "Bebidas")
        assert not compatible_fase5a(productos[8], productos[9], "Higiene Personal")
        assert not compatible_fase5a(productos[8], productos[10], "Higiene Personal")
        assert not compatible_fase5a(productos[11], productos[12], "Bebe")
        assert not compatible_fase5a(productos[13], productos[14], "Bebe")
    finally:
        db.close()


def test_rollback_logico_fase5c_con_csv_en_memoria():
    db = crear_db_fase5c()
    try:
        cambios = seleccionar_cambios(db, riesgos=set())
        originales = {int(c["producto_id"]): c["producto_base_anterior"] for c in cambios}
        aplicar_cambios(db, cambios)
        for cambio in cambios:
            producto = db.get(Producto, int(cambio["producto_id"]))
            producto.producto_base = cambio["producto_base_anterior"]
        db.commit()
        for producto_id, base in originales.items():
            assert db.get(Producto, producto_id).producto_base == base
    finally:
        db.close()
