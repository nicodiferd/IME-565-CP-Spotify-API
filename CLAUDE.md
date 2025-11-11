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
- **Streamlit dashboard** (`app/main.py`)
  - OAuth authentication
  - Real-time Spotify data fetching
  - Interactive visualizations
- **Jupyter notebook** (`notebooks/01_Phase1_EDA.ipynb`)
  - Complete EDA workflow

### 📋 Planned (Not Yet Implemented)
- **Streamlit app refactoring** (planned `app/func/` and `app/pages/` directories)
  - Currently all code is in single `main.py` file
  - Will be split into modular structure with separate pages and function modules
  - See "Streamlit App Structure (Planned)" section for details
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

### Adding a New Audio Feature or Composite Metric

1. **Define the metric** in `src/feature_engineering.py`:
```python
def create_composite_features(df: pd.DataFrame) -> pd.DataFrame:
    # Add your new metric
    df['your_metric'] = (0.5 * df['energy'] + 0.5 * df['valence'])
    return df
```

2. **Update visualizations** in `src/visualization.py` if needed

3. **Test in notebook** (`notebooks/01_Phase1_EDA.ipynb`):
```python
df_processed = create_composite_features(df_clean)
print(df_processed['your_metric'].describe())
```

4. **Add to Streamlit dashboard** (`app/main.py`) for interactive display

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
#   SPOTIFY_REDIRECT_URI=http://localhost:8888/callback
# Get credentials from: https://developer.spotify.com/dashboard
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
# Run the Streamlit dashboard
streamlit run app/main.py

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

### Streamlit App Structure (Planned)

The Streamlit dashboard will be organized into a multi-page application with the following structure:

**Main Entry Point:**
- **`app/main.py`**: The main file to run (`streamlit run app/main.py`)
  - Handles app configuration and initialization
  - Manages session state
  - Provides navigation between pages
  - Currently contains all functionality (to be refactored)

**Function Modules (`app/func/`):**
Reusable functions for API calls, data processing, and utilities:
- **`auth.py`**: Spotify OAuth authentication, credential management, token handling
- **`data_fetching.py`**: API calls to Spotify Web API (fetch tracks, artists, playlists, audio features)
- **`data_processing.py`**: Transform API responses into processed DataFrames, apply feature engineering
- **`visualizations.py`**: Plotly chart generation functions for all visualizations

**Page Modules (`app/pages/`):**
Individual Streamlit pages using session state for navigation:
- **`dashboard.py`**: Overview page with key metrics and temporal patterns
- **`analytics.py`**: Advanced analytics with audio features and mood analysis
- **`recent_listening.py`**: Detailed view of recently played tracks
- **`top_tracks.py`**: Top tracks across different time ranges
- **`playlists.py`**: Playlist overview and management
- **`deep_user.py`**: Historical analytics page showing long-term trends and patterns

**Design Principles:**
- Use `st.session_state` for navigation and shared data between pages
- Import functions from `app/func/` modules (avoid duplicating code across pages)
- Each page module should be self-contained and focused on a single feature area
- Keep `main.py` as the main orchestrator (routing, auth flow, sidebar)

### Data Collection & Storage (Deep User Analytics)

The app automatically collects and stores user listening data to enable longitudinal analysis:

**Storage Backend:**
- **Cloudflare R2** (S3-compatible object storage)
- Parquet file format for efficient storage and querying
- Organized by user ID and timestamp

**Data Collection Trigger:**
- Automatically collects data on every app session (when user authenticates)
- Captures: recently played tracks, top tracks/artists (all time ranges), computed metrics
- Stored in R2 bucket with structure: `users/{user_id}/snapshots/{timestamp}_{data_type}.parquet`

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
# Required
R2_ACCESS_KEY_ID=your_r2_access_key_id
R2_SECRET_ACCESS_KEY=your_r2_secret_access_key
R2_BUCKET_NAME=ime565spotify

# Use custom domain (recommended) OR account ID
R2_CUSTOM_DOMAIN=s3.diferdinando.com
# CLOUDFLARE_ACCOUNT_ID=24df8bb5d20dca402dfc277d4c38cc80
```

**Your R2 Bucket Configuration:**
- Bucket Name: `ime565spotify`
- Custom Domain: `s3.diferdinando.com` (configured with TLS 1.0)
- Region: Western North America (WNAM)
- Account ID: `24df8bb5d20dca402dfc277d4c38cc80`

See `R2_SETUP.md` for detailed setup instructions.

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

5. **Streamlit Dashboard** (`app/main.py`)
   - OAuth authentication with Spotify API
   - Session-based token management (multi-user support)
   - Interactive visualizations with Plotly
   - Real-time data fetching from user's Spotify account


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
- Batch requests: Spotify allows up to 100 tracks per audio features request
- Throttle to stay below 2 requests per second (limit is ~180 requests per minute)

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

### Composite Feature Engineering
- **Mood Score**: Combine valence, energy, and acousticness for emotional profile
- **Grooviness Index**: Merge danceability, energy, and tempo
- **Focus Suitability**: Weight low speechiness, moderate energy, high instrumentalness

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
├── app/                          # Streamlit application
│   ├── main.py      # Main entry point - run this file
│   ├── func/                     # Function modules (planned structure)
│   │   ├── __init__.py
│   │   ├── auth.py               # Authentication & OAuth functions
│   │   ├── data_fetching.py      # Spotify API data fetching
│   │   ├── data_processing.py    # Data transformation & processing
│   │   └── visualizations.py     # Plotting and chart functions
│   └── pages/                    # Streamlit pages (planned structure)
│       ├── __init__.py
│       ├── dashboard.py          # Main dashboard page
│       ├── analytics.py          # Advanced analytics page
│       ├── recent_listening.py   # Recent listening page
│       ├── top_tracks.py         # Top tracks page
│       └── playlists.py          # Playlists page
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

**Important Notes:**
- Always commit with clear, descriptive messages
- Use descriptive branch names for features (e.g., `feature/playlist-health-metrics`)
- Review changes with `git diff` before committing

## Important Considerations

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
- **`docs/IME565_Project_Proposal_Final.md`**: Full project proposal and research foundation
- **`docs/notes.md`**: Research notes and technical patterns
- **`data/README.md`**: Kaggle dataset download instructions

## References

Key research papers informing this project:
- Marey et al. (2024): Activity-driven music listening patterns
- Brinker et al. (2012): Audio features and emotional valence/arousal
- Schedl et al. (2018): Music recommender system challenges

See `docs/IME565_Project_Proposal_Final.md` for full citations.
