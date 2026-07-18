import re
from urllib.parse import urlencode


def generar_url_busqueda(base_url: str, parametro: str, termino: str) -> str:
    return f"{base_url}?{urlencode({parametro: termino or ''})}"


def ean13_check_digit(datos12):
    """Dígito verificador EAN-13 a partir de los 12 dígitos de datos."""
    suma = sum((3 if i % 2 else 1) * int(c) for i, c in enumerate(datos12))
    return str((10 - suma % 10) % 10)


def extraer_ean_lider(url):
    """Extrae el EAN-13 real desde una URL de producto de Lider.

    OJO: el id de 14 dígitos de las URLs de super.lider.cl NO es un GTIN-14
    estándar. Es `00` + los 12 dígitos de datos del EAN-13, SIN el dígito
    verificador (ej: `/00780292000963` -> datos `780292000963` ->
    EAN-13 `7802920009636`). La versión anterior sólo quitaba ceros y devolvía
    12 dígitos, que no casaban con el EAN real de Jumbo/Unimarc. Acá se
    reconstruye el check digit. Se normaliza quitando ceros a la izquierda,
    igual que `ean_fetch.normalizar_ean`, para comparar entre fuentes.
    """
    if not url:
        return ""
    m = re.search(r"/(\d{8,14})(?:[/?#]|$)", url)
    if not m:
        return ""
    num = m.group(1)
    if len(num) == 14:
        datos12 = num[2:]           # "00" + 12 dígitos de datos
    elif len(num) == 13:
        datos12 = num[:12]          # ya es EAN-13: recalcular da el mismo
    else:
        return ""                   # formato inesperado: mejor sin EAN que uno malo
    ean = (datos12 + ean13_check_digit(datos12)).lstrip("0")
    return ean if len(ean) >= 8 else ""
