from sqlalchemy import Column, Integer, BigInteger, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .database import Base


class Annonce(Base):
    """La 'Super-Annonce' : un bien unique, même s'il est sur plusieurs sites."""
    __tablename__ = "annonces"

    id = Column(Integer, primary_key=True, index=True)
    titre = Column(String, index=True)
    # Titre en minuscules sans accents, pour la comparaison mathématique
    titre_normalise = Column(String, nullable=True, index=True)
    type_de_bien = Column(String, nullable=True, index=True)
    localisation_brute = Column(String, nullable=True)
    description = Column(Text, nullable=True)
    urls_images = Column(Text, nullable=True)
    date_collecte = Column(DateTime(timezone=True), server_default=func.now())

    # Prix et plateforme de référence (la première source trouvée)
    meilleur_prix = Column(BigInteger, nullable=True)

    # Relation vers toutes les sources qui publient ce bien
    sources = relationship("SourceAnnonce", back_populates="annonce", cascade="all, delete-orphan")


class SourceAnnonce(Base):
    """Une source = une plateforme qui publie un bien. Une Super-Annonce peut en avoir plusieurs."""
    __tablename__ = "sources_annonces"

    id = Column(Integer, primary_key=True, index=True)
    annonce_id = Column(Integer, ForeignKey("annonces.id"), nullable=False, index=True)
    nom_plateforme = Column(String, nullable=False)
    url_source = Column(String, nullable=False, unique=True)
    prix_entier = Column(BigInteger, nullable=True)
    date_collecte = Column(DateTime(timezone=True), server_default=func.now())

    annonce = relationship("Annonce", back_populates="sources")
    particularite = Column(String, nullable=True)
