from datetime import datetime, timedelta

from app.estado_pipeline import diagnostico, registrar


def test_registrar_ok_y_fallo(tmp_path):
    ruta = tmp_path / "estado.json"

    registrar("pipeline-completo", True, "OK (lider, jumbo)", 42.5, path=ruta)
    d = diagnostico(path=ruta)
    assert d["ok"] and d["problemas"] == []
    assert d["tareas"]["pipeline-completo"]["duracion_min"] == 42.5

    registrar("ean-backfill", False, "HTTPError 500", path=ruta)
    d = diagnostico(path=ruta)
    assert not d["ok"]
    assert any("ean-backfill" in p for p in d["problemas"])


def test_conserva_el_ultimo_ok_al_fallar(tmp_path):
    """Lo que importa no es "fallo recien" sino "hace cuanto que no funciona"."""
    ruta = tmp_path / "estado.json"
    ayer = datetime.now() - timedelta(days=1)

    registrar("tottus", True, "OK", ahora=ayer, path=ruta)
    registrar("tottus", False, "timeout", path=ruta)

    tarea = diagnostico(path=ruta)["tareas"]["tottus"]
    assert tarea["ok"] is False
    # el ultimo OK sigue apuntando a ayer, no se pierde
    assert tarea["ultimo_ok"].startswith(ayer.strftime("%Y-%m-%d"))


def test_detecta_tarea_atrasada_aunque_nunca_haya_fallado(tmp_path):
    """El caso silencioso: un scheduler que no dispara no deja ningun error."""
    ruta = tmp_path / "estado.json"
    registrar("lider", True, "OK", ahora=datetime.now() - timedelta(hours=40), path=ruta)

    d = diagnostico(path=ruta)
    assert not d["ok"]
    assert any("lider" in p and "sin corrida exitosa" in p for p in d["problemas"])

    # dentro de la ventana normal no molesta
    registrar("lider", True, "OK", ahora=datetime.now() - timedelta(hours=10), path=ruta)
    assert diagnostico(path=ruta)["ok"]


def test_archivo_ausente_o_corrupto_no_revienta(tmp_path):
    assert diagnostico(path=tmp_path / "no-existe.json") == {
        "ok": True, "problemas": [], "tareas": {}
    }
    roto = tmp_path / "roto.json"
    roto.write_text("{ esto no es json", encoding="utf-8")
    assert diagnostico(path=roto)["tareas"] == {}
