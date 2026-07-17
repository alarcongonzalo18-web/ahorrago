"""Nucleo conversacional de AhorraGo, independiente del canal.

Cualquier canal de chat (WhatsApp via Twilio o Meta Cloud API, Telegram,
un widget web) recibe texto y espera texto. Este modulo hace esa
traduccion: interpreta el mensaje del usuario y responde usando el mismo
backend que la web (services.comparar_lista), que es la calculadora
oficial. El canal solo transporta.
"""

import re
import unicodedata

from . import services
from .schemas import ItemLista

CANTIDAD_MAXIMA = 99
ITEMS_MAXIMOS = 20

SALUDOS = {"hola", "buenas", "buenos dias", "buenas tardes", "buenas noches", "wena", "hey", "alo"}
PEDIDOS_AYUDA = {"ayuda", "help", "menu", "como funciona", "que haces", "info", "instrucciones", "?"}

MENSAJE_BIENVENIDA = (
    "¡Hola! Soy AhorraGo 🛒\n"
    "Te digo dónde comprar más barato entre Líder, Jumbo y Unimarc.\n\n"
    "Mándame tu lista de compras separada por comas, por ejemplo:\n\n"
    "2 leches, arroz, aceite\n\n"
    "y te respondo con la comparación de precios y la compra óptima."
)

MENSAJE_SIN_RESULTADOS = (
    "No encontré esos productos 😕\n"
    "Prueba con nombres más simples (ej: \"leche\", \"arroz\", \"detergente\") "
    "o de a un producto a la vez."
)


def _normalizar(texto):
    texto = unicodedata.normalize("NFD", texto or "")
    texto = "".join(c for c in texto if unicodedata.category(c) != "Mn")
    return re.sub(r"\s+", " ", texto).strip().lower()


def _singularizar(nombre):
    # "leches" -> "leche" para que el ilike de buscar_producto encuentre.
    # Solo quita la "s" final y solo con cantidad explicita ("2 leches");
    # cualquier regla mas ambiciosa ("panes" -> ?) falla mas de lo que ayuda.
    if len(nombre) > 4 and nombre.endswith("s"):
        return nombre[:-1]
    return nombre


def interpretar_item(fragmento):
    """'2 leches' / 'leche x2' / 'leche x 2' / 'leche' -> (nombre, cantidad) o None."""
    fragmento = fragmento.strip(" .;-")
    if not fragmento:
        return None

    cantidad = 1
    con_cantidad = False

    m = re.match(r"^(\d{1,3})\s*(?:x\s*)?(\D.*)$", fragmento)
    if m:
        cantidad, fragmento = int(m.group(1)), m.group(2)
        con_cantidad = True
    else:
        m = re.match(r"^(.+?)\s*x\s*(\d{1,3})$", fragmento)
        if m:
            fragmento, cantidad = m.group(1), int(m.group(2))
            con_cantidad = True

    nombre = fragmento.strip()
    if not nombre or nombre.isdigit():
        return None
    if con_cantidad:
        nombre = _singularizar(nombre)

    return nombre, max(1, min(cantidad, CANTIDAD_MAXIMA))


def interpretar_lista(texto):
    """Divide el mensaje en items. Separadores: coma, salto de linea, ' y '."""
    partes = re.split(r"[,\n;]| y ", texto)
    items = []
    for parte in partes:
        item = interpretar_item(parte)
        if item:
            items.append(item)
    return items[:ITEMS_MAXIMOS]


def responder(db, texto):
    """Punto de entrada del bot: mensaje del usuario -> respuesta en texto."""
    limpio = _normalizar(texto)

    if not limpio or limpio in SALUDOS or limpio in PEDIDOS_AYUDA:
        return MENSAJE_BIENVENIDA

    items = interpretar_lista(limpio)
    if not items:
        return MENSAJE_BIENVENIDA

    lista = [ItemLista(nombre=nombre, cantidad=cantidad) for nombre, cantidad in items]
    resultado = services.comparar_lista(db, lista)

    if not resultado["comparacion"]:
        return MENSAJE_SIN_RESULTADOS

    return resultado["mensaje"]
