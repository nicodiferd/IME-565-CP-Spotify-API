# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a multi-phase Spotify analytics platform project for IME 565 (Predictive Data Analytics for Engineers). The goal is to build a comprehensive music analytics tool that goes beyond Spotify's annual "Wrapped" feature by providing temporal intelligence, playlist optimization, and predictive recommendations.

**Team**: Nicolo DiFerdinando, Joe Mascher, Rithvik Shetty
**Course**: IME 565, Fall Quarter 2025

**Current Phase**: Phase 1 - Foundation analytics using Kaggle datasets and initial Streamlit dashboard

## Implementation Status

### ✅ Currently Implemented
- **Data processing pipeline** (`src/data_processing.py`)
  - Multi-encoding CSV loader
  - Data cleaning and validation
  - Audio feature identification
- **Feature engineering** (`src/feature_engineering.py`)
  - Composite metrics (mood, grooviness, focus, relaxation)
  - Context classification (5 categories)
- **Visualization modules** (`src/visualization.py`)
  - Distribution plots, correlation matrices
  - Top artists/genres charts
- **Kaggle Dataset Integration** (`app/func/dashboard_helpers.py`)
  - Audio features enrichment from ~114k track dataset
  - 60-80% coverage for popular tracks
  - Automatic feature engineering and context classification
- **Streamlit dashboard** (fully modularized with snapshot architecture)
  - `app/Home.py` - Home page and main entry point for multi-page app
  - `app/func/` - Function modules (auth, data fetching, processing, visualizations, UI, S3 storage, data collection, **dashboard_helpers**)
  - `app/pages/` - Page modules (**all migrated to snapshot architecture**)
    - `1_Dashboard.py` - Overview with taste consistency, genre breakdown
    - `2_Advanced_Analytics.py` - Full audio feature analysis (now functional!)
    - `3_Recent_Listening.py` - Timeline with enriched data
    - `4_Top_Tracks.py` - Three view modes with time range comparisons
    - `5_Playlists.py` - Playlist overview
    - `6_Deep_User.py` - Historical analytics
  - OAuth authentication
  - **Snapshot-based data loading** (5-10x faster page loads)
  - Interactive visualizations with Plotly
  - Cloudflare R2 storage for historical data
- **Jupyter notebook** (`notebooks/01_Phase1_EDA.ipynb`)
  - Complete EDA workflow

### 🎉 Recent Updates (November 2025)
**Major Dashboard Migration Complete**:
- ✅ All dashboards now use `load_current_snapshot()` from R2 storage
- ✅ Kaggle audio features integration (mood, grooviness, focus, relaxation, context)
- ✅ Dashboard 2 (Advanced Analytics) completely rebuilt - now shows radar charts, mood distributions, composite features
- ✅ Dashboard 4 (Top Tracks) enhanced with side-by-side comparisons and taste evolution analysis
- ✅ Fixed critical bugs:
  - Environment variable loading in multi-page Streamlit apps (`load_dotenv()` in `s3_storage.py`)
  - Parquet file reading from S3 (BytesIO wrapper for seekable stream)
- ✅ Performance: 5-10x faster page loads (no API calls on every page view)

### 📋 Planned (Not Yet Implemented)
- **Data collection scripts** (planned `scripts/` directory)
  - `spotify_auth.py` - Multi-user OAuth
  - `collect_spotify_data.py` - API data collection
  - `enrich_with_audio_features.py` - Feature enrichment
  - `merge_team_data.py` - Team data merging
- **Phase 2 features**: Playlist intelligence, health metrics
- **Phase 3 features**: ML models, predictive recommendations

**Note**: The `scripts/` directory and data collection scripts don't exist yet. Phase 1 focuses on analysis using Kaggle datasets.

## Development Phases

The project follows a three-phase development strategy:

### Phase 1: Foundation Analytics (Weeks 6-7)
- Core visualization and analysis pipeline using public Kaggle datasets
- Interactive Streamlit dashboard with temporal analysis
- Audio feature distributions and correlations
- Top tracks/artists/genres identification

### Phase 2: Playlist Intelligence (Weeks 8-9)
- Playlist health metrics (save-to-play ratio, recency scores)
- Overlap detection across playlists
- Freshness analysis and optimization recommendations

### Phase 3: Predictive Modeling (Week 10+)
- Machine learning models for preference prediction (Random Forest, XGBoost, ensemble methods)
- Context detection through clustering (workout, focus, relaxation)
- Mood trajectory tracking
- Explainable recommendations

## Tech Stack

- **Frontend/Dashboard**: Streamlit
- **Data Processing**: Python with pandas, numpy
- **Machine Learning**: scikit-learn, XGBoost
- **Data Visualization**: Plotly, Matplotlib, Seaborn
- **API Integration**: Spotipy (Spotify API wrapper) [https://spotipy.readthedocs.io/en/latest/]

## Common Development Workflows

### Adding a New Streamlit Page

Streamlit automatically discovers pages in the `app/pages/` directory. To add a new page:

1. **Create page file** in `app/pages/` with numbered prefix:
```python
# File: app/pages/7_Your_Page.py
import streamlit as st
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from func.ui_components import apply_page_config, get_custom_css
from func.page_auth import require_auth
from func.dashboard_helpers import load_current_snapshot, handle_missing_data, display_sync_status

# Apply page config and styling
apply_page_config()
st.markdown(get_custom_css(), unsafe_allow_html=True)

# Require authentication
sp, profile = require_auth()
if not sp:
    st.warning("Please connect your Spotify account to view this page.")
    st.stop()

user_id = profile['id']

# Load current snapshot data
try:
    data = load_current_snapshot(user_id)
except Exception as e:
    handle_missing_data(redirect_to_sync=True)

# Page header with sync status
st.header("🎨 Your Page Title")
display_sync_status(data['metadata'])

# Page content using snapshot data
st.subheader("Your Analysis")
# Use data['recent_tracks'], data['top_tracks']['short'], etc.
```

2. **File naming convention**:
   - Prefix with a number to control order: `7_`, `8_`, etc.
   - Use descriptive name with underscores: `Your_Page.py`
   - **NEVER use emojis** in filenames (causes cross-platform issues)
   - Result: `7_Your_Page.py`

3. **That's it!** Streamlit automatically:
   - Discovers the new page
   - Adds it to sidebar navigation
   - Renders the name in the menu

**No need to modify** `Home.py` or any routing logic - Streamlit handles it automatically!

### Adding a New Audio Feature or Composite Metric

1. **Define the metric** in `src/feature_engineering.py`:
```python
def create_composite_features(df: pd.DataFrame) -> pd.DataFrame:
    # Add your new metric
    df['your_metric'] = (0.5 * df['energy'] + 0.5 * df['valence'])
    return df
```

2. **Update visualizations** in `src/visualization.py` or `app/func/visualizations.py` if needed

3. **Test in notebook** (`notebooks/01_Phase1_EDA.ipynb`):
```python
df_processed = create_composite_features(df_clean)
print(df_processed['your_metric'].describe())
```

4. **Add to Streamlit dashboard** by creating a new page or adding to an existing page

### Adding a New Context Classification Rule

Edit the `classify_context()` function in `src/feature_engineering.py`:
```python
def classify_context(df: pd.DataFrame) -> pd.DataFrame:
    def _classify(row):
        # Add your rule (check existing rules first)
        if row['energy'] > 0.8 and row['tempo'] > 140:
            return 'running'
        # ... existing rules

    df['context'] = df.apply(_classify, axis=1)
    return df
```

### Debugging Data Loading Issues

If `load_spotify_data()` fails:
1. Check file exists: `ls data/raw/*.csv`
2. Try loading manually with different encodings:
```python
import pandas as pd
encodings = ['utf-8', 'latin-1', 'iso-8859-1', 'cp1252']
for enc in encodings:
    try:
        df = pd.read_csv('data/raw/dataset.csv', encoding=enc)
        print(f"Success with {enc}")
        break
    except:
        print(f"Failed with {enc}")
```
3. Check for required columns: `danceability`, `energy`, `valence`, etc.

## Key Commands

### Environment Setup
```bash
# Create virtual environment (Python 3.12 recommended)
python3.12 -m venv venv
source venv/bin/activate  # Mac/Linux
# venv\Scripts\activate   # Windows

# Install dependencies
pip install -r requirements-mac.txt  # Mac
pip install -r requirements-windows.txt  # Windows

# Set up Spotify API credentials (for dashboard authentication)
cp .env.example .env
# Edit .env and add:
#   SPOTIFY_CLIENT_ID=your_client_id_here
#   SPOTIFY_CLIENT_SECRET=your_client_secret_here
#   SPOTIFY_REDIRECT_URI=http://127.0.0.1:8501/
# Get credentials from: https://developer.spotify.com/dashboard
# IMPORTANT: Add the exact redirect URI to your Spotify app settings (including trailing slash)
```

### Data Acquisition
```bash
# Download datasets from Kaggle and place in data/ directory
# See data/README.md for specific dataset links
# Required: At least one of these datasets:
#   - Spotify Tracks Dataset (~114k tracks): dataset.csv
#   - Top Spotify Songs 2023: spotify-2023.csv
#   - Alternative: Spotify 1921-2020 (160k+ tracks): tracks.csv
```

### Running the Application
```bash
# Run the Streamlit dashboard (multi-page app)
streamlit run app/Home.py

# Run Jupyter notebook for exploratory data analysis
jupyter notebook notebooks/01_Phase1_EDA.ipynb
```

### Jupyter Notebook Tips
```bash
# Launch notebook server
jupyter notebook

# If kernel issues occur, reinstall kernel
python -m ipykernel install --user --name=venv --display-name "Python (Spotify Analytics)"

# List installed kernels
jupyter kernelspec list
```

### Working with Jupyter Notebooks for API Testing
The `notebooks/` directory contains testing notebooks for API exploration:

- **`notebooks/api_testing.ipynb`**: Tests Spotify API capabilities and limitations
- **`notebooks/01_Phase1_EDA.ipynb`**: Full exploratory data analysis workflow

**Key Patterns**:
```python
# Test API endpoints
import sys
sys.path.insert(0, '..')  # Access app modules from notebook

from app.func.auth import get_spotify_client
from app.func.data_fetching import fetch_recent_tracks

# Initialize client
sp = get_spotify_client()

# Test endpoint
recent = sp.current_user_recently_played(limit=50)
print(f"Fetched {len(recent['items'])} tracks")
```

**Best Practices**:
- Use notebooks to test API endpoints before implementing in dashboard
- Document findings in `docs/SPOTIFY_API_CAPABILITIES.md`
- Cache results to avoid rate limiting during exploration
- Keep `.cache_notebook` in .gitignore (contains auth tokens)

### Running Tests
```bash
# Currently no tests implemented
# Tests directory: tests/
# Planned: pytest for unit tests in Phase 2
```

## Architecture Notes

### Code Organization Philosophy

This project follows standard data science practices:
- **`notebooks/`**: Exploration and analysis (Jupyter notebooks)
- **`src/`**: Reusable Python modules (imported by notebooks and app)
- **`app/`**: Streamlit dashboard with Spotify authentication
- **`data/`**: Kaggle datasets and processed outputs
- **`docs/`**: Project documentation and guides

**Golden Rule**: Extract shared code from notebooks to `src/`, import from both notebooks and app.

### Streamlit App Structure

The Streamlit dashboard uses **Streamlit's native multi-page app** structure with automatic navigation:

**Main Entry Point:**
- **`app/Home.py`**: The home page and entry point (`streamlit run app/Home.py`)
  - Welcome page content
  - Authentication UI (optional - doesn't block access to home)
  - Uses Streamlit's native multi-page architecture (pages auto-discovered)

**Function Modules (`app/func/`):**
Reusable functions for API calls, data processing, and utilities:
- **`auth.py`**: Spotify OAuth authentication, credential management, session state initialization, token handling
- **`page_auth.py`**: Shared authentication wrapper (`require_auth()`) used by all pages
- **`data_fetching.py`**: API calls to Spotify Web API (fetch tracks, artists, playlists, audio features) with caching
- **`data_processing.py`**: Transform API responses into processed DataFrames, apply feature engineering, diversity calculations
- **`visualizations.py`**: Plotly chart generation functions (9 visualization functions with Spotify theming)
- **`ui_components.py`**: Page configuration, custom CSS styling, reusable UI elements
- **`s3_storage.py`**: Cloudflare R2 upload/download functions
- **`data_collection.py`**: Snapshot collection and metrics computation
- **`dashboard_helpers.py`**: Helper functions for loading current snapshot data in dashboard pages (provides `load_current_snapshot()`, `handle_missing_data()`, and time-range specific getters)

**Page Modules (`app/pages/`):**
Individual Streamlit pages - automatically discovered and added to navigation:
- **`0_Data_Sync.py`**: Mandatory onboarding data collection page with Spotify facts and progress tracking
- **`1_Dashboard.py`**: Overview page with key metrics, temporal patterns, and artist analysis
- **`2_Advanced_Analytics.py`**: Advanced analytics with audio features, mood analysis, and feature distributions
- **`3_Recent_Listening.py`**: Detailed timeline of recently played tracks with downloadable CSV
- **`4_Top_Tracks.py`**: Top tracks across different time ranges with audio profiles
- **`5_Playlists.py`**: Playlist overview with metadata and Spotify links
- **`6_Deep_User.py`**: Historical analytics showing long-term trends and patterns

**IMPORTANT**: Page filenames should NEVER contain emojis. Use simple alphanumeric characters, underscores, and numbers only.

**Design Principles:**
- **Streamlit native multi-page**: Pages in `app/pages/` are automatically discovered and added to sidebar navigation
- **Numbered prefixes**: Files prefixed with numbers (0_, 1_, 2_, etc.) control display order in navigation
- **NO EMOJIS IN FILENAMES**: Never use emojis in Python filenames - causes encoding issues across platforms
- Use `st.session_state` for shared data across pages (authentication tokens, user data)
- Import functions from `app/func/` modules (avoid duplicating code across pages)
  - The `app/func/__init__.py` exports all functions for clean imports
  - Example: `from func.page_auth import require_auth`
- Each page script is standalone and executes top-to-bottom
- All authenticated pages call `require_auth()` at the start:
  ```python
  from func.page_auth import require_auth
  sp, profile = require_auth()
  if not sp:
      st.warning("Please connect to continue")
      st.stop()
  ```

**User Onboarding Flow:**
1. User visits `Home.py` and authenticates with Spotify OAuth
2. After authentication, user is automatically redirected to `0_Data_Sync.py`
3. Data collection runs automatically with progress tracking and Spotify facts
4. Upon completion, user is redirected to `1_Dashboard.py`
5. All subsequent visits skip the data sync (unless manually triggered)

### Data Collection & Storage (Deep User Analytics)

The app automatically collects and stores user listening data to enable longitudinal analysis:

**Storage Backend:**
- **Cloudflare R2** (S3-compatible object storage)
- Parquet file format for efficient storage and querying
- Organized by user ID and timestamp

**File Structure:**
```
cloudflare-r2://ime565spotify/
├── reference_data/
│   └── kaggle_tracks_audio_features.parquet    # Audio features lookup table
└── users/
    └── {user_id}/
        ├── current/                            # Latest snapshot (for dashboards)
        │   ├── metadata.json
        │   ├── recent_tracks.parquet
        │   ├── top_tracks_short.parquet
        │   ├── top_tracks_medium.parquet
        │   ├── top_tracks_long.parquet
        │   ├── top_artists_short.parquet
        │   ├── top_artists_medium.parquet
        │   ├── top_artists_long.parquet
        │   └── computed_metrics.json
        ├── snapshots/                          # Historical point-in-time collections
        │   └── {timestamp}/
        │       ├── metadata.json
        │       ├── recent_tracks.parquet
        │       ├── top_tracks_short.parquet
        │       ├── top_tracks_medium.parquet
        │       ├── top_tracks_long.parquet
        │       ├── top_artists_short.parquet
        │       ├── top_artists_medium.parquet
        │       ├── top_artists_long.parquet
        │       └── computed_metrics.json
        └── aggregated/                         # Pre-computed for fast loading
            ├── all_recent_tracks.parquet       # Deduplicated history
            ├── all_snapshots_metrics.parquet   # Time series
            └── last_updated.json
```

**Important**:
- The `current/` directory contains the most recent snapshot used by dashboard pages (1-5)
- Dashboard pages should use `load_current_snapshot()` from `dashboard_helpers.py` to access this data
- The `snapshots/` directory contains historical data used by the Deep User page (6) for longitudinal analysis
- The `aggregated/` directory is for pre-computed analysis (future implementation)

**Data Collection Strategy:**
- **Current**: Collects on every session (during onboarding flow)
- **Recommended**: Smart scheduling - collect only if >24 hours since last snapshot
- **Implementation**: Check `last_updated.json` before triggering collection
- **User Control**: Manual refresh button to force collection

**Data Collection Trigger:**
- First-time users: Automatic onboarding data collection in `0_Data_Sync.py`
- Returning users: Check if last collection was >24 hours ago
- Manual trigger: User can force refresh via dashboard
- Captures: recently played tracks, top tracks/artists (all time ranges), computed metrics
- Stored in R2 bucket with structure: `users/{user_id}/snapshots/{timestamp}/`

**Collected Data Types:**
1. **Recent Tracks** (`recent_tracks.parquet`): Last 50 played tracks with audio features, timestamps, and composite metrics
2. **Top Tracks** (`top_tracks_short/medium/long.parquet`): Top 50 tracks for each time range with audio features
3. **Top Artists** (`top_artists_short/medium/long.parquet`): Top 50 artists for each time range with genres and popularity
4. **Computed Metrics** (`metrics.parquet`): Aggregated metrics including diversity scores, average audio features, context distributions

**Deep User Page Features:**
- **Artist Evolution**: Track how your top artists change over time, genre trends by month
- **Listening Patterns**: Daily activity, hour-of-day patterns, day-of-week patterns over time
- **Team Comparison**: Compare listening habits with team members (taste overlap, diversity, etc.)
- **Metrics Over Time**: Visualize audio feature trends, diversity scores, context distributions

**Configuration:**
Required environment variables in `.env`:
```
# Required for S3 API access
R2_ACCESS_KEY_ID=your_r2_access_key_id
R2_SECRET_ACCESS_KEY=your_r2_secret_access_key
R2_BUCKET_NAME=ime565spotify
CLOUDFLARE_ACCOUNT_ID=24df8bb5d20dca402dfc277d4c38cc80

# Note: Custom domains (like s3.diferdinando.com) are for public HTTP access,
# not for S3 API operations. API always uses the account-specific endpoint.
```

**Your R2 Bucket Configuration:**
- Bucket Name: `ime565spotify`
- Region: Western North America (WNAM)
- Account ID: `24df8bb5d20dca402dfc277d4c38cc80`
- S3 API Endpoint: `https://{CLOUDFLARE_ACCOUNT_ID}.r2.cloudflarestorage.com`

See `docs/INTEGRATION_GUIDE.md` for detailed setup instructions.

**Implementation Modules:**
- `app/func/s3_storage.py`: R2 upload/download functions using boto3 with custom endpoint
- `app/func/data_collection.py`: Snapshot collection, metric computation, automatic uploads
- `app/pages/deep_user.py`: Historical analytics visualizations and insights

### Data Pipeline (Current Implementation)

**Phase 1 uses Kaggle public datasets** for initial analysis:

1. **Data Loading** (`src/data_processing.py`)
   - `load_spotify_data()`: Auto-detect CSV encoding, load datasets from `data/raw/`
   - Supports multiple encodings (utf-8, latin-1, iso-8859-1, cp1252)
   - Prioritizes `dataset.csv` if available

2. **Data Cleaning** (`src/data_processing.py`)
   - `clean_dataset()`: Remove duplicates, invalid loudness (>0 dB), short tracks (<5s)
   - `identify_audio_features()`: Detect which columns contain Spotify audio features

3. **Feature Engineering** (`src/feature_engineering.py`)
   - `create_composite_features()`: Mood, grooviness, focus, relaxation scores
   - `classify_context()`: Rule-based context categorization (workout, focus, party, relaxation, general)

4. **Visualization** (`src/visualization.py`)
   - `plot_feature_distributions()`: Histograms for audio features
   - `plot_correlation_matrix()`: Feature correlation heatmap
   - `plot_top_artists_genres()`: Bar charts for top items

5. **Streamlit Dashboard** (`app/Home.py`)
   - OAuth authentication with Spotify API
   - Session-based token management (multi-user support)
   - Interactive visualizations with Plotly
   - Real-time data fetching from user's Spotify account
   - Cloudflare R2 integration for historical data storage


### Module Usage Guide

**Working with `src/data_processing.py`:**
```python
from src.data_processing import load_spotify_data, clean_dataset, identify_audio_features

# Load dataset (tries multiple encodings automatically)
df, filename = load_spotify_data(data_dir='data/raw')

# Clean the data
df_clean = clean_dataset(df)

# Identify audio feature columns
audio_features = identify_audio_features(df_clean)
```

**Working with `src/feature_engineering.py`:**
```python
from src.feature_engineering import create_composite_features, classify_context

# Create composite scores
df_with_features = create_composite_features(df_clean)
# Adds: mood_score, grooviness, focus_score, relaxation_score

# Classify listening context
df_with_context = classify_context(df_with_features)
# Adds: context column (workout, focus, party, relaxation, general)
```

**Working with `src/visualization.py`:**
```python
from src.visualization import plot_feature_distributions, plot_correlation_matrix

# Visualize audio feature distributions
plot_feature_distributions(df, audio_features)

# Create correlation heatmap
plot_correlation_matrix(df, audio_features)
```

**Working with `app/func/dashboard_helpers.py`:**
```python
from func.dashboard_helpers import load_current_snapshot, handle_missing_data, display_sync_status
from func.page_auth import require_auth

# Authenticate
sp, profile = require_auth()
if not sp:
    st.stop()

user_id = profile['id']

# Load current snapshot data (cached for 1 hour)
try:
    data = load_current_snapshot(user_id)
except Exception as e:
    handle_missing_data(redirect_to_sync=True)

# Show sync status indicator
display_sync_status(data['metadata'])

# Access data
recent_tracks = data['recent_tracks']  # DataFrame
top_tracks_short = data['top_tracks']['short']  # DataFrame
top_artists_long = data['top_artists']['long']  # DataFrame
metrics = data['metrics']  # dict

# Or use quick access functions
from func.dashboard_helpers import get_recent_tracks, get_top_tracks, get_metrics

recent = get_recent_tracks(user_id)
top_short = get_top_tracks(user_id, 'short')
metrics = get_metrics(user_id)
```

### Jupyter Notebook Workflow (notebooks/01_Phase1_EDA.ipynb)

Standard analysis pipeline:
1. Import from `src/` modules
2. Load data using `load_spotify_data('data/raw')`
3. Clean with `clean_dataset()`
4. Engineer features with `create_composite_features()` and `classify_context()`
5. Visualize using functions from `visualization.py`
6. Export processed data to `data/processed/`

**Expected DataFrame columns after processing**:
- **Core audio features**: danceability, energy, valence, acousticness, instrumentalness, speechiness, tempo, loudness, liveness
- **Metadata**: track_name, artists, album_name, track_genre (if available), popularity
- **Composite features**: mood_score, grooviness, focus_score, relaxation_score, context

### Spotify API Authentication (for Streamlit app)
- Use **session-based cache handler** for multi-user Streamlit deployment
- Store tokens in `st.session_state` to prevent users from sharing the same token
- Implement token refresh logic at the 50-minute mark (tokens expire after 60 minutes)
- Never store tokens in file-based cache (single .cache file causes all users to share tokens)

**Important pattern**:
```python
class SessionCacheHandler(CacheHandler):
    def get_cached_token(self):
        return st.session_state.get('token_info', None)

    def save_token_to_cache(self, token_info):
        st.session_state['token_info'] = token_info
```

### Streamlit Caching Strategy
- Use `@st.cache_resource` for Spotify API client initialization (returns same object)
- Use `@st.cache_data(ttl=3600)` for data fetching operations (returns copies, auto-refresh hourly)
- Store user-specific data in `st.session_state`, NOT in cache
- Initialize all session state keys at app startup to avoid KeyErrors

### API Rate Limiting and Error Handling
- Wrap all API calls with retry logic and exponential backoff
- Handle HTTP 429 (Too Many Requests): Extract 'Retry-After' header and delay appropriately
- Handle HTTP 401 errors: Clear session token and prompt re-authentication
- Batch requests: Spotify allows up to 100 tracks per request (50 for most endpoints)
- Throttle to stay below 2 requests per second (limit is ~180 requests per minute)

### Critical API Limitation: Audio Features
**IMPORTANT**: The Spotify Web API endpoint for audio features (`sp.audio_features()`) returns **HTTP 403 Forbidden** for this application.

**Impact**:
- Cannot access danceability, energy, valence, acousticness, instrumentalness, speechiness, tempo, loudness directly from API
- These features are critical for mood analysis, context classification, and predictive modeling

**Workarounds**:
1. **Kaggle Dataset Lookup** (Current approach):
   - Pre-load Kaggle Spotify Tracks Dataset (~114k tracks) with audio features
   - Merge user's tracks with dataset by track_id
   - Coverage: ~60-80% for popular tracks, lower for obscure tracks

2. **Request Extended API Access** (Future):
   - Contact Spotify Developer Support for extended quota
   - Required for production deployment with full audio feature access
   - URL: https://developer.spotify.com/support

**Dashboard Strategy**:
- Show "Audio Features Available: X%" metric
- Display full analytics for tracks with audio features
- Show alternative metrics (popularity-based) for tracks without audio features
- Clear user messaging when audio features unavailable

### Data Processing Pipeline
1. **Data Acquisition**: Load public datasets or fetch from Spotify API
2. **Preprocessing**:
   - Filter plays under 5 seconds (indicates skipping)
   - Remove duplicates and invalid entries
   - Normalize audio features to [0,1] scale using MinMaxScaler
3. **Feature Engineering**: Create composite metrics (mood scores, grooviness indices)
4. **Aggregation**: Generate temporal summaries by hour/day/week/season

## Key Audio Features

Spotify provides machine-generated audio features (0.0-1.0 scale for most):
- **danceability**: How suitable for dancing
- **energy**: Intensity and activity level
- **valence**: Musical positiveness (happy vs sad)
- **acousticness**: Likelihood of being acoustic
- **instrumentalness**: Predicts if track has no vocals
- **speechiness**: Presence of spoken words
- **tempo**: BPM (beats per minute)
- **loudness**: Overall loudness in decibels

**Note**: These features are only available via Kaggle dataset lookup (not directly from API). See [Critical API Limitation](#critical-api-limitation-audio-features) section.

### Composite Feature Engineering
- **Mood Score**: Combine valence, energy, and acousticness for emotional profile
- **Grooviness Index**: Merge danceability, energy, and tempo
- **Focus Suitability**: Weight low speechiness, moderate energy, high instrumentalness

### Alternative Metrics (Without Audio Features)
When audio features are unavailable, derive insights from API metadata:

**Popularity-Based Analysis**:
- Average popularity score (0-100)
- Mainstream vs Niche classification (high popularity = mainstream)
- Popularity distribution and trends over time

**Temporal Intelligence**:
- Hour-of-day listening patterns (from `played_at` timestamps)
- Day-of-week patterns (weekday vs weekend)
- Monthly trends and seasonal changes
- Listening streaks and session duration

**Artist & Genre Diversity**:
- Unique artists / total tracks ratio
- Genre diversity score (unique genres / total artists)
- Artist loyalty (repeat artist rate)
- Discovery rate (new artists per month)

**Content Preferences**:
- Explicit vs clean content ratio
- Album vs single preference
- Average track duration
- Release year distribution (new releases vs classics)

**Artist Evolution**:
- Top artist changes month-over-month
- Artist rank trajectories over time
- Genre drift analysis

See `docs/DATA_ARCHITECTURE_RECOMMENDATION.md` for full list of metrics available without audio features.

## Data Sources

### Kaggle Public Datasets (Current Implementation)
**Primary data source for Phase 1**:
- **Spotify Tracks Dataset**: ~114,000 tracks with comprehensive audio features (recommended)
  - Download: https://www.kaggle.com/datasets/maharshipandya/-spotify-tracks-dataset
- **Top Spotify Songs 2023**: ~50,000 tracks with popularity metrics
  - Download: https://www.kaggle.com/datasets/nelgiriyewithana/top-spotify-songs-2023
- **Spotify 1921-2020**: 160k+ historical tracks
  - Download: https://www.kaggle.com/datasets/yamaerenay/spotify-dataset-19212020-600k-tracks
- **Location**: Place downloaded CSVs in `data/raw/`
- **Required columns**: track_name, artists, audio features (danceability, energy, valence, etc.)

### Streamlit Dashboard Data (Real-Time)
- Users authenticate with their Spotify account via OAuth
- Dashboard fetches real-time data from Spotify API:
  - Recently played tracks
  - Top tracks and artists
  - Saved playlists
  - Audio features for tracks
- Data is session-based and not persisted to disk

## Machine Learning Targets (Phase 3)

### Model Architecture
- **Random Forest**: Baseline achieving 74-77% accuracy
- **XGBoost**: Gradient boosting achieving 70-75% accuracy
- **Ensemble Voting**: Combine RF, XGBoost, SVM, K-Neighbors for 80-85% accuracy

### Key Features for Prediction
- Audio characteristics: energy, speechiness, acousticness, danceability, valence
- Temporal patterns: hour-of-day, day-of-week preferences
- Historical behavior: genre distributions, artist preferences, skip patterns
- Context indicators: playlist sources, session duration, shuffle behavior

### Validation Strategy
- 80/20 train-test split with stratification by genre
- Cross-validation for hyperparameter tuning
- Metrics: accuracy, precision, recall, F1-score, confusion matrices
- Interpretability: feature importance rankings, SHAP values

## Common Patterns

### Context Separation
Users want to separate listening contexts:
- Sleep/relaxation music
- Workout/high-energy music
- Kids music
- Focus/work music
- Background noise

Implement clustering to automatically classify activities based on audio features and temporal patterns.

### Temporal Intelligence
- Weekday morning peaks: commuting music
- Working hours: focus music
- Weekend evenings: social/party music
- Analyze by hour-of-day, day-of-week, and seasonal cycles

## File Structure

```
.
├── README.md                     # Project overview and quick start
├── CLAUDE.md                     # This file - development guide
├── LICENSE
├── .env.example                  # Spotify API credentials template
├── .gitignore                    # Git ignore rules
├── requirements-mac.txt          # Python dependencies for Mac
├── requirements-windows.txt      # Python dependencies for Windows
├── SpotifyDevoloperAppPage.png  # Documentation screenshot
│
├── notebooks/                    # Jupyter notebooks for analysis
│   └── 01_Phase1_EDA.ipynb       # Phase 1: Exploratory Data Analysis
│
├── src/                          # Reusable Python modules
│   ├── __init__.py
│   ├── data_processing.py        # Data loading, cleaning, preprocessing
│   ├── feature_engineering.py    # Composite features, context classification
│   └── visualization.py          # Reusable plotting functions
│
├── app/                          # Streamlit application (native multi-page)
│   ├── Home.py                   # Home page and main entry point
│   ├── func/                     # Function modules
│   │   ├── __init__.py           # Exports all functions
│   │   ├── auth.py               # Authentication & OAuth functions
│   │   ├── page_auth.py          # Shared authentication wrapper
│   │   ├── data_fetching.py      # Spotify API data fetching (with caching)
│   │   ├── data_processing.py    # Data transformation & processing
│   │   ├── visualizations.py     # Plotly chart generation (Spotify theming)
│   │   ├── ui_components.py      # Page config, CSS styling
│   │   ├── s3_storage.py         # Cloudflare R2 storage functions
│   │   ├── data_collection.py    # Snapshot collection & metrics
│   │   └── dashboard_helpers.py  # Load current snapshot data for dashboards
│   └── pages/                    # Streamlit pages (auto-discovered)
│       ├── 0_Data_Sync.py        # Onboarding data collection page
│       ├── 1_Dashboard.py        # Main dashboard page
│       ├── 2_Advanced_Analytics.py    # Advanced analytics page
│       ├── 3_Recent_Listening.py      # Recent listening page
│       ├── 4_Top_Tracks.py       # Top tracks page
│       ├── 5_Playlists.py        # Playlists page
│       └── 6_Deep_User.py        # Historical analytics page
│
├── data/                         # Data files (git-ignored except README)
│   ├── README.md                 # Dataset download instructions
│   ├── raw/                      # Kaggle CSVs go here
│   ├── processed/                # Cleaned/processed outputs
│   └── personal/                 # Optional: User's personal Spotify data
│
├── tests/                        # Empty (planned for Phase 2)
│   └── __init__.py
├── models/                       # Empty (Phase 3: Saved ML models)
├── outputs/                      # Empty (generated plots will go here)
└── docs/                         # Project documentation
    ├── notes.md                  # Research notes
    ├── IME565_Project_Proposal_Final.md  # Full project proposal
    └── *.md                      # Additional documentation files
```

**Note**: The `scripts/` directory mentioned in some documentation does not yet exist. Data collection automation is planned for a future phase.

## Git Workflow

**Current Branch Structure:**
- `main`: Production-ready code
- `dev`: Development branch (current)

**Making Changes:**
```bash
# Check current branch and status
git status
git branch

# Before making changes, ensure you're on dev
git checkout dev

# After making changes
git add <files>
git commit -m "descriptive message"

# Push to dev for review before merging to main
git push origin dev

# When ready for production
git checkout main
git merge dev
git push origin main
```

**Note**: Currently on `dev` branch. The app has been fully migrated to Streamlit's native multi-page architecture.

**Important Notes:**
- Always commit with clear, descriptive messages
- Use descriptive branch names for features (e.g., `feature/playlist-health-metrics`)
- Review changes with `git diff` before committing

## Known Issues and Debugging

### Common Errors

**"No data found" on Dashboard Pages (FIXED ✅)**
- **Cause**: Environment variables not loading in multi-page Streamlit apps
- **Impact**: Dashboards can't connect to R2 storage, show "No data found" error
- **Solution**: Added `load_dotenv()` to `s3_storage.py` module (fixed Nov 2025)
- **Code Change**: Import and call `load_dotenv()` at module level in `app/func/s3_storage.py`

**"Failed to load parquet: seek" Error (FIXED ✅)**
- **Cause**: `pandas.read_parquet()` requires seekable file object, S3 stream doesn't support seeking
- **Impact**: Cannot load snapshot data from R2
- **Solution**: Read full content into `BytesIO` before passing to pandas (fixed Nov 2025)
- **Code Change**: `parquet_bytes = response['Body'].read(); pd.read_parquet(io.BytesIO(parquet_bytes))`

**KeyError: 'explicit' in data_collection.py (FIXED ✅)**
- **Cause**: The 'explicit' field is missing from track data when audio features are unavailable (HTTP 403)
- **Impact**: Snapshot collection fails during metrics computation
- **Solution**: Use `safe_mean()` helper for all potentially missing fields in `compute_snapshot_metrics()`
- **Status**: Already implemented with safe accessors throughout the code

**ScriptRunContext Missing Warnings**
- **Cause**: Streamlit's threading model and background data collection
- **Impact**: Console warnings during data sync (can be safely ignored in bare mode)
- **Solution**: These warnings are expected and do not affect functionality

**Audio Features HTTP 403**
- **Cause**: Spotify API access restrictions for this application
- **Impact**: Cannot retrieve audio features for tracks directly via API
- **Workaround**: ✅ **Fully integrated** - Kaggle dataset lookup provides 60-80% coverage via `enrich_with_audio_features()`

### Debugging Data Collection

If data sync fails:
1. Check the browser console and terminal for error messages
2. Look for the specific step where collection failed (recent tracks, top tracks, etc.)
3. Verify R2 credentials are set in `.env`
4. Check that all required fields exist in the data before computing metrics
5. Review `errors.md` for documented issues and solutions

## Data Collection System

### Current Implementation
The app includes an **automatic onboarding data collection** triggered when users first authenticate.

**Onboarding Flow (`0_Data_Sync.py`):**
- Mandatory data sync page shown after authentication
- Rotating Spotify facts displayed during collection
- Real-time progress tracking
- Takes ~60-90 seconds for full collection
- Automatically redirects to dashboard when complete

**What Gets Collected:**
- Recent tracks (50 items) with audio features
- Top tracks for all time ranges (50 items each: short/medium/long term)
- Top artists for all time ranges (50 items each: short/medium/long term)
- Computed metrics (diversity scores, averages, context distributions)

**Storage:**
- Data stored in Cloudflare R2 (S3-compatible) as Parquet files
- Structure: `users/{user_id}/snapshots/{timestamp}_{data_type}.parquet`
- 8 files per snapshot (recent_tracks, 3×top_tracks, 3×top_artists, metrics)

**Rate Limiting:**
- Exponential backoff and retry logic for API calls
- Graceful handling of HTTP 429 (Too Many Requests)
- Progress updates shown to user during collection

## Important Considerations

### Code Style
- **NEVER use emojis in filenames** - causes cross-platform encoding issues
- Use only alphanumeric characters, underscores, and numbers in file/folder names
- Emojis are fine in UI text, markdown, and comments - just not filenames

### Security
- Never commit `.env` file with actual Spotify API credentials
- Client ID and Client Secret should be stored in environment variables
- Use `.gitignore` to exclude sensitive files
- `.spotify_cache/` tokens are also git-ignored for security

### User Experience
- Provide explanations for recommendations (not black-box algorithms)
- Focus on actionable insights over vanity metrics
- Enable ongoing utility (weekly/monthly engagement) vs one-time novelty

### Data Quality and Cleaning Rules
- **Invalid loudness**: Remove tracks with loudness > 0 dB (violates spec, should be negative)
- **Short tracks**: Filter out tracks < 5 seconds (indicates skips or noise)
- **Missing values**: Audio features occasionally null for deleted content (handle in preprocessing)
- **Duplicates**: Check for and remove duplicate track entries
- **Heavy users**: Expect 120,000-174,000 streaming events in personal Spotify data exports
- **Encoding**: CSV files may require different encodings (try utf-8, latin-1, iso-8859-1, cp1252)

## Project Goals

The platform differentiates from existing tools (Stats.fm, Obscurify, Spotify Wrapped) by providing:
1. Deep temporal pattern analysis (weekly/monthly, not just annual)
2. Playlist intelligence with health metrics and optimization
3. Context separation and activity detection
4. Predictive recommendations with explanations
5. Ongoing utility with weekly engagement

## Documentation

For detailed information on specific topics:

- **`README.md`**: Project overview and quick start guide
- **`CLAUDE.md`**: This file - comprehensive development guide for Claude Code
- **`errors.md`**: Known errors, troubleshooting steps, and solutions
- **`docs/IME565_Project_Proposal_Final.md`**: Full project proposal and research foundation
- **`docs/SPOTIFY_API_CAPABILITIES.md`**: Complete API endpoint testing results, limitations, and workarounds
- **`docs/DATA_ARCHITECTURE_RECOMMENDATION.md`**: Original data storage strategy recommendation
- **`docs/DATA_ARCHITECTURE_RECOMMENDATION_REVISED.md`**: Revised data storage strategy with current/ directory
- **`docs/IMPLEMENTATION_SUMMARY.md`**: Summary of recent implementation changes
- **`docs/USER_ANALYTICS_SURVEY.md`**: User analytics features and metrics survey
- **`docs/INTEGRATION_GUIDE.md`**: Cloudflare R2 setup and integration instructions (if exists)
- **`docs/notes.md`**: Research notes and technical patterns
- **`data/README.md`**: Kaggle dataset download instructions

## References

Key research papers informing this project:
- Marey et al. (2024): Activity-driven music listening patterns
- Brinker et al. (2012): Audio features and emotional valence/arousal
- Schedl et al. (2018): Music recommender system challenges

See `docs/IME565_Project_Proposal_Final.md` for full citations.
