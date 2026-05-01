from sqlalchemy.orm import Session
from .models import Producto, Precio


def buscar_producto(db: Session, nombre: str):
    nombre = nombre.lower().strip()

    producto = db.query(Producto).filter(
        Producto.nombre.ilike(f"%{nombre}%")
    ).first()

    if producto:
        return producto

    return db.query(Producto).filter(
        Producto.subcategoria.has(nombre=nombre)
    ).first()


def formatear_precio(valor):
    return f"${int(valor):,}".replace(",", ".")


def buscar_productos_equivalentes(db: Session, producto: Producto):
    if not producto.producto_base:
        return [producto]

    equivalentes = db.query(Producto).filter(
        Producto.producto_base == producto.producto_base
    ).all()

    return equivalentes or [producto]


def comparar_lista(db: Session, lista_productos):
    resultados = {}

    for item in lista_productos:
        producto = buscar_producto(db, item.nombre)

        if not producto:
            continue

        productos_equivalentes = buscar_productos_equivalentes(db, producto)
        mejor_por_supermercado = {}

        for producto_equivalente in productos_equivalentes:
            precios = db.query(Precio).filter(
                Precio.producto_id == producto_equivalente.id
            ).all()

            for precio in precios:
                valor = precio.precio_oferta if precio.precio_oferta else precio.precio_normal
                supermercado = precio.supermercado.nombre

                mejor_actual = mejor_por_supermercado.get(supermercado)
                if mejor_actual and mejor_actual["valor"] <= valor:
                    continue

                mejor_por_supermercado[supermercado] = {
                    "producto": producto_equivalente,
                    "precio": precio,
                    "valor": valor
                }

        for supermercado, mejor in mejor_por_supermercado.items():
            producto_comparado = mejor["producto"]
            precio = mejor["precio"]
            valor = mejor["valor"]
            subtotal = valor * item.cantidad

            if supermercado not in resultados:
                resultados[supermercado] = {
                    "supermercado": supermercado,
                    "total": 0,
                    "productos": []
                }

            resultados[supermercado]["total"] += subtotal

            resultados[supermercado]["productos"].append({
                "nombre": producto_comparado.nombre,
                "marca": producto_comparado.marca,
                "tipo": producto_comparado.tipo,
                "formato": producto_comparado.formato,
                "producto_base": producto_comparado.producto_base,
                "precio_unitario": valor,
                "cantidad": item.cantidad,
                "subtotal": subtotal,
                "promocion": precio.promocion,
                "url_producto": precio.url_producto
            })

    ordenado = sorted(
        resultados.values(),
        key=lambda x: x["total"]
    )

    if not ordenado:
        return {
            "mensaje": "No se encontraron productos para comparar.",
            "comparacion": []
        }

    mas_barato = ordenado[0]
    mas_caro = ordenado[-1]
    ahorro = mas_caro["total"] - mas_barato["total"]

    productos_comparados = {}

    for supermercado in ordenado:
        for prod in supermercado["productos"]:
            nombre_producto = prod.get("producto_base") or prod["nombre"]

            if nombre_producto not in productos_comparados:
                productos_comparados[nombre_producto] = []

            productos_comparados[nombre_producto].append({
                "nombre": prod["nombre"],
                "supermercado": supermercado["supermercado"],
                "precio": prod["precio_unitario"],
                "cantidad": prod["cantidad"],
                "subtotal": prod["subtotal"],
                "url": prod.get("url_producto")
            })

    compra_optima = {}

    def generar_link(nombre, supermercado):
        base = {
            "Líder": "https://www.lider.cl/supermercado/search?query=",
            "Unimarc": "https://www.unimarc.cl/search?q=",
            "Jumbo": "https://www.jumbo.cl/search?ft="
        }

        # limpiar texto
        palabras_eliminar = ["1 L", "1L", "ml", "cc"]

        limpio = nombre
        for palabra in palabras_eliminar:
            limpio = limpio.replace(palabra, "")

        limpio = limpio.strip()

        query = limpio.replace(" ", "%20")

        return base.get(supermercado, "") + query

    for nombre_producto, lista in productos_comparados.items():
        mejor = min(lista, key=lambda x: x["precio"])
        supermercado = mejor["supermercado"]

        if supermercado not in compra_optima:
            compra_optima[supermercado] = []

        compra_optima[supermercado].append({
            "nombre": mejor["nombre"],
            "precio": mejor["precio"],
            "cantidad": mejor["cantidad"],
            "subtotal": mejor["subtotal"],
            "url": mejor.get("url") or generar_link(mejor["nombre"], supermercado)
        })

    mensaje = "🛒 Comparación de compra\n\n"
    mensaje += f"🥇 Más barato total: {mas_barato['supermercado']}\n"
    mensaje += f"💰 Ahorro estimado: {formatear_precio(ahorro)}\n\n"

    mensaje += "🧠 Mejor opción por producto:\n"

    for nombre_producto, lista in productos_comparados.items():
        mejor = min(lista, key=lambda x: x["precio"])
        nombre_visible = mejor["nombre"]

        mensaje += f"\n🛒 {nombre_visible}\n"

        for item in lista:
            check = " ✅" if item["precio"] == mejor["precio"] else ""
            mensaje += f"- {item['supermercado']}: {formatear_precio(item['precio'])}{check}\n"

    mensaje += "\n🧠 Compra óptima sugerida:\n"

    for supermercado, productos in compra_optima.items():
        mensaje += f"\n🏬 {supermercado}:\n"

        total_supermercado = 0

        for producto in productos:
            total_supermercado += producto["subtotal"]
            mensaje += (
                f"- {producto['nombre']} "
                f"x{producto['cantidad']} "
                f"→ {formatear_precio(producto['subtotal'])}\n"
            )

            if producto.get("url"):
                mensaje += f"  🔗 {producto['url']}\n"

        mensaje += f"Subtotal en {supermercado}: {formatear_precio(total_supermercado)}\n"

    mensaje += "\n📌 Precios referenciales sujetos a stock y disponibilidad."

    return {
        "mejor_opcion": mas_barato["supermercado"],
        "ahorro": ahorro,
        "comparacion": ordenado,
        "compra_optima": compra_optima,
        "mensaje": mensaje
    }


def buscar_opciones_producto(db: Session, texto: str):
    texto = texto.lower().strip()

    productos = db.query(Producto).filter(
        Producto.nombre.ilike(f"%{texto}%")
    ).all()

    return [
        {
            "id": producto.id,
            "nombre": producto.nombre,
            "categoria": producto.categoria.nombre if producto.categoria else None,
            "subcategoria": producto.subcategoria.nombre if producto.subcategoria else None,
            "marca": producto.marca,
            "tipo": producto.tipo,
            "formato": producto.formato
        }
        for producto in productos
    ]
