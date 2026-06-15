import unicodedata
from rapidfuzz import fuzz
from sqlalchemy.orm import Session
from .models import Annonce, SourceAnnonce


def normaliser_titre(titre: str) -> str:
    """Convertit un titre en minuscules sans accents pour la comparaison."""
    nfkd = unicodedata.normalize('NFKD', titre.lower())
    return "".join(c for c in nfkd if not unicodedata.combining(c))


def trouver_doublon(db: Session, nouvelle_annonce: Annonce) -> Annonce | None:
    """
    Cherche si une annonce similaire existe déjà dans la base.
    Retourne l'annonce existante si c'est un doublon, sinon None.
    """
    if not nouvelle_annonce.prix_entier or not nouvelle_annonce.titre_normalise:
        return None

    prix = nouvelle_annonce.prix_entier
    marge = 0.15  # On accepte une différence de prix de ±15%
    prix_min = prix * (1 - marge)
    prix_max = prix * (1 + marge)

    # Étape 1 : Filtrer uniquement les annonces avec un prix dans la même fourchette
    candidats = db.query(Annonce).filter(
        Annonce.prix_entier >= prix_min,
        Annonce.prix_entier <= prix_max,
    ).all()

    # Étape 2 : Pour chaque candidat, comparer les titres avec Levenshtein
    for candidat in candidats:
        if not candidat.titre_normalise:
            continue
        score = fuzz.ratio(nouvelle_annonce.titre_normalise, candidat.titre_normalise)
        if score >= 78:
            print(f"   [DOUBLON DÉTECTÉ] Score={score}% | '{nouvelle_annonce.titre}' ≈ '{candidat.titre}'")
            return candidat

    return None  # Aucun doublon trouvé


def fusionner_ou_inserer(db: Session, nouvelle_annonce: Annonce):
    """
    Logique principale :
    - Si doublon → on ajoute juste une nouvelle SourceAnnonce à la Super-Annonce existante
    - Sinon → on crée une nouvelle Annonce + sa première SourceAnnonce
    """
    # Normalisation du titre avant tout
    nouvelle_annonce.titre_normalise = normaliser_titre(nouvelle_annonce.titre)

    # Vérification : cette URL source exacte existe-t-elle déjà ?
    source_existante = db.query(SourceAnnonce).filter(
        SourceAnnonce.url_source == nouvelle_annonce.url_source
    ).first()
    if source_existante:
        print(f"   [IGNORÉ] Source déjà connue : {nouvelle_annonce.url_source}")
        return

    # Recherche d'un doublon sémantique
    doublon = trouver_doublon(db, nouvelle_annonce)

    if doublon:
        # CAS 1 : C'est un doublon → on ajoute une nouvelle source à la Super-Annonce
        nouvelle_source = SourceAnnonce(
            annonce_id=doublon.id,
            nom_plateforme=nouvelle_annonce.nom_plateforme,
            url_source=nouvelle_annonce.url_source,
            prix_entier=nouvelle_annonce.prix_entier,
        )
        db.add(nouvelle_source)
        print(f"   [FUSION] Nouvelle source ajoutée à la Super-Annonce #{doublon.id}")
    else:
        # CAS 2 : Nouvelle annonce inconnue → on la crée avec sa première source
        db.add(nouvelle_annonce)
        db.flush()  # On a besoin de l'ID généré pour créer la source
        premiere_source = SourceAnnonce(
            annonce_id=nouvelle_annonce.id,
            nom_plateforme=nouvelle_annonce.nom_plateforme,
            url_source=nouvelle_annonce.url_source,
            prix_entier=nouvelle_annonce.prix_entier,
        )
        db.add(premiere_source)
        print(f"   [NOUVEAU] Annonce créée : '{nouvelle_annonce.titre}'")
