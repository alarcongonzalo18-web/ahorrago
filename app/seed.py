import csv
from pathlib import Path

from .database import SessionLocal, Base, engine
from .models import Supermercado, Categoria, Subcategoria, Producto, Precio


ROOT = Path(__file__).resolve().parent.parent
PRODUCTOS_CSV = ROOT / "data" / "productos.csv"


Base.metadata.create_all(bind=engine)

db = SessionLocal()


def get_or_create_supermercado(nombre):
    supermercado = db.query(Supermercado).filter(Supermercado.nombre == nombre).first()

    if supermercado:
        return supermercado

    supermercado = Supermercado(nombre=nombre)
    db.add(supermercado)
    db.commit()
    db.refresh(supermercado)
    return supermercado


def get_or_create_categoria(nombre):
    categoria = db.query(Categoria).filter(Categoria.nombre == nombre).first()

    if categoria:
        return categoria

    categoria = Categoria(nombre=nombre)
    db.add(categoria)
    db.commit()
    db.refresh(categoria)
    return categoria


def get_or_create_subcategoria(nombre, categoria):
    subcategoria = db.query(Subcategoria).filter(
        Subcategoria.nombre == nombre,
        Subcategoria.categoria_id == categoria.id
    ).first()

    if subcategoria:
        return subcategoria

    subcategoria = Subcategoria(
        nombre=nombre,
        categoria_id=categoria.id
    )
    db.add(subcategoria)
    db.commit()
    db.refresh(subcategoria)
    return subcategoria


def get_or_create_producto(row, categoria, subcategoria):
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


def get_or_create_precio(producto, supermercado, precio_normal):
    precio = db.query(Precio).filter(
        Precio.producto_id == producto.id,
        Precio.supermercado_id == supermercado.id
    ).first()

    if not precio:
        precio = Precio(
            producto_id=producto.id,
            supermercado_id=supermercado.id
        )
        db.add(precio)

    precio.precio_normal = precio_normal
    db.commit()
    return precio


# Supermercados base
lider = get_or_create_supermercado("Líder")
jumbo = get_or_create_supermercado("Jumbo")
unimarc = get_or_create_supermercado("Unimarc")


# Categorias base
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

for nombre_categoria, lista_subcategorias in categorias_data.items():
    categoria = get_or_create_categoria(nombre_categoria)

    for nombre_subcategoria in lista_subcategorias:
        get_or_create_subcategoria(nombre_subcategoria, categoria)


if not PRODUCTOS_CSV.exists():
    raise FileNotFoundError(f"No existe el archivo CSV: {PRODUCTOS_CSV}")

productos = []

with PRODUCTOS_CSV.open("r", encoding="utf-8-sig", newline="") as archivo:
    reader = csv.DictReader(archivo)

    for row in reader:
        categoria = get_or_create_categoria(row["categoria"].strip())
        subcategoria = get_or_create_subcategoria(row["subcategoria"].strip(), categoria)
        producto = get_or_create_producto(
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


# Precios de prueba
for producto in productos:
    get_or_create_precio(producto, lider, 1290)
    get_or_create_precio(producto, jumbo, 1390)
    get_or_create_precio(producto, unimarc, 1350)


db.close()

print(f"Datos cargados correctamente desde {PRODUCTOS_CSV}")
