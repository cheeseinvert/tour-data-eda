# External API City-State Lookup - Complete Guide

## Overview

This system automatically looks up US states for any city name using external geocoding APIs. When you encounter new cities in your data that aren't in your existing mapping, the system can automatically query geocoding services to determine their states.

## 🎯 Use Cases

1. **New Cities in Data** - Automatically map states for cities you haven't seen before
2. **Data Validation** - Verify existing mappings against authoritative sources
3. **Expanding Coverage** - Continuously grow your city database as new venues appear
4. **Zero Manual Entry** - No need to manually research and enter state information

## 🔑 Available API Providers

### 1. OpenStreetMap Nominatim (Recommended for Most Users)

**Pros:**
- ✅ **Completely FREE**
- ✅ **No API key required**
- ✅ **No signup needed**
- ✅ **Good coverage**

**Cons:**
- ⏱️ Rate limited to 1 request per second
- 🌍 Best for batch processing, not real-time lookups

**When to use:** Perfect for one-time updates or batch processing of new cities

---

### 2. Google Geocoding API

**Pros:**
- ✅ **Highly accurate**
- ✅ **Fast and reliable**
- ✅ **Excellent coverage**

**Cons:**
- 💰 **Requires billing account** ($5/1000 requests, but $200 free monthly credit)
- 🔑 **Requires API key**

**When to use:** When you need high accuracy or have many cities to process

**Get API Key:** https://developers.google.com/maps/documentation/geocoding/get-api-key

---

### 3. MapBox Geocoding API

**Pros:**
- ✅ **Good accuracy**
- ✅ **Modern API**
- ✅ **100,000 free requests/month**

**Cons:**
- 🔑 **Requires access token**

**When to use:** Good middle ground between free and premium

**Get Access Token:** https://account.mapbox.com/access-tokens/

---

## 📦 Installation

```bash
# Install required package
pip install requests
```

That's it! No other dependencies needed.

---

## 🚀 Quick Start

### Method 1: Automatic Processing (Easiest)

Process a new CSV file and automatically look up any unknown cities:

```bash
# Using free Nominatim API (no key required)
python auto_update_mapping.py new_concerts.csv

# Using Google API (requires key)
python auto_update_mapping.py new_concerts.csv --provider google --api-key YOUR_KEY

# Preview changes without saving
python auto_update_mapping.py new_concerts.csv --dry-run
```

**What it does:**
1. ✅ Loads your existing city-state mapping
2. ✅ Finds US cities in your new data that aren't mapped yet
3. ✅ Automatically looks them up using the geocoding API
4. ✅ Updates your mapping file
5. ✅ Adds State column to your CSV
6. ✅ Saves everything

---

### Method 2: Python Code Integration

```python
from external_city_lookup import get_state_from_api, batch_lookup_cities

# Single city lookup
state = get_state_from_api("Bozeman")
print(state)  # "Montana"

# Batch lookup multiple cities
cities = ["Bozeman", "Missoula", "Billings"]
results = batch_lookup_cities(cities)
# {'Bozeman': 'Montana', 'Missoula': 'Montana', 'Billings': 'Montana'}
```

---

### Method 3: Update Existing Mapping

```python
import json
from external_city_lookup import update_mapping_with_new_cities

# Load your existing mapping
with open('city_state_mapping.json', 'r') as f:
    mapping = json.load(f)

# Add new cities
new_cities = ["Bozeman", "Anchorage", "Honolulu", "Cheyenne"]
updated = update_mapping_with_new_cities(mapping, new_cities)

# Save updated mapping
with open('city_state_mapping.json', 'w') as f:
    json.dump(updated, f, indent=2)
```

---

## 💻 Detailed Usage Examples

### Example 1: Process New Concert Data

You receive a new CSV file `march_2025_concerts.csv` with some cities you've never seen before:

```bash
# Automatic processing with free API
python auto_update_mapping.py march_2025_concerts.csv
```

**Output:**
```
================================================================================
Processing: march_2025_concerts.csv
================================================================================

1. Loading data...
   Loaded 150 rows

2. Loading existing city-state mapping...
   Current mapping has 373 cities

3. Checking for unmapped US cities...
   Found 5 unmapped cities:
      - Bozeman
      - Missoula
      - Cheyenne
      - Anchorage
      - Honolulu

4. Looking up new cities using nominatim API...
--------------------------------------------------------------------------------
Looking up 1/5: Bozeman... ✓ Montana
Looking up 2/5: Missoula... ✓ Montana
Looking up 3/5: Cheyenne... ✓ Wyoming
Looking up 4/5: Anchorage... ✓ Alaska
Looking up 5/5: Honolulu... ✓ Hawaii
--------------------------------------------------------------------------------
   Successfully mapped: 5
   Failed: 0 cities

6. Saving updated mapping...
✓ Saved updated mapping to city_state_mapping.json

7. Applying state mapping to DataFrame...
   US cities with states: 148
   US cities without states: 0

✓ Saved updated data to: march_2025_concerts_with_states.csv

================================================================================
✓ COMPLETE!
================================================================================
```

---

### Example 2: Using Google API for Higher Accuracy

```bash
python auto_update_mapping.py new_data.csv \
  --provider google \
  --api-key AIzaSyD... \
  --output concerts_with_states.csv
```

---

### Example 3: Preview Before Saving

```bash
# See what would change without saving anything
python auto_update_mapping.py new_data.csv --dry-run
```

---

### Example 4: Python Integration in Your Data Pipeline

```python
import pandas as pd
from external_city_lookup import CityStateLookup

# Your data processing pipeline
df = pd.read_csv('concerts.csv')

# Initialize lookup service (with caching)
lookup = CityStateLookup()

# Add states for any unmapped US cities
def add_state(row):
    if row['Country'] == 'United States' and pd.isna(row.get('State')):
        return lookup.lookup(row['City'])
    return row.get('State')

df['State'] = df.apply(add_state, axis=1)
df.to_csv('concerts_with_states.csv', index=False)
```

---

### Example 5: Verify Existing Mappings

```python
"""Double-check existing mappings against an external API"""
from external_city_lookup import CityStateLookup
import json

# Load existing mapping
with open('city_state_mapping.json', 'r') as f:
    mapping = json.load(f)

# Initialize lookup with Google for accuracy
lookup = CityStateLookup()

# Check a sample of cities
sample_cities = list(mapping.keys())[:10]
print("Verifying sample mappings:")

for city in sample_cities:
    our_state = mapping[city]
    api_state = lookup.lookup(city, provider="nominatim")
    
    match = "✓" if our_state == api_state else "✗"
    print(f"{match} {city}: {our_state} vs {api_state}")
```

---

## 🎓 Advanced Features

### Caching System

The system automatically caches all API results to avoid redundant lookups:

```python
from external_city_lookup import CityStateLookup

lookup = CityStateLookup(cache_file="my_cache.json")

# First lookup hits the API
state1 = lookup.lookup("Las Vegas")  # API call made

# Second lookup uses cache (instant, no API call)
state2 = lookup.lookup("Las Vegas")  # From cache

# Check cache statistics
stats = lookup.get_cache_stats()
print(f"Cached cities: {stats['total_cached']}")
```

**Benefits:**
- ⚡ Instant lookups for previously queried cities
- 💰 Saves API quota/costs
- 🌐 Works offline for cached cities

---

### Using Multiple Providers

```python
from external_city_lookup import CityStateLookup

lookup = CityStateLookup()

# Try free API first
state = lookup.lookup("Obscure City", provider="nominatim")

# If that fails, try Google
if not state:
    state = lookup.lookup("Obscure City", 
                         provider="google", 
                         api_key="YOUR_KEY")

print(state)
```

---

### Custom Provider Selection

```python
def smart_lookup(city, google_key=None):
    """
    Use free API for common cities, paid API for uncommon ones.
    """
    lookup = CityStateLookup()
    
    # Try free API first
    state = lookup.lookup(city, provider="nominatim")
    
    # If not found and we have a Google key, try that
    if not state and google_key:
        print(f"  Trying Google API for {city}...")
        state = lookup.lookup(city, provider="google", api_key=google_key)
    
    return state
```

---

## 📊 Rate Limits & Costs

| Provider | Free Tier | Rate Limit | Cost After Free |
|----------|-----------|------------|-----------------|
| **Nominatim** | Unlimited | 1 req/sec | Always free |
| **Google** | $200/month credit | ~50 req/sec | $5/1000 requests |
| **MapBox** | 100,000 req/month | 600 req/min | $0.50/1000 requests |

### Cost Examples

**Scenario:** You have 100 new cities to map

| Provider | Cost | Time |
|----------|------|------|
| Nominatim | $0 | ~100 seconds |
| Google | ~$0 (within free tier) | ~2 seconds |
| MapBox | $0 (within free tier) | ~10 seconds |

---

## 🔧 Configuration

### Setting Provider Defaults

```python
# In your code
import os
os.environ['DEFAULT_GEO_PROVIDER'] = 'google'
os.environ['GOOGLE_GEOCODING_KEY'] = 'your-key-here'
```

### Custom Cache Location

```python
from external_city_lookup import CityStateLookup

# Use custom cache file
lookup = CityStateLookup(cache_file="/path/to/my_cache.json")
```

---

## 🐛 Troubleshooting

### Problem: "Rate limit exceeded"

**Solution for Nominatim:**
```python
# Add longer delay between requests
import time

for city in cities:
    state = lookup.lookup(city)
    time.sleep(2)  # Wait 2 seconds instead of 1
```

**Solution for Google/MapBox:**
- Upgrade to paid tier
- Batch process overnight

---

### Problem: "API key invalid"

**For Google:**
1. Verify key at https://console.cloud.google.com/apis/credentials
2. Enable Geocoding API for your project
3. Check billing is enabled

**For MapBox:**
1. Verify token at https://account.mapbox.com/access-tokens/
2. Check token scope includes geocoding

---

### Problem: Cities not found

Some cities may not be found because:
- Spelling variation (e.g., "St. Louis" vs "Saint Louis")
- Very small/new cities
- Non-standard names

**Solution:**
```python
# Try multiple variations
variations = [
    "Saint Louis",
    "St. Louis",
    "St Louis"
]

for variant in variations:
    state = lookup.lookup(variant)
    if state:
        print(f"Found with: {variant} → {state}")
        break
```

---

## 📝 Best Practices

### 1. Use Nominatim for Batch Processing

```bash
# Perfect for nightly/weekly updates
python auto_update_mapping.py weekly_data.csv
```

### 2. Cache Everything

The caching system is automatic, but you can:
```python
# Keep cache file in version control
lookup = CityStateLookup(cache_file="data/city_cache.json")

# Or backup regularly
import shutil
shutil.copy("city_state_cache.json", "backups/cache_backup.json")
```

### 3. Validate Results

```python
# Always check if lookup succeeded
state = lookup.lookup(city)
if state:
    print(f"✓ {city} → {state}")
else:
    print(f"✗ {city} not found - requires manual review")
```

### 4. Handle Errors Gracefully

```python
try:
    state = lookup.lookup(city, provider="google", api_key=key)
except Exception as e:
    print(f"API error for {city}: {e}")
    # Fall back to existing mapping or manual entry
    state = manual_mappings.get(city)
```

---

## 🔄 Integration with Existing Workflow

### Current Workflow (Manual)
```
1. Receive new data
2. Find unknown cities
3. Google each city manually
4. Update mapping file
5. Re-run data processing
```

### New Workflow (Automated)
```bash
# One command does everything
python auto_update_mapping.py new_data.csv
```

---

## 📈 Performance

### Speed Comparison (100 cities)

| Method | Time | Cost |
|--------|------|------|
| Manual lookup | ~30 minutes | Your time |
| Nominatim API | ~100 seconds | $0 |
| Google API | ~2 seconds | ~$0 (free tier) |
| Cached | <1 second | $0 |

---

## 🎯 Real-World Example

You're a concert data analyst and receive monthly updates:

```bash
#!/bin/bash
# monthly_update.sh

# 1. Download new data
wget https://api.concerts.com/monthly/2025-03.csv

# 2. Automatically add states for any new cities
python auto_update_mapping.py 2025-03.csv

# 3. Generate reports
python generate_reports.py 2025-03_with_states.csv

# Done! No manual intervention needed.
```

---

## 📚 API Reference

### `get_state_from_api(city, provider="nominatim", **kwargs)`

Look up a single city.

**Parameters:**
- `city` (str): City name
- `provider` (str): "nominatim", "google", or "mapbox"
- `**kwargs`: Provider-specific args (api_key, access_token)

**Returns:** State name (str) or None

---

### `batch_lookup_cities(cities, provider="nominatim", **kwargs)`

Look up multiple cities.

**Parameters:**
- `cities` (list): List of city names
- `provider` (str): API provider
- `**kwargs`: Provider-specific args

**Returns:** Dict mapping cities to states

---

### `update_mapping_with_new_cities(existing_mapping, new_cities, provider="nominatim", **kwargs)`

Update an existing mapping with new cities.

**Parameters:**
- `existing_mapping` (dict): Current city→state mapping
- `new_cities` (list): Cities to add
- `provider` (str): API provider
- `**kwargs`: Provider-specific args

**Returns:** Updated mapping dict

---

## 🎓 Summary

**What you get:**
- ✅ Automatic state lookup for any US city
- ✅ Three API options (free to premium)
- ✅ Built-in caching system
- ✅ Command-line tool for batch processing
- ✅ Python library for custom integration
- ✅ Zero manual data entry

**Next steps:**
1. Try the free Nominatim API first
2. Process your data: `python auto_update_mapping.py your_data.csv`
3. Upgrade to paid API if you need speed/volume

**That's it!** You now have a fully automated system for handling new cities. 🎉
