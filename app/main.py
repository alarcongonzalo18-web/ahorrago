from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from collections import defaultdict
import unicodedata
import re
from .database import Base, engine, SessionLocal
from . import models, schemas, services

Base.metadata.create_all(bind=engine)

SUPERMERCADOS_REQUERIDOS = {"Líder", "Jumbo", "Unimarc"}

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
    "Río Bueno",
    "Los Tilos",
    "Las Parcelas de Valdivia",
    "Huentelauquen",
    "No+Gluten",
    "Nescafe",
    "Nescafé",
    "Canada Dry",
    "Coca-Cola",
    "Coca Cola",
    "Lonco Leche",
    "Loncoleche",
    "Limón Soda",
    "Limon Soda",
    "Miraflores",
    "Schweppes",
    "Kardamili",
    "Quillayes",
    "Copacabana",
    "San Ignacio",
    "Hydroshock",
    "Copacabana",
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
    "Castaño",
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
    "Líder",
    "Jumbo",
    "Unimarc",
    "Nestlé",
    "Nestle",
    "Milo",
    "Nido",
    "Danone",
    "Chef",
    "Merkat",
    "Mizos",
    "Vilay",
    "Orasí",
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

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.get("/")
def inicio():
    return {"mensaje": "SuperCheck funcionando 🚀"}


@app.get("/buscar/{texto}")
def buscar(texto: str, db: Session = Depends(get_db)):
    return services.buscar_opciones_producto(db, texto)


@app.post("/comparar")
def comparar(request: schemas.ComparacionRequest, db: Session = Depends(get_db)):
    resultado = services.comparar_lista(db, request.productos)
    return resultado

@app.get("/categorias")
def obtener_categorias(db: Session = Depends(get_db)):
    return db.query(models.Categoria).all()

@app.get("/subcategorias/{categoria_id}")
def obtener_subcategorias(categoria_id: int, db: Session = Depends(get_db)):
    return db.query(models.Subcategoria).filter(
        models.Subcategoria.categoria_id == categoria_id
    ).all()


@app.get("/diagnostico/calidad")
def diagnostico_calidad(db: Session = Depends(get_db)):
    por_supermercado = defaultdict(int)
    por_subcategoria = defaultdict(int)
    sin_imagen = 0
    sin_url = 0
    url_generica = 0
    precio_sospechoso = []

    precios = db.query(models.Precio).join(models.Producto).join(models.Supermercado).all()

    for precio in precios:
        producto = precio.producto
        supermercado = precio.supermercado.nombre
        subcategoria = producto.subcategoria.nombre if producto.subcategoria else "Sin subcategoria"
        valor = valor_precio_producto(producto, precio)

        por_supermercado[supermercado] += 1
        por_subcategoria[subcategoria] += 1

        if not precio.imagen_url:
            sin_imagen += 1

        if not precio.url_producto:
            sin_url += 1
        elif es_url_generica(precio.url_producto):
            url_generica += 1

        if (
            not valor or
            valor <= 0 or
            (precio.precio_oferta and precio.precio_normal and precio.precio_oferta < 500 and precio.precio_normal > precio.precio_oferta * 2)
        ):
            precio_sospechoso.append({
                "producto": producto.nombre,
                "supermercado": supermercado,
                "precio_normal": precio.precio_normal,
                "precio_oferta": precio.precio_oferta,
                "valor_usado": valor,
            })

    return {
        "productos": db.query(models.Producto).count(),
        "precios": len(precios),
        "supermercados": dict(sorted(por_supermercado.items())),
        "subcategorias": dict(sorted(por_subcategoria.items())),
        "sin_imagen": sin_imagen,
        "sin_url": sin_url,
        "url_generica": url_generica,
        "precios_sospechosos": {
            "total": len(precio_sospechoso),
            "muestra": precio_sospechoso[:20],
        },
    }


def es_url_generica(url):
    if not url:
        return True

    return "/busqueda" in url or "/search" in url


def es_url_producto_especifica(url):
    if es_url_generica(url):
        return False

    return (
        "/p" in url or
        "/product/" in url or
        "super.lider.cl/ip/" in url
    )


def normalizar_texto(valor):
    texto = str(valor or "").lower().replace(",", ".")
    texto = unicodedata.normalize("NFKD", texto)
    texto = "".join(c for c in texto if not unicodedata.combining(c))
    texto = texto.replace("litros", "l").replace("litro", "l").replace("lt", "l")
    texto = re.sub(r"(\d+(?:\.\d+)?)\s*(ml|cc|kg|g|l)\b", r"\1 \2 ", texto)
    return " ".join(texto.split())


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
    return texto


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

    if compactado.endswith("g") or " g" in texto:
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

    if "papel higienico" in texto or "papel higienico" in texto:
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
        ",".join(detectar_atributos(texto)),
        ",".join(detectar_calificadores(texto)),
    ]

    clave = "|".join(partes)

    if clave.strip("|"):
        return clave

    return producto.producto_base or f"producto:{producto.id}"


def candidato_compatible(producto, candidato):
    texto_producto = normalizar_texto(
        f"{producto.nombre} {producto.marca} {producto.tipo} {producto.formato}"
    )
    texto_candidato = normalizar_texto(
        f"{candidato.nombre} {candidato.marca} {candidato.tipo} {candidato.formato}"
    )
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

    return True


def precio_valido_para_comparar(producto, precio):
    valor = valor_precio_producto(producto, precio)
    familia = detectar_familia(normalizar_texto(producto.nombre))

    if not valor or valor <= 0:
        return False

    if familia == "papel_higienico" and valor < 500:
        return False

    return True


def valor_precio_producto(producto, precio):
    familia = detectar_familia(normalizar_texto(producto.nombre))

    if (
        precio.precio_oferta and
        precio.precio_normal and
        precio.precio_oferta < 500 and
        precio.precio_normal > precio.precio_oferta * 2
    ):
        return precio.precio_normal

    if (
        familia == "papel_higienico" and
        precio.precio_oferta and
        precio.precio_normal and
        precio.precio_oferta < 500 and
        precio.precio_normal >= 500
    ):
        return precio.precio_normal

    return precio.precio_oferta if precio.precio_oferta else precio.precio_normal


def buscar_url_por_atributos(db, producto, precio):
    requeridos = tokens_utiles(
        "" if producto.marca == "Sin marca" else producto.marca,
        "" if producto.tipo == "general" else producto.tipo,
        producto.formato
    )

    if not requeridos:
        return None

    candidatos = db.query(models.Producto, models.Precio).join(models.Precio).filter(
        models.Precio.supermercado_id == precio.supermercado_id,
        models.Precio.url_producto.isnot(None)
    ).all()

    mejor = None
    mejor_puntaje = -1
    nombre_original = set(tokens_utiles(producto.nombre))

    for candidato, precio_candidato in candidatos:
        if not es_url_producto_especifica(precio_candidato.url_producto):
            continue

        if not candidato_compatible(producto, candidato):
            continue

        nombre_candidato = normalizar_texto(candidato.nombre)

        if not all(token in nombre_candidato for token in requeridos):
            continue

        tokens_candidato = set(tokens_utiles(candidato.nombre))
        puntaje = len(nombre_original.intersection(tokens_candidato))

        if "sin lactosa" not in normalizar_texto(producto.nombre) and "sin lactosa" in nombre_candidato:
            puntaje -= 2

        if puntaje > mejor_puntaje:
            mejor = precio_candidato.url_producto
            mejor_puntaje = puntaje

    return mejor


def obtener_url_especifica(db, producto, precio):
    url_actual = precio.url_producto

    if es_url_producto_especifica(url_actual):
        return url_actual

    if not producto.producto_base:
        return None

    candidatos = db.query(models.Precio).join(models.Producto).filter(
        models.Precio.supermercado_id == precio.supermercado_id,
        models.Producto.producto_base == producto.producto_base,
        models.Precio.url_producto.isnot(None)
    ).all()

    for candidato in candidatos:
        if (
            es_url_producto_especifica(candidato.url_producto) and
            candidato_compatible(producto, candidato.producto)
        ):
            return candidato.url_producto

    return None



@app.get("/productos/buscar/{texto}")
def buscar_productos(texto: str, db: Session = Depends(get_db)):
    palabras = tokens_utiles(texto)
    productos = [
        producto
        for producto in db.query(models.Producto).all()
        if all(palabra in normalizar_texto(producto.nombre) for palabra in palabras)
        and not ("azucar" in palabras and "sin azucar" in normalizar_texto(producto.nombre))
    ]

    resultado = []
    grupos_vistos = set()
    grupos_por_clave = defaultdict(list)

    for candidato in db.query(models.Producto).all():
        grupos_por_clave[clave_comparable(candidato)].append(candidato)

    for producto in productos:
        grupo_id = clave_comparable(producto)

        if grupo_id in grupos_vistos:
            continue

        grupos_vistos.add(grupo_id)

        equivalentes = grupos_por_clave[grupo_id] or [producto]

        mejor_por_supermercado = {}

        for equivalente in equivalentes:
            if not candidato_compatible(producto, equivalente):
                continue

            precios = db.query(models.Precio).filter(
                models.Precio.producto_id == equivalente.id
            ).all()

            for precio in precios:
                if not precio_valido_para_comparar(equivalente, precio):
                    continue

                valor = valor_precio_producto(equivalente, precio)
                supermercado = precio.supermercado.nombre
                tiene_descuento = bool(
                    precio.precio_oferta and
                    precio.precio_normal and
                    valor == precio.precio_oferta and
                    precio.precio_oferta < precio.precio_normal and
                    precio.precio_normal <= precio.precio_oferta * 2
                )

                mejor_actual = mejor_por_supermercado.get(supermercado)
                if mejor_actual and mejor_actual["precio"] <= valor:
                    continue

                mejor_por_supermercado[supermercado] = {
                    "supermercado": supermercado,
                    "precio": valor,
                    "precio_normal": precio.precio_normal,
                    "precio_oferta": precio.precio_oferta,
                    "tiene_descuento": tiene_descuento,
                    "descuento": int(round((1 - precio.precio_oferta / precio.precio_normal) * 100)) if tiene_descuento else 0,
                    "promocion": precio.promocion,
                    "precio_referencia": precio.precio_referencia or calcular_precio_referencia(valor, equivalente.formato),
                    "url": obtener_url_especifica(db, equivalente, precio),
                    "imagen_url": precio.imagen_url,
                    "nombre": equivalente.nombre
                }

        lista_precios = sorted(
            mejor_por_supermercado.values(),
            key=lambda item: item["precio"]
        )

        supermercados_presentes = {
            item["supermercado"]
            for item in lista_precios
        }

        if not SUPERMERCADOS_REQUERIDOS.issubset(supermercados_presentes):
            continue

        imagen_url = next(
            (item["imagen_url"] for item in lista_precios if item.get("imagen_url")),
            None
        )

        resultado.append({
            "id": producto.id,
            "nombre": producto.nombre,
            "marca": producto.marca,
            "tipo": producto.tipo,
            "formato": producto.formato,
            "imagen_url": imagen_url,
            "precios": lista_precios
        })

    return resultado
