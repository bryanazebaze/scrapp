# =====================================================================
#  CONTEXTE COMPLET DU PROJET : CentralImmo (Agrégateur Immobilier)
#  🗓️  Dernière mise à jour : 18 Juin 2026
#  📁  Dossier racine du projet : /home/bryan/Documents/soutenance/new/scrapp
# =====================================================================

## C'est quoi le projet ?

CentralImmo est un **agrégateur immobilier** pour le marché camerounais.
L'idée est simple : au lieu que l'utilisateur aille sur Kasastay, puis Mapiole, puis d'autres sites un par un, notre application récupère les annonces de tous ces sites automatiquement, les déduplique, et les affiche en un seul endroit, propre et sans redondance.

C'est le projet de soutenance de Licence 3 en Génie Logiciel.
L'encadreur académique a proposé le thème. Smart Service Hub (SSH) a fourni l'accompagnement professionnel.

---

## Architecture du Projet

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
├── main.py              ← Orchestrateur : lance tous les scrapers → appelle fusion.py
├── main_api.py          ← Serveur FastAPI (2 routes : /annonces et /annonces/{id})
├── init_db.py           ← Réinitialiser la base de données (drop_all + create_all)
├── core/
│   ├── models.py        ← Deux tables : Annonce (Super) + SourceAnnonce
│   ├── schemas.py       ← Trois schémas Pydantic : SourceAnnonceSchema, AnnonceBreve, AnnonceDetaillee
│   ├── fusion.py        ← Algorithme de déduplication avec rapidfuzz
│   └── database.py      ← Connexion à la base de données
├── scrapers/
│   ├── base.py          ← Classe de base commune à tous les scrapers
│   ├── kasastay.py      ← Scraper Kasastay ✅ (retourne des dict{})
│   └── mapiole.py       ← Scraper Mapiole ✅ (retourne des dict{})
├── static/images/       ← Images téléchargées localement (style Trivago)
└── immo_app/            ← Application mobile Flutter
    └── lib/
        ├── main.dart
        ├── models/annonce.dart         ← ⚠️ À METTRE À JOUR (voir section Flutter ci-dessous)
        ├── services/api_service.dart   ← Appels HTTP vers FastAPI
        └── screens/
            ├── home_screen.dart        ← ⚠️ À METTRE À JOUR (voir section Flutter ci-dessous)
            └── detail_screen.dart      ← ⚠️ À METTRE À JOUR (voir section Flutter ci-dessous)
```

---

## Ce qui a été fait dans cette session (18 Juin 2026) ✅

### Vision Produit définie
L'expérience utilisateur a été clarifiée et est la suivante :
- Le client **ne sait pas** quelle plateforme a posté la maison sur l'écran d'accueil.
- Sur la **page de détail**, il voit en grand : le **meilleur prix** avec une mention textuelle courte ("L'offre la moins chère"), une description **essentielle** (pas de roman), et un bouton "Voir l'offre" vers le site source.
- En bas, une **liste de cartes verticales** présente les autres plateformes qui publient la même maison, avec leur prix et une petite particularité, et un bouton "Voir l'offre" pour chacune.

### Backend (Python) ✅
- **`core/models.py`** : Refactorisé. Le modèle `Annonce` est maintenant la "Super-Annonce" (`meilleur_prix`, sans `nom_plateforme` ni `url_source`). La table `SourceAnnonce` contient le champ `particularite`.
- **`core/fusion.py`** : Entièrement réécrit pour accepter des `dict{}` en entrée (et non plus des objets `Annonce`). L'algorithme normalise les titres, compare les prix à ±15% et utilise `rapidfuzz` (score ≥ 78%) pour détecter les doublons. Il met à jour `meilleur_prix` si une source moins chère est trouvée.
- **`scrapers/kasastay.py`** et **`scrapers/mapiole.py`** : Ne retournent plus des `Annonce(...)` mais des `dict(...)`. L'import `from core.models import Annonce` a été supprimé.
- **`main.py`** : Simplifié. La boucle appelle directement `fusionner_ou_inserer(db, annonce)` sans normaliser manuellement le titre.
- **`core/schemas.py`** : Trois schémas clairs : `SourceAnnonceSchema` (avec `particularite`), `AnnonceBreve` (pour HomeScreen, léger), `AnnonceDetaillee` (pour DetailScreen, avec la liste des sources).
- **`main_api.py`** : Deux endpoints :
  - `GET /annonces` → retourne `List[AnnonceBreve]` (ultra-léger pour la liste)
  - `GET /annonces/{id}` → retourne `AnnonceDetaillee` avec les sources triées par prix croissant ✅

---

## Ce qui reste à faire 🚧

### 🔴 PRIORITÉ 1 : Mettre à jour l'Application Mobile Flutter

#### Étape A — Mettre à jour `immo_app/lib/models/annonce.dart`
Le modèle Dart est encore calé sur l'ancienne API. Il faut le refactoriser pour coller aux deux nouveaux schémas Pydantic :
- Classe `Source` : ajouter le champ `String? particularite`
- Classe `Annonce` : remplacer `int? prixEntier` par `int? meilleurPrix`, supprimer `String urlSource` et `String? nomPlateforme` (en tant que champs requis en HomeScreen)

#### Étape B — Mettre à jour `immo_app/lib/services/api_service.dart`
Vérifier que le service appelle bien `/annonces` pour la liste, et `/annonces/{id}` pour le détail.

#### Étape C — Mettre à jour `immo_app/lib/screens/home_screen.dart`
- Remplacer `annonce.prixEntier` par `annonce.meilleurPrix`
- Supprimer le badge de plateforme (le client ne doit pas voir d'où vient l'annonce !)

#### Étape D — Refaire `immo_app/lib/screens/detail_screen.dart`
C'est le gros du travail restant. La nouvelle interface de détail doit avoir :
1. **En haut** : Photo carousel, titre, localisation
2. **Prix mis en valeur** : Grand chiffre + texte *"L'offre la moins chère de toutes les propositions"* (couleur verte de la charte)
3. **Description courte** : Seulement l'essentiel (pas de texte interminable)
4. **Bouton principal** : "Voir l'offre" → ouvre l'URL de la source la moins chère
5. **Séparateur** avec titre "Autres offres disponibles"
6. **Liste verticale de cartes** : une carte par `SourceAnnonce` avec :
   - Nom de la plateforme (Kasastay, Mapiole...)
   - Prix proposé
   - Petite particularité textuelle
   - Bouton "Voir l'offre" → ouvre l'URL de cette source

### 🟡 PRIORITÉ 2 : Recherche par Temps de Trajet (Isochrone)
- Créer un écran `MapSearchScreen` dans Flutter
- Connecter la barre de recherche de `HomeScreen` à cet écran
- Utiliser `flutter_map` (OpenStreetMap) pour la carte interactive
- Appeler l'API OpenRouteService pour calculer la zone isochrone

### 🟢 PRIORITÉ 3 : Valorisation et Statistiques des Quartiers
- Agréger les données de prix par zone géographique
- Créer un widget de statistiques (prix moyen du quartier, types de biens dominants)

---

## Charte Graphique (à respecter dans Flutter)
- **Couleur principale** : Vert Émeraude `#00695C` (fond header, accents)
- **Couleur secondaire** : Or Premium `#D4AF37` (chips sélectionnées, badges)
- **Fond général** : `Colors.grey.shade100`
- **Cartes** : Blanc avec coins arrondis à 20px et ombre douce

---

## Comment lancer le projet

```bash
# 1. Activer l'environnement virtuel Python
cd /home/bryan/Documents/soutenance/new/scrapp
source env/bin/activate

# 2. (Si 1ère fois ou reset) — Réinitialiser la base de données
python init_db.py

# 3. Lancer le scraper (collecte les données + déduplication)
python main.py

# 4. Lancer le serveur API (dans un terminal séparé)
uvicorn main_api:app --reload --host 127.0.0.1 --port 8000

# 5. Lancer l'application Flutter (dans un autre terminal)
cd immo_app
flutter run
```

> 💡 **Port de l'API** : Sur émulateur Android, utiliser `10.0.2.2:8000` au lieu de `127.0.0.1:8000`. Sur appareil physique sur le même réseau Wi-Fi, utiliser l'adresse IP locale de la machine.
