from pathlib import Path

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base
from app.main import app, get_db
from app.models import Categoria, Precio, Producto, Subcategoria, Supermercado


def crear_cliente_con_datos():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)

    db = TestingSessionLocal()
    try:
        categoria = Categoria(nombre="Despensa")
        subcategoria = Subcategoria(nombre="Leche", categoria=categoria)
        lider = Supermercado(nombre="Lider")
        jumbo = Supermercado(nombre="Jumbo")
        leche_1l = Producto(
            nombre="Leche Soprole 1L",
            marca="Soprole",
            tipo="entera",
            formato="1 L",
            producto_base="leche_soprole_entera_1l",
            categoria=categoria,
            subcategoria=subcategoria,
        )
        leche_1000ml = Producto(
            nombre="Leche Soprole 1000ml",
            marca="Soprole",
            tipo="entera",
            formato="1000 ml",
            producto_base="leche_soprole_entera_1l",
            categoria=categoria,
            subcategoria=subcategoria,
        )
        arroz = Producto(
            nombre="Arroz Test 1kg",
            marca="Test",
            tipo="general",
            formato="1 kg",
            producto_base="arroz_test_1kg",
            categoria=categoria,
            subcategoria=subcategoria,
        )
        db.add_all([categoria, subcategoria, lider, jumbo, leche_1l, leche_1000ml, arroz])
        db.flush()
        db.add_all([
            Precio(producto=leche_1l, supermercado=lider, precio_normal=1200, url_producto="https://lider.test/p/1"),
            Precio(producto=leche_1000ml, supermercado=jumbo, precio_normal=1100, url_producto="https://jumbo.test/p/1"),
            Precio(producto=arroz, supermercado=lider, precio_normal=1800, url_producto="https://lider.test/p/2"),
        ])
        db.commit()
    finally:
        db.close()

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    return TestClient(app)


def test_busqueda_basica_con_sqlite_temporal():
    client = crear_cliente_con_datos()
    try:
        response = client.get("/productos/buscar/leche")
        assert response.status_code == 200
        data = response.json()
        assert data
        assert data[0]["nombre"] == "Leche Soprole 1L"
        assert len(data[0]["precios"]) == 2
    finally:
        app.dependency_overrides.clear()


def test_busqueda_respeta_limite():
    client = crear_cliente_con_datos()
    try:
        response = client.get("/buscar/leche?limit=1")
        assert response.status_code == 200
        assert len(response.json()) == 1
    finally:
        app.dependency_overrides.clear()


def test_estado_datos_usa_conteos_basicos():
    client = crear_cliente_con_datos()
    try:
        response = client.get("/estado-datos")
        assert response.status_code == 200
        data = response.json()
        assert data["productos"] == 3
        assert data["precios"] == 3
        assert data["supermercados"]["Lider"] == 2
        assert Path("supercheck.db").exists() or data["base_actualizada"] is None
    finally:
        app.dependency_overrides.clear()


def test_endpoint_diagnostico_matching_responde_resumen():
    client = crear_cliente_con_datos()
    try:
        response = client.get("/diagnostico/matching")
        assert response.status_code == 200
        data = response.json()
        assert data["total_productos"] == 3
        assert "categorias_peor_matching" in data
        assert "recomendaciones" in data
    finally:
        app.dependency_overrides.clear()
