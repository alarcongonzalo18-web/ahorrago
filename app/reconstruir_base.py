from .database import SessionLocal, Base, engine
from .models import Precio, Producto, Subcategoria, Categoria, Supermercado
from .importar_csv import importar_productos


def limpiar_base(db):
    db.query(Precio).delete()
    db.query(Producto).delete()
    db.query(Subcategoria).delete()
    db.query(Categoria).delete()
    db.query(Supermercado).delete()
    db.commit()


def reconstruir():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    try:
        limpiar_base(db)
    finally:
        db.close()

    importar_productos()
    print("Base reconstruida desde data/productos_supermercados.csv")


if __name__ == "__main__":
    reconstruir()
