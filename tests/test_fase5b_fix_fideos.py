import csv

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base
from app.models import Categoria, Producto, Subcategoria
from app.scripts.auditoria_categorias import auditar_categorias, escribir_reportes
from app.scripts.fix_fideos_limpieza_fase5b import EXPECTED_IDS, aplicar_fix
from app.scripts.rollback_fix_fideos_fase5b import aplicar_rollback


def crear_db_fix():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    db = Session()

    limpieza = Categoria(nombre="Limpieza")
    despensa = Categoria(nombre="Despensa")
    mascotas = Categoria(nombre="Mascotas")
    blanqueadores = Subcategoria(nombre="Blanqueadores", categoria=limpieza)
    detergentes = Subcategoria(nombre="Detergentes", categoria=limpieza)
    fideos = Subcategoria(nombre="Fideos", categoria=despensa)
    alimento_perros = Subcategoria(nombre="Alimento Perros", categoria=mascotas)
    db.add_all([limpieza, despensa, mascotas, blanqueadores, detergentes, fideos, alimento_perros])
    db.flush()

    for producto_id in sorted(EXPECTED_IDS):
        db.add(Producto(
            id=producto_id,
            nombre=f"Fideo Pasta Test {producto_id} Bolsa 400 g",
            marca="Sin marca",
            formato="400 g",
            producto_base="limpieza_400_g",
            categoria=limpieza,
            subcategoria=blanqueadores,
        ))

    detergente = Producto(
        id=90001,
        nombre="Blanqueador Ropa Test 1 L",
        marca="Test",
        formato="1 L",
        producto_base="limpieza_blanqueador_test_1000_ml",
        categoria=limpieza,
        subcategoria=detergentes,
    )
    mascota = Producto(
        id=90002,
        nombre="Alimento Perro Adulto Test 15 kg",
        marca="Test",
        formato="15 kg",
        producto_base="mascotas_perro_test_15kg",
        categoria=mascotas,
        subcategoria=alimento_perros,
    )
    db.add_all([detergente, mascota])
    db.commit()
    return db


def leer_trace(path):
    with path.open(newline="", encoding="utf-8-sig") as archivo:
        return list(csv.DictReader(archivo))


def test_fix_corrige_solo_los_25_ids_y_no_toca_otros(tmp_path):
    db = crear_db_fix()
    trace = tmp_path / "fix.csv"
    try:
        result = aplicar_fix(db, trace_path=trace, crear_backup_previo=False)
        assert result.aplicados == 25
        assert {int(row["producto_id"]) for row in leer_trace(trace)} == EXPECTED_IDS

        residuales = db.query(Producto).join(Categoria).join(Subcategoria).filter(
            Categoria.nombre == "Limpieza",
            Subcategoria.nombre == "Blanqueadores",
            Producto.id.in_(sorted(EXPECTED_IDS)),
        ).count()
        assert residuales == 0

        for producto_id in EXPECTED_IDS:
            producto = db.get(Producto, producto_id)
            assert producto.categoria.nombre == "Despensa"
            assert producto.subcategoria.nombre == "Fideos"
            assert producto.producto_base.startswith("fideo_pasta_")

        assert db.get(Producto, 90001).producto_base == "limpieza_blanqueador_test_1000_ml"
        assert db.get(Producto, 90001).categoria.nombre == "Limpieza"
        assert db.get(Producto, 90002).producto_base == "mascotas_perro_test_15kg"
        assert db.get(Producto, 90002).categoria.nombre == "Mascotas"
    finally:
        db.close()


def test_fix_es_idempotente_y_rollback_especifico_funciona(tmp_path):
    db = crear_db_fix()
    trace = tmp_path / "fix.csv"
    try:
        primero = aplicar_fix(db, trace_path=trace, crear_backup_previo=False)
        segundo = aplicar_fix(db, trace_path=trace, crear_backup_previo=False)
        assert primero.aplicados == 25
        assert segundo.aplicados == 0
        assert segundo.noop == 25

        revertidos = aplicar_rollback(db, trace_path=trace)
        assert revertidos == 25
        for producto_id in EXPECTED_IDS:
            producto = db.get(Producto, producto_id)
            assert producto.categoria.nombre == "Limpieza"
            assert producto.subcategoria.nombre == "Blanqueadores"
            assert producto.producto_base == "limpieza_400_g"

        revertidos_segunda = aplicar_rollback(db, trace_path=trace)
        assert revertidos_segunda == 0
    finally:
        db.close()


def test_auditoria_categorias_detecta_incompatibilidades_y_escribe_reportes(tmp_path):
    db = crear_db_fix()
    try:
        hallazgos = auditar_categorias(db)
        escribir_reportes(hallazgos, tmp_path)
    finally:
        db.close()

    assert any(item["regla"] == "alimento_en_limpieza" for item in hallazgos)
    assert (tmp_path / "auditoria_categorias.md").exists()
    assert (tmp_path / "auditoria_categorias.csv").exists()
