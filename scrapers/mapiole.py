import os
import requests
import uuid
import hashlib
from bs4 import BeautifulSoup
from typing import List
import time
import re

from .base import BaseScraper
from core.models import Annonce

def telecharger_image_localement(url: str, prefix: str = "img") -> str:
    """Télécharge l'image physiquement (sans faire de doublons)"""
    if not url or not url.startswith('http'): 
        return ""
    
    # On transforme l'URL en un nom unique mais TOUJOURS LE MÊME pour cette URL
    hash_nom = hashlib.md5(url.encode('utf-8')).hexdigest()[:10]
    nom_fichier = f"{prefix}_{hash_nom}.jpg"
    
    # On prépare le dossier de sauvegarde
    dossier_destination = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static", "images")
    os.makedirs(dossier_destination, exist_ok=True)
    chemin_sauvegarde = os.path.join(dossier_destination, nom_fichier)
    
    url_locale = f"/static/images/{nom_fichier}"
    
    # ARCHITECTURE SÉCURE: On vérifie si le fichier existe déjà physiquement !
    # S'il existe déjà, on le retourne directement sans le télécharger une 2ème fois
    if os.path.exists(chemin_sauvegarde):
        return url_locale
    
    # S'il n'existe pas, on le télécharge avec les faux headers
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Referer': 'https://mapiole.com/'
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            with open(chemin_sauvegarde, 'wb') as f:
                f.write(response.content)
            return url_locale
    except Exception as e:
        print(f"Erreur de téléchargement image : {e}")
        
    return ""


class MapioleScraper(BaseScraper):
    def __init__(self):
        super().__init__()
        self.platform_name = "Mapiole"
        self.base_url = "https://mapiole.com"
        self.catalogue_url = "https://mapiole.com"

    def parse_prix(self, prix_text: str) -> int:
        if not prix_text:
            return None
        # Extraire uniquement les chiffres (ex: "150 000 FCFA" -> 150000)
        digits = re.sub(r'[^\d]', '', prix_text)
        return int(digits) if digits else None

    def extract_images(self, soup: BeautifulSoup) -> str:
        images = []
        # On cible uniquement les images enfermées dans la galerie
        for img in soup.select('.ab-gallery img'):
            src = img.get('src')
            if src:
                images.append(src)

        valid_images = [img if img.startswith('http') else self.base_url + img for img in images]
        
        # Architecture Robuste: on télécharge l'image localement au lieu de juste garder le lien
        urls_locales = []
        for url in list(dict.fromkeys(valid_images))[:5]:
            chemin_local = telecharger_image_localement(url, prefix="mapiole")
            if chemin_local:
                urls_locales.append(chemin_local)
                
        return ",".join(urls_locales)

    def scrape(self) -> List[Annonce]:
        print(f"[{self.platform_name}] Début de l'exploration...")
        annonces_scrapees = []
        
        try:
            reponse = requests.get(self.catalogue_url, timeout=15)
            soup = BeautifulSoup(reponse.text, 'html.parser')
            liens_annonces = soup.find_all('a', class_='prop-card__title')
            
            print(f"[{self.platform_name}] {len(liens_annonces)} annonces détectées.")

            # Pour le test, on limite à 5 résultats maximum dans un premier temps
            for lien in liens_annonces[:5]:
                url_detail = self.base_url + lien.get('href')
                print(f"Extraction de : {url_detail}")
                
                try:
                    resp_detail = requests.get(url_detail, timeout=10)
                    soup_detail = BeautifulSoup(resp_detail.text, 'html.parser')
                    
                    titre_el = soup_detail.find('h1', class_='ab-title')
                    prix_el = soup_detail.find('div', class_='ab-sidebar-price')
                    loc_el = soup_detail.find('div', class_='ab-subtitle')
                    
                    desc_els = soup_detail.find_all('p') 
                    
                    titre = titre_el.text.strip() if titre_el else "Non renseigné"
                    prix_brut = prix_el.text.strip() if prix_el else ""
                    prix_entier = self.parse_prix(prix_brut)
                    
                    loc = "Non renseigné"
                    if loc_el:
                        loc_a = loc_el.find('a')
                        loc = loc_a.text.strip() if loc_a else loc_el.text.strip()
                    
                    mots_interdits = [
                        "Non spécifié", "FCFA / mensuel", 
                        "Aucun avis pour le moment", "Vous ne serez pas encore facturé",
                        "Total:", "Cameroon", "Suivez-nous sur les réseaux", 
                        "Restez à jour", "Recherche populaire", "Liens rapides", 
                        "© Mapiole.com", "en direct ?\nAssistance"
                    ]

                    paragraphes_propres = []
                    for p in desc_els:
                        texte = p.text.strip()
                        if len(texte) > 10 and not any(interdit in texte for interdit in mots_interdits):
                            paragraphes_propres.append(texte)
                            
                    description = "\n".join(paragraphes_propres)

                    urls_images = self.extract_images(soup_detail)
                    
                    texte_analyse = (titre + " " + url_detail).lower()
                    if "appartement" in texte_analyse or "studio" in texte_analyse or "apartment" in texte_analyse:
                        type_bien_trouve = "Appartement"
                    elif "terrain" in texte_analyse or "land" in texte_analyse:
                        type_bien_trouve = "Terrain"
                    elif "maison" in texte_analyse or "villa" in texte_analyse or "house" in texte_analyse:
                        type_bien_trouve = "Maison"
                    else:
                        type_bien_trouve = "Autre"
                    
                    annonce = Annonce(
                        titre=titre,
                        type_de_bien=type_bien_trouve,
                        prix_entier=prix_entier,
                        localisation_brute=loc,
                        description=description,
                        url_source=url_detail,
                        nom_plateforme=self.platform_name,
                        urls_images=urls_images
                    )
                    annonces_scrapees.append(annonce)
                    
                    time.sleep(1)
                    
                except Exception as e:
                    print(f"Erreur sur la page de détail : {e}")
                    
        except Exception as e:
            print(f"Erreur d'accès au catalogue : {e}")
            
        print(f"[{self.platform_name}] Extraction finalisée. ({len(annonces_scrapees)} recensées).")
        return annonces_scrapees
