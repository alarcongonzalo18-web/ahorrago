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

import os
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
    servidor se define la variable y entonces hace falta el header (o ?token=).
    """
    esperado = token_admin()
    if not esperado:
        return True

    recibido = (
        request.headers.get("x-admin-token")
        or request.query_params.get("token")
        or ""
    ).strip()
    if recibido != esperado:
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

    def permitido(self, ip, ahora=None):
        if self.limite <= 0:          # 0 o negativo = sin limite
            return True
        ahora = ahora if ahora is not None else time.monotonic()
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


def ip_del_cliente(request: Request):
    """IP real detras de un proxy inverso (nginx/Caddy ponen X-Forwarded-For)."""
    reenviada = request.headers.get("x-forwarded-for", "")
    if reenviada:
        return reenviada.split(",")[0].strip()
    return request.client.host if request.client else "desconocida"
