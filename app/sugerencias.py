"""Terminos para el autocomplete del buscador.

El primer beta tester busco por marca ("Trencito", dos veces) y por categoria
("leche", "yogurt"). Un vocabulario fijo no alcanza — "Trencito" no figura en
MARCAS_CONOCIDAS — asi que los terminos se minan del catalogo real: palabras
frecuentes en los nombres de producto, mas las marcas multi-palabra conocidas.

La lista se arma una vez y se cachea en memoria; la base cambia una vez por
noche, asi que un TTL de horas sobra.
"""

import re
import time
from collections import Counter

from app import models
from app.normalizacion import MARCAS_CONOCIDAS, normalizar_texto

TTL_SEGUNDOS = 6 * 3600
MINIMO_APARICIONES = 15
# Con el minimo de 15 apariciones quedan ~2.200 terminos (~60 KB de JSON, se
# pide una vez). Un tope menor deja afuera marcas buscadas: "trencito" (73
# productos) quedaba en el puesto 601.
MAXIMO_TERMINOS = 3000

# Palabras frecuentes que no identifican un producto: envases, medidas y
# descriptores de formato. Un usuario no busca "bolsa".
NO_SUGERIR = {
    "bolsa", "caja", "frasco", "botella", "lata", "tarro", "doypack", "sachet",
    "envasado", "envase", "paquete", "formato", "display", "unidad", "unidades",
    "pack", "granel", "bandeja", "pote", "bidon", "caluga", "rollo", "rollos",
    "las", "los", "con", "sin", "para", "del", "por", "mas", "extra",
    "tradicional", "clasico", "clasica", "original", "variedades", "surtido",
}

_cache = {"ts": 0.0, "terminos": []}


def _tokens_nombre(nombre):
    for token in re.findall(r"[a-zñ&]{3,}", normalizar_texto(nombre)):
        if token not in NO_SUGERIR:
            yield token


def construir_terminos(nombres):
    """Devuelve [{"t": termino, "n": productos}] ordenado por frecuencia."""
    conteo = Counter()
    for nombre in nombres:
        # set(): una aparicion por producto, para que "Leche Leche" no cuente doble
        conteo.update(set(_tokens_nombre(nombre)))

    # Marcas multi-palabra: el conteo por token las parte ("juan", "valdez");
    # se agregan como frase con el conteo real de productos que las contienen.
    frases = Counter()
    marcas = {normalizar_texto(m) for m in MARCAS_CONOCIDAS if " " in m.strip()}
    for nombre in nombres:
        texto = normalizar_texto(nombre)
        for marca in marcas:
            if marca in texto:
                frases[marca] += 1

    conteo.update(frases)
    pares = [(t, n) for t, n in conteo.items() if n >= MINIMO_APARICIONES]
    pares.sort(key=lambda par: (-par[1], par[0]))
    return [{"t": t, "n": n} for t, n in pares[:MAXIMO_TERMINOS]]


def obtener(db):
    ahora = time.time()
    if ahora - _cache["ts"] > TTL_SEGUNDOS or not _cache["terminos"]:
        nombres = [n for (n,) in db.query(models.Producto.nombre).all()]
        _cache["terminos"] = construir_terminos(nombres)
        _cache["ts"] = ahora
    return _cache["terminos"]
