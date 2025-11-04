# Spotify Data Collection Scripts

This directory contains the complete pipeline for collecting, enriching, and merging real Spotify listening data from team members.

---

## Scripts Overview

### 1. `spotify_auth.py`
**Purpose**: OAuth authentication for Spotify API

**Key Features**:
- Multi-user authentication support
- Automatic token refresh
- Secure token caching per user
- Browser-based OAuth flow

**Usage**:
```bash
# Authenticate single user
python spotify_auth.py --user nicolo

# Authenticate all team members
python spotify_auth.py --user all

# Force re-authentication
python spotify_auth.py --user nicolo --force-refresh
```

**Classes**:
- `SpotifyAuthenticator`: Single-user authentication
- `TeamAuthenticator`: Multi-user authentication manager

**Required Scopes**:
- `user-read-recently-played`
- `user-top-read`
- `playlist-read-private`
- `user-read-private`
- `user-library-read`

---

### 2. `collect_spotify_data.py`
**Purpose**: Fetch listening data from Spotify API

**What It Collects**:
- Recently played tracks (last 50)
- Top tracks (3 time ranges)
- Top artists (3 time ranges)
- User playlists (metadata)

**Usage**:
```bash
# Full collection for all team members
python collect_spotify_data.py --user all

# Full collection for single user
python collect_spotify_data.py --user nicolo

# Recently played only (faster, for weekly updates)
python collect_spotify_data.py --user all --recently-played-only

# Custom output directory
python collect_spotify_data.py --user all --output-dir data/custom
```

**Classes**:
- `SpotifyDataCollector`: Single-user data collector
- `TeamDataCollector`: Multi-user collection manager

**Output Files** (per user):
- `{user}_recently_played.json`: Recent plays with timestamps
- `{user}_top_tracks_all.json`: Top tracks across time ranges
- `{user}_top_artists_all.json`: Top artists across time ranges
- `{user}_playlists.json`: Playlist metadata
- `{user}_collection_stats.json`: Collection statistics

**Typical Runtime**: 1-2 minutes per user (full collection)

---

### 3. `enrich_with_audio_features.py`
**Purpose**: Add audio features and derive composite metrics

**What It Adds**:
- **Spotify API audio features**: danceability, energy, valence, tempo, acousticness, speechiness, instrumentalness, liveness, loudness, key, mode, time_signature
- **Kaggle database fallback**: For tracks missing API features
- **Composite scores**: mood_score, grooviness, focus_score, relaxation_score
- **Temporal features**: hour, day_of_week, is_weekend, time_period
- **Context inference**: workout, focus, relaxation, party, commute, sleep, general

**Usage**:
```bash
# Enrich all team members
python enrich_with_audio_features.py --user all

# Enrich single user
python enrich_with_audio_features.py --user nicolo

# Use custom Kaggle database
python enrich_with_audio_features.py --user all --kaggle-db data/custom_tracks.csv
```

**Classes**:
- `AudioFeaturesEnricher`: Fetches and merges audio features

**API Rate Limiting**:
- Batches: 100 tracks per request
- Delay: 0.5s between batches
- Handles 429 errors with exponential backoff

**Output Files** (per user):
- `{user}_listening_history.csv`: Enriched listening history
- `{user}_enrichment_stats.json`: Enrichment statistics

**Typical Runtime**: 2-5 minutes per user

---

### 4. `merge_team_data.py`
**Purpose**: Combine all team members into unified dataset

**What It Does**:
- Loads processed data from all members
- Adds user_id mapping
- Deduplicates intelligently (keeps all timestamped plays)
- Calculates team statistics
- Generates data quality report

**Usage**:
```bash
# Merge all team members
python merge_team_data.py

# Merge specific members
python merge_team_data.py --members nicolo joe

# Custom output filename
python merge_team_data.py --output custom_team_data.csv
```

**Classes**:
- `TeamDataMerger`: Merges and validates team data

**Deduplication Logic**:
- **Recently played** (with timestamps): Keep all plays (represent multiple listens)
- **Top tracks** (no timestamps): Keep unique tracks per user/time_range

**Output Files**:
- `team_listening_history.csv`: Final merged dataset
- `team_merge_statistics.json`: Comprehensive statistics
- Data quality report (printed to console)

**Typical Runtime**: <1 minute

---

## Complete Pipeline

### First-Time Setup (Week 7)
```bash
# 1. Authenticate all team members (each member runs once)
python spotify_auth.py --user nicolo
python spotify_auth.py --user joe
python spotify_auth.py --user rithvik

# 2. Collect full data (one person runs)
python collect_spotify_data.py --user all

# 3. Enrich with audio features
python enrich_with_audio_features.py --user all

# 4. Merge into unified dataset
python merge_team_data.py
```

### Weekly Updates (Weeks 8-10)
```bash
# Quick collection (recently played only)
python collect_spotify_data.py --user all --recently-played-only

# Enrich new data
python enrich_with_audio_features.py --user all

# Merge updates
python merge_team_data.py
```

---

## Data Flow

```
┌────────────────────┐
│ Spotify API        │
│ (User Accounts)    │
└──────┬─────────────┘
       │
       │ spotify_auth.py
       │ (OAuth tokens)
       │
       ▼
┌────────────────────┐
│ collect_spotify    │──► data/raw/{user}_*.json
│ _data.py           │    (Recently played, top tracks, playlists)
└──────┬─────────────┘
       │
       │ enrich_with_audio_features.py
       │ (Fetch audio features, derive metrics)
       │
       ▼
┌────────────────────┐
│ Audio Features     │──► data/processed/{user}_listening_history.csv
│ Enricher           │    (Enriched with features + context)
└──────┬─────────────┘
       │
       │ merge_team_data.py
       │ (Combine all users)
       │
       ▼
┌────────────────────┐
│ Unified Dataset    │──► data/team_listening_history.csv
│                    │    (Ready for analysis!)
└────────────────────┘
```

---

## Error Handling

All scripts include:
- ✅ Try-catch blocks for API calls
- ✅ Retry logic with exponential backoff
- ✅ Detailed error logging
- ✅ Graceful degradation (continue on partial failures)
- ✅ Statistics tracking

**Common Errors**:
1. **Authentication Failed**: Run `spotify_auth.py` with `--force-refresh`
2. **Rate Limited (429)**: Scripts automatically wait and retry
3. **Missing Audio Features**: Falls back to Kaggle database
4. **No Data Found**: Check that user has Spotify listening history

---

## Security Notes

**Protected Files** (in .gitignore):
- `.env.*` - Spotify API credentials
- `.spotify_cache/` - OAuth tokens
- `data/raw/*.json` - Personal listening data

**Never Commit**:
- Client IDs and secrets
- OAuth tokens
- Personal listening data

**Safe to Commit**:
- Script files (*.py)
- Documentation (*.md)
- Aggregated statistics (if anonymized)
- .env.example template

---

## Dependencies

**Python Packages**:
```
spotipy>=2.23.0          # Spotify API wrapper
pandas>=2.0.0            # Data manipulation
python-dotenv>=1.0.0     # Environment variable management
numpy>=1.24.0            # Numerical operations
```

**Install**:
```bash
pip install -r requirements-mac.txt
```

---

## Performance

**Typical Runtime (3 Team Members)**:
- Authentication: 1-2 min per person (one-time)
- Full collection: 3-6 minutes
- Audio features enrichment: 5-10 minutes
- Merging: <1 minute
- **Total**: ~10-15 minutes

**Weekly Updates**:
- Collection (recently played only): 1-2 minutes
- Enrichment: 2-3 minutes
- Merging: <1 minute
- **Total**: ~5 minutes

**Data Volume**:
- Initial: 150-600 listening events
- After 4 weeks: 600-1200 listening events
- Disk space: ~5-10 MB total

---

## Testing

**Test Single User**:
```bash
# Test authentication
python spotify_auth.py --user nicolo

# Test data collection
python collect_spotify_data.py --user nicolo --recently-played-only

# Test enrichment
python enrich_with_audio_features.py --user nicolo

# Check outputs
ls data/raw/nicolo_*
ls data/processed/nicolo_*
```

**Validate Pipeline**:
```bash
# Run full pipeline for one user
python spotify_auth.py --user nicolo && \
python collect_spotify_data.py --user nicolo && \
python enrich_with_audio_features.py --user nicolo

# Check CSV
head -n 5 data/processed/nicolo_listening_history.csv
```

---

## Extending the Scripts

### Adding New Features

**Custom Context Detection**:
Edit `enrich_with_audio_features.py`, function `_infer_context()`:
```python
def _infer_context(row):
    # Add your custom logic here
    if row.get('energy') > 0.8 and row.get('tempo') > 140:
        return 'running'
    # ...
```

**Additional Composite Metrics**:
Edit `enrich_with_audio_features.py`, function `_add_derived_features()`:
```python
# Add excitement score
df['excitement_score'] = (
    0.6 * df['energy'] +
    0.4 * df['valence']
)
```

### Collecting More Data

**Playlist Tracks**:
Add to `collect_spotify_data.py`:
```python
def collect_playlist_tracks(self, playlist_id, limit=100):
    """Fetch all tracks in a playlist"""
    results = self.sp.playlist_tracks(playlist_id, limit=limit)
    # Process results...
```

**Saved Albums**:
Add to `collect_spotify_data.py`:
```python
def collect_saved_albums(self, limit=50):
    """Fetch user's saved albums"""
    results = self.sp.current_user_saved_albums(limit=limit)
    # Process results...
```

---

## Troubleshooting

### Script Hangs on Authentication
- **Cause**: Browser didn't open or callback wasn't received
- **Solution**: Copy URL from terminal and paste in browser manually

### "No module named 'spotipy'"
- **Cause**: Dependencies not installed
- **Solution**: `pip install -r requirements-mac.txt`

### Empty Dataset After Collection
- **Cause**: User hasn't listened to Spotify recently
- **Solution**: Play some songs, wait 10 minutes, try again

### Audio Features Missing for All Tracks
- **Cause**: Kaggle database not found
- **Solution**: Ensure `data/processed_spotify_data.csv` exists

---

## Support

- **Documentation**: `docs/SPOTIFY_DATA_COLLECTION_GUIDE.md`
- **Quick Start**: `docs/QUICK_START_GUIDE.md`
- **Spotify API Docs**: https://developer.spotify.com/documentation/web-api
- **Spotipy Docs**: https://spotipy.readthedocs.io/

---

## Version History

**v1.0** (Nov 3, 2025)
- Initial release
- Multi-user authentication
- Complete data collection pipeline
- Audio features enrichment
- Team data merging
- Context inference
