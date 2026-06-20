import os
import requests
import uuid
import hashlib
from bs4 import BeautifulSoup
from typing import List
import time
import re
import urllib.parse

from .base import BaseScraper

def telecharger_image_localement(url: str, prefix: str = "img") -> str:
    """Télécharge l'image physiquement (Architecture Trivago) sans faire de doublons"""
    if not url or not url.startswith('http'): 
        return ""
    
    # On transforme l'URL en un nom unique mais constant
    hash_nom = hashlib.md5(url.encode('utf-8')).hexdigest()[:10]
    nom_fichier = f"{prefix}_{hash_nom}.jpg"
    
    dossier_destination = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static", "images")
    os.makedirs(dossier_destination, exist_ok=True)
    chemin_sauvegarde = os.path.join(dossier_destination, nom_fichier)
    url_locale = f"/static/images/{nom_fichier}"
    
    # Si le fichier a déjà été téléchargé, on donne juste le lien existant
    if os.path.exists(chemin_sauvegarde):
        return url_locale
    
    # On ajoute des entêtes pour rassurer le serveur Kasastay
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Referer': 'https://kasastay.com/'
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            with open(chemin_sauvegarde, 'wb') as f:
                f.write(response.content)
            return url_locale
    except Exception as e:
        print(f"Erreur téléchargement image Kasastay : {e}")
        
    return ""


class KasastayScraper(BaseScraper):
    def __init__(self):
        super().__init__()
        self.platform_name = "Kasastay"
        self.base_url = "https://kasastay.com" 
        self.catalogue_url = "https://kasastay.com/fr/property/search?business=LongStay"

    def parse_prix(self, prix_text: str) -> int:
        if not prix_text:
            return None
        try:
            if "XAF" in prix_text:
                partie_prix = prix_text.split("XAF")[1]
            else:
                partie_prix = prix_text

            bloc_chiffres = re.search(r'[\d\s.,]+', partie_prix).group()
            digits = re.sub(r'[^\d]', '', bloc_chiffres)
            return int(digits)
        except Exception:
            return None

    def extract_images(self, soup: BeautifulSoup) -> str:
        images = []
        for img in soup.find_all('img'):
            src = img.get('src')
            if not src:
                continue
                
            # STRATÉGIE AVANCÉE : Kasastay utilise Next.js et masque les vraies URL.
            if '_next/image' in src and 'url=' in src:
                # On découpe l'URL pour extraire la vraie adresse cachée et on la "désencode"
                vraie_url = urllib.parse.unquote(src.split('url=')[1].split('&')[0])
                images.append(vraie_url)
                
            # Stratégie classique pour les autres images (.webp ajouté !)
            elif '.jpg' in src or '.png' in src or '.jpeg' in src or '.webp' in src:
                # On ignore le logo pour garder un rendu propre dans l'application
                if "logo" not in src.lower():
                    images.append(src)
        valid_images = [img if img.startswith('http') else self.base_url + img for img in images]
        
        urls_locales = []
        # On télécharge un tableau de 5 vraies images
        for url in list(dict.fromkeys(valid_images))[:5]:
            chemin_local = telecharger_image_localement(url, prefix="kasastay")
            if chemin_local:
                urls_locales.append(chemin_local)
                
        return ",".join(urls_locales)
    def scrape(self) -> List[dict]:
        print(f"[{self.platform_name}] Début de l'exploration...")
        annonces_scrapees = []
        
        try:
            reponse = requests.get(self.catalogue_url, timeout=15)
            soup = BeautifulSoup(reponse.text, 'html.parser')
            
            liens_annonces = soup.find_all('a', class_='group flex h-full flex-col')
            print(f"[{self.platform_name}] {len(liens_annonces)} annonces détectées.")

            for lien in liens_annonces[:5]:
                url_detail = self.base_url + lien.get('href')
                print(f"Extraction de : {url_detail}")
                
                try:
                    resp_detail = requests.get(url_detail, timeout=10)
                    soup_detail = BeautifulSoup(resp_detail.text, 'html.parser')
                    
                    titre_el = soup_detail.find('h1')
                    titre = titre_el.text.strip() if titre_el else "Appartement Kasastay"
                    
                    prix_entier = None
                    prix_texte = soup_detail.find(string=re.compile("XAF"))
                    if prix_texte:
                        prix_entier = self.parse_prix(prix_texte)
                    
                    desc_els = soup_detail.find_all('p')
                    description = "\n".join([p.text.strip() for p in desc_els if len(p.text.strip()) > 10])
                    
                    # NOUVEAU: Extraction et téléchargement Trivago-style !
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
                    # Extraction de la vraie localisation
                    localisation = ""
                    meta_desc = soup_detail.find("meta", {"property": "og:description"})
                    if meta_desc and meta_desc.get("content"):
                        localisation = meta_desc["content"].strip()[:80]

                    if not localisation:
                        villes = ["Douala", "Yaoundé", "Bafoussam", "Garoua", "Maroua",
                                  "Bamenda", "Ngaoundéré", "Bertoua", "Ebolowa", "Kribi",
                                  "Limbe", "Buea", "Nkongsamba", "Edéa", "Kumba"]
                        for tag in soup_detail.find_all(['span', 'p', 'div']):
                            text = tag.get_text(strip=True)
                            for ville in villes:
                                if ville.lower() in text.lower() and len(text) < 100:
                                    localisation = text
                                    break
                            if localisation:
                                break

                    if not localisation:
                        meta_title = soup_detail.find("meta", {"property": "og:title"})
                        if meta_title and meta_title.get("content"):
                            localisation = meta_title["content"].strip()[:80]

                    if not localisation:
                        localisation = "Cameroun"  # sera rejeté par le filtre
 
                        

                        
                    annonce = dict(
                        titre=titre,
                        type_de_bien=type_bien_trouve,
                        prix_entier=prix_entier,
                        localisation_brute=localisation,

                        description=description,
                        url_source=url_detail,
                        nom_plateforme=self.platform_name,
                        urls_images=urls_images  # L'URL locale a été insérée ici !
                    )
                    annonces_scrapees.append(annonce)
                    time.sleep(1)
                    
                except Exception as e:
                    print(f"Erreur sur la page de détail : {e}")
                    
        except Exception as e:
            print(f"Erreur d'accès au catalogue : {e}")
            
        print(f"[{self.platform_name}] Extraction finalisée. ({len(annonces_scrapees)} recensées).")
        return annonces_scrapees
