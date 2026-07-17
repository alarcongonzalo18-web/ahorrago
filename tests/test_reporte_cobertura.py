from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base
from app.models import Categoria, Precio, Producto, Proveedor
from app.reporte_cobertura import calcular_cobertura, formatear_reporte


def crear_db():
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    db = Session()

    categoria = Categoria(nombre="Despensa")
    lider = Proveedor(nombre="Lider")
    jumbo = Proveedor(nombre="Jumbo")
    db.add_all([categoria, lider, jumbo])
    db.flush()

    # comparable: mismo producto_base en 2 proveedores
    a1 = Producto(nombre="Arroz G1 1 kg", producto_base="arroz_g1_1kg", categoria_id=categoria.id)
    a2 = Producto(nombre="Arroz Grado 1 1kg", producto_base="arroz_g1_1kg", categoria_id=categoria.id)
    # no comparable: solo en un proveedor
    solo = Producto(nombre="Aceite Raro 1 L", producto_base="aceite_raro_1l", categoria_id=categoria.id)
    db.add_all([a1, a2, solo])
    db.flush()

    db.add_all([
        Precio(producto_id=a1.id, proveedor_id=lider.id, precio_normal=1500),
        Precio(producto_id=a2.id, proveedor_id=jumbo.id, precio_normal=1400),
        Precio(producto_id=solo.id, proveedor_id=lider.id, precio_normal=3000),
    ])
    db.commit()
    return db


def test_cobertura_cuenta_comparables_y_no_comparables():
    db = crear_db()
    try:
        datos = calcular_cobertura(db)
        assert datos["productos_totales"] == 3
        assert datos["grupos_producto_base"] == 2
        assert datos["grupos_comparables"] == 1
        assert datos["porcentaje_comparable"] == 50.0
        assert datos["productos_por_proveedor"] == {"Lider": 2, "Jumbo": 1}
        despensa = datos["comparables_por_categoria"]["Despensa"]
        assert despensa == {"grupos": 2, "comparables": 1, "porcentaje": 50.0}
    finally:
        db.close()


def test_formatear_reporte_es_legible():
    db = crear_db()
    try:
        texto = formatear_reporte(calcular_cobertura(db))
        assert "comparables (2+ proveedores): 1 (50.0%)" in texto
        assert "Despensa" in texto
    finally:
        db.close()


def test_cobertura_con_db_vacia_no_revienta():
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    Base.metadata.create_all(bind=engine)
    db = sessionmaker(bind=engine)()
    try:
        datos = calcular_cobertura(db)
        assert datos["porcentaje_comparable"] == 0.0
        assert formatear_reporte(datos)
    finally:
        db.close()
