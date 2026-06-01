import re
import unicodedata


MARCAS_CONOCIDAS = [
    "Nuestra Cocina",
    "Family Care",
    "Cuisine & Co",
    "Smart Clean",
    "Juan Valdez",
    "Marley Coffee",
    "Los Criadores",
    "La Rotunda",
    "Rio Bueno",
    "Rio Bueno",
    "Los Tilos",
    "Las Parcelas de Valdivia",
    "Huentelauquen",
    "No+Gluten",
    "Nescafe",
    "Nescafe",
    "Canada Dry",
    "Coca-Cola",
    "Coca Cola",
    "Lonco Leche",
    "Loncoleche",
    "Limon Soda",
    "Limon Soda",
    "Miraflores",
    "Schweppes",
    "Kardamili",
    "Quillayes",
    "Copacabana",
    "San Ignacio",
    "Hydroshock",
    "Monterrey",
    "Cruzeiro",
    "Pahuilmo",
    "Santa Rosa",
    "Confort",
    "Favorita",
    "Nubelin",
    "Quilque",
    "Matthei",
    "Longavi",
    "Spagnolia",
    "Kingsbury",
    "Banquete",
    "Belmont",
    "Carozzi",
    "Tucapel",
    "Lucchetti",
    "Soprole",
    "Surlat",
    "Natura",
    "Castano",
    "Castano",
    "Iansa",
    "Elite",
    "Scott",
    "Noble",
    "Ideal",
    "Sprite",
    "Pepsi",
    "Crush",
    "Fanta",
    "Bilz",
    "Point",
    "Ariel",
    "Drive",
    "Rinso",
    "Popeye",
    "Finish",
    "Fuzol",
    "Lider",
    "Lider",
    "Jumbo",
    "Unimarc",
    "Nestle",
    "Nestle",
    "Milo",
    "Nido",
    "Danone",
    "Chef",
    "Merkat",
    "Mizos",
    "Vilay",
    "Orasi",
    "Orasi",
    "Artisan",
    "Colun",
    "Omo",
    "Calo",
    "Kem",
    "Pap",
]

TOKENS_GENERICOS = {
    "",
    "sin",
    "marca",
    "general",
    "de",
    "del",
    "la",
    "el",
    "y",
    "con",
    "para",
    "en",
    "un",
    "una",
    "botella",
    "bolsa",
    "doypack",
    "pack",
    "pote",
    "caja",
    "lata",
    "bidon",
    "frasco",
    "recarga",
    "sabor",
    "original",
    "no",
    "retornable",
    "desechable",
    "libre",
    "colesterol",
    "gr",
    "ml",
    "cc",
    "kg",
    "l",
}

SABORES_CONOCIDOS = {
    "chocolate",
    "vainilla",
    "frutilla",
    "frutilla-plátano",
    "frutilla platano",
    "platano",
    "natural",
    "durazno",
    "berries",
    "coco",
    "mora",
    "limon",
    "naranja",
}


def normalizar_texto(valor):
    texto = str(valor or "").lower().replace(",", ".")
    texto = unicodedata.normalize("NFKD", texto)
    texto = "".join(c for c in texto if not unicodedata.combining(c))
    texto = re.sub(r"\b(litros|litro|lts|lt)\b", "l", texto)
    texto = re.sub(
        r"(\d+(?:\.\d+)?)\s*(ml|cc|kg|g|gr|l|unidades|unidad|un|rollos|rollo)\b",
        r"\1 \2 ",
        texto,
    )
    return " ".join(texto.split())


def _formatear_decimal(valor):
    return f"{valor:g}"


def _numero(valor):
    try:
        return float(str(valor).replace(",", "."))
    except (TypeError, ValueError):
        return None


def normalizar_marca(valor):
    marca = normalizar_texto(valor)
    if marca == "sin marca":
        return ""

    equivalencias = {
        "coca cola": "coca-cola",
        "lonco leche": "loncoleche",
        "lider": "lider",
        "limon soda": "limon soda",
        "orasi": "orasi",
        "nestle": "nestle",
    }

    return equivalencias.get(marca, marca)


def detectar_marca_en_nombre(nombre):
    texto = normalizar_texto(nombre)

    for marca in sorted(MARCAS_CONOCIDAS, key=len, reverse=True):
        marca_normalizada = normalizar_marca(marca)
        if marca_normalizada and marca_normalizada in texto:
            return marca_normalizada

    return ""


def marca_producto(producto):
    return normalizar_marca(producto.marca) or detectar_marca_en_nombre(producto.nombre)


def tokens_utiles(*valores):
    tokens = []

    for valor in valores:
        for token in normalizar_texto(valor).replace("-", " ").split():
            if token not in TOKENS_GENERICOS and token not in tokens:
                tokens.append(token)

    return tokens


def normalizar_formato(valor):
    texto = normalizar_texto(valor)
    texto = texto.replace(" ", "")
    texto = texto.replace("lts", "l").replace("lt", "l")
    texto = texto.replace("litros", "l").replace("litro", "l")
    texto = texto.replace("unidades", "un").replace("unidad", "un")
    texto = texto.replace("rollos", "un").replace("rollo", "un")
    texto = re.sub(r"^pack(\d+)$", r"\1un", texto)
    texto = re.sub(r"^(\d+)pack$", r"\1un", texto)
    texto = re.sub(r"^x(\d+)$", r"\1un", texto)
    texto = re.sub(r"^packx(\d+)$", r"\1un", texto)

    texto = re.sub(
        r"^(\d+(?:\.\d+)?)(ml|cc)$",
        lambda match: f"{_formatear_decimal(float(match.group(1)) / 1000)}l",
        texto,
    )
    texto = re.sub(
        r"^(\d+(?:\.\d+)?)(g|gr)$",
        lambda match: f"{_formatear_decimal(float(match.group(1)) / 1000)}kg",
        texto,
    )
    return texto


def extraer_medida(texto):
    texto = normalizar_texto(texto)

    volumen = None
    peso = None
    unidad = None

    for numero, unidad_raw in re.findall(r"(\d+(?:\.\d+)?)\s*(ml|cc|l)\b", texto):
        valor = _numero(numero)
        if valor is None:
            continue
        if unidad_raw in {"ml", "cc"}:
            volumen = int(round(valor))
        else:
            volumen = int(round(valor * 1000))
        unidad = "ml"
        break

    for numero, unidad_raw in re.findall(r"(\d+(?:\.\d+)?)\s*(kg|g|gr)\b", texto):
        valor = _numero(numero)
        if valor is None:
            continue
        if unidad_raw == "kg":
            peso = int(round(valor * 1000))
        else:
            peso = int(round(valor))
        if unidad is None:
            unidad = "g"
        break

    return volumen, peso, unidad


def extraer_cantidad(texto):
    texto = normalizar_texto(texto)
    patrones = [
        r"\bpack\s*(?:x\s*)?(\d+)\b",
        r"\bx\s*(\d+)\b",
        r"\b(\d+)\s*(?:un|unidad|unidades|rollo|rollos)\b",
    ]
    for patron in patrones:
        match = re.search(patron, texto)
        if match:
            return int(match.group(1))
    return None


def extraer_sabores(texto):
    texto = normalizar_texto(texto)
    return sorted(sabor for sabor in SABORES_CONOCIDOS if sabor in texto)


def extraer_atributos(nombre_producto):
    texto = normalizar_texto(nombre_producto)
    volumen, peso, unidad = extraer_medida(texto)

    atributos = {
        "marca": detectar_marca_en_nombre(texto),
        "volumen": volumen,
        "peso": peso,
        "unidad": unidad,
        "cantidad": extraer_cantidad(texto),
        "categoria": detectar_familia(texto),
        "sabores": extraer_sabores(texto),
        "tokens": tokens_utiles(texto),
    }
    return atributos


def obtener_unidad_base(formato):
    texto = normalizar_texto(formato)
    numero_texto = "".join(caracter for caracter in texto if caracter.isdigit() or caracter == ".")

    try:
        numero = float(numero_texto)
    except ValueError:
        return None

    if numero <= 0:
        return None

    compactado = texto.replace(" ", "")

    if "ml" in compactado or "cc" in compactado:
        return numero / 1000, "L"

    if compactado.endswith("l") or " l" in texto:
        return numero, "L"

    if "kg" in compactado:
        return numero, "kg"

    if compactado.endswith("g") or " g" in texto or compactado.endswith("gr"):
        return numero / 1000, "kg"

    return None


def calcular_precio_referencia(precio, formato):
    unidad = obtener_unidad_base(formato)
    if not precio or not unidad:
        return None

    cantidad, nombre_unidad = unidad
    if cantidad <= 0:
        return None

    valor = int(precio / cantidad)
    return f"${valor:,}".replace(",", ".") + f" / {nombre_unidad}"


def detectar_familia(texto):
    if "detergente" in texto:
        return "detergente"

    if "papel higienico" in texto or "papel toilet" in texto:
        return "papel_higienico"

    if "aceite" in texto:
        return "aceite"

    if "cafe" in texto:
        return "cafe"

    if "azucar" in texto and "sin azucar" not in texto:
        return "azucar"

    if "fideo" in texto or "pasta" in texto:
        return "fideos"

    if "queso" in texto:
        return "queso"

    if "yogurt" in texto or "yoghurt" in texto or "yogur" in texto:
        return "yogurt"

    if "huevo" in texto:
        return "huevos"

    if "pan" in texto:
        return "pan"

    if "bebida" in texto or "gaseosa" in texto:
        return "bebida"

    if "leche" in texto:
        if any(token in texto for token in ["postre", "flan", "galleta", "formula lactea"]):
            return "derivado_leche"
        return "leche"

    if "arroz" in texto:
        if "bebida" in texto:
            return "bebida_arroz"
        if "fideo" in texto or "pasta" in texto:
            return "pasta_arroz"
        if "galleta" in texto:
            return "galleta_arroz"
        if "sopa" in texto or "caldo" in texto:
            return "preparado_arroz"
        return "arroz"

    return ""


def detectar_familia_busqueda(texto):
    texto = normalizar_texto(texto)

    familias = {
        "papel_higienico": ["papel higienico", "confort"],
        "detergente": ["detergente"],
        "aceite": ["aceite"],
        "cafe": ["cafe"],
        "azucar": ["azucar"],
        "arroz": ["arroz"],
        "fideos": ["fideo", "fideos", "pasta"],
        "queso": ["queso"],
        "yogurt": ["yogurt", "yoghurt", "yogur"],
        "huevos": ["huevo", "huevos"],
        "pan": ["pan"],
        "bebida": ["bebida", "bebidas", "gaseosa", "gaseosas"],
        "leche": ["leche"],
    }

    for familia, claves in familias.items():
        if any(clave in texto for clave in claves):
            return familia

    return ""


def detectar_atributos(texto):
    atributos = [
        "sin lactosa",
        "sin azucar",
        "semidescremada",
        "descremada",
        "entera",
        "proteina",
        "light",
        "zero",
        "normal",
        "polvo",
        "liquido",
        "maravilla",
        "oliva",
        "girasol",
        "canola",
        "vegetal",
        "grado 1",
        "grado 2",
        "integral",
        "descafeinado",
        "instantaneo",
        "molido",
        "granulado",
        "blanca",
        "rubia",
    ]

    return [
        atributo.replace(" ", "_")
        for atributo in atributos
        if atributo in texto
    ]


def detectar_calificadores(texto):
    calificadores = [
        "chocolate",
        "vainilla",
        "frutilla",
        "cappuccino",
        "capuccino",
        "caramelo",
        "natural",
        "cultivada",
        "asada",
        "avena",
        "cola",
        "papaya",
        "pomelo",
        "pina",
        "limon",
        "lima",
        "naranja",
        "ginger",
        "capsulas",
        "doypack",
        "pack",
        "basmati",
        "sushi",
        "risotto",
        "champinon",
        "chaufan",
        "canola",
        "maiz",
        "coco",
        "pepa",
        "uva",
        "spray",
        "aloe",
        "bicarbonato",
        "hipoalergenico",
        "flores",
        "lirios",
        "rosas",
        "mantecoso",
        "gauda",
        "chanco",
        "laminado",
        "rallado",
        "natural",
        "griego",
        "batido",
        "frutilla",
        "marraqueta",
        "hallulla",
        "molde",
        "doble",
        "hoja",
    ]

    return [
        calificador.replace(" ", "_")
        for calificador in calificadores
        if calificador in texto
    ]


def detectar_metros_papel(texto):
    texto = normalizar_texto(texto)

    if detectar_familia(texto) != "papel_higienico":
        return ""

    match = re.search(r"(\d+(?:\.\d+)?)\s*(?:m|metros)\b", texto)
    if not match:
        return ""

    numero = match.group(1).rstrip("0").rstrip(".")
    return f"{numero}m"


def generar_producto_base(nombre, marca, tipo, formato):
    def normalizar_base(valor):
        texto = normalizar_texto(valor)
        reemplazos = {
            "deslactosada": "sin lactosa",
            "sin lactosa": "sin lactosa",
            "sin tapa": "",
            "con tapa": "",
            "s/t": "",
            "c/t": "",
            "natural": "",
            "lonco leche": "loncoleche",
        }

        for original, reemplazo in reemplazos.items():
            texto = texto.replace(original, reemplazo)

        texto = re.sub(
            r"\b(\d+(?:\.\d+)?)\s*(ml|cc)\b",
            lambda match: f"{_formatear_decimal(float(match.group(1)) / 1000)}l",
            texto,
        )
        texto = re.sub(
            r"\b(\d+(?:\.\d+)?)\s*(g|gr)\b",
            lambda match: f"{_formatear_decimal(float(match.group(1)) / 1000)}kg",
            texto,
        )
        texto = re.sub(r"\b(\d+(?:\.\d+)?)\s*l\b", r"\1l", texto)
        texto = re.sub(r"\b(\d+(?:\.\d+)?)\s*kg\b", r"\1kg", texto)
        texto = re.sub(r"\b(\d+)\s*(unidades|unidad|un|rollo|rollos)\b", r"\1un", texto)
        texto = re.sub(r"[^a-z0-9\s.]", " ", texto)
        return re.sub(r"\s+", " ", texto).strip()

    def tokenizar(valor):
        return normalizar_base(valor).replace(".", "_").split()

    palabras_nombre = tokenizar(nombre)
    palabras_marca = tokenizar(marca)
    palabras_tipo = tokenizar(tipo)
    palabras_formato = tokenizar(formato)

    stopwords = {"de", "la", "el", "y"}
    palabras_excluir = set(palabras_marca + palabras_tipo + palabras_formato)
    palabras_base = [
        palabra
        for palabra in palabras_nombre
        if palabra not in stopwords and palabra not in palabras_excluir
    ]

    palabras = palabras_base + palabras_marca + palabras_tipo + palabras_formato

    resultado = []
    for palabra in palabras:
        if palabra not in resultado:
            resultado.append(palabra)

    return "_".join(resultado[:6])


def tokens_firma(producto, texto, marca):
    tokens_excluir = set(tokens_utiles(
        marca,
        producto.marca,
        producto.tipo,
        producto.formato,
        detectar_familia(texto),
    ))

    tokens = []
    for token in tokens_utiles(producto.nombre):
        if token in tokens_excluir:
            continue
        if token.isdigit() or token.replace(".", "", 1).isdigit():
            continue
        if token not in tokens:
            tokens.append(token)

    return tokens[:4]


def clave_comparable(producto):
    texto = normalizar_texto(producto.nombre)
    marca = marca_producto(producto)

    partes = [
        detectar_familia(texto),
        marca,
        normalizar_formato(producto.formato),
        detectar_metros_papel(texto),
        ",".join(detectar_atributos(texto)),
        ",".join(detectar_calificadores(texto)),
    ]

    clave = "|".join(partes)

    if clave.strip("|"):
        return clave

    return producto.producto_base or f"producto:{producto.id}"
