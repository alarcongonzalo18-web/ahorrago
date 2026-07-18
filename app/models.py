from sqlalchemy import Column, Date, Integer, String, Float, ForeignKey, Index
from sqlalchemy.orm import relationship
from .database import Base


class Vertical(Base):
    __tablename__ = "verticales"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, nullable=False, unique=True)
    slug = Column(String, nullable=False, unique=True)  # e.g., 'supermercados', 'tecnologia', 'mascotas'


class Proveedor(Base):
    __tablename__ = "proveedores"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, nullable=False)
    vertical_id = Column(Integer, ForeignKey("verticales.id"))

    vertical = relationship("Vertical")


class Categoria(Base):
    __tablename__ = "categorias"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, nullable=False)
    vertical_id = Column(Integer, ForeignKey("verticales.id"))

    vertical = relationship("Vertical")


class Subcategoria(Base):
    __tablename__ = "subcategorias"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, nullable=False)
    categoria_id = Column(Integer, ForeignKey("categorias.id"))

    categoria = relationship("Categoria")


class Producto(Base):
    __tablename__ = "productos"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, nullable=False, index=True)

    categoria_id = Column(Integer, ForeignKey("categorias.id"))
    subcategoria_id = Column(Integer, ForeignKey("subcategorias.id"))

    marca = Column(String, nullable=True)
    tipo = Column(String, nullable=True)
    formato = Column(String, nullable=True)
    producto_base = Column(String, index=True, nullable=True)
    # Codigo de barras normalizado (sin ceros a la izquierda). Mismo ean =
    # mismo producto por definicion, sin importar como lo nombre cada tienda.
    ean = Column(String, index=True, nullable=True)

    categoria = relationship("Categoria")
    subcategoria = relationship("Subcategoria")


class Precio(Base):
    __tablename__ = "precios"

    id = Column(Integer, primary_key=True, index=True)
    producto_id = Column(Integer, ForeignKey("productos.id"), index=True)
    proveedor_id = Column(Integer, ForeignKey("proveedores.id"), index=True)

    precio_normal = Column(Float)
    precio_oferta = Column(Float, nullable=True)
    precio_referencia = Column(String, nullable=True)
    promocion = Column(String, nullable=True)
    url_producto = Column(String, nullable=True)
    imagen_url = Column(String, nullable=True)

    producto = relationship("Producto")
    proveedor = relationship("Proveedor")


class HistorialPrecio(Base):
    """Un punto de precio por producto, proveedor y dia.

    OJO con el diseno: `reconstruir_base` borra y recrea productos/precios en
    cada corrida, asi que los ids CAMBIAN todas las noches. Por eso el historial
    no referencia producto_id ni proveedor_id, sino identificadores estables:
    el EAN (o el nombre normalizado si no hay) y el nombre del proveedor.

    Esta tabla NO se limpia en `limpiar_base`: es la unica que acumula. Sin ella
    no hay media historica y por lo tanto no hay alertas de "bajo de precio"
    (ver docs/roadmap-producto.md).
    """

    __tablename__ = "historial_precios"

    id = Column(Integer, primary_key=True, index=True)
    # clave estable: "ean:<codigo>" o "nombre:<normalizado>" si el producto no tiene EAN
    clave = Column(String, nullable=False, index=True)
    ean = Column(String, nullable=True, index=True)
    producto_nombre = Column(String, nullable=True)
    proveedor = Column(String, nullable=False, index=True)
    precio = Column(Float, nullable=False)
    fecha = Column(Date, nullable=False, index=True)


# Un solo punto por clave/proveedor/dia: si el pipeline corre dos veces el mismo
# dia, el segundo snapshot actualiza en vez de duplicar.
Index(
    "ix_historial_unico",
    HistorialPrecio.clave,
    HistorialPrecio.proveedor,
    HistorialPrecio.fecha,
    unique=True,
)
