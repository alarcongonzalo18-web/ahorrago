"""Endurecimiento de la API para exponerla a internet.

Tres cosas, todas configurables por entorno para no estorbar en desarrollo:

- **CORS**: hoy solo la red local. `AHORRAGO_ORIGENES` suma el dominio real.
- **Endpoints internos** (`/diagnostico/*`, `/estado-datos`): muestran conteos,
  calidad del matching y rutas del disco. Con `AHORRAGO_ADMIN_TOKEN` definido
  quedan detras del token; sin la variable siguen abiertos (desarrollo local).
- **Rate limiting**: sin esto cualquiera raspa la base entera — que es
  exactamente lo que nosotros le hacemos a los retailers.

Nada de esto se activa solo: en local, sin variables de entorno, la API se
comporta igual que siempre. El endurecimiento se enciende en el servidor.
"""

import base64
import hashlib
import hmac
import os
import secrets
import time
from collections import deque

from fastapi import HTTPException, Request

# Red local para desarrollo: el frontend corre en 5500 y el dev server en 3000.
ORIGENES_LOCALES = (
    r"http://(localhost|127\.0\.0\.1|192\.168\.\d+\.\d+|10\.\d+\.\d+\.\d+):(5500|3000)"
)

LIMITE_POR_MINUTO = int(os.environ.get("AHORRAGO_LIMITE_MINUTO", "120"))
VENTANA_SEGUNDOS = 60


def origenes_permitidos():
    """Regex de CORS: la red local + los dominios de AHORRAGO_ORIGENES."""
    extra = [o.strip() for o in os.environ.get("AHORRAGO_ORIGENES", "").split(",") if o.strip()]
    if not extra:
        return ORIGENES_LOCALES
    import re

    dominios = "|".join(re.escape(o) for o in extra)
    return f"{ORIGENES_LOCALES}|{dominios}"


def token_admin():
    return os.environ.get("AHORRAGO_ADMIN_TOKEN", "").strip()


def verificar_admin(request: Request):
    """Dependencia para los endpoints internos.

    Sin AHORRAGO_ADMIN_TOKEN definido no exige nada: es el modo desarrollo. En el
    servidor se define la variable y entonces hace falta el header `x-admin-token`.

    El token va SOLO por header, no por query string: `?token=` termina en los
    logs del servidor, el historial del navegador y la cabecera Referer. La
    comparacion es constant-time para no filtrar el token por timing.
    """
    esperado = token_admin()
    if not esperado:
        return True

    recibido = (request.headers.get("x-admin-token") or "").strip()
    if not recibido or not secrets.compare_digest(recibido, esperado):
        raise HTTPException(status_code=404, detail="No encontrado")
    return True


class LimitadorMemoria:
    """Rate limit por IP con ventana deslizante.

    En memoria a proposito: un solo proceso sirviendo SQLite no necesita Redis.
    Si algun dia hay varios workers, esto se cambia por algo compartido.
    """

    def __init__(self, limite=LIMITE_POR_MINUTO, ventana=VENTANA_SEGUNDOS):
        self.limite = limite
        self.ventana = ventana
        self._visitas = {}
        self._ultima_limpieza = None

    def permitido(self, ip, ahora=None):
        if self.limite <= 0:          # 0 o negativo = sin limite
            return True
        ahora = ahora if ahora is not None else time.monotonic()
        # Limpieza oportunista: como mucho una vez por ventana. Sin esto _visitas
        # crece sin fin (un deque por IP, para siempre) y una IP rotada/spoofeada
        # infla la memoria del proceso indefinidamente.
        if self._ultima_limpieza is None or ahora - self._ultima_limpieza >= self.ventana:
            self.limpiar(ahora)
            self._ultima_limpieza = ahora
        cola = self._visitas.setdefault(ip, deque())
        limite_inferior = ahora - self.ventana
        while cola and cola[0] < limite_inferior:
            cola.popleft()
        if len(cola) >= self.limite:
            return False
        cola.append(ahora)
        return True

    def limpiar(self, ahora=None):
        """Descarta las IPs sin visitas recientes (evita crecer sin fin)."""
        ahora = ahora if ahora is not None else time.monotonic()
        limite_inferior = ahora - self.ventana
        for ip in [k for k, v in self._visitas.items() if not v or v[-1] < limite_inferior]:
            del self._visitas[ip]


limitador = LimitadorMemoria()


def confiar_en_proxy():
    """Si la API vive detras de un proxy inverso propio que SETEA X-Forwarded-For.

    Apagado por defecto: si estuviera siempre encendido, un cliente directo puede
    mandar `X-Forwarded-For: <IP falsa>` distinta en cada request y saltear el
    rate limit por completo. Se enciende con AHORRAGO_CONFIAR_PROXY=1 SOLO cuando
    el proxy reescribe (no agrega) el header.
    """
    return os.environ.get("AHORRAGO_CONFIAR_PROXY", "").strip().lower() in (
        "1", "true", "si", "yes",
    )


def ip_del_cliente(request: Request):
    """IP del cliente para el rate limit.

    Por defecto usa la IP de la conexion (no spoofeable). Solo cuando
    AHORRAGO_CONFIAR_PROXY esta activo lee X-Forwarded-For, porque ahi el proxy
    confiable garantiza su valor.
    """
    if confiar_en_proxy():
        reenviada = request.headers.get("x-forwarded-for", "")
        if reenviada:
            return reenviada.split(",")[0].strip()
    return request.client.host if request.client else "desconocida"


# --- Webhook de WhatsApp (Twilio) -------------------------------------------

def token_twilio():
    return os.environ.get("TWILIO_AUTH_TOKEN", "").strip()


def firma_twilio_esperada(auth_token, url, params):
    """Firma que Twilio calcula para un request (HMAC-SHA1, base64).

    Es: HMAC-SHA1(auth_token, url + concat(k+v por cada param, ordenado por k)).
    Función pura: testeable sin red.
    """
    datos = url + "".join(k + str(params[k]) for k in sorted(params))
    mac = hmac.new(auth_token.encode("utf-8"), datos.encode("utf-8"), hashlib.sha1)
    return base64.b64encode(mac.digest()).decode("ascii")


def firma_twilio_valida(auth_token, url, params, firma_recibida):
    """Valida X-Twilio-Signature. Sin TWILIO_AUTH_TOKEN definido no exige nada
    (modo desarrollo, igual que el resto del modulo)."""
    if not auth_token:
        return True
    esperada = firma_twilio_esperada(auth_token, url, params)
    return bool(firma_recibida) and hmac.compare_digest(esperada, firma_recibida)


def url_webhook(request: Request):
    """URL que Twilio firmó. Detrás de un proxy con TLS el esquema no coincide;
    AHORRAGO_WEBHOOK_URL lo fija explícito."""
    override = os.environ.get("AHORRAGO_WEBHOOK_URL", "").strip()
    return override or str(request.url)
