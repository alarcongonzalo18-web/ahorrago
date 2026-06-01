from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base
from app.matching import candidato_compatible
from app.matching_diagnostics import clasificar_conflicto, diagnosticar_matching, metricas_por_categoria
from app.models import Categoria, Precio, Producto, Supermercado
from app.normalizacion import extraer_atributos, normalizar_formato
from app.scripts.simular_reconstruccion_producto_base import simular


def producto(nombre, marca, formato, producto_base=""):
    return Producto(nombre=nombre, marca=marca, tipo="general", formato=formato, producto_base=producto_base)


def crear_db():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    db = Session()
    categoria = Categoria(nombre="Bebidas")
    lider = Supermercado(nombre="Lider")
    jumbo = Supermercado(nombre="Jumbo")
    a = producto("Bebida Coca Cola 1.5 L", "Coca Cola", "1.5 L", "bebida_coca_1500")
    b = producto("Coca-Cola Bebida 1500 ml", "Coca-Cola", "1500 ml", "bebida_coca_1500")
    c = producto("Aceite Natura 250 ml", "Natura", "250 ml", "aceite_natura_250")
    db.add_all([categoria, lider, jumbo, a, b, c])
    db.flush()
    for item in [a, b, c]:
        item.categoria_id = categoria.id
    db.add_all([
        Precio(producto=a, supermercado=lider, precio_normal=1500),
        Precio(producto=b, supermercado=jumbo, precio_normal=1490),
        Precio(producto=c, supermercado=lider, precio_normal=900),
    ])
    db.commit()
    return db


def test_clasificar_conflicto_detecta_formato_y_volumen():
    row = {
        "motivos": "formatos incompatibles",
        "marcas": "soprole",
        "formatos": "0.2l;1l",
        "cantidad_productos": "2",
        "producto_base": "leche_soprole",
        "muestra_nombres": "Leche Soprole 200 ml | Leche Soprole 1 L",
    }
    clases = clasificar_conflicto(row)
    assert "formato distinto" in clases
    assert "volumen distinto" in clases
    assert "posible falso positivo" in clases


def test_metricas_por_categoria_y_diagnostico(tmp_path):
    db = crear_db()
    try:
        conflictos = [{
            "productos_ids": "1;2",
            "motivos": "formatos incompatibles",
            "marcas": "coca-cola",
            "formatos": "1.5l;1.5l",
            "cantidad_productos": "2",
            "muestra_nombres": "Bebida Coca Cola 1.5 L | Coca-Cola Bebida 1500 ml",
        }]
        metricas = metricas_por_categoria(db, conflictos)
        assert metricas[0]["categoria"] == "Bebidas"
        assert metricas[0]["productos_totales"] == 3
        resumen = diagnosticar_matching(db, tmp_path)
        assert resumen["total_productos"] == 3
        assert (tmp_path / "diagnostico_matching.md").exists()
        assert (tmp_path / "equivalencias_por_categoria.csv").exists()
    finally:
        db.close()


def test_simulacion_reconstruccion_no_modifica_db():
    db = crear_db()
    try:
        original = {p.id: p.producto_base for p in db.query(Producto).all()}
        filas, resumen = simular(db)
        despues = {p.id: p.producto_base for p in db.query(Producto).all()}
        assert original == despues
        assert resumen["productos_evaluados"] == 3
        assert filas
    finally:
        db.close()


def test_nuevas_reglas_normalizacion_y_falsos_positivos():
    assert normalizar_formato("3L") == normalizar_formato("3000ml")
    assert normalizar_formato("170g") == normalizar_formato("0.17kg")
    assert normalizar_formato("15kg") == normalizar_formato("15000g")
    assert normalizar_formato("12 rollos") == normalizar_formato("pack 12")
    assert extraer_atributos("Papel Higienico Elite 12 rollos")["cantidad"] == 12

    assert candidato_compatible(
        producto("Detergente Liquido Omo 3 L", "Omo", "3 L"),
        producto("Detergente Líquido Omo 3000 ml", "Omo", "3000 ml"),
    )
    assert not candidato_compatible(
        producto("Aceite Natura Maravilla 1 L", "Natura", "1 L"),
        producto("Aceite Natura Maravilla 250 ml", "Natura", "250 ml"),
    )
