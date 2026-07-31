

def test_lider_no_se_duplica_entre_sus_dos_fuentes(tmp_path, monkeypatch):
    """Lider llega por /v/ y por /browse; el mismo EAN no debe entrar dos veces.

    Los endpoints dan distinto nombre y categoria para el mismo producto, asi que
    la dedup por (nombre, precio) no alcanza: hace falta la dedup por EAN.
    """
    import csv as _csv
    from app import combinar_supermercados as cs

    def _csv_con(path, filas):
        with open(path, "w", newline="", encoding="utf-8") as f:
            w = _csv.DictWriter(f, fieldnames=[
                "categoria", "subcategoria", "nombre", "precio", "precio_normal",
                "precio_oferta", "precio_referencia", "promocion", "url", "imagen_url", "ean"])
            w.writeheader()
            w.writerows(filas)

    browse = tmp_path / "lider_browse.csv"
    viejo = tmp_path / "lider_real.csv"
    comun = {"ean": "7805000315559", "precio": "3000", "precio_normal": "3690",
             "precio_oferta": "", "precio_referencia": "", "promocion": "",
             "url": "/ip/jabones/00780500031555", "imagen_url": ""}
    _csv_con(browse, [dict(comun, categoria="Higiene Personal", subcategoria="Jabones",
                           nombre="Jabon Liquido Dove Karite 700ml")])
    _csv_con(viejo, [
        dict(comun, categoria="Higiene Personal", subcategoria="Jabon",
             nombre="Jabon Dove Karite 700 Ml", precio="3100"),          # mismo EAN, otro nombre
        dict(comun, ean="7802920008141", categoria="Lacteos, Huevos y Congelados",
             subcategoria="Leche", nombre="Leche Colun Entera 1 L",
             url="/ip/leche/00780292000814"),                            # solo en el viejo
    ])

    monkeypatch.setattr(cs, "FUENTES", [(str(browse), "Líder"), (str(viejo), "Líder")])
    monkeypatch.setattr(cs, "OUTPUT", tmp_path / "salida.csv")
    cs.combinar()

    filas = list(_csv.DictReader(open(tmp_path / "salida.csv", encoding="utf-8-sig")))
    eans = [f["ean"] for f in filas]
    assert len(filas) == 2, "el producto comun a las dos fuentes se duplico"
    assert sorted(eans) == ["7802920008141", "7805000315559"]
    # gana la version del /browse (va primero en FUENTES)
    jabon = next(f for f in filas if f["ean"] == "7805000315559")
    assert jabon["subcategoria"] == "Jabones"
