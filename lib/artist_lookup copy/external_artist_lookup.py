#!/usr/bin/env python3
"""
External API Artist-Genre Lookup
=================================
This module uses external music APIs to automatically determine the genre(s)
for any artist name, even artists not in your existing database.

Supports multiple music data services:
1. MusicBrainz (Free, no API key required)
2. Spotify Web API (Free, requires client credentials)
3. Last.fm API (Free, requires API key)

Usage:
    from external_artist_lookup import get_genres_from_api, batch_lookup_artists
    
    # Single lookup
    genres = get_genres_from_api("Coldplay", provider="musicbrainz")
    print(genres)  # ["pop", "rock", "alternative rock"]
    
    # Batch lookup
    artists = ["Coldplay", "Beyoncé", "Taylor Swift"]
    results = batch_lookup_artists(artists)
"""

import requests
import time
import json
import base64
from typing import Optional, Dict, List, Tuple
from urllib.parse import quote


class ArtistGenreLookup:
    """Lookup music genres for artists using external music APIs."""
    
    def __init__(self, cache_file: str = "artist_genre_cache.json"):
        """
        Initialize the lookup service.
        
        Args:
            cache_file: Path to JSON file for caching results
        """
        self.cache_file = cache_file
        self.cache = self._load_cache()
        self.spotify_token = None
        self.spotify_token_expiry = 0
        
    def _load_cache(self) -> Dict[str, List[str]]:
        """Load cached artist-genre mappings from file."""
        try:
            with open(self.cache_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return {}
    
    def _save_cache(self):
        """Save cache to file."""
        with open(self.cache_file, 'w') as f:
            json.dump(self.cache, f, indent=2)
    
    def lookup_musicbrainz(self, artist: str) -> Optional[List[str]]:
        """
        Look up genres using MusicBrainz API (Free, no key required).
        
        MusicBrainz is an open music encyclopedia with comprehensive artist data.
        
        Args:
            artist: Artist name
            
        Returns:
            List of genres or None if not found
        """
        # Check cache first
        cache_key = f"{artist.lower()}|musicbrainz"
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        # MusicBrainz requires User-Agent and rate limiting
        headers = {
            'User-Agent': 'ArtistGenreMapper/1.0 (Educational Purpose)'
        }
        
        url = "https://musicbrainz.org/ws/2/artist/"
        params = {
            'query': artist,
            'fmt': 'json',
            'limit': 1
        }
        
        try:
            # MusicBrainz requires 1 second between requests
            time.sleep(1)
            
            response = requests.get(url, params=params, headers=headers, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if data.get('artists') and len(data['artists']) > 0:
                artist_data = data['artists'][0]
                
                # Get tags (genres) from artist
                artist_id = artist_data.get('id')
                if artist_id:
                    # Fetch tags for the artist
                    tags_url = f"https://musicbrainz.org/ws/2/artist/{artist_id}"
                    tags_params = {'inc': 'tags', 'fmt': 'json'}
                    
                    time.sleep(1)
                    tags_response = requests.get(tags_url, params=tags_params, 
                                                headers=headers, timeout=10)
                    tags_data = tags_response.json()
                    
                    if tags_data.get('tags'):
                        genres = [tag['name'] for tag in tags_data['tags'][:5]]
                        
                        if genres:
                            self.cache[cache_key] = genres
                            self._save_cache()
                            return genres
            
            return None
            
        except Exception as e:
            print(f"Error looking up {artist} with MusicBrainz: {e}")
            return None
    
    def _get_spotify_token(self, client_id: str, client_secret: str) -> Optional[str]:
        """
        Get Spotify access token using client credentials flow.
        
        Args:
            client_id: Spotify client ID
            client_secret: Spotify client secret
            
        Returns:
            Access token or None if failed
        """
        # Check if we have a valid token cached
        current_time = time.time()
        if self.spotify_token and current_time < self.spotify_token_expiry:
            return self.spotify_token
        
        # Get new token
        url = "https://accounts.spotify.com/api/token"
        
        # Encode credentials
        credentials = f"{client_id}:{client_secret}"
        encoded_credentials = base64.b64encode(credentials.encode()).decode()
        
        headers = {
            'Authorization': f'Basic {encoded_credentials}',
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        
        data = {
            'grant_type': 'client_credentials'
        }
        
        try:
            response = requests.post(url, headers=headers, data=data, timeout=10)
            response.raise_for_status()
            token_data = response.json()
            
            self.spotify_token = token_data['access_token']
            # Token expires in 1 hour, refresh 5 minutes early
            self.spotify_token_expiry = current_time + token_data['expires_in'] - 300
            
            return self.spotify_token
            
        except Exception as e:
            print(f"Error getting Spotify token: {e}")
            return None
    
    def lookup_spotify(self, artist: str, client_id: str, client_secret: str) -> Optional[List[str]]:
        """
        Look up genres using Spotify Web API (Free, requires app credentials).
        
        Get credentials: https://developer.spotify.com/dashboard/applications
        
        Args:
            artist: Artist name
            client_id: Spotify client ID
            client_secret: Spotify client secret
            
        Returns:
            List of genres or None if not found
        """
        cache_key = f"{artist.lower()}|spotify"
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        # Get access token
        token = self._get_spotify_token(client_id, client_secret)
        if not token:
            return None
        
        # Search for artist
        url = "https://api.spotify.com/v1/search"
        headers = {
            'Authorization': f'Bearer {token}'
        }
        params = {
            'q': artist,
            'type': 'artist',
            'limit': 1
        }
        
        try:
            response = requests.get(url, headers=headers, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if data.get('artists') and data['artists'].get('items'):
                artist_data = data['artists']['items'][0]
                genres = artist_data.get('genres', [])
                
                if genres:
                    self.cache[cache_key] = genres
                    self._save_cache()
                    return genres
            
            return None
            
        except Exception as e:
            print(f"Error looking up {artist} with Spotify: {e}")
            return None
    
    def lookup_lastfm(self, artist: str, api_key: str) -> Optional[List[str]]:
        """
        Look up genres using Last.fm API (Free, requires API key).
        
        Get API key: https://www.last.fm/api/account/create
        
        Args:
            artist: Artist name
            api_key: Last.fm API key
            
        Returns:
            List of genres or None if not found
        """
        cache_key = f"{artist.lower()}|lastfm"
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        url = "http://ws.audioscrobbler.com/2.0/"
        params = {
            'method': 'artist.getinfo',
            'artist': artist,
            'api_key': api_key,
            'format': 'json'
        }
        
        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if data.get('artist') and data['artist'].get('tags'):
                tags = data['artist']['tags'].get('tag', [])
                
                if tags:
                    # Extract tag names
                    genres = [tag['name'] for tag in tags[:5]]
                    
                    if genres:
                        self.cache[cache_key] = genres
                        self._save_cache()
                        return genres
            
            return None
            
        except Exception as e:
            print(f"Error looking up {artist} with Last.fm: {e}")
            return None
    
    def lookup(self, artist: str, provider: str = "musicbrainz", **kwargs) -> Optional[List[str]]:
        """
        Look up genres using specified provider.
        
        Args:
            artist: Artist name
            provider: One of "musicbrainz", "spotify", "lastfm"
            **kwargs: Additional arguments for specific provider
                      - Spotify: client_id, client_secret
                      - Last.fm: api_key
        
        Returns:
            List of genres or None if not found
        """
        if provider == "musicbrainz":
            return self.lookup_musicbrainz(artist)
        elif provider == "spotify":
            client_id = kwargs.get('client_id')
            client_secret = kwargs.get('client_secret')
            if not client_id or not client_secret:
                raise ValueError("Spotify provider requires 'client_id' and 'client_secret'")
            return self.lookup_spotify(artist, client_id, client_secret)
        elif provider == "lastfm":
            api_key = kwargs.get('api_key')
            if not api_key:
                raise ValueError("Last.fm provider requires 'api_key'")
            return self.lookup_lastfm(artist, api_key)
        else:
            raise ValueError(f"Unknown provider: {provider}")
    
    def batch_lookup(self, artists: List[str], provider: str = "musicbrainz", 
                    **kwargs) -> Dict[str, Optional[List[str]]]:
        """
        Look up genres for multiple artists.
        
        Args:
            artists: List of artist names
            provider: Music data provider to use
            **kwargs: Additional provider-specific arguments
        
        Returns:
            Dictionary mapping artist names to genre lists
        """
        results = {}
        total = len(artists)
        
        for idx, artist in enumerate(artists, 1):
            print(f"Looking up {idx}/{total}: {artist}...", end=" ")
            genres = self.lookup(artist, provider, **kwargs)
            results[artist] = genres
            
            if genres:
                print(f"✓ {', '.join(genres[:3])}")
            else:
                print(f"✗ Not found")
            
        return results
    
    def get_cache_stats(self) -> Dict:
        """Get statistics about the cache."""
        return {
            'total_cached': len(self.cache),
            'cached_artists': list(set(k.split('|')[0] for k in self.cache.keys()))
        }


# Convenience functions for direct usage
_default_lookup = ArtistGenreLookup()

def get_genres_from_api(artist: str, provider: str = "musicbrainz", **kwargs) -> Optional[List[str]]:
    """
    Look up genres for an artist using external API.
    
    Args:
        artist: Artist name
        provider: One of "musicbrainz" (free), "spotify", or "lastfm"
        **kwargs: Provider-specific arguments
    
    Returns:
        List of genres or None if not found
        
    Example:
        genres = get_genres_from_api("Coldplay")  # Uses free MusicBrainz
        genres = get_genres_from_api("Taylor Swift", provider="spotify", 
                                     client_id="...", client_secret="...")
    """
    return _default_lookup.lookup(artist, provider, **kwargs)


def batch_lookup_artists(artists: List[str], provider: str = "musicbrainz", 
                        **kwargs) -> Dict[str, Optional[List[str]]]:
    """
    Look up genres for multiple artists.
    
    Args:
        artists: List of artist names
        provider: Music data provider
        **kwargs: Provider-specific arguments
    
    Returns:
        Dictionary mapping artists to genre lists
        
    Example:
        artists = ["Coldplay", "Beyoncé", "Taylor Swift"]
        results = batch_lookup_artists(artists)
    """
    return _default_lookup.batch_lookup(artists, provider, **kwargs)


def update_mapping_with_new_artists(existing_mapping: Dict[str, List[str]],
                                    new_artists: List[str],
                                    provider: str = "musicbrainz",
                                    **kwargs) -> Dict[str, List[str]]:
    """
    Update an existing artist-genre mapping with new artists from API lookup.
    
    Args:
        existing_mapping: Current artist -> genres dictionary
        new_artists: List of new artist names to add
        provider: Music data provider to use
        **kwargs: Provider-specific arguments
    
    Returns:
        Updated mapping dictionary
        
    Example:
        # Load existing mapping
        with open('artist_genre_mapping.json', 'r') as f:
            mapping = json.load(f)
        
        # Add new artists
        new = ["Olivia Rodrigo", "Sabrina Carpenter"]
        updated = update_mapping_with_new_artists(mapping, new)
        
        # Save updated mapping
        with open('artist_genre_mapping.json', 'w') as f:
            json.dump(updated, f, indent=2)
    """
    # Create a copy of existing mapping
    updated_mapping = existing_mapping.copy()
    
    # Find artists not already in mapping
    artists_to_lookup = [artist for artist in new_artists if artist not in updated_mapping]
    
    if not artists_to_lookup:
        print("All artists already in mapping!")
        return updated_mapping
    
    print(f"\nLooking up {len(artists_to_lookup)} new artists...")
    print("=" * 60)
    
    # Look up new artists
    results = batch_lookup_artists(artists_to_lookup, provider, **kwargs)
    
    # Add successful lookups to mapping
    added = 0
    failed = []
    
    for artist, genres in results.items():
        if genres:
            updated_mapping[artist] = genres
            added += 1
        else:
            failed.append(artist)
    
    print("=" * 60)
    print(f"\n✓ Added {added} new artists")
    if failed:
        print(f"✗ Failed to find: {', '.join(failed)}")
    
    return updated_mapping


if __name__ == "__main__":
    """Example usage and testing."""
    
    print("Artist-Genre API Lookup - Example Usage")
    print("=" * 60)
    
    # Initialize lookup service
    lookup = ArtistGenreLookup()
    
    # Test artists
    test_artists = [
        "Coldplay",
        "Beyoncé",
        "Taylor Swift",
        "Ed Sheeran",
        "Billie Eilish",
        "The Weeknd"
    ]
    
    print("\n1. Single Lookups (using free MusicBrainz API):")
    print("-" * 60)
    
    for artist in test_artists[:3]:
        genres = lookup.lookup(artist)
        if genres:
            print(f"{artist:20} → {', '.join(genres)}")
        else:
            print(f"{artist:20} → Not found")
    
    print("\n2. Batch Lookup:")
    print("-" * 60)
    
    results = lookup.batch_lookup(test_artists)
    
    print("\n3. Cache Statistics:")
    print("-" * 60)
    stats = lookup.get_cache_stats()
    print(f"Total cached entries: {stats['total_cached']}")
    
    print("\n4. Example: Update existing mapping")
    print("-" * 60)
    print("""
# Load existing mapping
with open('artist_genre_mapping.json', 'r') as f:
    mapping = json.load(f)

# Add new artists
new_artists = ["Olivia Rodrigo", "Sabrina Carpenter", "Chappell Roan"]
updated = update_mapping_with_new_artists(mapping, new_artists)

# Save updated mapping
with open('artist_genre_mapping.json', 'w') as f:
    json.dump(updated, f, indent=2)
    """)
    
    print("\n" + "=" * 60)
    print("✓ Examples complete!")
    print("\nNote: Results are cached in 'artist_genre_cache.json'")
    print("      Delete this file to clear cache and re-query APIs")
