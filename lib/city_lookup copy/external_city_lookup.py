#!/usr/bin/env python3
"""
External API City-State Lookup
===============================
This module uses external geocoding APIs to automatically determine the state
for any US city name, even cities not in your existing database.

Supports multiple geocoding services:
1. OpenStreetMap Nominatim (Free, no API key required)
2. Google Geocoding API (Requires API key)
3. MapBox Geocoding API (Requires API key)

Usage:
    from external_city_lookup import get_state_from_api, batch_lookup_cities
    
    # Single lookup
    state = get_state_from_api("Las Vegas", provider="nominatim")
    print(state)  # "Nevada"
    
    # Batch lookup
    cities = ["Las Vegas", "New York", "Chicago"]
    results = batch_lookup_cities(cities)
"""

import requests
import time
import json
from typing import Optional, Dict, List, Tuple
from urllib.parse import quote


class CityStateLookup:
    """Lookup US states for cities using external geocoding APIs."""
    
    def __init__(self, cache_file: str = "city_state_cache.json"):
        """
        Initialize the lookup service.
        
        Args:
            cache_file: Path to JSON file for caching results
        """
        self.cache_file = cache_file
        self.cache = self._load_cache()
        
    def _load_cache(self) -> Dict[str, str]:
        """Load cached city-state mappings from file."""
        try:
            with open(self.cache_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return {}
    
    def _save_cache(self):
        """Save cache to file."""
        with open(self.cache_file, 'w') as f:
            json.dump(self.cache, f, indent=2)
    
    def lookup_nominatim(self, city: str, country: str = "United States") -> Optional[str]:
        """
        Look up state using OpenStreetMap Nominatim API (Free, no key required).
        
        Args:
            city: City name
            country: Country name (default: "United States")
            
        Returns:
            State name or None if not found
        """
        # Check cache first
        cache_key = f"{city.lower()}|{country.lower()}"
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        # Nominatim requires a User-Agent header
        headers = {
            'User-Agent': 'CityStateMapper/1.0 (Educational Purpose)'
        }
        
        url = f"https://nominatim.openstreetmap.org/search"
        params = {
            'q': f"{city}, {country}",
            'format': 'json',
            'addressdetails': 1,
            'limit': 1
        }
        
        try:
            # Nominatim requires 1 second between requests
            time.sleep(1)
            
            response = requests.get(url, params=params, headers=headers, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if data and len(data) > 0:
                address = data[0].get('address', {})
                state = address.get('state')
                
                if state:
                    # Cache the result
                    self.cache[cache_key] = state
                    self._save_cache()
                    return state
            
            return None
            
        except Exception as e:
            print(f"Error looking up {city}: {e}")
            return None
    
    def lookup_google(self, city: str, api_key: str, country: str = "US") -> Optional[str]:
        """
        Look up state using Google Geocoding API (Requires API key).
        
        Get API key: https://developers.google.com/maps/documentation/geocoding/get-api-key
        
        Args:
            city: City name
            api_key: Google Maps API key
            country: Country code (default: "US")
            
        Returns:
            State name or None if not found
        """
        cache_key = f"{city.lower()}|google|{country.lower()}"
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        url = "https://maps.googleapis.com/maps/api/geocode/json"
        params = {
            'address': f"{city}, {country}",
            'key': api_key
        }
        
        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if data['status'] == 'OK' and data['results']:
                components = data['results'][0].get('address_components', [])
                
                for component in components:
                    if 'administrative_area_level_1' in component['types']:
                        state = component['long_name']
                        self.cache[cache_key] = state
                        self._save_cache()
                        return state
            
            return None
            
        except Exception as e:
            print(f"Error looking up {city} with Google: {e}")
            return None
    
    def lookup_mapbox(self, city: str, access_token: str, country: str = "us") -> Optional[str]:
        """
        Look up state using MapBox Geocoding API (Requires access token).
        
        Get token: https://account.mapbox.com/access-tokens/
        
        Args:
            city: City name
            access_token: MapBox access token
            country: Country code (default: "us")
            
        Returns:
            State name or None if not found
        """
        cache_key = f"{city.lower()}|mapbox|{country.lower()}"
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        url = f"https://api.mapbox.com/geocoding/v5/mapbox.places/{quote(city)}.json"
        params = {
            'access_token': access_token,
            'country': country,
            'types': 'place',
            'limit': 1
        }
        
        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if data.get('features'):
                feature = data['features'][0]
                context = feature.get('context', [])
                
                for item in context:
                    if item['id'].startswith('region'):
                        state = item['text']
                        self.cache[cache_key] = state
                        self._save_cache()
                        return state
            
            return None
            
        except Exception as e:
            print(f"Error looking up {city} with MapBox: {e}")
            return None
    
    def lookup(self, city: str, provider: str = "nominatim", **kwargs) -> Optional[str]:
        """
        Look up state using specified provider.
        
        Args:
            city: City name
            provider: One of "nominatim", "google", "mapbox"
            **kwargs: Additional arguments for specific provider
                      (e.g., api_key for Google, access_token for MapBox)
        
        Returns:
            State name or None if not found
        """
        if provider == "nominatim":
            return self.lookup_nominatim(city)
        elif provider == "google":
            api_key = kwargs.get('api_key')
            if not api_key:
                raise ValueError("Google provider requires 'api_key' parameter")
            return self.lookup_google(city, api_key)
        elif provider == "mapbox":
            access_token = kwargs.get('access_token')
            if not access_token:
                raise ValueError("MapBox provider requires 'access_token' parameter")
            return self.lookup_mapbox(city, access_token)
        else:
            raise ValueError(f"Unknown provider: {provider}")
    
    def batch_lookup(self, cities: List[str], provider: str = "nominatim", 
                    **kwargs) -> Dict[str, Optional[str]]:
        """
        Look up states for multiple cities.
        
        Args:
            cities: List of city names
            provider: Geocoding provider to use
            **kwargs: Additional provider-specific arguments
        
        Returns:
            Dictionary mapping city names to states
        """
        results = {}
        total = len(cities)
        
        for idx, city in enumerate(cities, 1):
            print(f"Looking up {idx}/{total}: {city}...", end=" ")
            state = self.lookup(city, provider, **kwargs)
            results[city] = state
            print(f"{'✓' if state else '✗'} {state or 'Not found'}")
            
        return results
    
    def get_cache_stats(self) -> Dict:
        """Get statistics about the cache."""
        return {
            'total_cached': len(self.cache),
            'cached_cities': list(set(k.split('|')[0] for k in self.cache.keys()))
        }


# Convenience functions for direct usage
_default_lookup = CityStateLookup()

def get_state_from_api(city: str, provider: str = "nominatim", **kwargs) -> Optional[str]:
    """
    Look up state for a city using external API.
    
    Args:
        city: City name
        provider: One of "nominatim" (free), "google", or "mapbox"
        **kwargs: Provider-specific arguments (api_key, access_token, etc.)
    
    Returns:
        State name or None if not found
        
    Example:
        state = get_state_from_api("Las Vegas")  # Uses free Nominatim
        state = get_state_from_api("Las Vegas", provider="google", api_key="YOUR_KEY")
    """
    return _default_lookup.lookup(city, provider, **kwargs)


def batch_lookup_cities(cities: List[str], provider: str = "nominatim", 
                       **kwargs) -> Dict[str, Optional[str]]:
    """
    Look up states for multiple cities.
    
    Args:
        cities: List of city names
        provider: Geocoding provider
        **kwargs: Provider-specific arguments
    
    Returns:
        Dictionary mapping cities to states
        
    Example:
        cities = ["Las Vegas", "New York", "Chicago"]
        results = batch_lookup_cities(cities)
    """
    return _default_lookup.batch_lookup(cities, provider, **kwargs)


def update_mapping_with_new_cities(existing_mapping: Dict[str, str],
                                   new_cities: List[str],
                                   provider: str = "nominatim",
                                   **kwargs) -> Dict[str, str]:
    """
    Update an existing city-state mapping with new cities from API lookup.
    
    Args:
        existing_mapping: Current city -> state dictionary
        new_cities: List of new city names to add
        provider: Geocoding provider to use
        **kwargs: Provider-specific arguments
    
    Returns:
        Updated mapping dictionary
        
    Example:
        # Load existing mapping
        with open('city_state_mapping.json', 'r') as f:
            mapping = json.load(f)
        
        # Add new cities
        new_cities = ["Bozeman", "Missoula", "Billings"]
        updated = update_mapping_with_new_cities(mapping, new_cities)
        
        # Save updated mapping
        with open('city_state_mapping.json', 'w') as f:
            json.dump(updated, f, indent=2)
    """
    # Create a copy of existing mapping
    updated_mapping = existing_mapping.copy()
    
    # Find cities not already in mapping
    cities_to_lookup = [city for city in new_cities if city not in updated_mapping]
    
    if not cities_to_lookup:
        print("All cities already in mapping!")
        return updated_mapping
    
    print(f"\nLooking up {len(cities_to_lookup)} new cities...")
    print("=" * 60)
    
    # Look up new cities
    results = batch_lookup_cities(cities_to_lookup, provider, **kwargs)
    
    # Add successful lookups to mapping
    added = 0
    failed = []
    
    for city, state in results.items():
        if state:
            updated_mapping[city] = state
            added += 1
        else:
            failed.append(city)
    
    print("=" * 60)
    print(f"\n✓ Added {added} new cities")
    if failed:
        print(f"✗ Failed to find: {', '.join(failed)}")
    
    return updated_mapping


if __name__ == "__main__":
    """Example usage and testing."""
    
    print("City-State API Lookup - Example Usage")
    print("=" * 60)
    
    # Initialize lookup service
    lookup = CityStateLookup()
    
    # Test cities
    test_cities = [
        "Las Vegas",
        "New York",
        "Chicago",
        "Bozeman",
        "Missoula",
        "Billings"
    ]
    
    print("\n1. Single Lookups (using free Nominatim API):")
    print("-" * 60)
    
    for city in test_cities[:3]:
        state = lookup.lookup(city)
        print(f"{city:20} → {state or 'Not found'}")
    
    print("\n2. Batch Lookup:")
    print("-" * 60)
    
    results = lookup.batch_lookup(test_cities)
    
    print("\n3. Cache Statistics:")
    print("-" * 60)
    stats = lookup.get_cache_stats()
    print(f"Total cached entries: {stats['total_cached']}")
    
    print("\n4. Example: Update existing mapping")
    print("-" * 60)
    print("""
# Load existing mapping
with open('city_state_mapping.json', 'r') as f:
    mapping = json.load(f)

# Add new cities
new_cities = ["Bozeman", "Anchorage", "Honolulu"]
updated = update_mapping_with_new_cities(mapping, new_cities)

# Save updated mapping
with open('city_state_mapping.json', 'w') as f:
    json.dump(updated, f, indent=2)
    """)
    
    print("\n" + "=" * 60)
    print("✓ Examples complete!")
    print("\nNote: Results are cached in 'city_state_cache.json'")
    print("      Delete this file to clear cache and re-query APIs")
