from sqlalchemy import Column, Integer, String, Float, ForeignKey
from sqlalchemy.orm import relationship
from .database import Base


class Supermercado(Base):
    __tablename__ = "supermercados"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, nullable=False)


class Categoria(Base):
    __tablename__ = "categorias"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, nullable=False)


class Subcategoria(Base):
    __tablename__ = "subcategorias"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, nullable=False)
    categoria_id = Column(Integer, ForeignKey("categorias.id"))

    categoria = relationship("Categoria")


class Producto(Base):
    __tablename__ = "productos"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, nullable=False)

    categoria_id = Column(Integer, ForeignKey("categorias.id"))
    subcategoria_id = Column(Integer, ForeignKey("subcategorias.id"))

    marca = Column(String, nullable=True)
    tipo = Column(String, nullable=True)
    formato = Column(String, nullable=True)
    producto_base = Column(String, index=True, nullable=True)

    categoria = relationship("Categoria")
    subcategoria = relationship("Subcategoria")


class Precio(Base):
    __tablename__ = "precios"

    id = Column(Integer, primary_key=True, index=True)
    producto_id = Column(Integer, ForeignKey("productos.id"))
    supermercado_id = Column(Integer, ForeignKey("supermercados.id"))

    precio_normal = Column(Float)
    precio_oferta = Column(Float, nullable=True)
    precio_referencia = Column(String, nullable=True)
    promocion = Column(String, nullable=True)
    url_producto = Column(String, nullable=True)
    imagen_url = Column(String, nullable=True)

    producto = relationship("Producto")
    supermercado = relationship("Supermercado")
