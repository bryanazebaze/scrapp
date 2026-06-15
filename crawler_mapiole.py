import requests
from bs4 import BeautifulSoup
import time
import csv

base_url = "https://mapiole.com"
url_catalogue = "https://mapiole.com/Douala/Apartments"

# Ouverture du fichier CSV en mode écriture
with open('annonces.csv', 'w', newline='', encoding='utf-8') as fichier_csv:
    writer = csv.DictWriter(fichier_csv, fieldnames=['titre', 'prix', 'localisation'], delimiter=';')
    writer.writeheader()

    print("Exploration du catalogue...")
    reponse = requests.get(url_catalogue)
    soup = BeautifulSoup(reponse.text, 'html.parser')

    # Récupération de tous les liens vers les annonces
    liens_annonces = soup.find_all('a', class_='prop-card_title')
    print(f"Nombre d'annonces trouvées : {len(liens_annonces)}")

    for lien in liens_annonces:
        url_annonce = base_url + lien.get('href')
        print(f"\nVisite de : {url_annonce}")
        
        try:
            resp_detail = requests.get(url_annonce, timeout=10)
            soup_detail = BeautifulSoup(resp_detail.text, 'html.parser')
            
            # --- DÉBOGAGE : On vérifie si les éléments sont bien trouvés ---
            titre_element = soup_detail.find('h1', class_='ab-title')
            prix_element = soup_detail.find('div', class_='ab-sidebar-price')
            loc_div = soup_detail.find('div', class_='ab-subtitle')
            
            print(f"DEBUG - Titre trouvé : {titre_element is not None}")
            print(f"DEBUG - Prix trouvé : {prix_element is not None}")
            
            # Extraction des données
            annonce = {
                'titre': titre_element.text.strip() if titre_element else "N/A",
                'prix': prix_element.text.strip() if prix_element else "N/A",
                'localisation': loc_div.find('a').text.strip() if loc_div and loc_div.find('a') else "N/A"
            }
            
            # Écriture dans le fichier
            writer.writerow(annonce)
            print("Données enregistrées dans CSV.")
            
        except Exception as e:
            print(f"Erreur lors de la visite : {e}")
        
        # Pause de politesse pour ne pas bloquer l'IP
        time.sleep(2)

print("\nCollecte terminée ! Ouvre annonces.csv pour voir le résultat.")