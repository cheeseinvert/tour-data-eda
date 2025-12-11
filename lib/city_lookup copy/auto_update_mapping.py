#!/usr/bin/env python3
"""
Auto-Update City-State Mapping
===============================
This script automatically detects new cities in your data and looks them up
using external geocoding APIs.

Usage:
    # Process new CSV file and add states for unknown cities
    python auto_update_mapping.py new_concerts.csv
    
    # Use specific API provider
    python auto_update_mapping.py new_concerts.csv --provider google --api-key YOUR_KEY
    
    # Preview changes without saving
    python auto_update_mapping.py new_concerts.csv --dry-run
"""

import sys
import argparse
import pandas as pd
import json
from pathlib import Path
from external_city_lookup import CityStateLookup, update_mapping_with_new_cities


def load_existing_mapping(mapping_file: str = "city_state_mapping.json") -> dict:
    """Load existing city-state mapping."""
    try:
        with open(mapping_file, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Warning: {mapping_file} not found. Starting with empty mapping.")
        return {}


def save_mapping(mapping: dict, output_file: str = "city_state_mapping.json"):
    """Save updated mapping to file."""
    with open(output_file, 'w') as f:
        json.dump(mapping, f, indent=2, sort_keys=True)
    print(f"✓ Saved updated mapping to {output_file}")


def find_unmapped_cities(df: pd.DataFrame, existing_mapping: dict, 
                        country_col: str = "Country") -> list:
    """
    Find US cities in the DataFrame that aren't in the existing mapping.
    
    Args:
        df: DataFrame with City and Country columns
        existing_mapping: Current city-state mapping
        country_col: Name of country column
    
    Returns:
        List of unmapped US city names
    """
    # Filter for US cities
    us_cities = df[df[country_col] == "United States"]["City"].dropna().unique()
    
    # Find cities not in mapping
    unmapped = [city for city in us_cities if city not in existing_mapping]
    
    return sorted(unmapped)


def process_csv_with_auto_lookup(csv_file: str, 
                                 mapping_file: str = "city_state_mapping.json",
                                 provider: str = "nominatim",
                                 dry_run: bool = False,
                                 **provider_kwargs) -> pd.DataFrame:
    """
    Process a CSV file and automatically look up states for unmapped cities.
    
    Args:
        csv_file: Path to input CSV file
        mapping_file: Path to city-state mapping JSON file
        provider: Geocoding provider (nominatim, google, mapbox)
        dry_run: If True, don't save changes
        **provider_kwargs: Additional arguments for geocoding provider
    
    Returns:
        DataFrame with State column added
    """
    print("=" * 80)
    print(f"Processing: {csv_file}")
    print("=" * 80)
    
    # Load data
    print("\n1. Loading data...")
    df = pd.read_csv(csv_file)
    print(f"   Loaded {len(df)} rows")
    
    # Load existing mapping
    print("\n2. Loading existing city-state mapping...")
    mapping = load_existing_mapping(mapping_file)
    print(f"   Current mapping has {len(mapping)} cities")
    
    # Find unmapped US cities
    print("\n3. Checking for unmapped US cities...")
    unmapped_cities = find_unmapped_cities(df, mapping)
    
    if not unmapped_cities:
        print("   ✓ All US cities already mapped!")
    else:
        print(f"   Found {len(unmapped_cities)} unmapped cities:")
        for city in unmapped_cities[:10]:
            print(f"      - {city}")
        if len(unmapped_cities) > 10:
            print(f"      ... and {len(unmapped_cities) - 10} more")
        
        # Look up new cities using API
        print(f"\n4. Looking up new cities using {provider} API...")
        print("-" * 80)
        
        lookup = CityStateLookup()
        results = lookup.batch_lookup(unmapped_cities, provider, **provider_kwargs)
        
        # Update mapping
        print("\n5. Updating mapping...")
        successful = 0
        failed = []
        
        for city, state in results.items():
            if state:
                mapping[city] = state
                successful += 1
                print(f"   ✓ {city} → {state}")
            else:
                failed.append(city)
                print(f"   ✗ {city} → Not found")
        
        print("-" * 80)
        print(f"   Successfully mapped: {successful}")
        if failed:
            print(f"   Failed: {len(failed)} cities")
            print(f"   Failed cities: {', '.join(failed)}")
        
        # Save updated mapping
        if not dry_run and successful > 0:
            print("\n6. Saving updated mapping...")
            save_mapping(mapping, mapping_file)
        elif dry_run:
            print("\n6. DRY RUN - Not saving changes")
            print(f"   Would have added {successful} new cities to mapping")
    
    # Apply mapping to DataFrame
    print("\n7. Applying state mapping to DataFrame...")
    
    def get_state(row):
        if row.get('Country') == 'United States':
            return mapping.get(row.get('City'))
        return None
    
    df['State'] = df.apply(get_state, axis=1)
    
    us_rows = df[df['Country'] == 'United States']
    mapped_count = us_rows['State'].notna().sum()
    unmapped_count = us_rows['State'].isna().sum()
    
    print(f"   US cities with states: {mapped_count}")
    print(f"   US cities without states: {unmapped_count}")
    
    if unmapped_count > 0:
        print("\n   Unmapped cities:")
        unmapped_cities_list = us_rows[us_rows['State'].isna()]['City'].unique()
        for city in unmapped_cities_list[:5]:
            print(f"      - {city}")
        if len(unmapped_cities_list) > 5:
            print(f"      ... and {len(unmapped_cities_list) - 5} more")
    
    return df


def main():
    parser = argparse.ArgumentParser(
        description="Automatically update city-state mapping for new cities in concert data"
    )
    parser.add_argument(
        "csv_file",
        help="Path to CSV file with concert data"
    )
    parser.add_argument(
        "--mapping-file",
        default="city_state_mapping.json",
        help="Path to city-state mapping JSON file (default: city_state_mapping.json)"
    )
    parser.add_argument(
        "--output",
        help="Path to save updated CSV file (default: <input>_with_states.csv)"
    )
    parser.add_argument(
        "--provider",
        choices=["nominatim", "google", "mapbox"],
        default="nominatim",
        help="Geocoding API provider (default: nominatim - free, no key required)"
    )
    parser.add_argument(
        "--api-key",
        help="API key for Google Geocoding API"
    )
    parser.add_argument(
        "--access-token",
        help="Access token for MapBox API"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview changes without saving"
    )
    
    args = parser.parse_args()
    
    # Prepare provider kwargs
    provider_kwargs = {}
    if args.provider == "google":
        if not args.api_key:
            print("Error: Google provider requires --api-key")
            sys.exit(1)
        provider_kwargs['api_key'] = args.api_key
    elif args.provider == "mapbox":
        if not args.access_token:
            print("Error: MapBox provider requires --access-token")
            sys.exit(1)
        provider_kwargs['access_token'] = args.access_token
    
    # Process CSV
    try:
        df = process_csv_with_auto_lookup(
            args.csv_file,
            args.mapping_file,
            args.provider,
            args.dry_run,
            **provider_kwargs
        )
        
        # Save updated CSV
        if not args.dry_run:
            output_file = args.output or args.csv_file.replace('.csv', '_with_states.csv')
            df.to_csv(output_file, index=False)
            print(f"\n✓ Saved updated data to: {output_file}")
        
        print("\n" + "=" * 80)
        print("✓ COMPLETE!")
        print("=" * 80)
        
        if args.dry_run:
            print("\nThis was a dry run. Run without --dry-run to save changes.")
        
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
