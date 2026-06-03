from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app import models
from app.database import Base
from app.importar_csv import crear_session_local_para_db, importar_productos
from app.scripts.comparar_bd_actual_vs_reload import comparar
from app.scripts.crear_bd_reload_test import crear_bd_reload_test


CSV_HEADER = (
    "supermercado,categoria,subcategoria,nombre,marca,tipo,formato,"
    "precio_normal,precio_oferta,precio_referencia,promocion,url,imagen_url,producto_base\n"
)


def _write_csv(path: Path, rows: list[str]) -> None:
    path.write_text(CSV_HEADER + "".join(rows), encoding="utf-8")


def _crear_db(path: Path, categoria: str = "Bebidas") -> None:
    engine = create_engine(f"sqlite:///{path}", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = Session()
    try:
        supermercado = models.Supermercado(nombre="Jumbo")
        cat = models.Categoria(nombre=categoria)
        db.add_all([supermercado, cat])
        db.commit()
        sub = models.Subcategoria(nombre="Bebidas", categoria_id=cat.id)
        db.add(sub)
        db.commit()
        producto = models.Producto(
            nombre="Coca Cola Original 1.5 L",
            categoria_id=cat.id,
            subcategoria_id=sub.id,
            marca="Coca Cola",
            tipo="Bebida",
            formato="1.5 L",
            producto_base="coca_cola_original_15l",
        )
        db.add(producto)
        db.commit()
        db.add(models.Precio(producto_id=producto.id, supermercado_id=supermercado.id, precio_normal=1990))
        db.commit()
    finally:
        db.close()


def test_crear_bd_reload_test_en_ruta_paralela(tmp_path):
    db_path = tmp_path / "supercheck_reload_test.db"
    csv_path = tmp_path / "productos.csv"
    _write_csv(
        csv_path,
        [
            "Jumbo,Bebidas,Bebidas,Coca Cola Original 1.5 L,Coca Cola,Bebida,1.5 L,1990,,,,http://x,,coca_cola_original_15l\n",
        ],
    )

    resultado = crear_bd_reload_test(db_path, csv_path)

    assert db_path.exists()
    assert db_path.stat().st_size > 0
    assert resultado["filas_csv_procesadas"] == 1
    assert "supercheck_reload_test.db" in resultado["db_path"]


def test_importar_csv_acepta_db_destino_y_no_crea_supercheck_en_tmp(tmp_path):
    db_path = tmp_path / "destino.db"
    csv_path = tmp_path / "productos.csv"
    _write_csv(
        csv_path,
        [
            "Lider,Despensa,Fideos,Fideo Spaghetti 400 g,Carozzi,Fideos,400 g,1290,,,,http://x,,fideo_spaghetti_400g\n",
        ],
    )
    session_factory, target_engine = crear_session_local_para_db(db_path)

    total = importar_productos(csv_path, session_factory, target_engine)

    db = session_factory()
    try:
        assert total == 1
        assert db.query(models.Producto).count() == 1
        assert not (tmp_path / "supercheck.db").exists()
    finally:
        db.close()


def test_comparacion_actual_vs_reload_con_rutas_separadas(tmp_path, monkeypatch):
    actual_db = tmp_path / "actual.db"
    reload_db = tmp_path / "reload.db"
    reports_dir = tmp_path / "reports"
    _crear_db(actual_db, "Bebe")
    _crear_db(reload_db, "Bebidas")

    import app.scripts.comparar_bd_actual_vs_reload as modulo

    monkeypatch.setattr(modulo, "REPORTS_DIR", reports_dir)
    resultado = comparar(actual_db, reload_db)

    assert resultado["actual"]["productos"] == 1
    assert resultado["reload"]["productos"] == 1
    assert (reports_dir / "comparacion_actual_vs_reload.csv").exists()
    assert (reports_dir / "FASE_5G_RELOAD_TEST.pdf").exists()
