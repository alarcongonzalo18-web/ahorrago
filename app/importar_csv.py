import csv
import re
import argparse
from pathlib import Path

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker

from .database import SessionLocal, Base, engine
from .models import Vertical, Proveedor, Categoria, Subcategoria, Producto, Precio
from .normalizacion import generar_producto_base
from .category_validator import is_valid_row

CSV_PATH = Path("data/productos_supermercados.csv")


def crear_engine_sqlite(db_path: Path):
    return create_engine(
        f"sqlite:///{db_path}",
        connect_args={"check_same_thread": False},
    )


def crear_session_local_para_db(db_path: Path):
    target_engine = crear_engine_sqlite(db_path)
    return sessionmaker(autocommit=False, autoflush=False, bind=target_engine), target_engine


def asegurar_columna_url_producto(target_engine=engine):
    columnas = [columna["name"] for columna in inspect(target_engine).get_columns("precios")]
    if "url_producto" in columnas:
        return
    with target_engine.begin() as conn:
        conn.execute(text("ALTER TABLE precios ADD COLUMN url_producto VARCHAR"))


def asegurar_columna_producto_base(target_engine=engine):
    columnas = [columna["name"] for columna in inspect(target_engine).get_columns("productos")]
    if "producto_base" in columnas:
        return
    with target_engine.begin() as conn:
        conn.execute(text("ALTER TABLE productos ADD COLUMN producto_base VARCHAR"))


def asegurar_columna_ean(target_engine=engine):
    columnas = [columna["name"] for columna in inspect(target_engine).get_columns("productos")]
    if "ean" in columnas:
        return
    with target_engine.begin() as conn:
        conn.execute(text("ALTER TABLE productos ADD COLUMN ean VARCHAR"))


def asegurar_columna_imagen_url(target_engine=engine):
    columnas = [columna["name"] for columna in inspect(target_engine).get_columns("precios")]
    if "imagen_url" in columnas:
        return
    with target_engine.begin() as conn:
        conn.execute(text("ALTER TABLE precios ADD COLUMN imagen_url VARCHAR"))


def asegurar_columna_precio_referencia(target_engine=engine):
    columnas = [columna["name"] for columna in inspect(target_engine).get_columns("precios")]
    if "precio_referencia" in columnas:
        return
    with target_engine.begin() as conn:
        conn.execute(text("ALTER TABLE precios ADD COLUMN precio_referencia VARCHAR"))


def limpiar_numero(valor):
    texto = str(valor or "").strip()
    if not texto:
        return None
    numeros = re.sub(r"[^0-9]", "", texto)
    return float(numeros) if numeros else None


def obtener_o_crear_vertical(db, nombre, slug):
    item = db.query(Vertical).filter(Vertical.slug == slug).first()
    if item:
        return item
    item = Vertical(nombre=nombre, slug=slug)
    db.add(item)
    db.flush()
    return item


def obtener_o_crear_proveedor(db, nombre, vertical_id):
    item = db.query(Proveedor).filter(Proveedor.nombre == nombre, Proveedor.vertical_id == vertical_id).first()
    if item:
        return item
    item = Proveedor(nombre=nombre, vertical_id=vertical_id)
    db.add(item)
    db.flush()
    return item


def obtener_o_crear_categoria(db, nombre, vertical_id):
    item = db.query(Categoria).filter(Categoria.nombre == nombre, Categoria.vertical_id == vertical_id).first()
    if item:
        return item
    item = Categoria(nombre=nombre, vertical_id=vertical_id)
    db.add(item)
    db.flush()
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
    db.flush()
    return item


def obtener_o_crear_producto(db, nombre, categoria_id, subcategoria_id, marca, tipo, formato):
    item = db.query(Producto).filter(Producto.nombre == nombre).first()
    if item:
        item.categoria_id = categoria_id
        item.subcategoria_id = subcategoria_id
        item.marca = marca
        item.tipo = tipo
        item.formato = formato
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
    db.flush()
    return item


def importar_productos(csv_path: Path = CSV_PATH, session_factory=SessionLocal, target_engine=engine) -> int:
    Base.metadata.create_all(bind=target_engine)
    asegurar_columna_url_producto(target_engine)
    asegurar_columna_producto_base(target_engine)
    asegurar_columna_ean(target_engine)
    asegurar_columna_imagen_url(target_engine)
    asegurar_columna_precio_referencia(target_engine)

    if not csv_path.exists():
        print("No se encontro el archivo:", csv_path)
        return 0

    importados = 0
    rechazados = 0
    db = session_factory()
    try:
        vertical_supermercados = obtener_o_crear_vertical(db, "Supermercados", "supermercados")

        with open(csv_path, newline="", encoding="utf-8-sig") as archivo:
            lector = csv.DictReader(archivo)

            for fila in lector:
                if not is_valid_row(fila, "importar_csv", Path("reports") / "pipeline_category_rejections.csv"):
                    rechazados += 1
                    continue
                proveedor = obtener_o_crear_proveedor(db, fila["supermercado"].strip(), vertical_supermercados.id)
                categoria = obtener_o_crear_categoria(db, fila["categoria"].strip(), vertical_supermercados.id)
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
                ean = (fila.get("ean") or "").strip()
                if ean:
                    producto.ean = ean

                precio_normal = limpiar_numero(fila.get("precio_normal")) or limpiar_numero(fila.get("precio")) or 0
                precio_oferta = limpiar_numero(fila.get("precio_oferta"))

                if precio_oferta and precio_oferta >= precio_normal:
                    precio_oferta = None

                precio_existente = db.query(Precio).filter(
                    Precio.producto_id == producto.id,
                    Precio.proveedor_id == proveedor.id
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
                        proveedor_id=proveedor.id,
                        precio_normal=precio_normal,
                        precio_oferta=precio_oferta,
                        precio_referencia=fila.get("precio_referencia"),
                        promocion=fila.get("promocion"),
                        url_producto=fila.get("url"),
                        imagen_url=fila.get("imagen_url")
                    )
                    db.add(nuevo_precio)

                importados += 1
                if importados % 500 == 0:
                    db.commit()

        db.commit()
        unificados = unificar_producto_base_por_ean(db)
        if unificados:
            print(f"Grupos unificados por EAN: {unificados} productos.")
        print("Productos importados correctamente.")
        if rechazados:
            print(f"Filas rechazadas por categoria imposible: {rechazados}")
        return importados
    finally:
        db.close()


def unificar_producto_base_por_ean(db):
    """Mismo EAN = mismo producto: unifica producto_base como 'ean:<codigo>'.

    Solo actua cuando 2+ productos comparten EAN. Un producto con EAN unico
    conserva su producto_base textual — aislarlo en un grupo propio le
    quitaria los matches por texto que ya tiene, y el EAN guardado queda
    listo para cuando otra fuente traiga el mismo codigo.
    """
    filas = db.query(Producto.ean, Producto.id).filter(
        Producto.ean.isnot(None), Producto.ean != ""
    ).all()
    por_ean = {}
    for ean, pid in filas:
        por_ean.setdefault(ean, []).append(pid)

    unificados = 0
    for ean, ids in por_ean.items():
        if len(ids) < 2:
            continue
        base = f"ean:{ean}"
        for producto in db.query(Producto).filter(Producto.id.in_(ids)):
            if producto.producto_base != base:
                producto.producto_base = base
                unificados += 1
    db.commit()
    return unificados


def main() -> int:
    parser = argparse.ArgumentParser(description="Importa productos desde CSV a una BD SQLite.")
    parser.add_argument("--db", default=None, help="Ruta de BD destino. Por defecto usa supercheck.db.")
    parser.add_argument("--csv", default=str(CSV_PATH), help="Ruta del CSV de productos.")
    args = parser.parse_args()

    if args.db:
        session_factory, target_engine = crear_session_local_para_db(Path(args.db))
    else:
        session_factory, target_engine = SessionLocal, engine

    total = importar_productos(Path(args.csv), session_factory, target_engine)
    print(f"Filas procesadas: {total}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
