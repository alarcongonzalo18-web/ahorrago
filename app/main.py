from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, Depends, Query, Request
from xml.sax.saxutils import escape as xml_escape
from sqlalchemy.orm import Session, joinedload
from collections import defaultdict
from datetime import datetime
from pathlib import Path
import json
from fastapi import Response
from sqlalchemy import func
from .database import Base, engine, SessionLocal
from . import chat, models, schemas, services
from .matching import candidato_compatible
from .matching_diagnostics import resumen_matching
from .normalizacion import (
    calcular_precio_referencia,
    clave_comparable,
    detectar_familia,
    detectar_familia_busqueda,
    normalizar_formato,
    normalizar_texto,
    tokens_utiles,
)

Base.metadata.create_all(bind=engine)

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"http://(localhost|127\.0\.0\.1|192\.168\.\d+\.\d+|10\.\d+\.\d+\.\d+):(5500|3000)",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Techo de productos crudos a considerar antes de agrupar. Tiene que ser holgado
# respecto del limit por pagina: si se corta antes de agrupar, cadenas enteras
# quedan fuera (paso con Tottus, cuyos ids son los mas altos).
CANDIDATOS_MAX = 600


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.get("/")
def inicio():
    return {"mensaje": "SuperCheck funcionando ðŸš€"}


@app.get("/buscar/{texto}")
def buscar(
    texto: str,
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    return services.buscar_opciones_producto(db, texto[:100], limit=limit, offset=offset)


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
    por_proveedor = defaultdict(int)
    por_subcategoria = defaultdict(int)
    sin_imagen = 0
    sin_url = 0
    url_generica = 0
    precio_sospechoso = []

    precios = db.query(
        models.Producto.nombre.label("producto_nombre"),
        models.Subcategoria.nombre.label("subcategoria_nombre"),
        models.Proveedor.nombre.label("proveedor_nombre"),
        models.Precio.precio_normal,
        models.Precio.precio_oferta,
        models.Precio.imagen_url,
        models.Precio.url_producto,
    ).join(
        models.Producto,
        models.Precio.producto_id == models.Producto.id,
    ).join(
        models.Proveedor,
        models.Precio.proveedor_id == models.Proveedor.id,
    ).outerjoin(
        models.Subcategoria,
        models.Producto.subcategoria_id == models.Subcategoria.id,
    ).yield_per(500)

    total_precios = 0
    for precio in precios:
        total_precios += 1
        supermercado = precio.proveedor_nombre
        subcategoria = precio.subcategoria_nombre or "Sin subcategoria"
        valor = valor_precio_por_nombre(
            precio.producto_nombre,
            precio.precio_normal,
            precio.precio_oferta,
        )

        por_proveedor[supermercado] += 1
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
                "producto": precio.producto_nombre,
                "proveedor": supermercado,
                "precio_normal": precio.precio_normal,
                "precio_oferta": precio.precio_oferta,
                "valor_usado": valor,
            })

    return {
        "productos": db.query(models.Producto).count(),
        "precios": total_precios,
        "proveedores": dict(sorted(por_proveedor.items())),
        "subcategorias": dict(sorted(por_subcategoria.items())),
        "sin_imagen": sin_imagen,
        "sin_url": sin_url,
        "url_generica": url_generica,
        "precios_sospechosos": {
            "total": len(precio_sospechoso),
            "muestra": precio_sospechoso[:20],
        },
    }


@app.get("/diagnostico/matching")
def diagnostico_matching(db: Session = Depends(get_db)):
    return resumen_matching(db)


@app.get("/estado-datos")
def estado_datos(db: Session = Depends(get_db)):
    root = Path(__file__).resolve().parents[1]
    db_path = root / "supercheck.db"
    csv_path = root / "data" / "productos_supermercados.csv"
    logs_path = root / "logs"
    por_proveedor = dict(
        db.query(models.Proveedor.nombre, func.count(models.Precio.id))
        .join(models.Precio, models.Precio.proveedor_id == models.Proveedor.id)
        .group_by(models.Proveedor.nombre)
        .all()
    )

    ultimo_log = None
    if logs_path.exists():
        logs = sorted(logs_path.glob("actualizacion_productos_*.log"), key=lambda item: item.stat().st_mtime, reverse=True)
        if logs:
            ultimo_log = {
                "archivo": logs[0].name,
                "fecha": datetime.fromtimestamp(logs[0].stat().st_mtime).isoformat(timespec="seconds"),
            }

    estado = {
        "productos": db.query(models.Producto).count(),
        "precios": db.query(models.Precio).count(),
        "proveedores": dict(sorted(por_proveedor.items())),
        "base_actualizada": datetime.fromtimestamp(db_path.stat().st_mtime).isoformat(timespec="seconds") if db_path.exists() else None,
        "csv_actualizado": datetime.fromtimestamp(csv_path.stat().st_mtime).isoformat(timespec="seconds") if csv_path.exists() else None,
        "ultimo_log": ultimo_log,
    }
    return Response(
        content=json.dumps(estado, ensure_ascii=True),
        media_type="application/json",
    )


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


def valor_precio_por_nombre(nombre_producto, precio_normal, precio_oferta):
    familia = detectar_familia(normalizar_texto(nombre_producto))

    if (
        precio_oferta and
        precio_normal and
        precio_oferta < 500 and
        precio_normal > precio_oferta * 2
    ):
        return precio_normal

    if (
        familia == "papel_higienico" and
        precio_oferta and
        precio_normal and
        precio_oferta < 500 and
        precio_normal >= 500
    ):
        return precio_normal

    return precio_oferta if precio_oferta else precio_normal


def precio_valido_para_comparar(producto, precio):
    valor = valor_precio_producto(producto, precio)
    familia = detectar_familia(normalizar_texto(producto.nombre))

    if not valor or valor <= 0:
        return False

    if familia == "papel_higienico" and valor < 500:
        return False

    return True


def valor_precio_producto(producto, precio):
    return valor_precio_por_nombre(producto.nombre, precio.precio_normal, precio.precio_oferta)


def buscar_url_por_atributos(db, producto, precio):
    requeridos = tokens_utiles(
        "" if producto.marca == "Sin marca" else producto.marca,
        "" if producto.tipo == "general" else producto.tipo,
        producto.formato
    )

    if not requeridos:
        return None

    candidatos = db.query(models.Producto, models.Precio).join(models.Precio).filter(
        models.Precio.proveedor_id == precio.proveedor_id,
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
        models.Precio.proveedor_id == precio.proveedor_id,
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



def _url_especifica_cached(producto, precio, urls_por_base, producto_por_id):
    if es_url_producto_especifica(precio.url_producto):
        return precio.url_producto
    if not producto.producto_base:
        return None
    for precio_candidato in urls_por_base.get((precio.proveedor_id, producto.producto_base), []):
        candidato = producto_por_id.get(precio_candidato.producto_id)
        if candidato and candidato_compatible(producto, candidato):
            return precio_candidato.url_producto
    return None


@app.get("/productos/buscar/{texto}")
def buscar_productos(
    texto: str,
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    texto = texto[:100]
    limit, offset = services.normalizar_paginacion(limit, offset)
    palabras = tokens_utiles(texto)
    if not palabras:
        return []
    familia_buscada = detectar_familia_busqueda(texto)

    # Filtrar en la BD usando los indices (en vez de cargar los 50k productos).
    #
    # OJO: el limit/offset NO va aca. Antes se cortaban las filas crudas ordenadas
    # por id y, como cada cadena se importa en bloque, la ultima quedaba fuera del
    # corte: al sumar Tottus (ids mas altos) desaparecio entera de los resultados.
    # Se toma un techo de candidatos, se agrupa, y recien ahi se pagina por GRUPO.
    condiciones = [models.Producto.nombre.ilike(f"%{p}%") for p in palabras]
    productos = db.query(models.Producto).filter(*condiciones).limit(CANDIDATOS_MAX).all()
    if familia_buscada:
        productos = [p for p in productos
                     if detectar_familia(normalizar_texto(p.nombre)) == familia_buscada]
    if "azucar" in palabras:
        productos = [p for p in productos
                     if "sin azucar" not in normalizar_texto(p.nombre)]

    # Cargar equivalentes vÃ­a producto_base (ya indexado) para el agrupamiento cross-proveedor
    bases = {p.producto_base for p in productos if p.producto_base}
    if bases:
        equivalentes = db.query(models.Producto).filter(
            models.Producto.producto_base.in_(bases)
        ).all()
    else:
        equivalentes = []
    todos_relevantes = {p.id: p for p in [*productos, *equivalentes]}
    producto_por_id = todos_relevantes

    # Cargar precios solo para los productos relevantes
    ids_relevantes = list(todos_relevantes.keys())
    todos_precios = db.query(models.Precio).filter(
        models.Precio.producto_id.in_(ids_relevantes)
    ).options(joinedload(models.Precio.proveedor)).all()

    precios_por_producto = defaultdict(list)
    urls_por_base = defaultdict(list)
    for precio in todos_precios:
        precios_por_producto[precio.producto_id].append(precio)
        if es_url_producto_especifica(precio.url_producto):
            prod = todos_relevantes.get(precio.producto_id)
            if prod and prod.producto_base:
                urls_por_base[(precio.proveedor_id, prod.producto_base)].append(precio)

    resultado = []
    grupos_vistos = set()
    grupos_por_clave = defaultdict(list)

    for candidato in todos_relevantes.values():
        grupos_por_clave[clave_comparable(candidato)].append(candidato)

    for producto in productos:
        grupo_id = clave_comparable(producto)

        if grupo_id in grupos_vistos:
            continue

        grupos_vistos.add(grupo_id)

        equivalentes = grupos_por_clave[grupo_id] or [producto]
        mejor_por_proveedor = {}

        for equivalente in equivalentes:
            if not candidato_compatible(producto, equivalente):
                continue

            for precio in precios_por_producto[equivalente.id]:
                if not precio_valido_para_comparar(equivalente, precio):
                    continue

                valor = valor_precio_producto(equivalente, precio)
                proveedor = precio.proveedor.nombre
                tiene_descuento = bool(
                    precio.precio_oferta and
                    precio.precio_normal and
                    valor == precio.precio_oferta and
                    precio.precio_oferta < precio.precio_normal and
                    precio.precio_normal <= precio.precio_oferta * 2
                )

                mejor_actual = mejor_por_proveedor.get(proveedor)
                if mejor_actual and mejor_actual["precio"] <= valor:
                    continue

                mejor_por_proveedor[proveedor] = {
                    "proveedor": proveedor,
                    "precio": valor,
                    "precio_normal": precio.precio_normal,
                    "precio_oferta": precio.precio_oferta,
                    "tiene_descuento": tiene_descuento,
                    "descuento": int(round((1 - precio.precio_oferta / precio.precio_normal) * 100)) if tiene_descuento else 0,
                    "promocion": precio.promocion,
                    "precio_referencia": precio.precio_referencia or calcular_precio_referencia(valor, equivalente.formato),
                    "url": _url_especifica_cached(equivalente, precio, urls_por_base, producto_por_id),
                    "imagen_url": precio.imagen_url,
                    "nombre": equivalente.nombre
                }

        lista_precios = sorted(
            mejor_por_proveedor.values(),
            key=lambda item: item["precio"]
        )

        if not lista_precios:
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

    # La paginacion se aplica sobre los grupos ya armados, no sobre las filas
    # crudas: asi todas las cadenas compiten por aparecer.
    return resultado[offset:offset + limit]


def equivalentes_por_item(db, items):
    """Para cada producto_id pedido, junta los productos comparables de otros proveedores.

    El carrito manda el id de un producto concreto, pero el mismo articulo existe con
    otro id en cada proveedor. El nexo es producto_base, igual que en /productos/buscar.
    """
    ids = [item.producto_id for item in items]

    productos = db.query(models.Producto).filter(
        models.Producto.id.in_(ids)
    ).all()
    producto_por_id = {p.id: p for p in productos}

    bases = {p.producto_base for p in productos if p.producto_base}
    if bases:
        candidatos = db.query(models.Producto).filter(
            models.Producto.producto_base.in_(bases)
        ).all()
    else:
        candidatos = []

    candidatos_por_base = defaultdict(list)
    for candidato in candidatos:
        candidatos_por_base[candidato.producto_base].append(candidato)

    comparables_por_id = {}
    for pid, producto in producto_por_id.items():
        grupo = {producto.id: producto}
        for candidato in candidatos_por_base.get(producto.producto_base, []):
            mismo_ean = bool(producto.ean) and candidato.ean == producto.ean
            if mismo_ean or candidato_compatible(producto, candidato):
                grupo[candidato.id] = candidato
        comparables_por_id[pid] = list(grupo.values())

    return producto_por_id, comparables_por_id


def calcular_resumen_compra(db, items):
    producto_por_id, comparables_por_id = equivalentes_por_item(db, items)

    ids_relevantes = {p.id for grupo in comparables_por_id.values() for p in grupo}
    if ids_relevantes:
        precios_todos = db.query(models.Precio).filter(
            models.Precio.producto_id.in_(ids_relevantes)
        ).options(joinedload(models.Precio.proveedor)).all()
    else:
        precios_todos = []

    precios_por_producto = defaultdict(list)
    for precio in precios_todos:
        precios_por_producto[precio.producto_id].append(precio)

    # Clave = id pedido por el carrito; valor = (producto que tiene ese precio, precio).
    # El producto viaja junto al precio porque valor_precio_producto lo necesita.
    precios_por_item = defaultdict(list)
    for pid, grupo in comparables_por_id.items():
        for equivalente in grupo:
            for precio in precios_por_producto.get(equivalente.id, []):
                if precio_valido_para_comparar(equivalente, precio):
                    precios_por_item[pid].append((equivalente, precio))

    mejor_precio_por_super = {}
    todos_proveedores = set()
    for pid, pares in precios_por_item.items():
        for equivalente, p in pares:
            pname = p.proveedor.nombre
            todos_proveedores.add(pname)
            val = valor_precio_producto(equivalente, p)
            key = (pid, pname)
            if key not in mejor_precio_por_super or val < mejor_precio_por_super[key]:
                mejor_precio_por_super[key] = val

    total_optimo = 0
    distribucion = defaultdict(lambda: {"cantidad": 0, "subtotal": 0})
    productos_sin_comparacion = []

    for item in items:
        pid = item.producto_id
        cantidad = item.cantidad
        producto = producto_por_id.get(pid)

        if not producto:
            productos_sin_comparacion.append({"id": pid, "nombre": "Producto no encontrado"})
            continue

        pares = precios_por_item.get(pid, [])
        if not pares:
            productos_sin_comparacion.append({"id": pid, "nombre": producto.nombre})
            continue

        proveedores_disponibles = {p.proveedor.nombre for _, p in pares}
        if len(proveedores_disponibles) == 1:
            productos_sin_comparacion.append({"id": pid, "nombre": producto.nombre})

        equivalente_mejor, mejor = min(pares, key=lambda par: valor_precio_producto(par[0], par[1]))
        valor = valor_precio_producto(equivalente_mejor, mejor)
        subtotal = valor * cantidad

        total_optimo += subtotal
        pname = mejor.proveedor.nombre
        distribucion[pname]["cantidad"] += cantidad
        distribucion[pname]["subtotal"] += subtotal

    if total_optimo == 0:
        return {
            "total_optimo": 0, "ahorro": 0, "porcentaje": 0,
            "mejor_proveedor_unico": None, "total_mejor_proveedor_unico": None,
            "distribucion": {}, "tiendas_optimas": 0,
            "productos_sin_comparacion": productos_sin_comparacion,
            "recomendacion": "sin_datos",
            "mensaje": "No encontramos precios para estos productos",
        }

    ids_con_precios = set(precios_por_item.keys())
    totales_proveedor_completo = {}
    for pname in todos_proveedores:
        total = 0
        completo = True
        for item in items:
            if item.producto_id not in ids_con_precios:
                continue
            key = (item.producto_id, pname)
            if key not in mejor_precio_por_super:
                completo = False
                break
            total += mejor_precio_por_super[key] * item.cantidad
        if completo:
            totales_proveedor_completo[pname] = total

    if totales_proveedor_completo:
        mejor_proveedor, total_mejor_proveedor = min(totales_proveedor_completo.items(), key=lambda x: x[1])
        ahorro = total_mejor_proveedor - total_optimo
    else:
        cobertura = {}
        totales_parciales = {}
        for pname in todos_proveedores:
            cobertura[pname] = sum(
                1 for item in items if (item.producto_id, pname) in mejor_precio_por_super
            )
            totales_parciales[pname] = sum(
                mejor_precio_por_super[(item.producto_id, pname)] * item.cantidad
                for item in items if (item.producto_id, pname) in mejor_precio_por_super
            )
        max_coverage = max(cobertura.values())
        proveedores_con_max = [s for s, c in cobertura.items() if c == max_coverage]
        mejor_proveedor = min(proveedores_con_max, key=lambda s: totales_parciales[s])
        total_mejor_proveedor = None
        ahorro = 0

    tiendas_optimas = len(distribucion)

    if total_mejor_proveedor is None:
        recomendacion = "una_tienda"
        mensaje = f"No encontramos todos los productos en una sola tienda. {mejor_proveedor} tiene la mayor cobertura."
    elif ahorro < 1000 or tiendas_optimas == 1:
        recomendacion = "una_tienda"
        mensaje = f"Te conviene comprar todo en {mejor_proveedor}"
    elif ahorro < 7000:
        recomendacion = "ahorro_bajo"
        mensaje = f"Por ${ahorro:,.0f} de diferencia, conviene comprar todo en {mejor_proveedor}".replace(",", ".")
    elif ahorro < 15000:
        recomendacion = "dividir_compra"
        mensaje = f"Te conviene dividir en {tiendas_optimas} supermercados"
    else:
        recomendacion = "dividir_fuerte"
        mensaje = f"Vale la pena dividir: ahorras ${ahorro:,.0f}".replace(",", ".")

    return {
        "total_optimo": total_optimo,
        "ahorro": ahorro,
        "porcentaje": round(ahorro / total_mejor_proveedor, 4) if total_mejor_proveedor else 0,
        "mejor_proveedor_unico": mejor_proveedor,
        "total_mejor_proveedor_unico": total_mejor_proveedor,
        "distribucion": dict(distribucion),
        "tiendas_optimas": tiendas_optimas,
        "productos_sin_comparacion": productos_sin_comparacion,
        "recomendacion": recomendacion,
        "mensaje": mensaje,
    }


@app.post("/productos/resumen-compra")
def resumen_compra(request: schemas.ResumenCompraRequest, db: Session = Depends(get_db)):
    return calcular_resumen_compra(db, request.items)


@app.post("/webhook/whatsapp")
async def webhook_whatsapp(request: Request, db: Session = Depends(get_db)):
    """Webhook de WhatsApp en formato Twilio: form-urlencoded entra, TwiML sale.

    Twilio manda el mensaje del usuario en el campo Body. La logica vive en
    app.chat (independiente del canal); esto solo traduce el transporte.
    """
    form = await request.form()
    respuesta = chat.responder(db, str(form.get("Body", "")))
    twiml = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        f"<Response><Message>{xml_escape(respuesta)}</Message></Response>"
    )
    return Response(content=twiml, media_type="application/xml")

