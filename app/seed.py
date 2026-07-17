import csv
from pathlib import Path

from .database import SessionLocal, Base, engine
from .models import Vertical, Proveedor, Categoria, Subcategoria, Producto, Precio


ROOT = Path(__file__).resolve().parent.parent
PRODUCTOS_CSV = ROOT / "data" / "productos.csv"


Base.metadata.create_all(bind=engine)


def get_or_create_vertical(db, nombre, slug):
    vertical = db.query(Vertical).filter(Vertical.slug == slug).first()
    if vertical:
        return vertical
    vertical = Vertical(nombre=nombre, slug=slug)
    db.add(vertical)
    db.commit()
    db.refresh(vertical)
    return vertical


def get_or_create_proveedor(db, nombre, vertical):
    proveedor = db.query(Proveedor).filter(Proveedor.nombre == nombre, Proveedor.vertical_id == vertical.id).first()
    if proveedor:
        return proveedor
    proveedor = Proveedor(nombre=nombre, vertical_id=vertical.id)
    db.add(proveedor)
    db.commit()
    db.refresh(proveedor)
    return proveedor


def get_or_create_categoria(db, nombre, vertical):
    categoria = db.query(Categoria).filter(Categoria.nombre == nombre, Categoria.vertical_id == vertical.id).first()
    if categoria:
        return categoria
    categoria = Categoria(nombre=nombre, vertical_id=vertical.id)
    db.add(categoria)
    db.commit()
    db.refresh(categoria)
    return categoria


def get_or_create_subcategoria(db, nombre, categoria):
    subcategoria = db.query(Subcategoria).filter(
        Subcategoria.nombre == nombre,
        Subcategoria.categoria_id == categoria.id
    ).first()
    if subcategoria:
        return subcategoria
    subcategoria = Subcategoria(nombre=nombre, categoria_id=categoria.id)
    db.add(subcategoria)
    db.commit()
    db.refresh(subcategoria)
    return subcategoria


def get_or_create_producto(db, row, categoria, subcategoria):
    producto = db.query(Producto).filter(Producto.nombre == row["nombre"]).first()
    if not producto:
        producto = Producto(nombre=row["nombre"])
        db.add(producto)
    producto.categoria_id = categoria.id
    producto.subcategoria_id = subcategoria.id
    producto.marca = row["marca"]
    producto.tipo = row["tipo"]
    producto.formato = row["formato"]
    db.commit()
    db.refresh(producto)
    return producto


def get_or_create_precio(db, producto, proveedor, precio_normal):
    precio = db.query(Precio).filter(
        Precio.producto_id == producto.id,
        Precio.proveedor_id == proveedor.id
    ).first()
    if not precio:
        precio = Precio(producto_id=producto.id, proveedor_id=proveedor.id)
        db.add(precio)
    precio.precio_normal = precio_normal
    db.commit()
    return precio


categorias_data = {
    "Frutas y Verduras": [
        "Frutas",
        "Verduras",
        "Ensaladas preparadas",
        "Frutos secos",
        "Hierbas y especias frescas"
    ],
    "Lácteos, Huevos y Congelados": [
        "Leche",
        "Yogurt",
        "Huevos",
        "Mantequilla y Margarina",
        "Cremas",
        "Postres refrigerados",
        "Helados",
        "Congelados"
    ],
    "Quesos y Fiambres": [
        "Quesos",
        "Jamón",
        "Cecinas",
        "Salames",
        "Patés",
        "Fiambres laminados"
    ],
    "Despensa": [
        "Arroz",
        "Aceite",
        "Fideos y Pastas",
        "Harina",
        "Azúcar y Endulzantes",
        "Conservas",
        "Salsas",
        "Legumbres",
        "Café, Té e Infusiones",
        "Cereales"
    ],
    "Carnes y Pescados": [
        "Vacuno",
        "Pollo",
        "Cerdo",
        "Pescados",
        "Mariscos",
        "Hamburguesas",
        "Embutidos"
    ],
    "Panadería y Pastelería": [
        "Pan",
        "Pan de molde",
        "Tortillas",
        "Queques",
        "Pasteles",
        "Masas"
    ],
    "Licores, Bebidas y Aguas": [
        "Bebidas",
        "Aguas",
        "Jugos",
        "Energéticas",
        "Cervezas",
        "Vinos",
        "Licores"
    ],
    "Chocolates, Galletas y Snacks": [
        "Chocolates",
        "Galletas",
        "Papas fritas",
        "Snacks salados",
        "Caramelos",
        "Barras de cereal"
    ],
    "Limpieza": [
        "Detergente",
        "Suavizante",
        "Lavalozas",
        "Limpiadores",
        "Cloro",
        "Desinfectantes",
        "Papel higiénico",
        "Toalla nova",
        "Bolsas de basura"
    ],
    "Cuidado Personal y Bebé": [
        "Shampoo",
        "Acondicionador",
        "Jabón",
        "Desodorante",
        "Pasta dental",
        "Pañales",
        "Toallitas húmedas",
        "Cuidado facial"
    ],
    "Mascotas": [
        "Alimento perros",
        "Alimento gatos",
        "Arena sanitaria",
        "Snacks mascotas",
        "Accesorios mascotas"
    ],
    "Hogar, Juguetería y Librería": [
        "Menaje",
        "Cocina",
        "Organización",
        "Juguetes",
        "Librería",
        "Pilas y baterías"
    ],
    "Farmacia": [
        "Vitaminas",
        "Primeros auxilios",
        "Dolor y fiebre",
        "Cuidado digestivo",
        "Cuidado respiratorio",
        "Dermocosmética"
    ]
}


def main():
    db = SessionLocal()
    try:
        vertical_super = get_or_create_vertical(db, "Supermercados", "supermercados")
        vertical_tech = get_or_create_vertical(db, "Tecnología", "tecnologia")
        vertical_mascotas = get_or_create_vertical(db, "Mascotas", "mascotas")
        vertical_vuelos = get_or_create_vertical(db, "Vuelos", "vuelos")
        vertical_hoteles = get_or_create_vertical(db, "Hoteles", "hoteles")

        lider = get_or_create_proveedor(db, "Líder", vertical_super)
        jumbo = get_or_create_proveedor(db, "Jumbo", vertical_super)
        unimarc = get_or_create_proveedor(db, "Unimarc", vertical_super)

        for nombre_categoria, lista_subcategorias in categorias_data.items():
            categoria = get_or_create_categoria(db, nombre_categoria, vertical_super)
            for nombre_subcategoria in lista_subcategorias:
                get_or_create_subcategoria(db, nombre_subcategoria, categoria)

        productos = []
        with PRODUCTOS_CSV.open("r", encoding="utf-8-sig", newline="") as archivo:
            reader = csv.DictReader(archivo)
            for row in reader:
                categoria = get_or_create_categoria(db, row["categoria"].strip(), vertical_super)
                subcategoria = get_or_create_subcategoria(db, row["subcategoria"].strip(), categoria)
                producto = get_or_create_producto(
                    db,
                    {
                        "nombre": row["nombre"].strip(),
                        "marca": row["marca"].strip(),
                        "tipo": row["tipo"].strip(),
                        "formato": row["formato"].strip()
                    },
                    categoria,
                    subcategoria
                )
                productos.append(producto)

        for producto in productos:
            get_or_create_precio(db, producto, lider, 1290)
            get_or_create_precio(db, producto, jumbo, 1390)
            get_or_create_precio(db, producto, unimarc, 1350)

        print(f"Datos cargados correctamente desde {PRODUCTOS_CSV}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
