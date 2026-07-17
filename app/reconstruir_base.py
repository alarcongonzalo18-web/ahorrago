from .database import SessionLocal, Base, engine
from .models import Precio, Producto, Subcategoria, Categoria, Proveedor, Vertical
from .importar_csv import importar_productos
from .fase5b_apply import seleccionar_cambios, aplicar_cambios


def limpiar_base(db):
    db.query(Precio).delete()
    db.query(Producto).delete()
    db.query(Subcategoria).delete()
    db.query(Categoria).delete()
    db.query(Proveedor).delete()
    db.query(Vertical).delete()
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
    
    print("Aplicando emparejamiento avanzado (fase 5b)...")
    db = SessionLocal()
    try:
        cambios = seleccionar_cambios(db, riesgos=set())
        if cambios:
            aplicados = aplicar_cambios(db, cambios)
            print(f"Emparejamiento avanzado completado. {aplicados} productos actualizados.")
        else:
            print("No se encontraron mejoras de emparejamiento seguras.")
    finally:
        db.close()


if __name__ == "__main__":
    reconstruir()
