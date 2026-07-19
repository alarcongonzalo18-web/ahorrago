from app.heredar_formato import heredar_formato_por_ean
from app.database import SessionLocal
from app import models


def _producto(db, nombre, ean, formato=""):
    p = models.Producto(nombre=nombre, ean=ean, formato=formato, producto_base=f"ean:{ean}")
    db.add(p)
    return p


def test_hereda_del_hermano_con_formato(tmp_path):
    import sqlalchemy
    from sqlalchemy.orm import sessionmaker
    engine = sqlalchemy.create_engine(f"sqlite:///{tmp_path/'t.db'}")
    models.Base.metadata.create_all(engine)
    db = sessionmaker(bind=engine)()

    _producto(db, "Trencito Caja", "111")                      # sin formato
    _producto(db, "Trencito 200 ml", "111", formato="200 mL")  # dona
    _producto(db, "Otro sin datos", "222")                     # nadie dona
    con_previo = _producto(db, "Ya tenia", "111", formato="1 L")
    db.commit()

    assert heredar_formato_por_ean(db) == 1

    heredado = db.query(models.Producto).filter_by(nombre="Trencito Caja").one()
    assert heredado.formato == "200 mL"
    # el que ya tenia formato no se toca, y el EAN sin donante queda vacio
    assert con_previo.formato == "1 L"
    assert db.query(models.Producto).filter_by(ean="222").one().formato == ""
