"""Carga de configuración desde `.env` (sin dependencias externas).

El pipeline corre desatendido (tarea programada de Windows), donde no hay una
shell que exporte variables. Para que `JUMBO_API_KEY` y compañía estén
disponibles igual, se leen de un archivo `.env` en la raíz del proyecto.

`.env` está en .gitignore (no se versiona); `.env.example` documenta las claves.
Las variables ya presentes en el entorno tienen prioridad: el `.env` sólo
completa lo que falta, así se puede sobrescribir puntualmente al correr a mano.
"""

import os
from pathlib import Path


RAIZ = Path(__file__).resolve().parents[1]
ENV_PATH = RAIZ / ".env"

_cargado = False


def cargar_env(path=None, forzar=False):
    """Vuelca las claves de `.env` en os.environ (sin pisar las ya definidas).

    Es idempotente: sólo lee el archivo la primera vez salvo que se fuerce.
    """
    global _cargado
    if _cargado and not forzar:
        return

    archivo = Path(path) if path else ENV_PATH
    _cargado = True

    if not archivo.exists():
        return

    for linea in archivo.read_text(encoding="utf-8").splitlines():
        linea = linea.strip()
        if not linea or linea.startswith("#") or "=" not in linea:
            continue
        clave, _, valor = linea.partition("=")
        clave, valor = clave.strip(), valor.strip().strip('"').strip("'")
        if clave and clave not in os.environ:
            os.environ[clave] = valor
