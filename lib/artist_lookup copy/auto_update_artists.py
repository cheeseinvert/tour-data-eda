#!/usr/bin/env python3
"""
Auto-Update Artist-Genre Mapping
=================================
This script automatically detects new artists in your data and looks up their
genres using external music APIs.

Usage:
    # Process new CSV file and add genres for unknown artists
    python auto_update_artists.py new_concerts.csv
    
    # Use specific API provider
    python auto_update_artists.py new_concerts.csv --provider spotify --client-id ID --client-secret SECRET
    
    # Preview changes without saving
    python auto_update_artists.py new_concerts.csv --dry-run
"""

import sys
import argparse
import pandas as pd
import json
from pathlib import Path
from external_artist_lookup import ArtistGenreLookup, update_mapping_with_new_artists


def load_existing_mapping(mapping_file: str = "artist_genre_mapping.json") -> dict:
    """Load existing artist-genre mapping."""
    try:
        with open(mapping_file, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Warning: {mapping_file} not found. Starting with empty mapping.")
        return {}


def save_mapping(mapping: dict, output_file: str = "artist_genre_mapping.json"):
    """Save updated mapping to file."""
    with open(output_file, 'w') as f:
        json.dump(mapping, f, indent=2, sort_keys=True)
    print(f"✓ Saved updated mapping to {output_file}")


def find_unmapped_artists(df: pd.DataFrame, existing_mapping: dict, 
                         artist_col: str = "Artist") -> list:
    """
    Find artists in the DataFrame that aren't in the existing mapping.
    
    Args:
        df: DataFrame with Artist column
        existing_mapping: Current artist-genre mapping
        artist_col: Name of artist column
    
    Returns:
        List of unmapped artist names
    """
    # Get unique artists
    artists = df[artist_col].dropna().unique()
    
    # Find artists not in mapping
    unmapped = [artist for artist in artists if artist not in existing_mapping]
    
    return sorted(unmapped)


def process_csv_with_auto_lookup(csv_file: str, 
                                 mapping_file: str = "artist_genre_mapping.json",
                                 provider: str = "musicbrainz",
                                 dry_run: bool = False,
                                 **provider_kwargs) -> pd.DataFrame:
    """
    Process a CSV file and automatically look up genres for unmapped artists.
    
    Args:
        csv_file: Path to input CSV file
        mapping_file: Path to artist-genre mapping JSON file
        provider: Music API provider (musicbrainz, spotify, lastfm)
        dry_run: If True, don't save changes
        **provider_kwargs: Additional arguments for music API provider
    
    Returns:
        DataFrame with Genre column added
    """
    print("=" * 80)
    print(f"Processing: {csv_file}")
    print("=" * 80)
    
    # Load data
    print("\n1. Loading data...")
    df = pd.read_csv(csv_file)
    print(f"   Loaded {len(df)} rows")
    
    # Load existing mapping
    print("\n2. Loading existing artist-genre mapping...")
    mapping = load_existing_mapping(mapping_file)
    print(f"   Current mapping has {len(mapping)} artists")
    
    # Find unmapped artists
    print("\n3. Checking for unmapped artists...")
    unmapped_artists = find_unmapped_artists(df, mapping)
    
    if not unmapped_artists:
        print("   ✓ All artists already mapped!")
    else:
        print(f"   Found {len(unmapped_artists)} unmapped artists:")
        for artist in unmapped_artists[:10]:
            print(f"      - {artist}")
        if len(unmapped_artists) > 10:
            print(f"      ... and {len(unmapped_artists) - 10} more")
        
        # Look up new artists using API
        print(f"\n4. Looking up new artists using {provider} API...")
        print("-" * 80)
        
        lookup = ArtistGenreLookup()
        results = lookup.batch_lookup(unmapped_artists, provider, **provider_kwargs)
        
        # Update mapping
        print("\n5. Updating mapping...")
        successful = 0
        failed = []
        
        for artist, genres in results.items():
            if genres:
                mapping[artist] = genres
                successful += 1
                print(f"   ✓ {artist} → {', '.join(genres[:3])}")
            else:
                failed.append(artist)
                print(f"   ✗ {artist} → Not found")
        
        print("-" * 80)
        print(f"   Successfully mapped: {successful}")
        if failed:
            print(f"   Failed: {len(failed)} artists")
            if len(failed) <= 10:
                print(f"   Failed artists: {', '.join(failed)}")
            else:
                print(f"   Failed artists (first 10): {', '.join(failed[:10])}")
        
        # Save updated mapping
        if not dry_run and successful > 0:
            print("\n6. Saving updated mapping...")
            save_mapping(mapping, mapping_file)
        elif dry_run:
            print("\n6. DRY RUN - Not saving changes")
            print(f"   Would have added {successful} new artists to mapping")
    
    # Apply mapping to DataFrame
    print("\n7. Applying genre mapping to DataFrame...")
    
    def get_genres(row):
        artist = row.get('Artist')
        genres = mapping.get(artist)
        if genres:
            # Return primary genre (first one) or all genres joined
            return genres[0] if len(genres) == 1 else ', '.join(genres[:3])
        return None
    
    df['Genre'] = df.apply(get_genres, axis=1)
    df['All_Genres'] = df['Artist'].map(lambda a: mapping.get(a))
    
    mapped_count = df['Genre'].notna().sum()
    unmapped_count = df['Genre'].isna().sum()
    
    print(f"   Artists with genres: {mapped_count}")
    print(f"   Artists without genres: {unmapped_count}")
    
    if unmapped_count > 0:
        print("\n   Unmapped artists:")
        unmapped_artists_list = df[df['Genre'].isna()]['Artist'].unique()
        for artist in unmapped_artists_list[:5]:
            print(f"      - {artist}")
        if len(unmapped_artists_list) > 5:
            print(f"      ... and {len(unmapped_artists_list) - 5} more")
    
    return df


def main():
    parser = argparse.ArgumentParser(
        description="Automatically update artist-genre mapping for new artists in concert data"
    )
    parser.add_argument(
        "csv_file",
        help="Path to CSV file with concert data"
    )
    parser.add_argument(
        "--mapping-file",
        default="artist_genre_mapping.json",
        help="Path to artist-genre mapping JSON file (default: artist_genre_mapping.json)"
    )
    parser.add_argument(
        "--output",
        help="Path to save updated CSV file (default: <input>_with_genres.csv)"
    )
    parser.add_argument(
        "--provider",
        choices=["musicbrainz", "spotify", "lastfm"],
        default="musicbrainz",
        help="Music API provider (default: musicbrainz - free, no key required)"
    )
    parser.add_argument(
        "--client-id",
        help="Spotify client ID"
    )
    parser.add_argument(
        "--client-secret",
        help="Spotify client secret"
    )
    parser.add_argument(
        "--api-key",
        help="Last.fm API key"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview changes without saving"
    )
    
    args = parser.parse_args()
    
    # Prepare provider kwargs
    provider_kwargs = {}
    if args.provider == "spotify":
        if not args.client_id or not args.client_secret:
            print("Error: Spotify provider requires --client-id and --client-secret")
            sys.exit(1)
        provider_kwargs['client_id'] = args.client_id
        provider_kwargs['client_secret'] = args.client_secret
    elif args.provider == "lastfm":
        if not args.api_key:
            print("Error: Last.fm provider requires --api-key")
            sys.exit(1)
        provider_kwargs['api_key'] = args.api_key
    
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
            output_file = args.output or args.csv_file.replace('.csv', '_with_genres.csv')
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
