import csv

from app import backfill_ean


def _escribir_csv(path, filas, campos):
    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=campos)
        w.writeheader()
        w.writerows(filas)


def _leer_csv(path):
    with open(path, newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def test_backfill_llena_ean_y_es_resumible(tmp_path, monkeypatch):
    csv_path = tmp_path / "jumbo_real.csv"
    # CSV sin columna ean (como los reales viejos); una fila ya con ean simulada aparte
    _escribir_csv(
        csv_path,
        [
            {"nombre": "Pan", "url": "https://www.jumbo.cl/pan-ideal/p"},
            {"nombre": "Leche", "url": "https://www.jumbo.cl/leche-colun/p"},
            {"nombre": "Raro", "url": "https://www.jumbo.cl/sin-slug-valido"},
        ],
        ["nombre", "url"],
    )

    llamadas = []

    def fake_fetch(slug):
        llamadas.append(slug)
        return {"pan-ideal": "7803473002662", "leche-colun": "7802920000084"}.get(slug, "")

    monkeypatch.setitem(backfill_ean.FUENTES, "jumbo", {
        "path": csv_path,
        "slug": backfill_ean.slug_jumbo,
        "fetch": fake_fetch,
    })
    monkeypatch.setattr(backfill_ean.time, "sleep", lambda *_: None)

    backfill_ean.backfill("jumbo", pausa=0)

    filas = _leer_csv(csv_path)
    por_nombre = {f["nombre"]: f for f in filas}
    assert por_nombre["Pan"]["ean"] == "7803473002662"
    assert por_nombre["Leche"]["ean"] == "7802920000084"
    assert por_nombre["Raro"]["ean"] == ""      # url sin slug -> no se consulta
    assert "sin-slug-valido" not in llamadas
    assert set(llamadas) == {"pan-ideal", "leche-colun"}

    # segunda corrida: es resumible -> no vuelve a consultar los que ya tienen ean
    llamadas.clear()
    backfill_ean.backfill("jumbo", pausa=0)
    assert llamadas == []


def test_backfill_respeta_limite(tmp_path, monkeypatch):
    csv_path = tmp_path / "unimarc_real.csv"
    _escribir_csv(
        csv_path,
        [{"nombre": f"P{i}", "url": f"https://www.unimarc.cl/product/p-{i}"} for i in range(5)],
        ["nombre", "url"],
    )

    llamadas = []

    def fake_fetch(slug):
        llamadas.append(slug)
        return "7801111111119"

    monkeypatch.setitem(backfill_ean.FUENTES, "unimarc", {
        "path": csv_path,
        "slug": backfill_ean.slug_unimarc,
        "fetch": fake_fetch,
    })
    monkeypatch.setattr(backfill_ean.time, "sleep", lambda *_: None)

    backfill_ean.backfill("unimarc", pausa=0, limite=2)
    assert len(llamadas) == 2
    con_ean = sum(1 for f in _leer_csv(csv_path) if f["ean"])
    assert con_ean == 2
