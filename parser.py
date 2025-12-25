"""
SoundCloud Data Parser
======================
Script pour parser les JSON sauvegardés et générer des statistiques.

Usage:
    python parser.py

Génère:
    - stats.json: Statistiques globales
    - top_tracks.csv: Classement des tracks par nombre d'écoutes
    - listening_history.csv: Historique détaillé
"""

import json
import csv
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional

DUMP_DIR = Path("./dump")
OUTPUT_DIR = Path("./output")
OUTPUT_DIR.mkdir(exist_ok=True)


class SoundCloudParser:
    """Parser pour analyser les données SoundCloud extraites."""

    def __init__(self):
        self.tracks = {}  # track_id -> track_info
        self.play_counts = defaultdict(int)  # track_id -> count
        self.first_seen = {}  # track_id -> first_seen timestamp
        self.last_seen = {}  # track_id -> last_seen timestamp
        self.listening_history = []  # Liste de toutes les écoutes

    def _extract_track_data(self, data: Any, source_url: str = ""):
        """Extrait les données de tracks depuis un objet JSON."""
        if isinstance(data, dict):
            # Chercher des tracks dans différentes structures
            if "collection" in data:
                for item in data["collection"]:
                    self._extract_track_data(item, source_url)
            
            if "tracks" in data:
                for track in data["tracks"]:
                    self._extract_track_data(track, source_url)
            
            if "items" in data:
                for item in data["items"]:
                    self._extract_track_data(item, source_url)
            
            # Si c'est un track individuel
            if "id" in data and ("title" in data or "track" in data):
                track_id = data.get("id")
                if not track_id:
                    return
                
                # Récupérer les infos du track
                track_info = data.get("track", data)
                
                title = track_info.get("title", data.get("title", "Unknown"))
                user = track_info.get("user", {})
                artist = user.get("username", user.get("full_name", "Unknown Artist"))
                
                # Récupérer les métriques d'écoute
                play_count = (
                    data.get("play_count", 0) or
                    data.get("count", 0) or
                    track_info.get("playback_count", 0) or
                    0
                )
                
                # Timestamps
                created_at = data.get("created_at") or track_info.get("created_at")
                played_at = data.get("played_at") or data.get("timestamp")
                
                # Stocker les infos du track
                if track_id not in self.tracks:
                    self.tracks[track_id] = {
                        "track_id": track_id,
                        "title": title,
                        "artist": artist,
                        "url": track_info.get("permalink_url") or data.get("permalink_url", ""),
                    }
                
                # Mettre à jour les compteurs
                if play_count > 0:
                    self.play_counts[track_id] = max(
                        self.play_counts[track_id],
                        play_count
                    )
                
                # Timestamps
                if played_at:
                    if track_id not in self.first_seen:
                        self.first_seen[track_id] = played_at
                    else:
                        # Comparer les timestamps
                        try:
                            current = datetime.fromisoformat(self.first_seen[track_id].replace("Z", "+00:00"))
                            new = datetime.fromisoformat(played_at.replace("Z", "+00:00"))
                            if new < current:
                                self.first_seen[track_id] = played_at
                        except:
                            pass
                    
                    self.last_seen[track_id] = played_at
                    
                    # Ajouter à l'historique
                    self.listening_history.append({
                        "track_id": track_id,
                        "title": title,
                        "artist": artist,
                        "played_at": played_at,
                        "source_url": source_url,
                    })
                
                if created_at and track_id not in self.first_seen:
                    self.first_seen[track_id] = created_at

        elif isinstance(data, list):
            for item in data:
                self._extract_track_data(item, source_url)

    def parse_dump_files(self):
        """Parse tous les fichiers JSON dans le dossier dump."""
        if not DUMP_DIR.exists():
            print(f"[✗] Le dossier {DUMP_DIR} n'existe pas")
            return
        
        json_files = list(DUMP_DIR.glob("*.json"))
        if not json_files:
            print(f"[✗] Aucun fichier JSON trouvé dans {DUMP_DIR}")
            return
        
        print(f"[i] Analyse de {len(json_files)} fichiers JSON...")
        
        for json_file in json_files:
            try:
                with open(json_file, "r", encoding="utf-8") as f:
                    payload = json.load(f)
                
                # Extraire les données
                data = payload.get("data", {})
                url = payload.get("url", "")
                
                self._extract_track_data(data, url)
                
            except Exception as e:
                print(f"[!] Erreur lors du parsing de {json_file.name}: {e}")
        
        print(f"[✓] Parsing terminé")
        print(f"    Tracks trouvés: {len(self.tracks)}")
        print(f"    Écoutes enregistrées: {len(self.listening_history)}")
        print()

    def generate_top_tracks_csv(self):
        """Génère un CSV avec le classement des tracks par nombre d'écoutes."""
        if not self.tracks:
            print("[!] Aucune track trouvée")
            return
        
        # Créer une liste de tracks avec leurs statistiques
        tracks_list = []
        for track_id, track_info in self.tracks.items():
            tracks_list.append({
                "track_id": track_id,
                "title": track_info["title"],
                "artist": track_info["artist"],
                "play_count": self.play_counts.get(track_id, 0),
                "first_seen": self.first_seen.get(track_id, ""),
                "last_seen": self.last_seen.get(track_id, ""),
                "url": track_info.get("url", ""),
            })
        
        # Trier par play_count décroissant
        tracks_list.sort(key=lambda x: x["play_count"], reverse=True)
        
        # Sauvegarder en CSV
        csv_path = OUTPUT_DIR / "top_tracks.csv"
        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(
                f,
                fieldnames=["track_id", "title", "artist", "play_count", "first_seen", "last_seen", "url"]
            )
            writer.writeheader()
            writer.writerows(tracks_list)
        
        print(f"[✓] CSV généré: {csv_path}")
        print(f"    {len(tracks_list)} tracks classées")
        
        # Afficher le top 10
        print("\nTop 10 des tracks les plus écoutées:")
        for i, track in enumerate(tracks_list[:10], 1):
            print(f"  {i}. {track['artist']} - {track['title']} ({track['play_count']} écoutes)")

    def generate_listening_history_csv(self):
        """Génère un CSV avec l'historique détaillé des écoutes."""
        if not self.listening_history:
            print("[!] Aucun historique d'écoute trouvé")
            return
        
        # Trier par date (plus récent en premier)
        history_sorted = sorted(
            self.listening_history,
            key=lambda x: x.get("played_at", ""),
            reverse=True
        )
        
        csv_path = OUTPUT_DIR / "listening_history.csv"
        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(
                f,
                fieldnames=["played_at", "track_id", "title", "artist", "source_url"]
            )
            writer.writeheader()
            writer.writerows(history_sorted)
        
        print(f"[✓] Historique généré: {csv_path}")
        print(f"    {len(history_sorted)} écoutes enregistrées")

    def generate_stats_json(self):
        """Génère un fichier JSON avec les statistiques globales."""
        stats = {
            "total_tracks": len(self.tracks),
            "total_listens": len(self.listening_history),
            "tracks_with_play_count": len([t for t in self.tracks.keys() if self.play_counts.get(t, 0) > 0]),
            "total_play_count": sum(self.play_counts.values()),
            "date_range": {
                "first_seen": min(self.first_seen.values()) if self.first_seen else None,
                "last_seen": max(self.last_seen.values()) if self.last_seen else None,
            },
            "top_artists": self._get_top_artists(),
        }
        
        json_path = OUTPUT_DIR / "stats.json"
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(stats, f, indent=2, ensure_ascii=False)
        
        print(f"[✓] Statistiques générées: {json_path}")

    def _get_top_artists(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Retourne les artistes les plus écoutés."""
        artist_counts = defaultdict(int)
        
        for track_id, track_info in self.tracks.items():
            artist = track_info["artist"]
            play_count = self.play_counts.get(track_id, 0)
            artist_counts[artist] += play_count
        
        top_artists = sorted(
            artist_counts.items(),
            key=lambda x: x[1],
            reverse=True
        )[:limit]
        
        return [{"artist": artist, "play_count": count} for artist, count in top_artists]

    def run(self):
        """Lance le parsing complet."""
        print("=" * 60)
        print("SoundCloud Data Parser")
        print("=" * 60)
        print()
        
        self.parse_dump_files()
        
        if not self.tracks:
            print("[!] Aucune donnée à traiter")
            return
        
        print("[→] Génération des fichiers de sortie...\n")
        
        self.generate_top_tracks_csv()
        print()
        
        self.generate_listening_history_csv()
        print()
        
        self.generate_stats_json()
        print()
        
        print("=" * 60)
        print("Parsing terminé!")
        print(f"Fichiers générés dans: {OUTPUT_DIR.absolute()}")
        print("=" * 60)


if __name__ == "__main__":
    parser = SoundCloudParser()
    parser.run()

