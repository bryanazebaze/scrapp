from pydantic import BaseModel
from typing import Optional, List


class SourceAnnonceSchema(BaseModel):
    """Représente une plateforme qui publie un bien, avec son propre prix."""
    id: int
    nom_plateforme: str
    url_source: str
    prix_entier: Optional[int]

    class Config:
        from_attributes = True


class AnnonceSchema(BaseModel):
    id: int
    titre: str
    prix_entier: Optional[int]
    type_de_bien: Optional[str]
    localisation_brute: Optional[str]
    description: Optional[str]
    urls_images: Optional[str]
    nom_plateforme: Optional[str]
    url_source: str
    # Liste de toutes les plateformes pour le bloc "Comparer les offres"
    sources: List[SourceAnnonceSchema] = []

    class Config:
        from_attributes = True
