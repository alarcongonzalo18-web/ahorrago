"""Captura de EAN (código de barras) de Jumbo y Unimarc desde sus BFF.

Líder ya trae el EAN en la URL (ver `url_utils.extraer_ean_lider`). Jumbo y
Unimarc lo exponen en sus backend-for-frontend, keyeado por el *slug* del
producto (el mismo que va en la URL que el scraper ya guarda):

- Jumbo:   POST https://bff.jumbo.cl/catalog/pdp
           body {"slug", "store"} + header apiKey  -> items[].ean
- Unimarc: GET  https://bff-unimarc-ecommerce.unimarc.cl/catalog/product/search/by-slug/<slug>
           headers channel/source/version (sin auth) -> products[0].item.ean

Contratos completos en `app/docs/ean-jumbo.md` y `app/docs/ean-unimarc.md`.

Las funciones puras (slug/normalización/parseo) son testeables sin red; las de
red (`fetch_ean_*`) hacen HTTP con backoff y distinguen bloqueo (429/403/503)
de "sin datos" (404/422).
"""

import http.client
import json
import os
import re
import time
import urllib.error
import urllib.request
import uuid
from urllib.parse import quote


# --- Jumbo ---
JUMBO_PDP_URL = "https://bff.jumbo.cl/catalog/pdp"
JUMBO_STORE = "jumboclj512"
# apiKey estático del cliente web (no es credencial de usuario). Si Jumbo lo
# rota y empieza a dar 401, recapturarlo de devtools y setear JUMBO_CATALOG_APIKEY.
JUMBO_APIKEY = os.environ.get(
    "JUMBO_CATALOG_APIKEY", "be-reg-groceries-jumbo-catalog-w54byfvkmju5"
)
JUMBO_CLIENT_VERSION = os.environ.get("JUMBO_CLIENT_VERSION", "3.3.98")

# --- Unimarc ---
UNIMARC_BYSLUG_URL = (
    "https://bff-unimarc-ecommerce.unimarc.cl/catalog/product/search/by-slug/{slug}"
)

# El WAF de Unimarc rechaza (403) requests sin User-Agent/Origin de navegador.
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)


class BloqueoError(Exception):
    """El BFF respondió con throttling (429/403/503) o falló de forma transitoria."""


# ---------------------------------------------------------------------------
# Funciones puras (testeables sin red)
# ---------------------------------------------------------------------------

def normalizar_ean(valor):
    """Deja solo dígitos y quita ceros a la izquierda, para casar con Líder.

    Devuelve "" si no queda un EAN creíble (>= 8 dígitos).
    """
    digitos = re.sub(r"\D", "", str(valor or "")).lstrip("0")
    return digitos if len(digitos) >= 8 else ""


def slug_jumbo(url):
    """`https://www.jumbo.cl/<slug>/p` -> `<slug>` (o "" si no matchea)."""
    m = re.search(r"jumbo\.cl/(.+?)/p(?:[/?#]|$)", url or "")
    return m.group(1) if m else ""


def slug_unimarc(url):
    """`https://www.unimarc.cl/product/<slug>` -> `<slug>` (o "" si no matchea)."""
    m = re.search(r"unimarc\.cl/product/([^/?#]+)", url or "")
    return m.group(1) if m else ""


def ean_desde_respuesta_jumbo(data):
    """Extrae el primer EAN normalizado de la respuesta de /catalog/pdp."""
    for item in (data or {}).get("items") or []:
        ean = normalizar_ean(item.get("ean"))
        if ean:
            return ean
    return ""


def ean_desde_respuesta_unimarc(data):
    """Extrae el primer EAN normalizado de la respuesta de by-slug."""
    for producto in (data or {}).get("products") or []:
        ean = normalizar_ean((producto.get("item") or {}).get("ean"))
        if ean:
            return ean
    return ""


# ---------------------------------------------------------------------------
# Red (con backoff)
# ---------------------------------------------------------------------------

def _pedir_json(req, intentos=5):
    """Ejecuta la request y devuelve el JSON.

    - 429/403/503 -> backoff exponencial y reintento (BloqueoError si persiste).
    - 404/422 -> None (producto sin datos / slug inválido; no es bloqueo).
    - red caída / JSON inválido -> reintento y luego BloqueoError.
    """
    ultimo = None
    for intento in range(1, intentos + 1):
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                return json.loads(resp.read().decode("utf-8", errors="replace"))
        except urllib.error.HTTPError as exc:
            ultimo = exc
            if exc.code in (429, 403, 503):
                if intento == intentos:
                    break
                time.sleep(min(60, 5 * 2 ** (intento - 1)))
                continue
            if exc.code in (404, 422):
                return None
            raise
        except (
            TimeoutError,
            ConnectionError,
            http.client.HTTPException,
            urllib.error.URLError,
            json.JSONDecodeError,
        ) as exc:
            ultimo = exc
            if intento == intentos:
                break
            time.sleep(min(30, 3 * intento))
    raise BloqueoError(f"fallo tras {intentos} intentos: {ultimo}")


def fetch_ean_jumbo(slug):
    """Devuelve el EAN de un producto de Jumbo por su slug ("" si no hay)."""
    if not slug:
        return ""
    body = json.dumps({"slug": slug, "store": JUMBO_STORE}).encode("utf-8")
    req = urllib.request.Request(
        JUMBO_PDP_URL,
        data=body,
        method="POST",
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json, text/plain, */*",
            "User-Agent": USER_AGENT,
            "Origin": "https://www.jumbo.cl",
            "Referer": "https://www.jumbo.cl/",
            "apiKey": JUMBO_APIKEY,
            "x-client-platform": "web",
            "x-client-version": JUMBO_CLIENT_VERSION,
            "x-trace-id": str(uuid.uuid4()),
        },
    )
    return ean_desde_respuesta_jumbo(_pedir_json(req))


def fetch_ean_unimarc(slug):
    """Devuelve el EAN de un producto de Unimarc por su slug ("" si no hay)."""
    if not slug:
        return ""
    req = urllib.request.Request(
        UNIMARC_BYSLUG_URL.format(slug=quote(slug, safe="")),
        headers={
            "Accept": "application/json, text/plain, */*",
            "User-Agent": USER_AGENT,
            "Origin": "https://www.unimarc.cl",
            "Referer": "https://www.unimarc.cl/",
            "channel": "UNIMARC",
            "source": "web",
            "version": "1.0.0",
        },
    )
    return ean_desde_respuesta_unimarc(_pedir_json(req))
