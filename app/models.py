from sqlalchemy import Column, Integer, String, Float, ForeignKey
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
