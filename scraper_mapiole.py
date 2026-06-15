import requests
from bs4 import BeautifulSoup
import csv  # On importe la bibliothèque pour gérer les fichiers CSV

url = "https://mapiole.com/Douala/Apartments/Studio-Moderne-semi-meuble-a-kotto-1382" 

reponse = requests.get(url)

if reponse.status_code == 200:
    soup = BeautifulSoup(reponse.text, 'html.parser')
    
    # Extraction (comme avant)
    annonce = {
        'titre': soup.find('h1', class_='ab-title').text.strip() if soup.find('h1', class_='ab-title') else "Non renseigné",
        'prix': soup.find('div', class_='ab-sidebar-price').text.strip() if soup.find('div', class_='ab-sidebar-price') else "Non renseigné",
        'localisation': soup.find('div', class_='ab-subtitle').find('a').text.strip() if soup.find('div', class_='ab-subtitle') else "Non renseigné"
    }

    # Ouverture du fichier CSV en mode "ajout" (append - 'a')
    # S'il n'existe pas, il sera créé.
    # Remplace cette ligne par celle-ci :
    with open('annonces.csv', 'a', newline='', encoding='utf-8') as fichier_csv:
        # On ajoute delimiter=';' pour que chaque info aille dans sa colonne
        writer = csv.DictWriter(fichier_csv, fieldnames=['titre', 'prix', 'localisation'], delimiter=';')
        
        # On écrit l'en-tête seulement si le fichier est vide
        # (Pour éviter d'avoir des titres de colonnes à chaque nouvelle ligne)
        if fichier_csv.tell() == 0:
            writer.writeheader()
        
        writer.writerow(annonce)
        
    print("Données enregistrées dans annonces.csv !")

else:
    print(f"Erreur de connexion : {reponse.status_code}")