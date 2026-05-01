from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from .database import Base, engine, SessionLocal
from . import models, schemas, services

Base.metadata.create_all(bind=engine)

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.get("/")
def inicio():
    return {"mensaje": "SuperCheck funcionando 🚀"}


@app.get("/buscar/{texto}")
def buscar(texto: str, db: Session = Depends(get_db)):
    return services.buscar_opciones_producto(db, texto)


@app.post("/comparar")
def comparar(request: schemas.ComparacionRequest, db: Session = Depends(get_db)):
    resultado = services.comparar_lista(db, request.productos)
    return resultado

@app.get("/categorias")
def obtener_categorias(db: Session = Depends(get_db)):
    return db.query(models.Categoria).all()

@app.get("/subcategorias/{categoria_id}")
def obtener_subcategorias(categoria_id: int, db: Session = Depends(get_db)):
    return db.query(models.Subcategoria).filter(
        models.Subcategoria.categoria_id == categoria_id
    ).all()

@app.get("/productos/buscar/{texto}")
def buscar_productos(texto: str, db: Session = Depends(get_db)):
    productos = db.query(models.Producto).filter(
        models.Producto.nombre.ilike(f"%{texto}%")
    ).all()

    return [
        {
            "id": producto.id,
            "nombre": producto.nombre,
            "marca": producto.marca,
            "tipo": producto.tipo,
            "formato": producto.formato,
            "precio_menor": min(
                [
                    precio.precio_oferta or precio.precio_normal
                    for precio in db.query(models.Precio).filter(
                        models.Precio.producto_id == producto.id
                    ).all()
                ],
                default=None
            )
        }
        for producto in productos
    ]
