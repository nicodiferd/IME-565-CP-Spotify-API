# Project Structure and File Organization

## Overview

This project follows standard data science practices: **notebooks for exploration/analysis**, **Python scripts for production code**.

---

## Directory Structure

```
IME-565-CP-Spotify-API/
├── README.md                          # Project overview (keep updated)
├── CLAUDE.md                          # Development guide for Claude Code
├── PROJECT_STRUCTURE.md               # This file - explains organization
├── LICENSE
├── .gitignore
├── .env.example                       # Spotify API credentials template
│
├── requirements-mac.txt               # Dependencies for Mac
├── requirements-windows.txt           # Dependencies for Windows
├── install_deps.sh                    # Installation script
├── quick_install.sh                   # Minimal install for Python 3.14
│
├── notebooks/                         # 📓 Jupyter notebooks (analysis & exploration)
│   ├── 01_Phase1_EDA.ipynb           # Phase 1: Exploratory Data Analysis
│   ├── 02_Phase2_Playlist_Analysis.ipynb  # Phase 2: Playlist Intelligence
│   └── 03_Phase3_ML_Models.ipynb     # Phase 3: Predictive Modeling
│
├── src/                               # 🐍 Python source code (reusable modules)
│   ├── __init__.py
│   ├── data_processing.py            # Data loading, cleaning, preprocessing
│   ├── feature_engineering.py        # Composite features, context classification
│   ├── visualization.py              # Reusable plotting functions
│   ├── spotify_auth.py               # Spotify API authentication helpers
│   └── utils.py                      # General utility functions
│
├── app/                               # 🎨 Streamlit application
│   ├── spotify_dashboard.py          # Main Streamlit app
│   ├── pages/                        # Multi-page app structure
│   │   ├── 1_Overview.py
│   │   ├── 2_Audio_Features.py
│   │   ├── 3_Playlists.py
│   │   └── 4_Predictions.py
│   └── components/                   # Reusable UI components
│       ├── charts.py
│       └── sidebar.py
│
├── data/                              # 📊 Data files (gitignored except README)
│   ├── README.md                     # Dataset download instructions
│   ├── raw/                          # Original datasets
│   │   ├── dataset.csv
│   │   ├── spotify-2023.csv
│   │   └── artists.csv
│   ├── processed/                    # Cleaned/processed data
│   │   └── processed_spotify_data.csv
│   └── personal/                     # User's personal Spotify data (optional)
│       └── .gitkeep
│
├── models/                            # 🤖 Saved ML models (Phase 3)
│   └── .gitkeep
│
├── outputs/                           # 📈 Generated plots, reports
│   ├── figures/
│   └── reports/
│
├── tests/                             # 🧪 Unit tests (optional but recommended)
│   ├── __init__.py
│   ├── test_data_processing.py
│   └── test_feature_engineering.py
│
└── docs/                              # 📚 Documentation
    ├── notes.md                      # Research notes
    └── IME565_Project_Proposal_Final.md
```

---

## File Purposes

### Notebooks (`.ipynb`) - For Exploration & Analysis

**Use notebooks when:**
- Exploring data for the first time
- Creating visualizations for presentations
- Documenting analysis workflow
- Iterating on models and features
- Generating reports

**Current notebooks:**
- `Spotify.ipynb` → Will become `notebooks/01_Phase1_EDA.ipynb`

**Future notebooks:**
- `notebooks/02_Phase2_Playlist_Analysis.ipynb` - Playlist health, overlap detection
- `notebooks/03_Phase3_ML_Models.ipynb` - Model training, evaluation, predictions

### Python Scripts (`.py`) - For Production & Reusability

**Use Python scripts when:**
- Building production applications (Streamlit)
- Creating reusable functions used across notebooks
- Deploying models
- Implementing APIs or web services

**Current scripts:**
- `spotify app.py` → Will become `app/spotify_dashboard.py`

**Future scripts:**
- `src/data_processing.py` - Extract data loading logic from notebooks
- `src/feature_engineering.py` - Composite features, classification
- `src/visualization.py` - Reusable plotting functions
- `app/spotify_dashboard.py` - Main Streamlit dashboard

---

## Development Workflow

### Phase 1: Foundation (Current)
```
1. Explore in notebook: notebooks/01_Phase1_EDA.ipynb ✅
2. Extract reusable functions → src/data_processing.py
3. Build basic Streamlit dashboard → app/spotify_dashboard.py
4. Present findings from notebook
```

### Phase 2: Playlist Intelligence
```
1. Analyze in notebook: notebooks/02_Phase2_Playlist_Analysis.ipynb
2. Extract playlist logic → src/playlist_analyzer.py
3. Add playlist page to dashboard → app/pages/3_Playlists.py
4. Integrate with existing dashboard
```

### Phase 3: Predictive Modeling
```
1. Train models in notebook: notebooks/03_Phase3_ML_Models.ipynb
2. Extract model code → src/models.py
3. Save trained models → models/
4. Add predictions page → app/pages/4_Predictions.py
5. Deploy final dashboard
```

---

## Best Practices

### 1. Notebooks
- ✅ Keep one notebook per major analysis phase
- ✅ Use clear section headers (markdown cells)
- ✅ Document findings and insights inline
- ✅ Include visualizations and interpretations
- ✅ Can be messy during exploration
- ❌ Don't put production code in notebooks

### 2. Python Scripts
- ✅ Write clean, modular, reusable functions
- ✅ Add docstrings to all functions
- ✅ Follow PEP 8 style guidelines
- ✅ Keep files focused (single responsibility)
- ✅ Import from src/ modules in notebooks and app
- ❌ Don't duplicate code between files

### 3. Data
- ✅ Keep raw data separate from processed data
- ✅ Never commit large CSV files (use .gitignore)
- ✅ Document data sources in data/README.md
- ✅ Use consistent naming conventions

### 4. Code Reuse
**Extract common code from notebooks to src/**

Example:
```python
# In notebook: notebooks/01_Phase1_EDA.ipynb
from src.data_processing import load_spotify_data, clean_dataset
from src.feature_engineering import create_composite_features

# Load and process data
df = load_spotify_data('data/raw/dataset.csv')
df_clean = clean_dataset(df)
df_clean = create_composite_features(df_clean)
```

---

## Migration Plan

### Step 1: Reorganize Current Files (Immediate)
```bash
# Create new directory structure
mkdir -p notebooks src app data/{raw,processed,personal} models outputs/{figures,reports} tests docs

# Move existing files
mv Spotify.ipynb notebooks/01_Phase1_EDA.ipynb
mv "spotify app.py" app/spotify_dashboard.py
mv notes.md docs/
mv IME565_Project_Proposal_Final.md docs/

# Organize data files
mv data/*.csv data/raw/
```

### Step 2: Extract Reusable Code (Next)
- Create `src/data_processing.py` with loading/cleaning functions
- Create `src/feature_engineering.py` with composite features
- Update notebook to import from src/

### Step 3: Build Streamlit App (Phase 1 completion)
- Implement basic dashboard in `app/spotify_dashboard.py`
- Use functions from src/ modules
- Display Phase 1 insights

### Step 4: Continue Through Phases
- Add new notebooks for Phase 2 and 3
- Extract code to src/ as patterns emerge
- Expand Streamlit app with new pages

---

## Git Strategy

### What to Commit
- ✅ All `.py` files in src/ and app/
- ✅ All `.ipynb` files in notebooks/
- ✅ README.md, requirements.txt, .gitignore
- ✅ Small data files (< 1 MB)

### What to Ignore (.gitignore)
- ❌ .env (contains secrets)
- ❌ venv/ (virtual environment)
- ❌ data/*.csv (large datasets)
- ❌ __pycache__/ (Python cache)
- ❌ .ipynb_checkpoints/ (Jupyter cache)
- ❌ models/*.pkl (trained models - too large)

---

## When to Create New Files

### Create a new notebook when:
- Starting a new analysis phase
- Exploring a completely different dataset
- Trying experimental approaches

### Create a new .py module when:
- You've written the same code in 2+ places
- A notebook cell exceeds ~50 lines
- You need the code in both notebook and Streamlit
- Building a new feature (playlists, predictions)

### Don't create new files when:
- Small one-off functions (keep in notebook)
- Highly specific to one analysis
- Still experimenting/iterating

---

## Current Status

### Completed
- ✅ Main analysis notebook (Spotify.ipynb)
- ✅ Data loading and cleaning pipeline
- ✅ Feature engineering (composite scores)
- ✅ Context classification
- ✅ Visualizations and EDA

### Next Steps
1. **Reorganize** files into proper structure
2. **Extract** reusable functions to src/
3. **Build** Streamlit dashboard using extracted functions
4. **Document** each module with docstrings
5. **Test** that everything still works

---

## Questions to Consider

**Q: Should I keep one large notebook or split by phase?**
A: Split by phase (one per phase). Easier to navigate, clearer documentation.

**Q: When do I move code from notebook to .py?**
A: When you need it in multiple places OR when building the Streamlit app.

**Q: Can notebooks import from src/?**
A: Yes! That's the recommended pattern. Notebooks stay clean, code is reusable.

**Q: Where does the Streamlit app code go?**
A: In `app/spotify_dashboard.py`. Import functions from `src/`.

**Q: Should I commit processed data?**
A: Only if < 10 MB. Otherwise, regenerate from raw data using notebooks.

---

## Summary

**Golden Rule**:
- **Notebooks** = Exploration, Analysis, Documentation, Presentation
- **Python Scripts** = Production Code, Reusability, Deployment

**Keep both!** They serve different purposes. Extract shared code to `src/`, reference it from both notebooks and Streamlit app.
