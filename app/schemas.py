from pydantic import BaseModel, Field, validator
from typing import List


class ItemLista(BaseModel):
    nombre: str
    cantidad: int = 1


class ComparacionRequest(BaseModel):
    productos: List[ItemLista]


class ItemCarrito(BaseModel):
    producto_id: int
    cantidad: int = Field(default=1, ge=1, le=99)


class ResumenCompraRequest(BaseModel):
    items: List[ItemCarrito]

    @validator("items")
    def items_no_vacios_y_consolidados(cls, v):
        if not v:
            raise ValueError("items no puede estar vacío")
        consolidado = {}
        for item in v:
            if item.producto_id in consolidado:
                consolidado[item.producto_id] += item.cantidad
            else:
                consolidado[item.producto_id] = item.cantidad
        return [ItemCarrito(producto_id=pid, cantidad=cant)
                for pid, cant in consolidado.items()]