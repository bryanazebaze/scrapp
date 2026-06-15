from core.database import get_db, Base, engine
from scrapers.mapiole import MapioleScraper
from scrapers.kasastay import KasastayScraper
from core.fusion import fusionner_ou_inserer, normaliser_titre

# Création automatique de toutes les tables (annonces + sources_annonces)
Base.metadata.create_all(bind=engine)

def main():
    print("=== Démarrage du système de collecte (Agrégateur) ===\n")

    scrapers = [
        MapioleScraper(),
        KasastayScraper(),
    ]

    db_gen = get_db()
    db = next(db_gen)

    try:
        for scraper in scrapers:
            print(f"--- Scraper : {scraper.platform_name} ---")
            annonces = scraper.scrape()

            for annonce in annonces:
                # On normalise le titre avant de chercher les doublons
                annonce.titre_normalise = normaliser_titre(annonce.titre)
                # L'algorithme de fusion gère tout : doublon ou nouvelle annonce
                fusionner_ou_inserer(db, annonce)

            db.commit()
            print(f"--> Terminé pour {scraper.platform_name}.\n")

    except Exception as e:
        print(f"Erreur inattendue : {e}")
        db.rollback()
    finally:
        db.close()

    print("=== Processus terminé. ===")

if __name__ == "__main__":
    main()
