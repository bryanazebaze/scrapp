# =====================================================================
#  CONTEXTE COMPLET DU PROJET : CentralImmo (Agrégateur Immobilier)
#  🗓️  Dernière mise à jour : 14 Juin 2026
#  📁  Dossier racine du projet : /home/bryan/Documents/soutenance/new/scrapp
# =====================================================================

## C'est quoi le projet ?

CentralImmo est un **agrégateur immobilier** pour le marché camerounais.
L'idée est simple : au lieu que l'utilisateur aille sur Kasastay, puis Mapiole, puis d'autres sites un par un, notre application récupère les annonces de tous ces sites automatiquement et les affiche en un seul endroit, propre et sans doublons.

C'est le projet de soutenance de Licence 3 en Génie Logiciel.
L'encadreur académique a proposé le thème. Smart Service Hub (SSH) a fourni l'accompagnement professionnel pour la réalisation.

---

## Architecture du Projet

Le projet est divisé en 3 parties qui communiquent entre elles :

```
[Sites web : Mapiole, Kasastay]
        |
        | (Extraction automatique la nuit)
        ↓
[Backend Python / FastAPI]  ←→  [Base de données PostgreSQL]
        |
        | (HTTP / JSON)
        ↓
[Application Mobile Flutter (Android / iOS)]
```

---

## Structure des fichiers importants

```
scrapp/
├── main.py              ← Orchestrateur : lance tous les scrapers
├── main_api.py          ← Serveur FastAPI (l'API REST)
├── core/
│   ├── models.py        ← Modèles de la base de données (SQLAlchemy)
│   ├── schemas.py       ← Format de sortie JSON (Pydantic)
│   └── database.py      ← Connexion à la base de données
├── scrapers/
│   ├── base.py          ← Classe de base commune à tous les scrapers
│   ├── kasastay.py      ← Scraper du site Kasastay ✅ (opérationnel)
│   └── mapiole.py       ← Scraper du site Mapiole ✅ (opérationnel)
├── static/images/       ← Images téléchargées localement (style Trivago)
└── immo_app/            ← Application mobile Flutter
    └── lib/
        ├── main.dart
        ├── models/annonce.dart    ← Modèle de données côté Flutter
        ├── services/api_service.dart ← Appels HTTP vers FastAPI
        └── screens/
            ├── home_screen.dart   ← Écran d'accueil ✅ (opérationnel)
            └── detail_screen.dart ← Écran de détail ✅ (opérationnel)
```

---

## Ce qui est déjà fait ✅

### Backend (Python)
- [x] Scraper Kasastay opérationnel (collecte titres, prix, images, URL source)
- [x] Scraper Mapiole opérationnel
- [x] Téléchargement local des images (architecture Trivago : hash MD5 pour éviter les doublons de fichiers)
- [x] Serveur FastAPI avec route `/annonces` qui renvoie les annonces en JSON
- [x] Route `/static` pour servir les images locales téléchargées
- [x] Déduplication basique par URL (si la même URL existe déjà, on ne la rajoute pas)

### Application Mobile (Flutter)
- [x] Écran d'accueil `HomeScreen` avec le design **Émeraude et Or**
  - En-tête dégradé (CentralImmo logo + tagline)
  - Barre de recherche (visuelle pour l'instant)
  - Chips de filtres (Tout, Appartement, Studio, Villa...)
  - Liste de cartes d'annonces avec photo, titre, prix
- [x] Écran de détail `DetailScreen` style Trivago :
  - Carrousel d'images avec points indicateurs
  - Prix affiché en grand
  - Localisation
  - Description complète
  - Bouton de redirection vers le site source avec animation de chargement

---

## Ce qui reste à faire 🚧

### 🔴 PRIORITÉ 1 : Vraie Déduplication inter-plateformes (Le cœur du projet)

**Objectif** : Si la même maison est postée sur Kasastay ET Mapiole, afficher une seule fiche mais montrer les 2 prix dans la page de détail (comme Trivago fait avec les hôtels).

**Plan d'implémentation (Solution A — 2 tables SQL) :**

**Étape 1 — Modifier la base de données** (`core/models.py`)
- Ajouter un champ `titre_normalise` dans le modèle `Annonce` pour stocker le titre en minuscules sans accents (pour faciliter la comparaison)
- Créer une nouvelle table `SourceAnnonce` avec les champs :
  - `id`, `annonce_id` (clé étrangère vers `Annonce`), `nom_plateforme`, `url_source`, `prix_entier`, `date_collecte`
- La table `Annonce` devient la "Super-Annonce" commune
- La table `SourceAnnonce` stock chaque doublon détecté sous différentes sources

**Étape 2 — Créer l'algorithme de fusion** (nouveau fichier `core/fusion.py`)
- Installer `rapidfuzz` (`pip install rapidfuzz`)
- Pour chaque nouvelle annonce scrapée, l'algorithme :
  1. Filtre les annonces existantes dont le prix est dans un intervalle de ±15%
  2. Compare les titres avec `fuzz.ratio()` (distance de Levenshtein)
  3. Si similarité > 78% → c'est un doublon → on ajoute une nouvelle `SourceAnnonce` à la super-annonce existante
  4. Sinon → on crée une nouvelle `Annonce` normalement

**Étape 3 — Mettre à jour `main.py`**
- Remplacer la vérification simple par URL par l'appel à `core/fusion.py`

**Étape 4 — Mettre à jour l'API** (`main_api.py`)
- Créer une route `/annonces/{id}/sources` qui retourne toutes les plateformes et prix d'une Super-Annonce

**Étape 5 — Mettre à jour Flutter** (`detail_screen.dart`)
- Afficher un bloc "Comparer les offres" dans la page de détail
- Chaque source est représentée par une carte avec le logo de la plateforme et son prix
- Un bouton "Voir sur [Plateforme]" sur chaque carte

### 🟡 PRIORITÉ 2 : Recherche par Temps de Trajet (Isochrone)
- Créer un écran `MapSearchScreen` dans Flutter
- Connecter la barre de recherche de `HomeScreen` à cet écran
- Utiliser `flutter_map` (OpenStreetMap) pour la carte interactive
- Appeler l'API OpenRouteService pour calculer la zone isochrone

### 🟢 PRIORITÉ 3 : Valorisation et Statistiques des Quartiers
- Agréger les données de prix par zone géographique (PostGIS ou regroupement simple par texte de localisation)
- Créer un widget de statistiques (prix moyen du quartier, types de biens dominants)
- L'afficher dans la page de détail ou dans un écran dédié

---

## Comment lancer le projet

```bash
# 1. Activer l'environnement virtuel Python
cd /home/bryan/Documents/soutenance/new/scrapp
source env/bin/activate

# 2. Lancer le scraper (collecte les données)
python main.py

# 3. Lancer le serveur API (dans un terminal séparé)
uvicorn main_api:app --reload --host 127.0.0.1 --port 8000

# 4. Lancer l'application Flutter (dans un autre terminal)
cd immo_app
flutter run
```

---

## Recommandation technique (Solution A vs B)

**→ Choisir la Solution A (2 tables).**

Pourquoi : c'est ce qui est décrit dans le mémoire (base de données relationnelle structurée). C'est plus propre, plus évolutif, et ça donnera une bien meilleure impression au jury lors de la soutenance. La Solution B (JSON dans une colonne) est une rustine qui se voit immédiatement dans un code review.
