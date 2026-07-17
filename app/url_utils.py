import re
from urllib.parse import urlencode


def generar_url_busqueda(base_url: str, parametro: str, termino: str) -> str:
    return f"{base_url}?{urlencode({parametro: termino or ''})}"


def extraer_ean_lider(url):
    """Extrae el EAN desde una URL de producto de Lider.

    Las URLs de super.lider.cl usan el GTIN-14 como id de item:
    /ip/<categoria>/<slug>/00780292000814?channable=...
    Se normaliza quitando ceros a la izquierda para que compare igual
    contra EANs de otras fuentes (que suelen venir sin padding).
    """
    if not url:
        return ""
    m = re.search(r"/(\d{8,14})(?:[/?#]|$)", url)
    if not m:
        return ""
    ean = m.group(1).lstrip("0")
    return ean if len(ean) >= 8 else ""
