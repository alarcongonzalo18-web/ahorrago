import csv

from app import backfill_ean, ean_cache


def _escribir_csv(path, filas, campos):
    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=campos)
        w.writeheader()
        w.writerows(filas)


# --- caché ---

def test_cache_roundtrip_y_semantica_del_vacio(tmp_path):
    ruta = tmp_path / "ean_cache.json"
    assert ean_cache.cargar(ruta) == {}      # no existe todavía

    cache = {}
    ean_cache.poner(cache, "Jumbo", "pan-ideal", "7803473002662")
    ean_cache.poner(cache, "Jumbo", "granel-sin-codigo", "")   # consultado, sin EAN
    ean_cache.guardar(cache, ruta)

    leida = ean_cache.cargar(ruta)
    assert ean_cache.obtener(leida, "Jumbo", "pan-ideal") == "7803473002662"
    # "" significa "ya se preguntó y no tiene": está cacheado aunque devuelva ""
    assert ean_cache.tiene(leida, "Jumbo", "granel-sin-codigo")
    assert ean_cache.obtener(leida, "Jumbo", "granel-sin-codigo") == ""
    # nunca consultado
    assert not ean_cache.tiene(leida, "Jumbo", "otro")
    assert ean_cache.total(leida) == (2, 1)


def test_cache_corrupta_no_revienta(tmp_path):
    ruta = tmp_path / "ean_cache.json"
    ruta.write_text("{ esto no es json", encoding="utf-8")
    assert ean_cache.cargar(ruta) == {}


# --- backfill ---

def test_backfill_puebla_cache_y_es_incremental(tmp_path, monkeypatch):
    csv_path = tmp_path / "jumbo_real.csv"
    ruta_cache = tmp_path / "ean_cache.json"
    _escribir_csv(
        csv_path,
        [
            {"nombre": "Pan", "url": "https://www.jumbo.cl/pan-ideal/p"},
            {"nombre": "Leche", "url": "https://www.jumbo.cl/leche-colun/p"},
            {"nombre": "Repetido", "url": "https://www.jumbo.cl/pan-ideal/p"},   # mismo slug
            {"nombre": "Raro", "url": "https://www.jumbo.cl/sin-slug-valido"},
        ],
        ["nombre", "url"],
    )

    llamadas = []

    def fake_fetch(slug):
        llamadas.append(slug)
        return {"pan-ideal": "7803473002662", "leche-colun": "7802920000084"}.get(slug, "")

    monkeypatch.setitem(backfill_ean.FUENTES, "jumbo", {
        "cadena": "Jumbo",
        "path": csv_path,
        "slug": backfill_ean.slug_jumbo,
        "fetch": fake_fetch,
    })
    monkeypatch.setattr(backfill_ean.time, "sleep", lambda *_: None)

    cache = backfill_ean.backfill("jumbo", pausa=0, cache_path=ruta_cache)

    assert ean_cache.obtener(cache, "Jumbo", "pan-ideal") == "7803473002662"
    assert ean_cache.obtener(cache, "Jumbo", "leche-colun") == "7802920000084"
    # el slug repetido se consulta una sola vez; la url sin slug no se consulta
    assert sorted(llamadas) == ["leche-colun", "pan-ideal"]

    # segunda corrida: incremental, no vuelve a consultar nada
    llamadas.clear()
    backfill_ean.backfill("jumbo", pausa=0, cache_path=ruta_cache)
    assert llamadas == []


def test_backfill_respeta_limite(tmp_path, monkeypatch):
    csv_path = tmp_path / "unimarc_real.csv"
    ruta_cache = tmp_path / "ean_cache.json"
    _escribir_csv(
        csv_path,
        [{"nombre": f"P{i}", "url": f"https://www.unimarc.cl/product/p-{i}"} for i in range(5)],
        ["nombre", "url"],
    )

    llamadas = []
    monkeypatch.setitem(backfill_ean.FUENTES, "unimarc", {
        "cadena": "Unimarc",
        "path": csv_path,
        "slug": backfill_ean.slug_unimarc,
        "fetch": lambda slug: (llamadas.append(slug), "7801111111119")[1],
    })
    monkeypatch.setattr(backfill_ean.time, "sleep", lambda *_: None)

    cache = backfill_ean.backfill("unimarc", pausa=0, limite=2, cache_path=ruta_cache)
    assert len(llamadas) == 2
    assert ean_cache.total(cache) == (2, 2)


# --- integración: combinar enriquece desde la caché ---

def test_combinar_enriquece_jumbo_desde_la_cache(tmp_path, monkeypatch):
    """El punto de todo: el CSV viene sin ean (re-scrapeado) y igual sale con EAN."""
    from app import combinar_supermercados as comb

    csv_path = tmp_path / "jumbo_real.csv"
    _escribir_csv(
        csv_path,
        [{
            "categoria": "Lacteos", "subcategoria": "Leche",
            "nombre": "Leche Colun Entera 1 L", "precio": "1290",
            "precio_normal": "1290", "precio_oferta": "", "precio_referencia": "",
            "promocion": "", "url": "https://www.jumbo.cl/leche-colun/p", "imagen_url": "",
        }],
        ["categoria", "subcategoria", "nombre", "precio", "precio_normal",
         "precio_oferta", "precio_referencia", "promocion", "url", "imagen_url"],
    )

    cache = {}
    ean_cache.poner(cache, "Jumbo", "leche-colun", "7802920777542")

    filas = comb.leer_filas(csv_path, "Jumbo", cache)
    assert len(filas) == 1
    assert filas[0]["ean"] == "7802920777542"

    # sin caché, la misma fila queda sin EAN (no inventa nada)
    assert comb.leer_filas(csv_path, "Jumbo", {})[0]["ean"] == ""
