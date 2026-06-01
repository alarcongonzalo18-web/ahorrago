from urllib.parse import urlencode


def generar_url_busqueda(base_url: str, parametro: str, termino: str) -> str:
    return f"{base_url}?{urlencode({parametro: termino or ''})}"
