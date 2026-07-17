from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base
from app.importar_csv import unificar_producto_base_por_ean
from app.models import Categoria, Precio, Producto, Proveedor
from app.url_utils import extraer_ean_lider


def test_extraer_ean_lider_desde_url_real():
    url = "https://super.lider.cl/ip/leches-colacion/leche-sin-lactosa/00780292000814?channable=06660b69640030"
    assert extraer_ean_lider(url) == "780292000814"


def test_extraer_ean_lider_sin_query():
    assert extraer_ean_lider("https://super.lider.cl/ip/leche/slug/00780292000814") == "780292000814"


def test_extraer_ean_lider_casos_invalidos():
    assert extraer_ean_lider("") == ""
    assert extraer_ean_lider("https://super.lider.cl/v/leches") == ""
    # id demasiado corto tras quitar ceros no es un EAN creible
    assert extraer_ean_lider("https://super.lider.cl/ip/x/0000000123?a=1") == ""


def crear_db():
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    Base.metadata.create_all(bind=engine)
    return sessionmaker(bind=engine)()


def test_unificar_por_ean_solo_con_dos_o_mas():
    db = crear_db()
    a = Producto(nombre="Leche Colun 1 L", producto_base="leche_colun_1l", ean="780111")
    b = Producto(nombre="Leche Colun Caja 1L", producto_base="leche_colun_caja", ean="780111")
    solitario = Producto(nombre="Aceite Chef 1 L", producto_base="aceite_chef_1l", ean="780999")
    sin_ean = Producto(nombre="Arroz Tucapel 1 kg", producto_base="arroz_tucapel_1kg")
    db.add_all([a, b, solitario, sin_ean])
    db.commit()

    unificados = unificar_producto_base_por_ean(db)

    assert unificados == 2
    assert a.producto_base == b.producto_base == "ean:780111"
    # EAN unico y sin EAN conservan su base textual (no se aislan)
    assert solitario.producto_base == "aceite_chef_1l"
    assert sin_ean.producto_base == "arroz_tucapel_1kg"


def test_fase5b_no_pisa_grupos_ean():
    from app.fase5b_apply import seleccionar_cambios

    db = crear_db()
    categoria = Categoria(nombre="Despensa")
    db.add(categoria)
    db.flush()
    # dos productos casi identicos que fase5b agruparia por texto,
    # pero ya unificados por EAN
    a = Producto(nombre="Arroz G1 Tucapel 1 kg", marca="Tucapel", tipo="general",
                 formato="1 kg", producto_base="ean:780555", ean="780555",
                 categoria_id=categoria.id)
    b = Producto(nombre="Arroz Grado 1 Tucapel 1kg", marca="Tucapel", tipo="general",
                 formato="1 kg", producto_base="ean:780555", ean="780555",
                 categoria_id=categoria.id)
    db.add_all([a, b])
    db.commit()

    cambios = seleccionar_cambios(db, riesgos=set())
    ids_tocados = {c["producto_id"] for c in cambios}
    assert a.id not in ids_tocados
    assert b.id not in ids_tocados


def test_resumen_compra_matchea_por_ean_aunque_el_texto_difiera():
    from fastapi.testclient import TestClient
    from app.main import app, get_db

    db = crear_db()
    lider = Proveedor(nombre="Lider")
    jumbo = Proveedor(nombre="Jumbo")
    db.add_all([lider, jumbo])
    db.flush()
    # nombres tan distintos que el matching textual jamas los uniria,
    # pero comparten codigo de barras
    a = Producto(nombre="Bebida Vegetal Almendra Original 1 L", marca="", tipo="general",
                 formato="1 L", producto_base="ean:780777", ean="780777")
    b = Producto(nombre="Not Milk Almendras Caja Familiar", marca="NotCo", tipo="general",
                 formato="", producto_base="ean:780777", ean="780777")
    db.add_all([a, b])
    db.flush()
    db.add_all([
        Precio(producto_id=a.id, proveedor_id=lider.id, precio_normal=2500),
        Precio(producto_id=b.id, proveedor_id=jumbo.id, precio_normal=1990),
    ])
    db.commit()

    def override_get_db():
        yield db

    app.dependency_overrides[get_db] = override_get_db
    try:
        client = TestClient(app)
        r = client.post("/productos/resumen-compra",
                        json={"items": [{"producto_id": a.id, "cantidad": 1}]})
        assert r.status_code == 200
        data = r.json()
        assert data["total_optimo"] == 1990
        assert "Jumbo" in data["distribucion"]
        assert data["productos_sin_comparacion"] == []
    finally:
        app.dependency_overrides.clear()
