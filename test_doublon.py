from core.database import get_db
from core.fusion import fusionner_ou_inserer

db = next(get_db())

# Annonce originale (comme si Mapiole l'avait scrapée)
annonce_mapiole = {
    "titre": "Appartement moderne 3 pièces à Bonanjo",
    "type_de_bien": "Appartement",
    "localisation_brute": "Bonanjo, Douala",
    "description": "Bel appartement avec vue sur le fleuve, sécurisé et calme.",
    "prix_entier": 150000,
    "nom_plateforme": "Mapiole",
    "url_source": "https://mapiole.com/test-appartement-bonanjo-001",
    "urls_images": "",
}

# Même bien, mais posté par Kasastay (titre légèrement différent, prix différent)
annonce_kasastay = {
    "titre": "Appartement 3 pièces Bonanjo Douala",
    "type_de_bien": "Appartement",
    "localisation_brute": "Bonanjo, Douala",
    "description": "Appartement lumineux, gardien 24h/24, parking inclus.",
    "prix_entier": 145000,
    "nom_plateforme": "Kasastay",
    "url_source": "https://kasastay.com/test-appartement-bonanjo-001",
    "urls_images": "",
}

print("=== Test de déduplication ===\n")
print("Insertion de l'annonce Mapiole...")
fusionner_ou_inserer(db, annonce_mapiole)

print("\nInsertion de l'annonce Kasastay (doublon simulé)...")
fusionner_ou_inserer(db, annonce_kasastay)

print("\n=== Résultat attendu : [FUSION] et non [NOUVEAU] ===")
db.close()
