from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base
from app.models import Categoria, Precio, Producto, Supermercado
from app.scripts.simular_mejora_matching_fase5a import simular


def test_simular_fase5a_no_modifica_producto_base():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    db = Session()
    try:
        categoria = Categoria(nombre="Bebidas")
        lider = Supermercado(nombre="Lider")
        jumbo = Supermercado(nombre="Jumbo")
        a = Producto(nombre="Bebida Coca Cola Original 1.5 L", marca="Coca Cola", formato="1.5 L", producto_base="old_a", categoria=categoria)
        b = Producto(nombre="Coca-Cola Bebida Original 1500 ml", marca="Coca-Cola", formato="1500 ml", producto_base="old_b", categoria=categoria)
        db.add_all([categoria, lider, jumbo, a, b])
        db.flush()
        db.add_all([Precio(producto=a, supermercado=lider, precio_normal=1500), Precio(producto=b, supermercado=jumbo, precio_normal=1490)])
        db.commit()
        antes = {p.id: p.producto_base for p in db.query(Producto).all()}
        detalle, falsos, totales = simular(db)
        despues = {p.id: p.producto_base for p in db.query(Producto).all()}
    finally:
        db.close()

    assert antes == despues
    assert detalle[0]["categoria"] == "Bebidas"
    assert totales["productos"] == 2
    assert falsos == []
