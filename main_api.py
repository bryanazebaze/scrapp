from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session, joinedload
from typing import List
from fastapi.staticfiles import StaticFiles
import os

from core.database import get_db
from core.models import Annonce
from core.schemas import AnnonceSchema

app = FastAPI(
    title="CentralImmo API",
    description="L'API officielle de l'agrégateur immobilier CentralImmo",
    version="2.0.0"
)

static_path = os.path.join(os.path.dirname(__file__), "static")
if not os.path.exists(static_path):
    os.makedirs(static_path, exist_ok=True)
app.mount("/static", StaticFiles(directory=static_path), name="static")

@app.get("/")
def bienvenue():
    return {"message": "Bienvenue sur CentralImmo API v2 🚀"}

@app.get("/annonces", response_model=List[AnnonceSchema])
def lire_annonces(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """
    Retourne la liste des Super-Annonces avec toutes leurs sources (plateformes).
    """
    annonces = (
        db.query(Annonce)
        .options(joinedload(Annonce.sources))  # Charge les sources en même temps
        .offset(skip)
        .limit(limit)
        .all()
    )
    return annonces
