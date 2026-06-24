# CentralImmo — Plateforme d'agrégation immobilière du Cameroun

CentralImmo agrège les annonces immobilières de plusieurs sites camerounais (Mapiole, Kasastay, et tout autre site via le scraper universel), déduplique les annonces en "Super-Annonces", suit l'historique des prix, calcule des scores de marché par quartier, et sert une application Flutter premium.

## Architecture

Voir `docs/architecture.md` pour le schéma complet.

**Backend**: FastAPI + SQLAlchemy + PostgreSQL + APScheduler
**Scrapers**: Python (requests + BeautifulSoup) avec anti-bot (BaseFetchMixin)
**Frontend**: Flutter (Riverpod + go_router + Dio + flutter_map + fl_chart)
**DB**: 5 tables core (sources, raw_listings, canonical_properties, listing_history, locations) + 3 opérationnelles (image_cache, scheduler_jobs, neighborhood_analytics)

## Démarrage rapide

### Prérequis
- Python 3.10+
- PostgreSQL 14+
- Flutter 3.35+ (Dart 3.9+)

### Backend

```bash
cd scrapp
cp .env.example .env          # éditer DATABASE_URL et autres configs
pip install -r requirements.txt

# Créer la base PostgreSQL
sudo -u postgres createdb immo_db
sudo -u postgres createuser immo_user
sudo -u postgres psql -c "ALTER USER immo_user WITH PASSWORD '1234';"
sudo -u postgres psql -c "GRANT ALL ON DATABASE immo_db TO immo_user;"

# Migrations (crée les tables + backfill depuis legacy si présent)
alembic upgrade head

# Premier crawl
python cli.py crawl --source mapiole --max-pages 2
python cli.py analytics    # calculer les scores des quartiers

# Démarrer l'API
uvicorn main_api:app --reload --host 0.0.0.0 --port 8000
```

### Flutter

```bash
cd scrapp/immo_app
flutter pub get

# Émulateur Android: utiliser 10.0.2.2 au lieu de localhost
flutter run --dart-define=API_BASE_URL=http://10.0.2.2:8000

# Téléphone physique (même réseau Wi-Fi):
# 1. Lancer le backend sur 0.0.0.0 (ci-dessus)
# 2. Trouver l'IP du PC: hostname -I | awk '{print $1}'
# 3. Lancer Flutter avec cette IP:
flutter run --dart-define=API_BASE_URL=http://192.168.1.42:8000

# Web (localhost):
flutter run -d chrome --dart-define=API_BASE_URL=http://127.0.0.1:8000
```

## Commandes CLI

```bash
python cli.py crawl                              # crawler toutes les sources actives
python cli.py crawl --source mapiole             # crawler une source
python cli.py crawl --source mapiole --max-pages 3
python cli.py refresh                            # re-crawler (détecter changements de prix)
python cli.py analytics                           # recalculer les scores des quartiers
python cli.py jobs                                # voir l'état des jobs planifiés
python cli.py universal --url https://example.com  # crawler un nouveau site
```

## API Endpoints

Voir `docs/api.md` pour la référence complète.

- `GET /annonces` — listings filtrés (type, ville, quartier, prix, chambres, surface)
- `GET /annonces/{id}` — détail avec sources, historique de prix, explication de matching
- `GET /search?q=3-bedroom house in Bastos under 120M` — recherche en langage naturel
- `GET /neighborhoods/{slug}` — intelligence de marché (5 scores 0-10)
- `GET /neighborhoods/trending/list` — quartiers en tendance
- `POST /admin/review/{id}` — approuver/rejeter une annonce universelle
- `GET /health` — santé de l'API + scheduler

## Documentation

- `docs/architecture.md` — schéma d'architecture complet
- `docs/adr/` — 8 ADRs (décisions architecturales)
- `docs/burp-analysis.md` — analyse Burp Suite de Mapiole et Kasastay
- `docs/api.md` — référence API
- `CLAUDE.md` — conventions pour le développement

## Planificateur

Le scheduler APScheduler tourne en arrière-plan avec l'API:
- **Quotidien 02:00** — crawl de toutes les sources actives
- **Toutes les 6h** — re-crawl (détecter les changements de prix/disponibilité)
- **Lundi 03:00** — recalcul des scores de quartier

État des jobs: `GET /admin/jobs` ou `python cli.py jobs`

## Stack technique

| Couche | Technologie |
|--------|-------------|
| Backend | FastAPI, SQLAlchemy 2.0, Pydantic, PostgreSQL |
| Scrapers | requests, BeautifulSoup, rapidfuzz, urllib3 Retry |
| Scheduling | APScheduler (BackgroundScheduler) |
| Migrations | Alembic |
| Frontend | Flutter, Riverpod, go_router, Dio, flutter_map, fl_chart |
| Config | pydantic-settings (.env), --dart-define (Flutter) |