from .database import SessionLocal, Base, engine
from .models import Precio, Producto, Subcategoria, Categoria, Proveedor, Vertical
from .importar_csv import importar_productos
from .fase5b_apply import seleccionar_cambios, aplicar_cambios
from .heredar_formato import heredar_formato_por_ean
from .historial_precios import registrar_snapshot, resumen


def limpiar_base(db):
    # OJO: historial_precios NO se limpia. Es la unica tabla que acumula entre
    # corridas; borrarla destruiria la historia de precios (y con ella la media
    # y las alertas). Ver app/historial_precios.py.
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

    # Formato via EAN: el mismo codigo de barras en otra cadena suele traer el
    # tamaño que a esta le falta (Lider a veces publica sin gramaje).
    db = SessionLocal()
    try:
        heredados = heredar_formato_por_ean(db)
        if heredados:
            print(f"Formato heredado via EAN en {heredados} productos.")
    finally:
        db.close()

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

    # Snapshot del dia: se corre al final, con los productos ya emparejados, para
    # que el historial quede con los EAN definitivos.
    db = SessionLocal()
    try:
        nuevos, actualizados = registrar_snapshot(db)
        dias, puntos = resumen(db)
        print(
            f"Historial de precios: +{nuevos} puntos nuevos, {actualizados} actualizados. "
            f"Acumulado: {puntos} puntos en {dias} dia(s)."
        )
    finally:
        db.close()


if __name__ == "__main__":
    reconstruir()
