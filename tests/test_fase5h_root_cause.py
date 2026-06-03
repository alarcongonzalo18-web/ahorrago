from app.scripts.auditoria_root_cause_fase5h import causa_probable, seleccionar_muestra, trazar_productos


def test_causa_probable_detecta_scraper_si_fuente_y_bd_coinciden_en_error():
    row = {"categoria_actual": "Bebe", "subcategoria_actual": "Alimentos Bebe"}
    fuente = {"categoria": "Bebe", "subcategoria": "Alimentos Bebe"}
    bd = {"categoria": "Bebe", "subcategoria": "Alimentos Bebe"}

    causa, script, punto = causa_probable(row, fuente, [fuente], bd)

    assert causa == "scraper_categoria_por_busqueda_amplia"
    assert script == "scraper_fuente"
    assert "CSV fuente" in punto


def test_seleccionar_muestra_incluye_productos_prioritarios():
    hallazgos = [
        {
            "producto_id": str(index),
            "nombre": nombre,
            "confianza": "Alta",
            "motivo": "Bebida detectada dentro de categoria Bebe",
        }
        for index, nombre in enumerate([
            "Bebida Vegetal NotMilk Original",
            "Bebida Yogu Yogu Mora",
            "Bebida Milo Chocolate",
            "Bebida Coca-Cola Original",
            "Producto Generico",
        ], start=1)
    ]

    muestra = seleccionar_muestra(hallazgos, minimo=4)
    nombres = " ".join(item["nombre"].lower() for item in muestra)

    assert "notmilk" in nombres
    assert "yogu yogu" in nombres
    assert "milo" in nombres
    assert "coca-cola" in nombres


def test_trazabilidad_real_read_only_contiene_ejemplos_criticos():
    trazas = trazar_productos(minimo=50)
    nombres = " ".join(row["producto_nombre"].lower() for row in trazas)
    causas = {row["causa_probable"] for row in trazas}

    assert len(trazas) >= 50
    for esperado in ["notmilk", "yogu yogu", "milo", "coca-cola", "master dog", "pet food", "nivea"]:
        assert esperado in nombres
    assert "scraper_categoria_por_busqueda_amplia" in causas
