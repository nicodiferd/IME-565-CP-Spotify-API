# Beyond Wrapped: Spotify Analytics Platform

**IME 565 - Predictive Data Analytics for Engineers**
**Team**: Nicolo DiFerdinando, Joe Mascher, Rithvik Shetty
**Fall Quarter 2025**

A comprehensive music analytics platform that goes beyond Spotify's annual "Wrapped" feature by providing temporal intelligence, playlist optimization, and predictive recommendations.

---

## 🎯 Project Overview

This project addresses critical gaps in existing music analytics tools by providing:
- **Temporal Pattern Analysis**: Weekly/monthly insights, not just annual summaries
- **Playlist Intelligence**: Health metrics, overlap detection, optimization recommendations
- **Context Separation**: Distinguish workout, focus, relaxation, and party music
- **Predictive Recommendations**: ML-powered suggestions with explainability
- **Ongoing Utility**: Weekly engagement instead of one-time novelty

---

## 📁 Project Structure

```
├── notebooks/              # Jupyter notebooks for analysis
│   └── 01_Phase1_EDA.ipynb
├── src/                    # Reusable Python modules
│   ├── data_processing.py
│   ├── feature_engineering.py
│   └── visualization.py
├── app/                    # Streamlit dashboard
│   ├── main.py            # Main app entry point
│   ├── func/              # Utility functions (auth, data fetching, S3)
│   └── pages/             # Dashboard pages (deep_user.py, etc.)
├── data/                   # Data files
│   ├── raw/               # Original datasets
│   ├── processed/         # Cleaned data
│   └── personal/          # User's personal data (optional)
├── docs/                   # Documentation
├── models/                 # Saved ML models (Phase 3)
└── outputs/                # Generated plots and reports
```

See [docs/PROJECT_STRUCTURE.md](docs/PROJECT_STRUCTURE.md) for detailed organization.

---

## 🚀 Quick Start

### 1. Environment Setup

```bash
# Clone the repository
git clone <repo-url>
cd IME-565-CP-Spotify-API

# Create virtual environment with Python 3.12 (recommended)
python3.12 -m venv venv
source venv/bin/activate  # On Mac/Linux
# venv\Scripts\activate   # On Windows

# Install dependencies
bash install_deps.sh  # Mac
# pip install -r requirements-windows.txt  # Windows
```

### 2. Data Acquisition

Download at least one dataset from Kaggle:
- [Spotify Tracks Dataset](https://www.kaggle.com/datasets/maharshipandya/-spotify-tracks-dataset) (~114k tracks) **[Recommended]**
- [Top Spotify Songs 2023](https://www.kaggle.com/datasets/nelgiriyewithana/top-spotify-songs-2023)
- [Spotify 1921-2020](https://www.kaggle.com/datasets/yamaerenay/spotify-dataset-19212020-600k-tracks) (160k+ tracks)

Place downloaded CSV files in `data/raw/` directory.

### 3. Run Analysis

```bash
# Option 1: Jupyter Notebook (exploration & analysis)
jupyter notebook notebooks/01_Phase1_EDA.ipynb

# Option 2: Streamlit Dashboard (interactive visualization)
streamlit run app/main.py
```

---

## 📊 Phase 1: Foundation Analytics (Current)

### What's Included

**Data Processing:**
- Multi-encoding CSV loader (handles UTF-8, Latin-1, etc.)
- Data cleaning (remove duplicates, invalid values, short tracks)
- Audio feature identification and validation

**Feature Engineering:**
- **Mood Score**: Happiness/energy metric (valence + energy + acousticness)
- **Grooviness**: Danceability/upbeat quality (danceability + energy + tempo)
- **Focus Score**: Concentration suitability (low speechiness, high instrumentalness)
- **Relaxation Score**: Calmness quality (low energy, high acousticness, low tempo)

**Context Classification:**
- Workout (high energy + high danceability)
- Focus (low speechiness + high instrumentalness)
- Relaxation (low energy + high acousticness)
- Party (high valence + high energy + high danceability)
- General (default)

**Visualizations:**
- Audio feature distributions and correlations
- Top artists, genres, and tracks
- Context distribution analysis
- Interactive Streamlit dashboard

**🆕 Deep User Analytics:**
- **Automatic data collection**: Snapshots saved to Cloudflare R2 on every login
- **Historical tracking**: Monitor your listening habits over time
- **Artist evolution**: See how your top artists change week-to-week
- **Listening patterns**: Temporal analysis of when and what you listen to
- **Team comparison**: Compare listening habits with teammates (coming soon)
- **Metrics over time**: Track audio features, diversity scores, and context distributions

See [docs/INTEGRATION_GUIDE.md](docs/INTEGRATION_GUIDE.md) for setup instructions.

### Key Results (114,000 tracks analyzed)

- 13 audio features per track
- 4 composite features engineered
- 5 listening contexts classified
- Top genres and artists identified
- Processed dataset exported for Phase 2

---

## 🔮 Roadmap

### Phase 2: Playlist Intelligence (Weeks 8-9)
- Playlist health metrics (save-to-play ratio, recency scores)
- Cross-playlist overlap detection
- Freshness analysis and optimization recommendations
- Dead playlist identification

### Phase 3: Predictive Modeling (Week 10+)
- Random Forest & XGBoost models (target: 75-80% accuracy)
- Ensemble predictions for music preferences
- Automated activity classification
- Explainable recommendations with SHAP values
- Mood trajectory tracking

---

## 🛠️ Tech Stack

- **Data Processing**: pandas, numpy
- **Visualization**: matplotlib, seaborn, plotly
- **Machine Learning**: scikit-learn, XGBoost, scipy
- **Dashboard**: Streamlit
- **API Integration**: Spotipy (Spotify Web API)

---

## 📚 Documentation

- [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md) - Detailed file organization
- [CLAUDE.md](CLAUDE.md) - Development guide
- [docs/IME565_Project_Proposal_Final.md](docs/IME565_Project_Proposal_Final.md) - Full project proposal
- [docs/notes.md](docs/notes.md) - Research notes and technical patterns

---

## 🎵 Audio Features Explained

| Feature | Range | Description |
|---------|-------|-------------|
| **danceability** | 0.0-1.0 | Suitability for dancing based on tempo, rhythm, beat strength |
| **energy** | 0.0-1.0 | Intensity and activity level |
| **valence** | 0.0-1.0 | Musical positiveness (happy vs sad) |
| **acousticness** | 0.0-1.0 | Likelihood of being acoustic |
| **instrumentalness** | 0.0-1.0 | Predicts lack of vocals |
| **speechiness** | 0.0-1.0 | Presence of spoken words |
| **tempo** | BPM | Beats per minute |
| **loudness** | dB | Overall loudness (negative values) |

---

## 🤝 Contributing

This is an academic project for IME 565. For questions or suggestions:
- Open an issue on GitHub
- Contact team members

---

## 📄 License

See [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- **Course**: IME 565 - Predictive Data Analytics for Engineers
- **Institution**: [Your University]
- **Instructor**: [Instructor Name]
- **Datasets**: Kaggle Community & Spotify for Developers
- **Research**: Academic papers on music information retrieval and recommendation systems

---

**Built with ❤️ and 🎵 by Team [Your Team Name]**
