from pydantic import BaseModel
from typing import Optional, List

class SourceAnnonceSchema(BaseModel):
    """Représente une plateforme concurrente pour le bloc 'Comparer les offres'"""
    id: int
    nom_plateforme: str
    url_source: str
    prix_entier: Optional[int]
    particularite: Optional[str]

    class Config:
        from_attributes = True

class AnnonceBreve(BaseModel):
    """Modèle ultra-léger pour la page d'accueil (HomeScreen)"""
    id: int
    titre: str
    meilleur_prix: Optional[int]
    type_de_bien: Optional[str]
    localisation_brute: Optional[str]
    urls_images: Optional[str]

    class Config:
        from_attributes = True

class AnnonceDetaillee(AnnonceBreve):
    """Modèle lourd quand l'utilisateur clique (DetailScreen)"""
    description: Optional[str]
    sources: List[SourceAnnonceSchema] = []

    class Config:
        from_attributes = True
