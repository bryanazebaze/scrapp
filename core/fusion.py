import unicodedata
from rapidfuzz import fuzz
from sqlalchemy.orm import Session
from .models import Annonce, SourceAnnonce

def normaliser_titre(titre: str) -> str:
    """Convertit un titre en minuscules sans accents pour la comparaison."""
    if not titre:
        return ""
    nfkd = unicodedata.normalize('NFKD', titre.lower())
    return "".join(c for c in nfkd if not unicodedata.combining(c))

def extraire_particularite(description: str) -> str:
    """Extrait une petite particularité depuis la description du scraper."""
    if not description:
        return ""
    phrases = [p.strip() for p in description.split('.') if len(p.strip()) > 5]
    return phrases[0][:50] + "..." if phrases else "Aucune"


LOCALISATIONS_INVALIDES = {
    "", "non renseignée", "non renseigné", "cameroun", "non spécifié",
    "non specifie", "non spécifiée", "inconnu", "inconnue", "n/a"
}

def est_annonce_valide(donnees_scrap: dict) -> bool:
    """Filtre qualité : rejette les annonces sans image ni localisation réelle."""
    # 1. Vérification des images
    urls_images = donnees_scrap.get("urls_images", "")
    if not urls_images or not urls_images.strip():
        return False
    images_valides = [img.strip() for img in urls_images.split(",") if img.strip().startswith("/static/")]
    if not images_valides:
        return False

    # 2. Vérification de la localisation
    localisation = donnees_scrap.get("localisation_brute", "")
    if not localisation:
        return False
    if normaliser_titre(localisation.strip()) in LOCALISATIONS_INVALIDES:
        return False

    return True

def trouver_doublon(db: Session, donnees_scrap: dict) -> Annonce | None:
    prix = donnees_scrap.get("prix_entier")
    titre = donnees_scrap.get("titre")
    
    if not prix or not titre:
        return None

    titre_norm = normaliser_titre(titre)
    prix_min = prix * (1 - 0.15)  # Marge de 15%
    prix_max = prix * (1 + 0.15)

    candidats = db.query(Annonce).filter(
        Annonce.meilleur_prix >= prix_min,
        Annonce.meilleur_prix <= prix_max,
    ).all()

    for candidat in candidats:
        if not candidat.titre_normalise: continue
        score = fuzz.token_set_ratio(titre_norm, candidat.titre_normalise)
        if score >= 70:
            return candidat
    return None



def fusionner_ou_inserer(db: Session, donnees_scrap: dict):
    # Filtre qualité : on rejette les annonces incomplètes
    if not est_annonce_valide(donnees_scrap):
        print(f"   [REJETÉ] Annonce incomplète : {donnees_scrap.get('titre', '?')[:50]}")
        return

    url_source = donnees_scrap.get("url_source")
    nom_pl = donnees_scrap.get("nom_plateforme")
    prix = donnees_scrap.get("prix_entier")
    
    # 1. Empêcher les urls dupliquées
    if db.query(SourceAnnonce).filter(SourceAnnonce.url_source == url_source).first():
        print(f"   [IGNORÉ] Source déjà connue : {url_source}")
        return

    # 2. Chercher dans les SuperAnnonces
    doublon = trouver_doublon(db, donnees_scrap)
    particularite = extraire_particularite(donnees_scrap.get("description", ""))

    if doublon:
        # Doublon -> Créer juste la source
        nouvelle_source = SourceAnnonce(
            annonce_id=doublon.id, nom_plateforme=nom_pl,
            url_source=url_source, prix_entier=prix, particularite=particularite
        )
        db.add(nouvelle_source)
        if prix and doublon.meilleur_prix and prix < doublon.meilleur_prix:
            doublon.meilleur_prix = prix  # Mise à jour du prix d'appel
        print(f"   [FUSION] Ajoutée à la Super-Annonce #{doublon.id}")
    else:
        # Nouveauté -> SuperAnnonce + sa Source
        nouvelle_annonce = Annonce(
            titre=donnees_scrap.get("titre"), titre_normalise=normaliser_titre(donnees_scrap.get("titre")),
            type_de_bien=donnees_scrap.get("type_de_bien"), localisation_brute=donnees_scrap.get("localisation_brute"),
            description=donnees_scrap.get("description", "")[:100] + "...", # Ultra court !
            urls_images=donnees_scrap.get("urls_images"), meilleur_prix=prix
        )
        db.add(nouvelle_annonce)
        db.flush() 

        db.add(SourceAnnonce(
            annonce_id=nouvelle_annonce.id, nom_plateforme=nom_pl,
            url_source=url_source, prix_entier=prix, particularite=particularite
        ))
        print(f"   [NOUVEAU] Super-Annonce créée !")
    db.commit()
