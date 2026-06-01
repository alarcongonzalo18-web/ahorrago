from rapidfuzz import fuzz

from .normalizacion import (
    detectar_calificadores,
    detectar_familia,
    detectar_metros_papel,
    extraer_atributos,
    marca_producto,
    normalizar_formato,
    normalizar_texto,
    tokens_firma,
    tokens_utiles,
)


def _texto_producto(producto):
    return normalizar_texto(
        f"{producto.nombre} {producto.marca} {producto.tipo} {producto.formato}"
    )


def _producto_base(producto):
    return normalizar_texto(getattr(producto, "producto_base", "") or "")


def _atributos_producto(producto):
    atributos = extraer_atributos(_texto_producto(producto))
    marca = marca_producto(producto)
    if marca:
        atributos["marca"] = marca
    return atributos


def _mismo_valor_si_existe(valor_a, valor_b):
    return valor_a is None or valor_b is None or valor_a == valor_b


def _sabores_compatibles(attrs_producto, attrs_candidato):
    sabores_producto = set(attrs_producto.get("sabores") or [])
    sabores_candidato = set(attrs_candidato.get("sabores") or [])
    if not sabores_producto or not sabores_candidato:
        return True
    return bool(sabores_producto.intersection(sabores_candidato))


def matching_score(producto, candidato):
    attrs_producto = _atributos_producto(producto)
    attrs_candidato = _atributos_producto(candidato)
    texto_producto = _texto_producto(producto)
    texto_candidato = _texto_producto(candidato)

    score = 0

    marca = attrs_producto.get("marca")
    marca_candidato = attrs_candidato.get("marca")
    if marca and marca_candidato:
        score += 20 if marca == marca_candidato else 0
    elif marca or marca_candidato:
        score += 8
    else:
        score += 12

    if attrs_producto.get("volumen") or attrs_candidato.get("volumen"):
        score += 15 if attrs_producto.get("volumen") == attrs_candidato.get("volumen") else 0
    elif attrs_producto.get("peso") or attrs_candidato.get("peso"):
        score += 15 if attrs_producto.get("peso") == attrs_candidato.get("peso") else 0
    else:
        score += 8

    if attrs_producto.get("cantidad") or attrs_candidato.get("cantidad"):
        score += 10 if attrs_producto.get("cantidad") == attrs_candidato.get("cantidad") else 0
    else:
        score += 6

    formato = normalizar_formato(getattr(producto, "formato", ""))
    formato_candidato = normalizar_formato(getattr(candidato, "formato", ""))
    if formato and formato_candidato and formato == formato_candidato:
        score += 5

    if attrs_producto.get("categoria") and attrs_candidato.get("categoria"):
        score += 10 if attrs_producto["categoria"] == attrs_candidato["categoria"] else 0
    else:
        score += 5

    base_producto = _producto_base(producto)
    base_candidato = _producto_base(candidato)
    if base_producto and base_candidato:
        score += 15 if base_producto == base_candidato else int(fuzz.token_set_ratio(base_producto, base_candidato) * 0.08)

    tokens_producto = set(attrs_producto.get("tokens") or [])
    tokens_candidato = set(attrs_candidato.get("tokens") or [])
    if tokens_producto and tokens_candidato:
        interseccion = tokens_producto.intersection(tokens_candidato)
        union = tokens_producto.union(tokens_candidato)
        score += int((len(interseccion) / len(union)) * 10)

    score += int(fuzz.token_set_ratio(texto_producto, texto_candidato) * 0.20)

    return max(0, min(100, score))


def candidato_compatible(producto, candidato):
    texto_producto = _texto_producto(producto)
    texto_candidato = _texto_producto(candidato)
    attrs_producto = _atributos_producto(producto)
    attrs_candidato = _atributos_producto(candidato)
    familia_producto = detectar_familia(texto_producto)
    familia_candidato = detectar_familia(texto_candidato)

    if familia_producto and familia_candidato and familia_producto != familia_candidato:
        return False

    if "sin lactosa" not in texto_producto and "sin lactosa" in texto_candidato:
        return False

    marca = marca_producto(producto)
    marca_candidato = marca_producto(candidato)
    if marca and marca_candidato and marca != marca_candidato:
        return False

    if marca and not marca_candidato and marca not in texto_candidato:
        return False

    if not _mismo_valor_si_existe(attrs_producto.get("volumen"), attrs_candidato.get("volumen")):
        return False

    if not _mismo_valor_si_existe(attrs_producto.get("peso"), attrs_candidato.get("peso")):
        return False

    if not _mismo_valor_si_existe(attrs_producto.get("cantidad"), attrs_candidato.get("cantidad")):
        return False

    if not _sabores_compatibles(attrs_producto, attrs_candidato):
        return False

    tipo = normalizar_texto(producto.tipo)
    if tipo and tipo != "general":
        if tipo == "sin lactosa" and "sin lactosa" not in texto_candidato:
            return False
        if tipo != "sin lactosa" and tipo not in texto_candidato:
            return False

    formato = normalizar_formato(producto.formato)
    formato_candidato = normalizar_formato(candidato.formato)
    if formato and formato_candidato and formato != formato_candidato:
        return False

    if formato and not formato_candidato:
        for token in tokens_utiles(producto.formato):
            if token not in texto_candidato:
                return False

    metros_papel = detectar_metros_papel(texto_producto)
    metros_papel_candidato = detectar_metros_papel(texto_candidato)
    if metros_papel and metros_papel_candidato and metros_papel != metros_papel_candidato:
        return False

    calificadores_producto = set(detectar_calificadores(texto_producto))
    calificadores_candidato = set(detectar_calificadores(texto_candidato))
    if calificadores_producto and calificadores_candidato:
        if not calificadores_producto.intersection(calificadores_candidato):
            return False

    firma_producto = set(tokens_firma(producto, texto_producto, marca))
    firma_candidato = set(tokens_firma(candidato, texto_candidato, marca_candidato))

    if firma_producto and firma_candidato:
        coincidencias = firma_producto.intersection(firma_candidato)
        minimo = 2 if min(len(firma_producto), len(firma_candidato)) >= 2 else 1
        if len(coincidencias) < minimo:
            return False

    return matching_score(producto, candidato) >= 68
