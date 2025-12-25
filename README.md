# SoundCloud Listening History Scraper

Script pour récupérer votre historique d'écoute SoundCloud personnel en interceptant les requêtes réseau utilisées par le site.

## 🎯 Objectif

Ce projet permet d'extraire vos données d'écoute SoundCloud en observant les requêtes API faites par le site web. Aucune automatisation de login n'est nécessaire - le script utilise votre session Edge existante.

## 📋 Prérequis

- Windows 11
- Microsoft Edge (Chromium)
- Python 3.8+
- Compte SoundCloud connecté dans Edge

## 🚀 Installation

1. **Cloner ou télécharger ce projet**

2. **Installer les dépendances Python** :
   ```bash
   pip install -r requirements.txt
   ```

3. **Installer les navigateurs Playwright** :
   ```bash
   playwright install chromium
   ```

## 📖 Utilisation

### Étape 1 : Scraping des requêtes réseau

Lancez le script principal pour intercepter les requêtes :

```bash
python scraper.py
```

**Options** :

- **Profil par défaut** : Le script utilisera automatiquement votre profil Edge par défaut
- **Profil personnalisé** : Pour utiliser un profil spécifique :
  ```bash
  python scraper.py "C:\Users\VotreNom\AppData\Local\Microsoft\Edge\User Data\Profile 1"
  ```

**Ce que fait le script** :

1. Lance Edge avec votre profil utilisateur existant
2. Ouvre SoundCloud
3. Navigue automatiquement vers différentes pages (For You, historique, profil)
4. Intercepte toutes les requêtes réseau vers les endpoints SoundCloud
5. Sauvegarde les réponses JSON pertinentes dans `./dump/`

**Pendant l'exécution** :

- Le navigateur reste ouvert et visible
- Vous pouvez naviguer manuellement sur SoundCloud pour déclencher plus de requêtes
- Toutes les requêtes pertinentes sont automatiquement sauvegardées
- Appuyez sur `Ctrl+C` pour arrêter

### Étape 2 : Parsing des données

Une fois le scraping terminé, analysez les données collectées :

```bash
python parser.py
```

**Fichiers générés** (dans `./output/`) :

- `top_tracks.csv` : Classement des tracks par nombre d'écoutes
  - Colonnes : `track_id`, `title`, `artist`, `play_count`, `first_seen`, `last_seen`, `url`
  
- `listening_history.csv` : Historique détaillé de toutes les écoutes
  - Colonnes : `played_at`, `track_id`, `title`, `artist`, `source_url`
  
- `stats.json` : Statistiques globales
  - Nombre total de tracks
  - Nombre total d'écoutes
  - Top artistes
  - Période couverte

## 🔧 Configuration

### Chemin du profil Edge sur Windows 11

Le profil Edge par défaut se trouve généralement à :
```
C:\Users\<VOTRE_NOM>\AppData\Local\Microsoft\Edge\User Data
```

Pour utiliser un profil spécifique (ex: Profile 1, Profile 2) :
```
C:\Users\<VOTRE_NOM>\AppData\Local\Microsoft\Edge\User Data\Profile 1
```

**Comment trouver votre profil** :

1. Ouvrez Edge
2. Allez dans `edge://version/`
3. Regardez la ligne "Profile Path"
4. Utilisez ce chemin dans le script

### Personnalisation des endpoints

Pour intercepter d'autres endpoints, modifiez la liste `SOUNDCLOUD_ENDPOINTS` dans `scraper.py` :

```python
SOUNDCLOUD_ENDPOINTS = [
    "api-v2.soundcloud.com",
    "votre-endpoint-personnalise",
    # ...
]
```

## 📁 Structure du projet

```
scrapper/
├── scraper.py          # Script principal de scraping
├── parser.py           # Script de parsing et génération de statistiques
├── requirements.txt    # Dépendances Python
├── README.md          # Ce fichier
├── dump/              # Dossier de sauvegarde des JSON bruts (créé automatiquement)
└── output/            # Dossier de sortie des fichiers analysés (créé automatiquement)
```

## 🔍 Détails techniques

### Endpoints interceptés

Le script intercepte les requêtes vers :
- `api-v2.soundcloud.com`
- `api.soundcloud.com`
- Endpoints contenant : `explore`, `play-history`, `replay`, `wrapped`, `listening`, `insights`, `stats`, `history`

### Filtrage des réponses

Seules les réponses contenant des mots-clés pertinents sont sauvegardées :
- `track_id`, `user_id`, `play_count`, `count`, `listening`, `timestamp`, `played_at`, `created_at`, `tracks`, `playlist`, `history`

### Format des fichiers sauvegardés

Chaque fichier JSON dans `./dump/` contient :
```json
{
  "url": "https://api-v2.soundcloud.com/...",
  "method": "GET",
  "status": 200,
  "status_text": "OK",
  "headers": {...},
  "timestamp": "2024-01-01T12:00:00",
  "data": {...}
}
```

## ⚠️ Notes importantes

- **Lecture seule** : Ce script n'effectue aucune modification sur votre compte
- **Données personnelles** : Les données extraites sont uniquement celles accessibles via votre session
- **Respect de la vie privée** : Ne partagez jamais vos fichiers `dump/` qui contiennent vos données personnelles
- **Rate limiting** : SoundCloud peut limiter les requêtes si vous en faites trop. Le script attend entre les navigations pour éviter cela

## 🐛 Dépannage

### Le script ne trouve pas Edge

Assurez-vous que Edge est installé. Playwright cherche automatiquement Edge via le canal `msedge`.

### Aucune requête interceptée

1. Vérifiez que vous êtes bien connecté à SoundCloud dans Edge
2. Naviguez manuellement sur différentes pages SoundCloud pendant l'exécution
3. Vérifiez que les endpoints correspondent bien (voir la configuration)

### Erreur de profil

Si vous obtenez une erreur liée au profil :
1. Fermez complètement Edge avant de lancer le script
2. Utilisez un chemin de profil valide
3. Vérifiez les permissions d'accès au dossier du profil

### Aucune donnée dans le parser

1. Vérifiez que des fichiers JSON ont bien été créés dans `./dump/`
2. Les structures de données SoundCloud peuvent varier - vous devrez peut-être adapter `parser.py` selon vos données

## 📝 Licence

Ce projet est fourni à des fins éducatives et personnelles uniquement. Respectez les conditions d'utilisation de SoundCloud.

## 🤝 Contribution

N'hésitez pas à adapter le code selon vos besoins. Les structures de données SoundCloud peuvent évoluer, donc le parser peut nécessiter des ajustements.

