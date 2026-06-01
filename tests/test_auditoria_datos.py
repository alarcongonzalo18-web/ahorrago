from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base
from app.models import Categoria, Precio, Producto, Subcategoria, Supermercado
from app.scripts.auditoria_datos import ejecutar_auditoria, escribir_reportes


def crear_db_auditoria():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    return Session()


def cargar_datos_sospechosos(db):
    categoria = Categoria(nombre="Despensa")
    subcategoria = Subcategoria(nombre="Leche", categoria=categoria)
    lider = Supermercado(nombre="Lider")
    jumbo = Supermercado(nombre="Jumbo")
    db.add_all([categoria, subcategoria, lider, jumbo])
    db.flush()

    leche_a = Producto(
        nombre="Leche Soprole Entera 1L",
        marca="Soprole",
        formato="1 L",
        producto_base="leche_conflictiva",
        categoria=categoria,
        subcategoria=subcategoria,
    )
    leche_b = Producto(
        nombre="Leche Colun Entera 1L",
        marca="Colun",
        formato="1 L",
        producto_base="leche_conflictiva",
        categoria=categoria,
        subcategoria=subcategoria,
    )
    duplicado_a = Producto(
        nombre="Arroz Test 1kg",
        marca="Test",
        formato="1 kg",
        producto_base="arroz_test_1kg",
        categoria=categoria,
        subcategoria=subcategoria,
    )
    duplicado_b = Producto(
        nombre="Arroz Test 1kg",
        marca="Test",
        formato="1 kg",
        producto_base="arroz_test_1kg",
        categoria=categoria,
        subcategoria=subcategoria,
    )
    sin_precio = Producto(
        nombre="Pan",
        marca="",
        formato="",
        producto_base="",
        categoria=categoria,
        subcategoria=subcategoria,
    )
    db.add_all([leche_a, leche_b, duplicado_a, duplicado_b, sin_precio])
    db.flush()

    db.add_all([
        Precio(producto=leche_a, supermercado=lider, precio_normal=1200),
        Precio(producto=leche_b, supermercado=jumbo, precio_normal=1300),
        Precio(producto=duplicado_a, supermercado=lider, precio_normal=0),
        Precio(producto=duplicado_b, supermercado_id=None, precio_normal=1800),
    ])
    db.commit()


def test_auditoria_detecta_riesgos_principales():
    db = crear_db_auditoria()
    try:
        cargar_datos_sospechosos(db)
        resultado = ejecutar_auditoria(db)
    finally:
        db.close()

    motivos = {item["motivo"] for item in resultado.productos_sospechosos}

    assert resultado.resumen["productos_totales"] == 5
    assert resultado.resumen["precios_totales"] == 4
    assert "producto sin precio" in motivos
    assert "precio en cero" in motivos
    assert "producto sin supermercado asociado" in motivos
    assert "producto_base faltante" in motivos
    assert resultado.productos_duplicados
    assert any("marcas distintas" in item["motivos"] for item in resultado.producto_base_conflictivos)


def test_auditoria_escribe_reportes(tmp_path):
    db = crear_db_auditoria()
    try:
        cargar_datos_sospechosos(db)
        resultado = ejecutar_auditoria(db)
        escribir_reportes(resultado, tmp_path)
    finally:
        db.close()

    assert (tmp_path / "auditoria_datos.md").exists()
    assert (tmp_path / "productos_duplicados.csv").exists()
    assert (tmp_path / "productos_sospechosos.csv").exists()
    assert (tmp_path / "producto_base_conflictivos.csv").exists()
    assert "Calidad estimada" in (tmp_path / "auditoria_datos.md").read_text(encoding="utf-8")
