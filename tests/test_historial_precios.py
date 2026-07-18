from datetime import date, timedelta

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base
from app.historial_precios import clave_estable, registrar_snapshot, resumen
from app.models import HistorialPrecio, Precio, Producto, Proveedor


def crear_db():
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    Base.metadata.create_all(bind=engine)
    return sessionmaker(bind=engine)()


def sembrar(db, precios):
    """precios: [(nombre, ean, proveedor, precio_normal, precio_oferta)]"""
    provs = {}
    for nombre, ean, proveedor, normal, oferta in precios:
        if proveedor not in provs:
            p = Proveedor(nombre=proveedor)
            db.add(p)
            db.flush()
            provs[proveedor] = p
        prod = Producto(nombre=nombre, ean=ean, producto_base=f"ean:{ean}" if ean else nombre)
        db.add(prod)
        db.flush()
        db.add(Precio(producto_id=prod.id, proveedor_id=provs[proveedor].id,
                      precio_normal=normal, precio_oferta=oferta))
    db.commit()


def test_clave_estable_prefiere_ean():
    assert clave_estable("7802920777542", "Leche Colun") == "ean:7802920777542"
    # sin EAN cae al nombre normalizado
    assert clave_estable("", "Leche Colun 1 L").startswith("nombre:")
    # los ids de producto no participan: la clave es la misma con distinto nombre-caso
    assert clave_estable("780111", "A") == clave_estable("780111", "B")
    assert clave_estable("", "") == ""


def test_snapshot_guarda_el_precio_que_se_paga():
    db = crear_db()
    sembrar(db, [
        ("Leche Colun 1 L", "780111", "Jumbo", 1350, 1090),   # con oferta -> paga 1090
        ("Arroz Tucapel 1 kg", "780222", "Líder", 1500, None),  # sin oferta -> paga 1500
    ])
    nuevos, actualizados = registrar_snapshot(db)
    assert (nuevos, actualizados) == (2, 0)

    por_clave = {h.clave: h for h in db.query(HistorialPrecio)}
    assert por_clave["ean:780111"].precio == 1090
    assert por_clave["ean:780222"].precio == 1500
    assert por_clave["ean:780111"].proveedor == "Jumbo"


def test_snapshot_es_idempotente_en_el_mismo_dia():
    db = crear_db()
    sembrar(db, [("Leche", "780111", "Jumbo", 1000, None)])

    assert registrar_snapshot(db) == (1, 0)
    # correr de nuevo el mismo dia no duplica
    assert registrar_snapshot(db) == (0, 0)
    assert db.query(HistorialPrecio).count() == 1

    # si el precio cambio, actualiza el punto del dia en vez de agregar otro
    db.query(Precio).first().precio_normal = 900
    db.commit()
    assert registrar_snapshot(db) == (0, 1)
    assert db.query(HistorialPrecio).count() == 1
    assert db.query(HistorialPrecio).first().precio == 900


def test_dias_distintos_acumulan_puntos():
    db = crear_db()
    sembrar(db, [("Leche", "780111", "Jumbo", 1000, None)])
    ayer = date.today() - timedelta(days=1)

    registrar_snapshot(db, fecha=ayer)
    registrar_snapshot(db, fecha=date.today())

    assert db.query(HistorialPrecio).count() == 2
    assert resumen(db) == (2, 2)   # 2 dias, 2 puntos


def test_el_historial_sobrevive_a_limpiar_la_base():
    """Lo que justifica todo el diseño: reconstruir borra productos y precios,
    y los ids cambian. El historial tiene que quedar en pie."""
    from app.reconstruir_base import limpiar_base

    db = crear_db()
    sembrar(db, [("Leche Colun 1 L", "780111", "Jumbo", 1000, None)])
    registrar_snapshot(db)
    assert db.query(HistorialPrecio).count() == 1

    limpiar_base(db)

    assert db.query(Producto).count() == 0      # productos borrados
    assert db.query(Precio).count() == 0        # precios borrados
    assert db.query(HistorialPrecio).count() == 1   # historial intacto
    guardado = db.query(HistorialPrecio).first()
    assert guardado.clave == "ean:780111" and guardado.precio == 1000
