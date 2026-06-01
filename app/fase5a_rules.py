from __future__ import annotations

import re

from app.matching import candidato_compatible, matching_score
from app.normalizacion import extraer_atributos, normalizar_marca, normalizar_texto, tokens_utiles


CATEGORIAS_OBJETIVO = {"Bebidas", "Limpieza", "Higiene Personal", "Bebe", "Mascotas"}
CATEGORIAS_EXCLUIDAS = {"Frutas y Verduras", "Carnes y Pescados", "Panaderia", "Congelados"}

BEBIDAS_SABORES = [
    "cola", "limon", "naranja", "ginger", "tonica", "pomelo", "papaya",
    "piña", "pina", "uva", "durazno", "manzana", "frutilla",
]
AROMAS = [
    "lavanda", "limon", "citrus", "floral", "flores", "vainilla", "coco",
    "aloe", "menta", "marine", "manzana", "bebe",
]
HIGIENE_FORMATOS = ["shampoo", "acondicionador", "jabon", "desodorante", "pasta dental", "crema"]
MASCOTA_ETAPAS = ["cachorro", "adulto", "senior", "gatito"]


def _flag(texto: str, positivos: list[str]) -> str:
    texto = normalizar_texto(texto)
    for item in positivos:
        if item in texto:
            return item.replace(" ", "_")
    return ""


def _zero_flag(texto: str) -> str:
    texto = normalizar_texto(texto)
    if any(token in texto for token in ["zero", "sin azucar", "light"]):
        return "zero"
    return "normal"


def _retornable_flag(texto: str) -> str:
    texto = normalizar_texto(texto)
    if "retornable" in texto and "no retornable" not in texto:
        return "retornable"
    if "no retornable" in texto or "desechable" in texto:
        return "no_retornable"
    return ""


def _mascota_tipo(texto: str) -> str:
    texto = normalizar_texto(texto)
    if "gato" in texto or "cat" in texto:
        return "gato"
    if "perro" in texto or "dog" in texto:
        return "perro"
    return ""


def _bebe_talla(texto: str) -> str:
    texto = normalizar_texto(texto)
    match = re.search(r"\btalla\s*([a-z0-9]+)\b", texto)
    if match:
        return f"talla_{match.group(1)}"
    return ""


def _bebe_etapa(texto: str) -> str:
    texto = normalizar_texto(texto)
    match = re.search(r"\betapa\s*(\d+)\b", texto)
    if match:
        return f"etapa_{match.group(1)}"
    return ""


def _medida(attrs: dict) -> str:
    if attrs.get("volumen"):
        return f"{attrs['volumen']}ml"
    if attrs.get("peso"):
        return f"{attrs['peso']}g"
    return ""


def _cantidad(attrs: dict) -> str:
    return f"{attrs['cantidad']}un" if attrs.get("cantidad") else ""


def atributos_fase5a(producto, categoria: str) -> dict:
    texto = normalizar_texto(f"{producto.nombre} {producto.marca or ''} {producto.tipo or ''} {producto.formato or ''}")
    attrs = extraer_atributos(texto)
    marca = normalizar_marca(producto.marca) or attrs.get("marca") or ""
    base = {
        "categoria": categoria,
        "marca": marca,
        "medida": _medida(attrs),
        "cantidad": _cantidad(attrs),
        "tokens": tokens_utiles(producto.nombre),
    }

    if categoria == "Bebidas":
        base.update({
            "familia": "bebida",
            "variante": _zero_flag(texto),
            "retornable": _retornable_flag(texto),
            "sabor": _flag(texto, BEBIDAS_SABORES),
        })
    elif categoria == "Limpieza":
        base.update({
            "familia": _flag(texto, ["detergente", "lavavajillas", "limpiador", "suavizante", "cloro"]),
            "aroma": _flag(texto, AROMAS),
            "variedad": _flag(texto, ["concentrado", "diluido", "antibacterial", "tradicional"]),
        })
    elif categoria == "Higiene Personal":
        base.update({
            "familia": _flag(texto, HIGIENE_FORMATOS),
            "aroma": _flag(texto, AROMAS),
            "genero": _flag(texto, ["hombre", "mujer", "infantil", "niño", "nino", "adulto"]),
        })
    elif categoria == "Bebe":
        base.update({
            "familia": _flag(texto, ["panal", "pañal", "alimento", "toallita", "formula"]),
            "talla": _bebe_talla(texto),
            "etapa": _bebe_etapa(texto),
        })
    elif categoria == "Mascotas":
        base.update({
            "familia": "mascota",
            "animal": _mascota_tipo(texto),
            "etapa": _flag(texto, MASCOTA_ETAPAS),
            "sabor": _flag(texto, ["carne", "pollo", "pescado", "salmon", "cordero"]),
        })

    return base


def key_fase5a(producto, categoria: str) -> str:
    attrs = atributos_fase5a(producto, categoria)
    partes = [
        attrs.get("categoria"),
        attrs.get("familia"),
        attrs.get("marca"),
        attrs.get("animal"),
        attrs.get("etapa"),
        attrs.get("talla"),
        attrs.get("genero"),
        attrs.get("variante"),
        attrs.get("retornable"),
        attrs.get("sabor"),
        attrs.get("aroma"),
        attrs.get("variedad"),
        attrs.get("medida"),
        attrs.get("cantidad"),
    ]
    limpio = "_".join(str(parte) for parte in partes if parte)
    return normalizar_texto(limpio).replace(" ", "_").replace("-", "_")


def compatible_fase5a(producto, candidato, categoria: str) -> bool:
    attrs_a = atributos_fase5a(producto, categoria)
    attrs_b = atributos_fase5a(candidato, categoria)
    for campo in ["marca", "medida", "cantidad", "familia", "animal", "etapa", "talla", "genero", "variante", "retornable", "sabor", "aroma", "variedad"]:
        if attrs_a.get(campo) and attrs_b.get(campo) and attrs_a[campo] != attrs_b[campo]:
            return False
    return candidato_compatible(producto, candidato) or matching_score(producto, candidato) >= 82
