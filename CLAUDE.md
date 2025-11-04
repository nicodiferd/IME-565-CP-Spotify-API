# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a multi-phase Spotify analytics platform project for IME 565 (Predictive Data Analytics for Engineers). The goal is to build a comprehensive music analytics tool that goes beyond Spotify's annual "Wrapped" feature by providing temporal intelligence, playlist optimization, and predictive recommendations.

**Team**: Nicolo DiFerdinando, Joe Mascher, Rithvik Shetty
**Course**: IME 565, Fall Quarter 2025

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
# Run the Streamlit app (main dashboard)
streamlit run "spotify app.py"

# Run Jupyter notebook for data exploration
jupyter notebook Spotify.ipynb

# Verify installation
python -c 'import pandas, numpy, matplotlib, seaborn, plotly; print("All packages imported successfully!")'
```

## Architecture Notes

### Jupyter Notebook Workflow (Spotify.ipynb)

The main analysis notebook follows this pipeline:
1. **Data Loading**: Auto-detects CSV files in `data/` directory, tries multiple encodings
2. **Data Cleaning**: Removes duplicates, invalid loudness values (>0 dB), tracks <5 seconds
3. **Feature Engineering**: Creates composite metrics (mood_score, grooviness, focus_score, relaxation_score)
4. **Context Classification**: Rule-based categorization into Workout, Focus, Relaxation, Party, General
5. **Visualization**: Distributions, correlations, top artists/genres
6. **Export**: Saves processed data to `data/processed_spotify_data.csv`

**Key feature columns**:
- Core audio: danceability, energy, valence, acousticness, instrumentalness, speechiness
- Metadata: track_name, artists, album_name, track_genre, popularity
- Composite: mood_score, grooviness, focus_score, relaxation_score, context

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

### Phase 1 (Public Datasets)
- Spotify Tracks Dataset: ~114,000 tracks with comprehensive audio features
- Top Spotify Songs datasets: 50,000-170,000 tracks with popularity metrics
- Available on Kaggle

### Phase 2-3 (User Data)
- Spotify API Recent History: Last 50 tracks via recently-played endpoint
- Privacy Export Data: Complete listening history (JSON format, 3-30 days delivery time)

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
├── spotify app.py                # Main Streamlit application (currently empty)
├── Spotify.ipynb                 # Data exploration and analysis notebook
├── requirements-mac.txt          # Python dependencies for Mac
├── requirements-windows.txt      # Python dependencies for Windows
├── install_deps.sh               # Shell script for installing dependencies
├── quick_install.sh              # Minimal install for Python 3.14
├── .env.example                  # Spotify API credentials template
├── .gitignore                    # Git ignore rules
├── notes.md                      # Research notes and technical patterns
├── IME565_Project_Proposal_Final.md  # Full project proposal
├── data/
│   ├── README.md                 # Instructions for downloading datasets
│   ├── dataset.csv               # Main Spotify tracks dataset (114k tracks)
│   ├── spotify-2023.csv          # Top songs 2023
│   ├── artists.csv               # Artist metadata (large file)
│   └── processed_spotify_data.csv # Output from Spotify.ipynb (generated)
└── README.md                     # Project overview
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

## References

Key research papers informing this project:
- Marey et al. (2024): Activity-driven music listening patterns
- Brinker et al. (2012): Audio features and emotional valence/arousal
- Schedl et al. (2018): Music recommender system challenges

See `IME565_Project_Proposal_Final.md` for full citations and research foundation.
