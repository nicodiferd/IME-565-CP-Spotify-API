# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Spotify analytics platform for IME 565 (Predictive Data Analytics for Engineers). Provides temporal intelligence, playlist optimization, and predictive recommendations beyond Spotify's annual "Wrapped" feature.

**Team**: Nicolo DiFerdinando, Joe Mascher, Rithvik Shetty
**Current Phase**: Phase 1 - Foundation analytics with Streamlit dashboard and Cloudflare R2 storage

## Quick Reference Commands

```bash
# Run the Streamlit dashboard
uv run streamlit run app/Home.py

# Run Jupyter notebook for EDA
uv run jupyter notebook notebooks/01_Phase1_EDA.ipynb

# Environment setup with UV (installs Python + all dependencies)
uv sync

# Add a new dependency
uv add <package-name>

# Add a dev dependency
uv add --group dev <package-name>

# Run any Python command in the project environment
uv run python script.py

# If kernel issues in Jupyter
uv run python -m ipykernel install --user --name=spotify-analytics --display-name "Python (Spotify Analytics)"
```

### UV Installation (if not installed)

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### Legacy Commands (deprecated - use UV instead)

```bash
# Old venv approach - still works but UV is preferred
python3.12 -m venv venv
source venv/bin/activate
pip install -r requirements-mac.txt
```

## Required Environment Variables

Copy `.env.example` to `.env` and configure:

```bash
# Spotify API (https://developer.spotify.com/dashboard)
SPOTIFY_CLIENT_ID=your_client_id
SPOTIFY_CLIENT_SECRET=your_client_secret
SPOTIFY_REDIRECT_URI=http://127.0.0.1:8501/  # Include trailing slash!

# Cloudflare R2 Storage
R2_ACCESS_KEY_ID=your_r2_access_key
R2_SECRET_ACCESS_KEY=your_r2_secret
R2_BUCKET_NAME=ime565spotify
CLOUDFLARE_ACCOUNT_ID=24df8bb5d20dca402dfc277d4c38cc80
```

## Architecture Overview

### Code Organization

```
app/                    # Streamlit multi-page application
├── Home.py             # Entry point (streamlit run app/Home.py)
├── func/               # Shared modules
│   ├── auth.py                 # Spotify OAuth, SessionCacheHandler
│   ├── page_auth.py            # require_auth() wrapper for pages
│   ├── data_fetching.py        # Spotify API calls with caching
│   ├── data_processing.py      # DataFrame transformations
│   ├── data_collection.py      # Snapshot collection & metrics
│   ├── dashboard_helpers.py    # load_current_snapshot(), handle_missing_data()
│   ├── s3_storage.py           # Cloudflare R2 upload/download (boto3)
│   ├── visualizations.py       # Plotly charts with Spotify theming
│   ├── ui_components.py        # Page config, custom CSS
│   └── datetime_utils.py       # Temporal formatting & aggregation helpers
└── pages/              # Auto-discovered by Streamlit
    ├── 0_Data_Sync.py          # Onboarding data collection
    ├── 1_Dashboard.py          # Overview metrics
    ├── 2_Advanced_Analytics.py # Audio feature analysis
    ├── 3_Recent_Listening.py   # Recent tracks timeline
    ├── 4_Top_Tracks.py         # Top tracks by time range
    ├── 5_Playlists.py          # Playlist overview
    └── 6_Deep_User.py          # Historical analytics

src/                    # Reusable modules (for notebooks & app)
├── data_processing.py          # load_spotify_data(), clean_dataset()
├── feature_engineering.py      # create_composite_features(), classify_context()
└── visualization.py            # Matplotlib/Seaborn plotting

notebooks/              # Jupyter notebooks
└── 01_Phase1_EDA.ipynb         # Phase 1 exploratory analysis
```

### Data Flow

1. **User authenticates** via OAuth in `Home.py`
2. **Data sync** runs automatically in `0_Data_Sync.py` (first visit)
3. **Snapshots stored** in Cloudflare R2 as Parquet files
4. **Dashboard pages** load from `current/` snapshot via `load_current_snapshot()`
5. **Audio features** enriched from Kaggle dataset (~60-80% coverage)

### R2 Storage Structure

```
ime565spotify/
├── reference_data/
│   └── kaggle_tracks_audio_features.parquet
└── users/{user_id}/
    ├── current/                    # Latest snapshot (dashboards use this)
    │   ├── metadata.json
    │   ├── recent_tracks.parquet
    │   ├── top_tracks_{short,medium,long}.parquet
    │   ├── top_artists_{short,medium,long}.parquet
    │   └── computed_metrics.json
    └── snapshots/{timestamp}/      # Historical (Deep User page)
```

## Critical Patterns

### Adding a New Streamlit Page

Create file in `app/pages/` with numbered prefix (e.g., `7_Your_Page.py`):

```python
import streamlit as st
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from func.ui_components import apply_page_config, get_custom_css
from func.page_auth import require_auth
from func.dashboard_helpers import load_current_snapshot, handle_missing_data, display_sync_status

apply_page_config()
st.markdown(get_custom_css(), unsafe_allow_html=True)

sp, profile = require_auth()
if not sp:
    st.warning("Please connect your Spotify account.")
    st.stop()

user_id = profile['id']
try:
    data = load_current_snapshot(user_id)
except Exception:
    handle_missing_data(redirect_to_sync=True)

st.header("Your Page Title")
display_sync_status(data['metadata'])

# Access data: data['recent_tracks'], data['top_tracks']['short'], data['metrics']
```

**IMPORTANT**: Never use emojis in filenames - causes cross-platform encoding issues.

### Spotify API Authentication

Use session-based cache handler for multi-user support:

```python
class SessionCacheHandler(CacheHandler):
    def get_cached_token(self):
        return st.session_state.get('token_info', None)
    def save_token_to_cache(self, token_info):
        st.session_state['token_info'] = token_info
```

- Tokens stored in `st.session_state`, not file cache
- Refresh at 50-minute mark (expire at 60 minutes)

### Caching Strategy

- `@st.cache_resource`: Spotify client initialization
- `@st.cache_data(ttl=3600)`: Data fetching operations
- User-specific data: `st.session_state` only

### Audio Features Workaround

**Critical**: `sp.audio_features()` returns HTTP 403 for this app.

**Solution**: Kaggle dataset lookup via `enrich_with_audio_features()` in `dashboard_helpers.py`
- Pre-loaded ~114k tracks with audio features
- 60-80% coverage for popular tracks
- Falls back gracefully for unmatched tracks

## Feature Engineering

### Composite Metrics (src/feature_engineering.py)

| Metric | Formula | Purpose |
|--------|---------|---------|
| mood_score | valence + energy - acousticness | Emotional profile |
| grooviness | danceability + energy + tempo_normalized | Upbeat quality |
| focus_score | instrumentalness - speechiness + (1-energy) | Work suitability |
| relaxation_score | acousticness - energy + (1-tempo_normalized) | Calmness |

### Context Classification

- **workout**: energy > 0.7 AND danceability > 0.6
- **focus**: instrumentalness > 0.5 OR (speechiness < 0.3 AND energy < 0.5)
- **party**: valence > 0.7 AND energy > 0.7 AND danceability > 0.7
- **relaxation**: energy < 0.4 AND acousticness > 0.5
- **general**: default

## Module Usage

### Loading Snapshot Data (Dashboard Pages)

```python
from func.dashboard_helpers import load_current_snapshot, get_recent_tracks, get_top_tracks

data = load_current_snapshot(user_id)  # Full snapshot
recent = data['recent_tracks']         # DataFrame
top_short = data['top_tracks']['short'] # DataFrame
metrics = data['metrics']              # dict

# Or use quick accessors
recent = get_recent_tracks(user_id)
top_medium = get_top_tracks(user_id, 'medium')
```

### Processing Kaggle Data (Notebooks)

```python
from src.data_processing import load_spotify_data, clean_dataset, identify_audio_features
from src.feature_engineering import create_composite_features, classify_context

df, filename = load_spotify_data('data/raw')
df_clean = clean_dataset(df)
df_features = create_composite_features(df_clean)
df_context = classify_context(df_features)
```

### Temporal Utilities

```python
from func.datetime_utils import (
    format_datetime,
    time_ago_string,
    get_freshness_indicator,
    extract_all_temporal_features,
    aggregate_by_hour,
    aggregate_by_day_of_week
)

# Format datetime
format_datetime(dt, 'display_datetime')  # "2025-11-23 14:30"

# Human-readable time ago
time_ago_string(last_played)  # "2 hours ago"

# Add all temporal features to DataFrame
df = extract_all_temporal_features(df, 'played_at')
# Adds: hour, day_of_week, is_weekend, month, season, etc.
```

## Known Issues & Solutions

### Environment Variables Not Loading (FIXED)
- **Cause**: Multi-page Streamlit apps don't auto-load .env
- **Solution**: `load_dotenv()` called in `s3_storage.py` module level

### Parquet "seek" Error (FIXED)
- **Cause**: S3 stream not seekable
- **Solution**: Read into `BytesIO` before pandas: `pd.read_parquet(io.BytesIO(response['Body'].read()))`

### KeyError for Missing Fields (FIXED)
- **Cause**: Fields like 'explicit' missing when audio features unavailable
- **Solution**: `safe_mean()` helper with `.get()` accessors

### ScriptRunContext Warnings
- **Cause**: Streamlit threading during background data collection
- **Status**: Expected, can be ignored

## Data Quality Rules

- Remove tracks with loudness > 0 dB (violates spec)
- Filter tracks < 5 seconds (skips/noise)
- Handle null audio features (deleted content)
- Try encodings: utf-8, latin-1, iso-8859-1, cp1252

## Git Workflow

```bash
# Current branch: main
git status
git add <files>
git commit -m "descriptive message"
git push origin main

# Feature branches
git checkout -b feature/your-feature
# ... work ...
git push origin feature/your-feature
# Create PR to main
```

## Documentation Reference

| File | Purpose |
|------|---------|
| `docs/SPOTIFY_API_CAPABILITIES.md` | API endpoint testing results & limitations |
| `docs/ARCHITECTURE.md` | Storage strategy with current/ directory |
| `docs/TEMPORAL_FEATURES_GUIDE.md` | Datetime utilities documentation |
| `docs/IMPLEMENTATION_SUMMARY.md` | Summary of Phase 1 implementation |
| `docs/IME565_Project_Proposal_Final.md` | Original project proposal |
| `docs/PRESENTATION_SPRINT_PLAN.md` | Sprint plan for presentation |
| `data/README.md` | Kaggle dataset download links |

## Development Phases

| Phase | Focus | Status |
|-------|-------|--------|
| 1 | Foundation analytics, Streamlit dashboard, R2 storage | **Complete** |
| 2 | Playlist intelligence, health metrics | Planned |
| 3 | ML models (Random Forest, XGBoost), predictive recommendations | Planned |
