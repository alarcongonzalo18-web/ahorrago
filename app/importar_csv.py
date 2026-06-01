import csv
import re
from pathlib import Path

from sqlalchemy import inspect, text

from .database import SessionLocal, Base, engine
from .models import Supermercado, Categoria, Subcategoria, Producto, Precio
from .normalizacion import generar_producto_base


Base.metadata.create_all(bind=engine)

CSV_PATH = Path("data/productos_supermercados.csv")


def asegurar_columna_url_producto():
    columnas = [columna["name"] for columna in inspect(engine).get_columns("precios")]

    if "url_producto" in columnas:
        return

    with engine.begin() as conn:
        conn.execute(text("ALTER TABLE precios ADD COLUMN url_producto VARCHAR"))


def asegurar_columna_producto_base():
    columnas = [columna["name"] for columna in inspect(engine).get_columns("productos")]

    if "producto_base" in columnas:
        return

    with engine.begin() as conn:
        conn.execute(text("ALTER TABLE productos ADD COLUMN producto_base VARCHAR"))


def asegurar_columna_imagen_url():
    columnas = [columna["name"] for columna in inspect(engine).get_columns("precios")]

    if "imagen_url" in columnas:
        return

    with engine.begin() as conn:
        conn.execute(text("ALTER TABLE precios ADD COLUMN imagen_url VARCHAR"))


def asegurar_columna_precio_referencia():
    columnas = [columna["name"] for columna in inspect(engine).get_columns("precios")]

    if "precio_referencia" in columnas:
        return

    with engine.begin() as conn:
        conn.execute(text("ALTER TABLE precios ADD COLUMN precio_referencia VARCHAR"))


def limpiar_numero(valor):
    texto = str(valor or "").strip()
    if not texto:
        return None

    numeros = re.sub(r"[^0-9]", "", texto)
    return float(numeros) if numeros else None


def obtener_o_crear_supermercado(db, nombre):
    item = db.query(Supermercado).filter(Supermercado.nombre == nombre).first()
    if item:
        return item

    item = Supermercado(nombre=nombre)
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


def obtener_o_crear_categoria(db, nombre):
    item = db.query(Categoria).filter(Categoria.nombre == nombre).first()
    if item:
        return item

    item = Categoria(nombre=nombre)
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


def obtener_o_crear_subcategoria(db, nombre, categoria_id):
    item = db.query(Subcategoria).filter(
        Subcategoria.nombre == nombre,
        Subcategoria.categoria_id == categoria_id
    ).first()

    if item:
        return item

    item = Subcategoria(nombre=nombre, categoria_id=categoria_id)
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


def obtener_o_crear_producto(db, nombre, categoria_id, subcategoria_id, marca, tipo, formato):
    item = db.query(Producto).filter(Producto.nombre == nombre).first()
    if item:
        item.categoria_id = categoria_id
        item.subcategoria_id = subcategoria_id
        item.marca = marca
        item.tipo = tipo
        item.formato = formato
        db.commit()
        db.refresh(item)
        return item

    item = Producto(
        nombre=nombre,
        categoria_id=categoria_id,
        subcategoria_id=subcategoria_id,
        marca=marca,
        tipo=tipo,
        formato=formato
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


def importar_productos():
    asegurar_columna_url_producto()
    asegurar_columna_producto_base()
    asegurar_columna_imagen_url()
    asegurar_columna_precio_referencia()

    if not CSV_PATH.exists():
        print("No se encontro el archivo:", CSV_PATH)
        return

    db = SessionLocal()
    try:
        with open(CSV_PATH, newline="", encoding="utf-8-sig") as archivo:
            lector = csv.DictReader(archivo)

            for fila in lector:
                supermercado = obtener_o_crear_supermercado(db, fila["supermercado"].strip())
                categoria = obtener_o_crear_categoria(db, fila["categoria"].strip())
                subcategoria = obtener_o_crear_subcategoria(
                    db,
                    fila["subcategoria"].strip(),
                    categoria.id
                )

                producto = obtener_o_crear_producto(
                    db,
                    nombre=fila["nombre"].strip(),
                    categoria_id=categoria.id,
                    subcategoria_id=subcategoria.id,
                    marca=fila["marca"].strip(),
                    tipo=fila["tipo"].strip(),
                    formato=fila["formato"].strip()
                )
                producto_base_csv = (fila.get("producto_base") or "").strip()
                producto.producto_base = producto_base_csv or generar_producto_base(
                    fila["nombre"],
                    fila["marca"],
                    fila["tipo"],
                    fila["formato"]
                )
                db.commit()

                precio_normal = limpiar_numero(fila.get("precio_normal")) or limpiar_numero(fila.get("precio")) or 0
                precio_oferta = limpiar_numero(fila.get("precio_oferta"))

                if precio_oferta and precio_oferta >= precio_normal:
                    precio_oferta = None

                precio_existente = db.query(Precio).filter(
                    Precio.producto_id == producto.id,
                    Precio.supermercado_id == supermercado.id
                ).first()

                if precio_existente:
                    precio_existente.precio_normal = precio_normal
                    precio_existente.precio_oferta = precio_oferta
                    precio_existente.precio_referencia = fila.get("precio_referencia")
                    precio_existente.promocion = fila.get("promocion")
                    precio_existente.url_producto = fila.get("url")
                    precio_existente.imagen_url = fila.get("imagen_url")
                else:
                    nuevo_precio = Precio(
                        producto_id=producto.id,
                        supermercado_id=supermercado.id,
                        precio_normal=precio_normal,
                        precio_oferta=precio_oferta,
                        precio_referencia=fila.get("precio_referencia"),
                        promocion=fila.get("promocion"),
                        url_producto=fila.get("url"),
                        imagen_url=fila.get("imagen_url")
                    )
                    db.add(nuevo_precio)

                db.commit()

        print("Productos importados correctamente.")
    finally:
        db.close()


if __name__ == "__main__":
    importar_productos()
