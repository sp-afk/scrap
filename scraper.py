"""
SoundCloud Listening History Scraper
=====================================
Script pour intercepter et sauvegarder les requêtes réseau SoundCloud
afin de récupérer l'historique d'écoute personnel.

Usage:
    python scraper.py

Prérequis:
    - Edge installé avec profil utilisateur contenant la session SoundCloud
    - Playwright installé: pip install playwright && playwright install chromium
"""

import asyncio
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Any
from urllib.parse import urlparse

from playwright.async_api import async_playwright, Page, Route, Response


# Configuration
DUMP_DIR = Path("./dump")
DUMP_DIR.mkdir(exist_ok=True)

# Endpoints SoundCloud à intercepter
SOUNDCLOUD_ENDPOINTS = [
    "api-v2.soundcloud.com",
    "api.soundcloud.com",
    "soundcloud.com/api",
    "explore",
    "play-history",
    "replay",
    "wrapped",
    "listening",
    "insights",
    "stats",
    "history",
]

# Mots-clés pour filtrer les réponses pertinentes
RELEVANT_KEYWORDS = [
    "track_id",
    "user_id",
    "play_count",
    "count",
    "listening",
    "timestamp",
    "played_at",
    "created_at",
    "tracks",
    "playlist",
    "history",
]


class SoundCloudScraper:
    """Scraper pour intercepter les requêtes réseau SoundCloud."""

    def __init__(self, edge_profile_path: str = None):
        """
        Initialise le scraper.
        
        Args:
            edge_profile_path: Chemin vers le profil Edge utilisateur.
                              Si None, utilise le profil par défaut.
        """
        self.edge_profile_path = edge_profile_path
        self.request_count = 0
        self.saved_count = 0

    def _is_soundcloud_endpoint(self, url: str) -> bool:
        """Vérifie si l'URL correspond à un endpoint SoundCloud à intercepter."""
        url_lower = url.lower()
        return any(endpoint in url_lower for endpoint in SOUNDCLOUD_ENDPOINTS)

    def _is_relevant_response(self, content: str) -> bool:
        """Vérifie si la réponse contient des données pertinentes."""
        content_lower = content.lower()
        return any(keyword in content_lower for keyword in RELEVANT_KEYWORDS)

    def _sanitize_filename(self, url: str) -> str:
        """Génère un nom de fichier valide à partir d'une URL."""
        parsed = urlparse(url)
        # Prendre le chemin et le nettoyer
        path = parsed.path.strip("/").replace("/", "_")
        if not path:
            path = "root"
        
        # Ajouter un timestamp pour éviter les collisions
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        
        # Limiter la longueur
        if len(path) > 100:
            path = path[:100]
        
        return f"{timestamp}_{path}.json"

    async def _handle_response(self, response: Response):
        """Gère une réponse réseau interceptée."""
        self.request_count += 1
        
        url = response.url
        
        # Vérifier si c'est un endpoint SoundCloud
        if not self._is_soundcloud_endpoint(url):
            return
        
        # Vérifier le Content-Type
        content_type = response.headers.get("content-type", "").lower()
        if "json" not in content_type and "text" not in content_type:
            return
        
        try:
            # Récupérer le contenu
            content = await response.text()
            
            # Vérifier si la réponse est pertinente
            if not self._is_relevant_response(content):
                return
            
            # Parser le JSON pour vérifier qu'il est valide
            try:
                data = json.loads(content)
            except json.JSONDecodeError:
                # Si ce n'est pas du JSON valide, on peut quand même sauvegarder
                data = {"raw_content": content}
            
            # Créer le payload à sauvegarder
            payload = {
                "url": url,
                "method": response.request.method,
                "status": response.status,
                "status_text": response.status_text,
                "headers": dict(response.headers),
                "timestamp": datetime.now().isoformat(),
                "data": data,
            }
            
            # Générer le nom de fichier
            filename = self._sanitize_filename(url)
            filepath = DUMP_DIR / filename
            
            # Sauvegarder
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(payload, f, indent=2, ensure_ascii=False)
            
            self.saved_count += 1
            
            # Logger
            print(f"[✓] Sauvegardé: {filename}")
            print(f"    URL: {url}")
            print(f"    Status: {response.status} {response.status_text}")
            print(f"    Taille: {len(content)} bytes")
            print()
            
        except Exception as e:
            print(f"[✗] Erreur lors du traitement de {url}: {e}")

    async def _navigate_and_wait(self, page: Page, url: str, description: str):
        """Navigue vers une URL et attend le chargement."""
        print(f"\n[→] Navigation vers: {description}")
        print(f"    URL: {url}")
        
        try:
            await page.goto(url, wait_until="networkidle", timeout=30000)
            await asyncio.sleep(2)  # Attendre un peu pour les requêtes asynchrones
            print(f"[✓] Page chargée: {description}\n")
        except Exception as e:
            print(f"[✗] Erreur lors du chargement de {url}: {e}\n")

    async def run(self):
        """Lance le scraper."""
        print("=" * 60)
        print("SoundCloud Listening History Scraper")
        print("=" * 60)
        print()
        
        async with async_playwright() as p:
            # Configuration pour Edge
            browser_args = []
            
            # Si un profil personnalisé est fourni, l'utiliser
            if self.edge_profile_path:
                browser_args.append(f"--user-data-dir={self.edge_profile_path}")
                print(f"[i] Utilisation du profil Edge: {self.edge_profile_path}")
            else:
                # Profil par défaut Edge sur Windows 11
                # Le profil par défaut sera utilisé automatiquement
                print("[i] Utilisation du profil Edge par défaut")
            
            print()
            
            # Lancer Edge
            print("[→] Lancement de Microsoft Edge...")
            browser = await p.chromium.launch(
                channel="msedge",
                headless=False,  # Mode visible pour voir ce qui se passe
                args=browser_args,
            )
            
            # Créer un contexte avec le profil utilisateur
            context = await browser.new_context(
                viewport={"width": 1920, "height": 1080},
            )
            
            page = await context.new_page()
            
            # Intercepter toutes les réponses
            page.on("response", self._handle_response)
            
            print("[✓] Edge lancé\n")
            
            # Étape 1: Ouvrir SoundCloud
            await self._navigate_and_wait(
                page,
                "https://soundcloud.com",
                "Page d'accueil SoundCloud"
            )
            
            # Attendre que l'utilisateur soit connecté (ou détecter)
            print("[i] Vérification de la connexion...")
            await asyncio.sleep(3)
            
            # Vérifier si on est connecté en cherchant des éléments de navigation
            try:
                # Chercher des éléments qui indiquent qu'on est connecté
                user_menu = await page.query_selector('a[href*="/you"]')
                if user_menu:
                    print("[✓] Connexion détectée\n")
                else:
                    print("[!] Connexion non détectée - assurez-vous d'être connecté\n")
            except:
                print("[!] Impossible de vérifier la connexion - continuez manuellement\n")
            
            # Étape 2: Naviguer vers différentes pages pour déclencher des requêtes
            print("[i] Navigation vers différentes pages pour déclencher des requêtes API...\n")
            
            # Page "For You"
            await self._navigate_and_wait(
                page,
                "https://soundcloud.com/you",
                "Page 'For You'"
            )
            
            # Attendre un peu pour que les requêtes se déclenchent
            await asyncio.sleep(5)
            
            # Essayer d'accéder à l'historique d'écoute
            # SoundCloud peut avoir différentes URLs pour l'historique
            history_urls = [
                "https://soundcloud.com/you/history",
                "https://soundcloud.com/you/listening-history",
                "https://soundcloud.com/you/tracks",
            ]
            
            for history_url in history_urls:
                try:
                    await self._navigate_and_wait(
                        page,
                        history_url,
                        f"Historique d'écoute ({history_url})"
                    )
                    await asyncio.sleep(5)
                except:
                    pass
            
            # Essayer d'accéder à la page de profil
            try:
                # Récupérer l'URL du profil depuis la page
                profile_link = await page.query_selector('a[href*="/you"]')
                if profile_link:
                    profile_href = await profile_link.get_attribute("href")
                    if profile_href:
                        if not profile_href.startswith("http"):
                            profile_href = f"https://soundcloud.com{profile_href}"
                        await self._navigate_and_wait(
                            page,
                            profile_href,
                            "Profil utilisateur"
                        )
                        await asyncio.sleep(5)
            except Exception as e:
                print(f"[!] Impossible d'accéder au profil: {e}\n")
            
            # Attendre que l'utilisateur navigue manuellement si nécessaire
            print("=" * 60)
            print("[i] Scraping en cours...")
            print("[i] Vous pouvez maintenant naviguer manuellement sur SoundCloud")
            print("[i] Toutes les requêtes pertinentes seront interceptées et sauvegardées")
            print("[i] Appuyez sur Ctrl+C pour arrêter")
            print("=" * 60)
            print()
            
            # Garder le navigateur ouvert pour interception continue
            try:
                await asyncio.sleep(300)  # Attendre 5 minutes (ou jusqu'à interruption)
            except KeyboardInterrupt:
                print("\n[i] Arrêt demandé par l'utilisateur...")
            
            # Statistiques finales
            print()
            print("=" * 60)
            print("Résumé")
            print("=" * 60)
            print(f"Requêtes interceptées: {self.request_count}")
            print(f"Réponses sauvegardées: {self.saved_count}")
            print(f"Dossier de sauvegarde: {DUMP_DIR.absolute()}")
            print("=" * 60)
            
            # Fermer le navigateur
            await browser.close()


def get_default_edge_profile_path() -> str:
    """
    Retourne le chemin par défaut du profil Edge sur Windows 11.
    
    Sur Windows, Edge stocke les profils dans:
    C:\Users\<USERNAME>\AppData\Local\Microsoft\Edge\User Data
    
    Pour utiliser un profil spécifique, utilisez:
    C:\Users\<USERNAME>\AppData\Local\Microsoft\Edge\User Data\Profile 1
    """
    import os
    username = os.getenv("USERNAME")
    if username:
        return f"C:\\Users\\{username}\\AppData\\Local\\Microsoft\\Edge\\User Data"
    return None


if __name__ == "__main__":
    import sys
    
    # Option pour spécifier un profil personnalisé
    profile_path = None
    if len(sys.argv) > 1:
        profile_path = sys.argv[1]
        print(f"[i] Profil personnalisé: {profile_path}")
    else:
        # Utiliser le profil par défaut
        default_profile = get_default_edge_profile_path()
        if default_profile:
            print(f"[i] Profil par défaut: {default_profile}")
            print("[i] Pour utiliser un profil spécifique, passez-le en argument:")
            print(f"    python scraper.py \"{default_profile}\\Profile 1\"")
            print()
    
    scraper = SoundCloudScraper(edge_profile_path=profile_path)
    
    try:
        asyncio.run(scraper.run())
    except KeyboardInterrupt:
        print("\n[i] Script interrompu par l'utilisateur")
    except Exception as e:
        print(f"\n[✗] Erreur: {e}")
        import traceback
        traceback.print_exc()

