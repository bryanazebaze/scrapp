from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
from typing import List
from fastapi.staticfiles import StaticFiles
import os

from core.database import get_db
from core.models import Annonce
from core.schemas import AnnonceBreve, AnnonceDetaillee

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

@app.get("/annonces", response_model=List[AnnonceBreve])
def lire_annonces_liste(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """
    Retourne la liste allégée des Super-Annonces pour l'écran d'accueil.
    """
    annonces = db.query(Annonce).offset(skip).limit(limit).all()
    return annonces

@app.get("/annonces/{annonce_id}", response_model=AnnonceDetaillee)
def lire_annonce_detail(annonce_id: int, db: Session = Depends(get_db)):
    """
    Retourne le détail d'une Super-Annonce avec ses plateformes concurrentes.
    """
    annonce = (
        db.query(Annonce)
        .options(joinedload(Annonce.sources))
        .filter(Annonce.id == annonce_id)
        .first()
    )
    if not annonce:
        raise HTTPException(status_code=404, detail="Annonce non trouvée")
    
    # On trie les sources par prix croissant pour afficher "De la moins chère à la plus chère"
    annonce.sources.sort(key=lambda s: s.prix_entier if s.prix_entier else float('inf'))
    
    return annonce

@app.get("/annonces/{annonce_id}/analyse")
def analyser_prix(annonce_id: int, db: Session = Depends(get_db)):
    """
    Compare le prix d'un bien avec la moyenne des biens similaires
    (même type + même ville).
    """
    annonce = db.query(Annonce).filter(Annonce.id == annonce_id).first()
    if not annonce:
        raise HTTPException(status_code=404, detail="Annonce non trouvée")

    if not annonce.meilleur_prix or not annonce.type_de_bien:
        return {"message": "Comparaison de prix non disponible pour ce bien."}

    # Extraire la ville depuis la localisation brute
    villes = ["Douala", "Yaoundé", "Bafoussam", "Garoua", "Maroua",
              "Bamenda", "Ngaoundéré", "Bertoua", "Ebolowa", "Kribi",
              "Limbe", "Buea", "Nkongsamba", "Edéa", "Kumba"]
    ville_detectee = None
    if annonce.localisation_brute:
        for ville in villes:
            if ville.lower() in annonce.localisation_brute.lower():
                ville_detectee = ville
                break

    if not ville_detectee:
        return {"message": "Comparaison de prix non disponible pour ce bien."}

    # Récupérer tous les biens du même type dans la même ville
    similaires = db.query(Annonce).filter(
        Annonce.type_de_bien == annonce.type_de_bien,
        Annonce.localisation_brute.ilike(f"%{ville_detectee}%"),
        Annonce.meilleur_prix != None,
        Annonce.id != annonce_id
    ).all()

    if not similaires:
        return {"message": f"Pas encore assez de données pour comparer les {annonce.type_de_bien.lower()}s à {ville_detectee}."}

    # Calculer la moyenne
    prix_valides = [a.meilleur_prix for a in similaires if a.meilleur_prix]
    if not prix_valides:
        return {"message": "Comparaison de prix non disponible pour ce bien."}

    moyenne = sum(prix_valides) / len(prix_valides)
    diff_pct = ((annonce.meilleur_prix - moyenne) / moyenne) * 100

    type_bien = annonce.type_de_bien.lower()

    if diff_pct <= -10:
        message = f"💚 Moins cher que la moyenne à {ville_detectee}"
    elif diff_pct >= 10:
        message = f"🔴 Plus cher que la moyenne à {ville_detectee}"
    else:
        message = f"🟡 Dans la moyenne à {ville_detectee}"

    return {"message": message}
