from pydantic import BaseModel
from typing import List


class ItemLista(BaseModel):
    nombre: str
    cantidad: int = 1


class ComparacionRequest(BaseModel):
    productos: List[ItemLista]