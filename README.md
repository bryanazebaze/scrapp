# Projet scrapp — instructions pour lancer localement

But : fournir les étapes minimum pour que tes camarades clonent le repo, installent l'environnement, lancent le backend (FastAPI) et l'application Flutter (immo_app) sur un téléphone ou émulateur.

Prérequis (sur Linux)
- Git
- Python 3.8+ (3.10 recommandé)
- pip
- Flutter SDK (stable) + Android SDK (ou Xcode si iOS)
- Pour appareil Android physique : activer Débogage USB
- (Optionnel) gh / ssh si vous poussez/pull via SSH

Racine du projet : `scrapp/`

1) Cloner le repo
```bash
git clone <URL_DU_REPO>   # ex: git@github.com:USER/REPO.git
cd scrapp
```

2) Backend — installation Python et lancement
- Créer et activer un virtualenv, installer dépendances :
```bash
# depuis scrapp/
python3 -m venv env
source env/bin/activate
# si requirements.txt existe :
pip install -r requirements.txt
# sinon installer les paquets usuels :
# pip install fastapi uvicorn sqlalchemy pydantic aiohttp
```

- Initialiser la base (si le repo fournit un script) :
```bash
# parfois nécessaire : vérifie si init_db.py existe
python init_db.py || true
```

- Lancer le serveur API en local (ordinateur seulement) :
```bash
uvicorn main_api:app --reload --host 127.0.0.1 --port 8000
```

- Si l'app Flutter tourne SUR UN TÉLÉPHONE physique (réseau local), lancer le backend sur toutes les interfaces :
```bash
uvicorn main_api:app --reload --host 0.0.0.0 --port 8000
# puis découvre l'IP de ton ordinateur sur le LAN :
hostname -I | awk '{print $1}'
# note l'IP (ex: 192.168.1.42)
```

Remarque CORS : pour Flutter mobile ce n'est pas nécessaire. Pour Flutter Web ajoute les middlewares CORS côté FastAPI si besoin.

3) Frontend Flutter — configuration et run
- Ouvrir un nouveau terminal, préparer Flutter :
```bash
cd immo_app
flutter pub get
```

- Configurer l'URL de l'API si besoin (si tu as lancé le backend sur 0.0.0.0) :  
  Ouvre `immo_app/lib/services/api_service.dart` et remplace l'URL de base par `http://<IP_ORDI>:8000` (remplace `<IP_ORDI>` par l'IP trouvée plus haut). Exemple :
```dart
// baseUrl = 'http://127.0.0.1:8000'; // localhost (ordinateur)
// si mobile physique, mettre l'IP du PC :
baseUrl = 'http://192.168.1.42:8000';
```

- Si tu testes sur un émulateur Android, tu peux aussi utiliser `adb reverse` pour que `127.0.0.1:8000` du PC soit accessible depuis l'émulateur :
```bash
# sur la machine dev (avec appareil connecté ou émulateur démarré)
adb reverse tcp:8000 tcp:8000
```

- Lister les devices disponibles et lancer :
```bash
flutter devices
# lancer sur le device désiré (ou par défaut)
flutter run -d <deviceId>
# pour Android physique connecte le téléphone via USB et accepte le débogage
# pour build release (apk) :
flutter build apk --release
```

Raccourcis pendant le dev
- Hot reload : appuie sur `r` dans le terminal où `flutter run` est lancé.
- Hot restart : `R`.

4) Points importants / dépannage
- Si le frontend n'arrive pas à joindre l'API :
  - Vérifie que uvicorn est lancé et sur la bonne interface/port.
  - Si mobile physique : assure-toi que le PC et le téléphone sont sur le même réseau Wi‑Fi.
  - Vérifie le firewall (ufw / iptables) et ouvre le port 8000 si nécessaire.
  - Pour émulateur Android, `adb reverse tcp:8000 tcp:8000` évite de changer l'URL dans le code.
- Si `flutter pub get` échoue : mets à jour Flutter (`flutter upgrade`) et vérifie la version channel stable.
- Si gros fichiers sont présents, ils ne doivent pas être poussés — le .gitignore contient déjà `env/` et artefacts.

5) Commandes utiles récapitulées
```bash
# Backend
cd scrapp
python3 -m venv env
source env/bin/activate
pip install -r requirements.txt
python init_db.py     # si présent
uvicorn main_api:app --reload --host 0.0.0.0 --port 8000

# Frontend
cd immo_app
flutter pub get
# si besoin : adb reverse tcp:8000 tcp:8000
flutter devices
flutter run -d <deviceId>
```

6) Si vous voulez tester sans config réseau
- Lancez le backend sur la même machine et utilisez un émulateur Android ; `adb reverse` simplifie la configuration.

Si vos camarades ont des erreurs spécifiques (logs), partagez ici l'erreur exacte et j'indiquerai la correction précise.
