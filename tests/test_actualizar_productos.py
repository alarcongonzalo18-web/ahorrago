

def test_lider_browse_no_corre_en_la_nocturna():
    """Necesita Chrome visible (Akamai): colgaria la tarea programada."""
    from app.actualizar_productos import SCRAPERS, SCRAPERS_AUTOMATICOS, parsear_args

    assert "lider-browse" in SCRAPERS
    assert "lider-browse" not in SCRAPERS_AUTOMATICOS
    assert parsear_args([]) == list(SCRAPERS_AUTOMATICOS)


def test_lider_browse_se_puede_pedir_a_mano():
    from app.actualizar_productos import nombre_tarea, parsear_args

    assert parsear_args(["--solo", "lider-browse"]) == ["lider-browse"]
    assert nombre_tarea(["lider-browse"]) == "lider-browse"
    # la corrida desatendida completa sigue etiquetandose igual
    assert nombre_tarea(["lider", "jumbo", "unimarc", "tottus"]) == "pipeline-completo"
