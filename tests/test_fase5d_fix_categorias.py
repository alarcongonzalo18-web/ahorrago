import csv

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base
from app.models import Categoria, Producto, Subcategoria
from app.scripts.aplicar_fix_categorias_fase5d import aplicar_fix
from app.scripts.auditoria_categorias import auditar_categorias
from app.scripts.rollback_fix_categorias_fase5d import aplicar_rollback


def crear_db_fase5d():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    db = Session()

    limpieza = Categoria(nombre="Limpieza")
    despensa = Categoria(nombre="Despensa")
    higiene = Categoria(nombre="Higiene Personal")
    mascotas = Categoria(nombre="Mascotas")
    blanqueadores = Subcategoria(nombre="Blanqueadores", categoria=limpieza)
    limpiadores = Subcategoria(nombre="Limpiadores", categoria=limpieza)
    fideos = Subcategoria(nombre="Fideos", categoria=despensa)
    cuidado_facial = Subcategoria(nombre="Cuidado Facial", categoria=higiene)
    shampoo = Subcategoria(nombre="Shampoo", categoria=higiene)
    alimento_perros = Subcategoria(nombre="Alimento Perros", categoria=mascotas)
    alimento_gatos = Subcategoria(nombre="Alimento Gatos", categoria=mascotas)
    db.add_all([
        limpieza,
        despensa,
        higiene,
        mascotas,
        blanqueadores,
        limpiadores,
        fideos,
        cuidado_facial,
        shampoo,
        alimento_perros,
        alimento_gatos,
    ])
    db.flush()

    productos = [
        Producto(id=1, nombre="Fideo Pasta Residual 400 g", producto_base="fideo_residual", categoria=limpieza, subcategoria=blanqueadores),
        Producto(id=2, nombre="Leche Limpiadora Nivea Facial 200 ml", producto_base="leche_limpiadora", categoria=limpieza, subcategoria=limpiadores),
        Producto(id=3, nombre="Shampoo Para Perro Canish 300 ml", producto_base="shampoo_perro", categoria=higiene, subcategoria=shampoo),
        Producto(id=4, nombre="Shampoo Hair Food Aguacate 300 ml", producto_base="hair_food", categoria=higiene, subcategoria=shampoo),
        Producto(id=5, nombre="Alimento Húmedo Perro Trocitos Jugosos 85 g", producto_base="alimento_perro", categoria=mascotas, subcategoria=alimento_perros),
        Producto(id=6, nombre="Pasta Limpiadora The Pink Stuff 500 g", producto_base="pink_stuff", categoria=limpieza, subcategoria=limpiadores),
        Producto(id=7, nombre="Betún Pasta Calzado Virginia Negro 80 ml", producto_base="betun", categoria=limpieza, subcategoria=limpiadores),
        Producto(id=8, nombre="Shampoo Gato Traper Neutro 260 cc", producto_base="shampoo_gato", categoria=higiene, subcategoria=shampoo),
    ]
    db.add_all(productos)
    db.commit()
    return db


def escribir_clasificacion(path):
    rows = [
        ("alimento_en_limpieza", 1, "Fideo Pasta Residual 400 g", "Limpieza", "Blanqueadores", "Despensa", "Alta", "Producto alimenticio tipo fideo/pasta"),
        ("alimento_en_limpieza", 2, "Leche Limpiadora Nivea Facial 200 ml", "Limpieza", "Limpiadores", "Higiene Personal", "Alta", "Producto de limpieza facial/cosmetica"),
        ("mascota_en_higiene", 3, "Shampoo Para Perro Canish 300 ml", "Higiene Personal", "Shampoo", "Mascotas", "Alta", "Producto de higiene para perro/gato"),
        ("mascota_en_higiene", 4, "Shampoo Hair Food Aguacate 300 ml", "Higiene Personal", "Shampoo", "Mascotas", "Alta", "Falso positivo"),
        ("bebida_en_mascotas", 5, "Alimento Húmedo Perro Trocitos Jugosos 85 g", "Mascotas", "Alimento Perros", "Bebidas", "Alta", "Falso positivo"),
        ("alimento_en_limpieza", 6, "Pasta Limpiadora The Pink Stuff 500 g", "Limpieza", "Limpiadores", "Despensa", "Alta", "Falso positivo"),
        ("alimento_en_limpieza", 7, "Betún Pasta Calzado Virginia Negro 80 ml", "Limpieza", "Limpiadores", "Despensa", "Alta", "Falso positivo"),
        ("mascota_en_higiene", 8, "Shampoo Gato Traper Neutro 260 cc", "Higiene Personal", "Shampoo", "Mascotas", "Alta", "Producto de higiene para gato"),
    ]
    fields = [
        "tipo_hallazgo",
        "producto_id",
        "producto_nombre",
        "categoria_actual",
        "subcategoria_actual",
        "categoria_sugerida",
        "confianza_correccion",
        "motivo",
    ]
    with path.open("w", newline="", encoding="utf-8-sig") as archivo:
        writer = csv.writer(archivo)
        writer.writerow(fields)
        writer.writerows(rows)


def test_fase5d_fix_aplica_solo_hallazgos_reales(tmp_path):
    db = crear_db_fase5d()
    clasificacion = tmp_path / "clasificacion.csv"
    trace = tmp_path / "trace.csv"
    escribir_clasificacion(clasificacion)
    try:
        result = aplicar_fix(db, clasificacion_path=clasificacion, trace_path=trace, crear_backup_previo=False)
        assert result.aplicados == 4

        assert db.get(Producto, 1).categoria.nombre == "Despensa"
        assert db.get(Producto, 1).subcategoria.nombre == "Fideos"
        assert db.get(Producto, 2).categoria.nombre == "Higiene Personal"
        assert db.get(Producto, 2).subcategoria.nombre == "Cuidado Facial"
        assert db.get(Producto, 3).categoria.nombre == "Mascotas"
        assert db.get(Producto, 3).subcategoria.nombre == "Alimento Perros"
        assert db.get(Producto, 8).categoria.nombre == "Mascotas"
        assert db.get(Producto, 8).subcategoria.nombre == "Alimento Gatos"
        assert db.get(Producto, 1).producto_base == "fideo_residual"

        assert db.get(Producto, 4).categoria.nombre == "Higiene Personal"
        assert db.get(Producto, 5).categoria.nombre == "Mascotas"
        assert db.get(Producto, 6).categoria.nombre == "Limpieza"
        assert db.get(Producto, 7).categoria.nombre == "Limpieza"
    finally:
        db.close()


def test_fase5d_fix_idempotente_y_rollback_especifico(tmp_path):
    db = crear_db_fase5d()
    clasificacion = tmp_path / "clasificacion.csv"
    trace = tmp_path / "trace.csv"
    escribir_clasificacion(clasificacion)
    try:
        primero = aplicar_fix(db, clasificacion_path=clasificacion, trace_path=trace, crear_backup_previo=False)
        segundo = aplicar_fix(db, clasificacion_path=clasificacion, trace_path=trace, crear_backup_previo=False)
        assert primero.aplicados == 4
        assert segundo.aplicados == 0
        assert segundo.noop == 4

        revertidos = aplicar_rollback(db, trace_path=trace)
        assert revertidos == 4
        assert db.get(Producto, 1).categoria.nombre == "Limpieza"
        assert db.get(Producto, 2).categoria.nombre == "Limpieza"
        assert db.get(Producto, 3).categoria.nombre == "Higiene Personal"
        assert db.get(Producto, 8).categoria.nombre == "Higiene Personal"
        assert aplicar_rollback(db, trace_path=trace) == 0
    finally:
        db.close()


def test_auditoria_categorias_reduce_falsos_positivos():
    db = crear_db_fase5d()
    try:
        hallazgos = auditar_categorias(db)
    finally:
        db.close()

    ids = {item["producto_id"] for item in hallazgos}
    assert ids == {1, 2, 3, 8}
    assert 4 not in ids
    assert 5 not in ids
    assert 6 not in ids
    assert 7 not in ids
