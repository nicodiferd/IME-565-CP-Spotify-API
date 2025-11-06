# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a multi-phase Spotify analytics platform project for IME 565 (Predictive Data Analytics for Engineers). The goal is to build a comprehensive music analytics tool that goes beyond Spotify's annual "Wrapped" feature by providing temporal intelligence, playlist optimization, and predictive recommendations.

**Team**: Nicolo DiFerdinando, Joe Mascher, Rithvik Shetty
**Course**: IME 565, Fall Quarter 2025

**Current Phase**: Phase 1 Complete - Real data collection system implemented

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
- **API Integration**: Spotipy (Spotify API wrapper)

## Key Commands

### Environment Setup
```bash
# Option 1: Quick install using shell script (recommended for Mac)
bash install_deps.sh

# Option 2: Manual install with requirements file
pip install -r requirements-mac.txt  # Mac
pip install -r requirements-windows.txt  # Windows

# Option 3: Minimal install (for Python 3.14 compatibility)
bash quick_install.sh

# Set up Spotify API credentials
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
streamlit run app/spotify_dashboard.py

# Run Jupyter notebook for exploratory data analysis
jupyter notebook notebooks/01_Phase1_EDA.ipynb

# Verify installation
python -c 'import pandas, numpy, matplotlib, seaborn, plotly; print("All packages imported successfully!")'
```

### Collecting Real Spotify Data
```bash
# Initial setup: Authenticate each team member (do once)
python scripts/spotify_auth.py --user nicolo
python scripts/spotify_auth.py --user joe
python scripts/spotify_auth.py --user rithvik

# Full collection (run weekly)
python scripts/collect_spotify_data.py --user all
python scripts/enrich_with_audio_features.py --user all
python scripts/merge_team_data.py

# Quick update (recently played only)
python scripts/collect_spotify_data.py --user all --recently-played-only
python scripts/enrich_with_audio_features.py --user all
python scripts/merge_team_data.py

# Output: data/team_listening_history.csv
```

## Architecture Notes

### Code Organization Philosophy

This project follows standard data science practices:
- **`notebooks/`**: Exploration and analysis (Jupyter notebooks)
- **`src/`**: Reusable Python modules (imported by notebooks and app)
- **`app/`**: Production Streamlit dashboard
- **`scripts/`**: Data collection automation (Spotify API)

**Golden Rule**: Extract shared code from notebooks to `src/`, import from both notebooks and app.

### Data Collection Pipeline (scripts/)

The 4-script pipeline collects real team listening data:

1. **`spotify_auth.py`**: OAuth authentication (do once per team member)
   - Multi-user token management
   - Automatic token refresh
   - Browser-based OAuth flow

2. **`collect_spotify_data.py`**: Fetch listening history from Spotify API
   - Recently played tracks (last 50 with timestamps)
   - Top tracks/artists (short/medium/long term)
   - User playlists metadata

3. **`enrich_with_audio_features.py`**: Add audio features and derived metrics
   - Fetch audio features from Spotify API (batched)
   - Fallback to Kaggle database for missing tracks
   - Compute composite scores (mood, grooviness, focus, relaxation)
   - Infer context (workout, focus, party, commute, sleep)
   - Add temporal features (hour, day, weekend, season)

4. **`merge_team_data.py`**: Combine all team members into unified dataset
   - Outputs: `data/team_listening_history.csv`

### Data Processing Modules (src/)

**`data_processing.py`**: Loading and cleaning functions
- `load_spotify_data()`: Auto-detect CSV encoding, load Kaggle datasets
- `clean_dataset()`: Remove duplicates, invalid loudness (>0 dB), short tracks (<5s)
- `identify_audio_features()`: Detect which columns contain audio features

**`feature_engineering.py`**: Composite metrics and classification
- `create_composite_features()`: Mood, grooviness, focus, relaxation scores
- `classify_context()`: Rule-based context categorization (5 categories)
- Formulas use weighted combinations of audio features

**`visualization.py`**: Reusable plotting functions
- `plot_feature_distributions()`: Histograms for audio features
- `plot_correlation_matrix()`: Feature correlation heatmap
- `plot_top_artists_genres()`: Bar charts for top items

### Jupyter Notebook Workflow (notebooks/01_Phase1_EDA.ipynb)

Analysis pipeline:
1. Import from `src/` modules (data_processing, feature_engineering, visualization)
2. Load data using `load_spotify_data()`
3. Clean with `clean_dataset()`
4. Engineer features with `create_composite_features()` and `classify_context()`
5. Visualize using functions from `visualization.py`
6. Export processed data to `data/processed/`

**Key feature columns**:
- Core audio: danceability, energy, valence, acousticness, instrumentalness, speechiness
- Metadata: track_name, artists, album_name, track_genre, popularity
- Composite: mood_score, grooviness, focus_score, relaxation_score, context
- Temporal (from real data): played_at, hour, day_of_week, is_weekend, season

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

### Real Team Listening Data (Primary - Implemented)
**Collected via scripts pipeline**:
- Recently played tracks with timestamps (last 50 per user)
- Top tracks/artists across time ranges (short/medium/long term)
- Complete audio features from Spotify API
- Fallback to Kaggle database for missing features
- **Output**: `data/team_listening_history.csv`
- **Timeline**: Collected weekly throughout project (Weeks 7-10)

### Kaggle Public Datasets (Supplementary)
**For audio feature fallback and benchmarking**:
- Spotify Tracks Dataset: ~114,000 tracks with comprehensive audio features
- Top Spotify Songs 2023: ~50,000 tracks with popularity metrics
- Spotify 1921-2020: 160k+ tracks
- **Location**: `data/raw/` (download manually from Kaggle)
- **Use case**: Enrich team data with features for older/obscure tracks

### Optional: Spotify Privacy Export
- Complete listening history (JSON format, 3-30 days delivery time)
- Provides historical data beyond API's 50-track limit
- **Location**: `data/personal/` if obtained

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
├── README.md                     # Project overview
├── CLAUDE.md                     # This file - development guide
├── LICENSE
├── .env.example                  # Spotify API credentials template
├── .gitignore                    # Git ignore rules
├── requirements-mac.txt          # Python dependencies for Mac
├── requirements-windows.txt      # Python dependencies for Windows
├── install_deps.sh               # Shell script for installing dependencies
├── quick_install.sh              # Minimal install for Python 3.14
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
│   ├── spotify_dashboard.py      # Main Streamlit dashboard (empty - to be built)
│   ├── pages/                    # Multi-page app structure (empty)
│   └── components/               # Reusable UI components (empty)
│
├── scripts/                      # Data collection automation
│   ├── README.md                 # Scripts documentation
│   ├── spotify_auth.py           # OAuth authentication for Spotify API
│   ├── collect_spotify_data.py   # Fetch listening history from Spotify
│   ├── enrich_with_audio_features.py  # Add audio features and metrics
│   └── merge_team_data.py        # Combine team members into unified dataset
│
├── data/                         # Data files (git-ignored except README)
│   ├── README.md                 # Dataset download instructions
│   ├── raw/                      # Original datasets (Kaggle CSVs, Spotify JSON)
│   ├── processed/                # Cleaned/processed data per user
│   ├── personal/                 # User's personal Spotify data (optional)
│   └── team_listening_history.csv  # Final merged team dataset (generated)
│
├── models/                       # Saved ML models (Phase 3)
├── outputs/                      # Generated plots and reports
├── tests/                        # Unit tests (empty - optional)
└── docs/                         # Documentation
    ├── PROJECT_STRUCTURE.md      # Detailed file organization
    ├── QUICK_START_GUIDE.md      # Step-by-step data collection instructions
    ├── SPOTIFY_DATA_COLLECTION_GUIDE.md  # Technical guide
    ├── DATA_STRATEGY_ANALYSIS.md # Why real data vs Kaggle
    ├── IMPLEMENTATION_SUMMARY.md # System overview
    ├── notes.md                  # Research notes
    └── IME565_Project_Proposal_Final.md  # Full project proposal
```

## Important Considerations

### Security
- Never commit `.env` file with actual Spotify API credentials
- Client ID and Client Secret should be stored in environment variables
- Use `.gitignore` to exclude sensitive files

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

- **`docs/QUICK_START_GUIDE.md`**: Step-by-step data collection walkthrough (20-30 min first time)
- **`docs/PROJECT_STRUCTURE.md`**: File organization philosophy and migration guide
- **`docs/SPOTIFY_DATA_COLLECTION_GUIDE.md`**: Complete technical guide to data collection
- **`docs/DATA_STRATEGY_ANALYSIS.md`**: Why real data vs Kaggle synthetic data
- **`docs/IMPLEMENTATION_SUMMARY.md`**: Overview of the data collection system
- **`scripts/README.md`**: Detailed documentation for each collection script
- **`docs/IME565_Project_Proposal_Final.md`**: Full project proposal and research foundation

## References

Key research papers informing this project:
- Marey et al. (2024): Activity-driven music listening patterns
- Brinker et al. (2012): Audio features and emotional valence/arousal
- Schedl et al. (2018): Music recommender system challenges

See `docs/IME565_Project_Proposal_Final.md` for full citations.
