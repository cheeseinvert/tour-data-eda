# External API Lookup Systems - Quick Comparison

## 📍 City → State Lookup vs 🎵 Artist → Genre Lookup

You now have **TWO powerful external API lookup systems** for automatically enriching your concert data!

---

## System Comparison

| Feature | City-State Lookup | Artist-Genre Lookup |
|---------|-------------------|---------------------|
| **Data Points** | 373 cities → 50 states | 879 artists → genres |
| **Primary Use** | Geographic mapping | Music categorization |
| **Free Option** | ✅ OpenStreetMap (Nominatim) | ✅ MusicBrainz |
| **Best Paid Option** | Google Geocoding | Spotify Web API (FREE!) |
| **Setup Time** | 0 min (Nominatim) | 2 min (Spotify) |
| **Speed (free)** | 1 req/sec | 1 req/sec |
| **Speed (paid)** | Very fast | Very fast |

---

## 🚀 Quick Commands

### City-State Lookup

```bash
# Process new cities (FREE, no setup)
python auto_update_mapping.py new_concerts.csv

# With Google API (faster)
python auto_update_mapping.py new_concerts.csv \
  --provider google --api-key YOUR_KEY
```

### Artist-Genre Lookup

```bash
# Process new artists (FREE, no setup)
python auto_update_artists.py new_concerts.csv

# With Spotify API (BEST, free but needs 2min setup)
python auto_update_artists.py new_concerts.csv \
  --provider spotify \
  --client-id YOUR_ID \
  --client-secret YOUR_SECRET
```

---

## 📊 Your Current Dataset

| Metric | Value |
|--------|-------|
| **Total Events** | 7,776 concerts |
| **Unique Cities** | 393 US cities |
| **Unique Artists** | 879 artists |
| **Cities Mapped** | 373 (94.9%) |
| **Artists Needing Genres** | 879 (100%) |

---

## 🎯 Recommended Workflow

### For New Concert Data

```bash
#!/bin/bash
# process_new_concerts.sh

# 1. Process cities (add State column)
python auto_update_mapping.py march_2025.csv

# 2. Process artists (add Genre column)  
python auto_update_artists.py march_2025_with_states.csv \
  --provider spotify \
  --client-id $SPOTIFY_ID \
  --client-secret $SPOTIFY_SECRET

# 3. Final output: march_2025_with_states_with_genres.csv
# Now has: City, State, Artist, Genre, and all original columns!
```

---

## 💡 Integration Example

```python
import pandas as pd
from external_city_lookup import get_state_from_api
from external_artist_lookup import get_genres_from_api

# Load your concert data
df = pd.read_csv('concerts.csv')

# Add State for US cities
def add_state(row):
    if row['Country'] == 'United States':
        return get_state_from_api(row['City'])
    return None

df['State'] = df.apply(add_state, axis=1)

# Add Genre for artists
df['Genre'] = df['Artist'].apply(
    lambda a: get_genres_from_api(a, provider="spotify",
                                   client_id="ID", 
                                   client_secret="SECRET")
)

# Save enriched data
df.to_csv('concerts_enriched.csv', index=False)
```

---

## 🔑 API Setup Guide

### OpenStreetMap Nominatim (Cities - FREE)
- ✅ No setup required!
- ✅ Just run the script

### MusicBrainz (Artists - FREE)
- ✅ No setup required!
- ✅ Just run the script

### Google Geocoding (Cities - PAID)
1. Go to: https://console.cloud.google.com/apis/credentials
2. Create API key
3. Enable Geocoding API
4. Enable billing (get $200 free/month)

### Spotify Web API (Artists - FREE!)
1. Go to: https://developer.spotify.com/dashboard
2. Click "Create app"
3. Name: "Genre Lookup"
4. Copy Client ID and Secret
5. **Total time: 2 minutes**

### Last.fm (Artists - FREE)
1. Go to: https://www.last.fm/api/account/create
2. Fill in form
3. Copy API key

---

## 📦 File Organization

```
Your Project/
├── Data Files
│   ├── us_concerts_with_states.csv          # Original with states
│   ├── us_concerts_with_states_with_genres.csv  # Fully enriched
│   └── new_monthly_data.csv                 # New data to process
│
├── Mapping Files
│   ├── city_state_mapping.json              # 373 cities
│   ├── city_state_cache.json                # City API cache
│   ├── artist_genre_mapping.json            # 879 artists
│   └── artist_genre_cache.json              # Artist API cache
│
├── Python Modules
│   ├── external_city_lookup.py              # City-state API module
│   ├── external_artist_lookup.py            # Artist-genre API module
│   ├── city_state_mapping.py                # Local city lookup
│   └── auto_update_mapping.py               # City automation
│   └── auto_update_artists.py               # Artist automation
│
└── Documentation
    ├── EXTERNAL_API_GUIDE.md                # City-state docs
    ├── ARTIST_GENRE_GUIDE.md                # Artist-genre docs
    └── API_COMPARISON.md                    # This file
```

---

## 💰 Cost Analysis

### Processing Your Full Dataset (One Time)

| Task | Provider | Records | Time | Cost |
|------|----------|---------|------|------|
| **Map cities** | Nominatim | 393 cities | ~7 min | $0 |
| **Map cities** | Google | 393 cities | ~10 sec | ~$0* |
| **Map artists** | MusicBrainz | 879 artists | ~15 min | $0 |
| **Map artists** | Spotify | 879 artists | ~2 min | $0 |

*Within free tier

### Monthly Updates (Assuming 50 new cities, 100 new artists)

| Task | Provider | Time/Month | Cost/Month |
|------|----------|------------|------------|
| **New cities** | Nominatim | ~1 min | $0 |
| **New cities** | Google | ~2 sec | $0* |
| **New artists** | MusicBrainz | ~2 min | $0 |
| **New artists** | Spotify | ~10 sec | $0 |

*Within free tier

**Total monthly cost: $0** (using free tiers)

---

## 🎓 Learning Path

### Beginner (5 minutes)
```bash
# 1. Try city lookup (no setup needed)
python auto_update_mapping.py sample_data.csv

# 2. Try artist lookup (no setup needed)
python auto_update_artists.py sample_data.csv
```

### Intermediate (15 minutes)
```bash
# 1. Set up Spotify credentials (2 min)
# 2. Process your full dataset with both systems
python auto_update_mapping.py us_concerts.csv
python auto_update_artists.py us_concerts_with_states.csv \
  --provider spotify --client-id ID --client-secret SECRET
```

### Advanced (Production)
```python
# Build a complete data enrichment pipeline
# See integration examples in documentation
```

---

## 🔥 Power User Tips

### 1. Chain Both Systems

```bash
# Process cities then artists in one command
python auto_update_mapping.py data.csv && \
python auto_update_artists.py data_with_states.csv \
  --provider spotify --client-id ID --client-secret SECRET
```

### 2. Use with Cron for Auto-Updates

```bash
# Add to crontab for weekly updates
0 3 * * 1 /path/to/process_weekly_data.sh
```

### 3. Combine with Your Analysis

```python
import pandas as pd

# Load fully enriched data
df = pd.read_csv('concerts_with_states_with_genres.csv')

# Now you can analyze by both geography AND genre!
# Revenue by state and genre
pivot = df.pivot_table(
    values='Revenue (USD)',
    index='State',
    columns='Genre',
    aggfunc='sum'
)

# Top genre in each state
top_genres_by_state = df.groupby('State')['Genre'].agg(
    lambda x: x.value_counts().index[0]
)
```

---

## 📊 Use Cases

### City-State Lookup Best For:
- ✅ Regional analysis
- ✅ State-level reporting
- ✅ Geographic market segmentation
- ✅ Tour routing optimization
- ✅ Regulatory compliance (state laws)

### Artist-Genre Lookup Best For:
- ✅ Genre trend analysis
- ✅ Content categorization
- ✅ Artist recommendations
- ✅ Festival lineup planning
- ✅ Marketing segmentation

### Combined Power:
- 🚀 **"What genres perform best in California vs Texas?"**
- 🚀 **"Rock concert capacity utilization by state"**
- 🚀 **"Average ticket price for pop shows in major metros"**
- 🚀 **"Genre diversity index by region"**

---

## 🎯 Quick Decision Guide

**Need to add states to cities?**
→ Use `auto_update_mapping.py`

**Need to add genres to artists?**
→ Use `auto_update_artists.py`

**Processing large dataset (500+ records)?**
→ Use Spotify for artists (faster)
→ Use Nominatim for cities (free is fine)

**Need production-grade accuracy?**
→ Use Google for cities
→ Use Spotify for artists

**Want completely free?**
→ Use Nominatim for cities
→ Use MusicBrainz for artists

**In a hurry?**
→ Use paid APIs (Google + Spotify)
→ Processes 1000s of records in minutes

---

## 📞 Support

**City-State Issues:**
- See: `EXTERNAL_API_GUIDE.md`
- Module: `external_city_lookup.py`

**Artist-Genre Issues:**
- See: `ARTIST_GENRE_GUIDE.md`
- Module: `external_artist_lookup.py`

**General Questions:**
- See: `INDEX.md`
- Check: `CHEAT_SHEET.txt`

---

## 🎉 Summary

You have complete systems for automatically enriching your concert data with:

✅ **Geographic context** (City → State)  
✅ **Music categorization** (Artist → Genre)  
✅ **Multiple API options** (free and premium)  
✅ **Automatic caching** (fast repeat lookups)  
✅ **Production-ready** (error handling, logging)  
✅ **Well-documented** (guides and examples)  

**Start enriching your data NOW:**

```bash
# Enrich cities
python auto_update_mapping.py your_data.csv

# Enrich artists  
python auto_update_artists.py your_data_with_states.csv \
  --provider spotify --client-id ID --client-secret SECRET
```

**Total setup time: ~5 minutes**  
**Total cost: $0 (with free tiers)**  
**Result: Fully enriched concert dataset!** 🎵

---

**Built for 393 cities and 879 artists in your concert dataset!**
