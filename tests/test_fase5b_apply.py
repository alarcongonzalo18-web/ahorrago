from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base
from app.fase5b_apply import (
    CATEGORIAS_BLOQUEADAS,
    CATEGORIAS_PERMITIDAS,
    aplicar_cambios,
    metricas_fase5b,
    seleccionar_cambios,
)
from app.fase5a_rules import key_fase5a
from app.models import Categoria, Precio, Producto, Supermercado


def crear_db_fase5b():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    db = Session()
    limpieza = Categoria(nombre="Limpieza")
    mascotas = Categoria(nombre="Mascotas")
    bebidas = Categoria(nombre="Bebidas")
    lider = Supermercado(nombre="Lider")
    jumbo = Supermercado(nombre="Jumbo")
    db.add_all([limpieza, mascotas, bebidas, lider, jumbo])
    db.flush()
    productos = [
        Producto(nombre="Detergente Liquido Omo Lavanda 3 L", marca="Omo", tipo="general", formato="3 L", producto_base="old_omo_a", categoria=limpieza),
        Producto(nombre="Detergente Líquido Omo Lavanda 3000 ml", marca="Omo", tipo="general", formato="3000 ml", producto_base="old_omo_b", categoria=limpieza),
        Producto(nombre="Alimento Perro Adulto Master Dog 15 kg", marca="Master Dog", tipo="general", formato="15 kg", producto_base="old_dog_a", categoria=mascotas),
        Producto(nombre="Alimento para Perro Adulto Master Dog 15000 g", marca="Master Dog", tipo="general", formato="15000 g", producto_base="old_dog_b", categoria=mascotas),
        Producto(nombre="Bebida Coca Cola Original 1.5 L", marca="Coca Cola", tipo="general", formato="1.5 L", producto_base="old_coke_a", categoria=bebidas),
        Producto(nombre="Coca-Cola Bebida Original 1500 ml", marca="Coca-Cola", tipo="general", formato="1500 ml", producto_base="old_coke_b", categoria=bebidas),
    ]
    db.add_all(productos)
    db.flush()
    for index, producto in enumerate(productos):
        db.add(Precio(producto=producto, supermercado=lider if index % 2 else jumbo, precio_normal=1000 + index))
    db.commit()
    return db


def test_categorias_permitidas_solo_mascotas_limpieza():
    assert CATEGORIAS_PERMITIDAS == {"Mascotas", "Limpieza"}


def test_categorias_bloqueadas_incluyen_bebidas():
    assert "Bebidas" in CATEGORIAS_BLOQUEADAS


def test_seleccionar_cambios_ignora_categorias_bloqueadas():
    db = crear_db_fase5b()
    try:
        cambios = seleccionar_cambios(db, riesgos=set())
    finally:
        db.close()
    assert cambios
    assert {cambio["categoria"] for cambio in cambios} <= {"Mascotas", "Limpieza"}


def test_seleccionar_cambios_no_incluye_grupos_riesgosos():
    db = crear_db_fase5b()
    try:
        producto = db.query(Producto).filter(Producto.nombre.like("%Omo%")).first()
        riesgo = {("Limpieza", key_fase5a(producto, "Limpieza"))}
        cambios = seleccionar_cambios(db, riesgos=riesgo)
    finally:
        db.close()
    assert all(cambio["categoria"] != "Limpieza" for cambio in cambios)


def test_aplicar_cambios_actualiza_producto_base():
    db = crear_db_fase5b()
    try:
        cambios = seleccionar_cambios(db, riesgos=set())
        aplicados = aplicar_cambios(db, cambios, batch_size=1)
        assert aplicados == len(cambios)
        for cambio in cambios:
            producto = db.get(Producto, cambio["producto_id"])
            assert producto.producto_base == cambio["producto_base_nuevo"]
    finally:
        db.close()


def test_metricas_aumentan_equivalencias_despues_de_aplicar():
    db = crear_db_fase5b()
    try:
        antes = metricas_fase5b(db)
        cambios = seleccionar_cambios(db, riesgos=set())
        aplicar_cambios(db, cambios)
        despues = metricas_fase5b(db)
        assert despues["TOTAL"]["productos_equivalentes"] >= antes["TOTAL"]["productos_equivalentes"]
    finally:
        db.close()


def test_rollback_logico_con_csv_en_memoria():
    db = crear_db_fase5b()
    try:
        cambios = seleccionar_cambios(db, riesgos=set())
        originales = {c["producto_id"]: c["producto_base_anterior"] for c in cambios}
        aplicar_cambios(db, cambios)
        for cambio in cambios:
            producto = db.get(Producto, cambio["producto_id"])
            producto.producto_base = cambio["producto_base_anterior"]
        db.commit()
        for pid, base in originales.items():
            assert db.get(Producto, pid).producto_base == base
    finally:
        db.close()


def test_no_hay_cambios_si_grupos_ya_estan_actualizados():
    db = crear_db_fase5b()
    try:
        cambios = seleccionar_cambios(db, riesgos=set())
        aplicar_cambios(db, cambios)
        nuevos = seleccionar_cambios(db, riesgos=set())
        assert nuevos == []
    finally:
        db.close()
