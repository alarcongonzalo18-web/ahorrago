from app.scraper_lider import (
    SUBCATEGORIAS_DEGRADADAS,
    contar_por_subcategoria,
    fusionar_preservando,
    guardar_productos,
    leer_conteo_previo,
    solo_subcategorias,
    validar_anti_regresion,
)


def _producto(subcategoria, nombre):
    return {"subcategoria": subcategoria, "nombre": nombre}


def test_contar_por_subcategoria_agrupa():
    productos = [
        _producto("Leche", "a"),
        _producto("Leche", "b"),
        _producto("Yogurt", "c"),
    ]
    assert contar_por_subcategoria(productos) == {"Leche": 2, "Yogurt": 1}


def test_solo_subcategorias_filtra_conteo_y_filas():
    # dict (conteo)
    conteo = {"Leches y cremas": 50, "leche": 30, "yogurt": 20}
    assert solo_subcategorias(conteo, {"Leches y cremas"}) == {"Leches y cremas": 50}
    # lista de filas
    filas = [_producto("Leches y cremas", "a"), _producto("leche", "vieja")]
    assert solo_subcategorias(filas, {"Leches y cremas"}) == [_producto("Leches y cremas", "a")]


def test_guard_no_reporta_caidas_tras_migrar_taxonomia():
    """El caso real: al migrar keyword->categoria, el CSV previo trae subcats
    viejas ('leche', 'yogurt'); el mapeo nuevo usa otras ('Leches y cremas').
    Filtrando el baseline, el guard no ve caidas falsas."""
    previos = {"leche": 300, "yogurt": 200}          # taxonomia vieja
    nuevos = {"Leches y cremas": 280, "Yoghurt": 190}  # taxonomia nueva
    subcats_nuevas = {"Leches y cremas", "Yoghurt"}
    previos_filtrado = solo_subcategorias(previos, subcats_nuevas)
    assert validar_anti_regresion(nuevos, previos_filtrado) == []


def test_validar_anti_regresion_detecta_caida_fuerte_y_a_cero():
    previos = {"Leche": 100, "Salsas": 500, "Bebe": 471}
    nuevos = {"Leche": 100, "Salsas": 48, "Bebe": 0}
    caidas = dict((c[0], (c[1], c[2])) for c in validar_anti_regresion(nuevos, previos))
    assert caidas["Salsas"] == (500, 48)   # 90% menos
    assert caidas["Bebe"] == (471, 0)      # a cero
    assert "Leche" not in caidas           # sin cambios


def test_validar_anti_regresion_ignora_subidas_y_categorias_nuevas():
    previos = {"Leche": 50}
    nuevos = {"Leche": 200, "Pisco": 30}   # Leche sube, Pisco es nueva
    assert validar_anti_regresion(nuevos, previos) == []


def test_validar_anti_regresion_respeta_el_borde_del_umbral():
    previos = {"X": 100}
    # exactamente a la mitad NO es regresion (umbral 50%); un producto menos si.
    assert validar_anti_regresion({"X": 50}, previos, umbral=0.5) == []
    assert validar_anti_regresion({"X": 49}, previos, umbral=0.5) == [("X", 100, 49)]


def test_validar_anti_regresion_exime_categorias_degradadas():
    # Jabon esta en la lista de degradadas permanentes: aunque caiga a cero,
    # NO debe reportarse como regresion (no bloquea la corrida).
    assert "Jabon" in SUBCATEGORIAS_DEGRADADAS
    previos = {"Jabon": 54, "Cecinas": 322}
    nuevos = {"Jabon": 10, "Cecinas": 322}
    caidas = dict((c[0], (c[1], c[2])) for c in validar_anti_regresion(nuevos, previos))
    assert "Jabon" not in caidas
    assert caidas == {}


def _p(sub, nombre, precio="100"):
    return {"subcategoria": sub, "nombre": nombre, "precio": precio}


def test_fusionar_preservando_conserva_categoria_caida():
    # Cecinas cae 4->1 (throttling): se conservan sus filas PREVIAS.
    # Quesos sube 1->3: se toma la data nueva. Nada retrocede.
    previos = [_p("Cecinas", f"c{i}") for i in range(4)] + [_p("Quesos", "q0")]
    nuevos = [_p("Cecinas", "c0")] + [_p("Quesos", f"q{i}") for i in range(3)]
    fusion, preservadas = fusionar_preservando(nuevos, previos)
    conteo = contar_por_subcategoria(fusion)
    assert conteo["Cecinas"] == 4          # se mantuvo la previa, no la nueva de 1
    assert conteo["Quesos"] == 3           # la nueva, que subio
    assert [c[0] for c in preservadas] == ["Cecinas"]


def test_fusionar_preservando_no_toca_nada_si_todo_sube():
    previos = [_p("Leche", "a")]
    nuevos = [_p("Leche", "a"), _p("Leche", "b"), _p("Pisco", "x")]
    fusion, preservadas = fusionar_preservando(nuevos, previos)
    assert preservadas == []
    assert fusion == nuevos


def test_fusionar_preservando_ignora_degradadas():
    # Jabon cae 5->1 pero esta exenta: se toma la nueva (no se conserva la vieja).
    previos = [_p("Jabon", f"j{i}") for i in range(5)]
    nuevos = [_p("Jabon", "j0")]
    fusion, preservadas = fusionar_preservando(nuevos, previos)
    assert preservadas == []
    assert contar_por_subcategoria(fusion)["Jabon"] == 1


def test_leer_conteo_previo_roundtrip_y_archivo_inexistente(tmp_path):
    destino = tmp_path / "lider.csv"
    assert leer_conteo_previo(destino) == {}   # todavia no existe

    productos = [
        _producto("Leche", "a"),
        _producto("Leche", "b"),
        _producto("Quesos", "c"),
    ]
    guardar_productos(productos, destino)
    assert leer_conteo_previo(destino) == {"Leche": 2, "Quesos": 1}


def test_migracion_de_taxonomia_se_detecta():
    """Caso real Tottus 25-07: al migrar keyword->categoria, 4 subcategorias
    sobrevivieron por nombre ("Bebidas", "Frutas", "Vinos", "Verduras") pero
    con otro significado; el guard las leyo como regresion y preservo filas
    viejas mal categorizadas (papilla de bebe dentro de "Verduras")."""
    from app.scraper_lider import es_migracion_de_taxonomia

    # proporciones reales medidas en Tottus: 8 de 49 subcategorias sobrevivieron (16%)
    viejas = {"Leche", "Huevos", "Yogurt", "Quesos", "Mantequilla", "Crema", "Frutas",
              "Verduras", "Carnes", "Aves", "Cecinas", "Pescados", "Bebidas", "Jugos",
              "Aguas", "Cervezas", "Vinos", "Pan", "Shampoo", "Jabon"}
    nuevas = {"Leches", "Yoghurt", "Quesos", "Huevos", "Frutas", "Verduras", "Bebidas",
              "Aguas", "Cervezas", "Vinos", "Jugos y Nectar", "Panaderia", "Pasteleria",
              "Belleza", "Cuidado Personal", "Helados", "Vacuno", "Pollo"}
    assert es_migracion_de_taxonomia(viejas, nuevas)


def test_corrida_normal_no_es_migracion():
    """Misma taxonomia (aunque una categoria desaparezca): el guard debe actuar."""
    from app.scraper_lider import es_migracion_de_taxonomia

    previas = {"Leches", "Yoghurt", "Quesos", "Huevos", "Aguas", "Vinos"}
    assert not es_migracion_de_taxonomia(previas, previas)
    assert not es_migracion_de_taxonomia(previas, previas - {"Vinos"})


def test_sin_baseline_no_es_migracion():
    """Primera corrida absoluta: no hay nada previo, el guard no aplica igual."""
    from app.scraper_lider import es_migracion_de_taxonomia

    assert not es_migracion_de_taxonomia(set(), {"Leches", "Aguas"})
