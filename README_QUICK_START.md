# Quick Start Guide - Spotify Analytics Project

**For**: Team members new to the codebase
**Time to Setup**: 10 minutes
**Presentation**: December 2-4, 2025

---

## 1. Get Started (5 minutes)

```bash
# Clone the repo
git clone https://github.com/nicodiferd/IME-565-CP-Spotify-API.git
cd IME-565-CP-Spotify-API

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # Mac/Linux
# venv\Scripts\activate   # Windows

# Install dependencies
pip install -r requirements-mac.txt    # Mac
# pip install -r requirements-windows.txt  # Windows

# Copy environment variables
cp .env.example .env
# Edit .env and add the Spotify credentials (ask Nicolo)
```

---

## 2. Run the App (2 minutes)

```bash
# Start the dashboard
streamlit run app/Home.py

# Opens in browser at http://localhost:8501
# Click "Connect Spotify" and login
```

---

## 3. Understanding the Project

### What We Built
A Spotify analytics dashboard that shows:
- Your listening patterns (when you listen to what)
- Audio features of your music (energy, mood, danceability)
- Top tracks and artists over different time periods
- Playlist organization insights

### Why It's Cool
- Unlike Spotify Wrapped (once a year), this updates daily
- Shows patterns Spotify doesn't (mood trajectories, context detection)
- Stores historical data to track changes over time

---

## 4. Where You Can Contribute (Pick One)

### Option A: Machine Learning Demo (EASIEST)
**File**: Create `notebooks/03_ML_Demo.ipynb`
**Task**: Build a Random Forest to predict genre from audio features
```python
# Starter code:
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split

# Load the Kaggle dataset
df = pd.read_csv('data/raw/dataset.csv')

# Select features and target
features = ['danceability', 'energy', 'loudness', 'speechiness',
            'acousticness', 'instrumentalness', 'liveness', 'valence', 'tempo']
X = df[features]
y = df['track_genre']  # or 'popularity' for regression

# Train model
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2)
model = RandomForestClassifier()
model.fit(X_train, y_train)

# Show results
print(f"Accuracy: {model.score(X_test, y_test)}")
```

### Option B: Add a Visualization
**File**: `app/func/visualizations.py`
**Task**: Add a new chart function
```python
def plot_your_new_chart(df):
    """
    Create a new visualization.
    Look at existing functions for the pattern.
    """
    fig = go.Figure()
    # Add your visualization logic
    return fig
```

### Option C: Improve Playlist Page
**File**: `app/pages/5_Playlists.py`
**Task**: Add playlist statistics (track count, total duration, etc.)

### Option D: Write Documentation
**File**: Create `docs/USER_GUIDE.md`
**Task**: Write a user guide explaining what each dashboard page shows

---

## 5. Project Structure (Simplified)

```
The Important Stuff:
├── app/
│   ├── Home.py              # Main entry point (DON'T MODIFY)
│   ├── pages/               # Dashboard pages (CAN MODIFY)
│   │   ├── 1_Dashboard.py   # Overview page
│   │   ├── 2_Advanced_Analytics.py
│   │   ├── 3_Recent_Listening.py
│   │   ├── 4_Top_Tracks.py
│   │   ├── 5_Playlists.py   # GOOD PLACE TO ADD FEATURES
│   │   └── 6_Deep_User.py
│   └── func/                # Core functions (BE CAREFUL)
│       └── visualizations.py # ADD NEW CHARTS HERE
│
├── notebooks/               # Jupyter notebooks
│   └── [CREATE ML DEMO HERE]
│
└── data/
    └── raw/                 # Kaggle datasets
        └── dataset.csv      # 114k tracks with audio features
```

---

## 6. Key Concepts

### Audio Features (What Spotify provides)
- **Danceability**: How suitable for dancing (0-1)
- **Energy**: Intensity and activity (0-1)
- **Valence**: Musical positivity/happiness (0-1)
- **Tempo**: Beats per minute
- **Acousticness**: Likelihood of being acoustic (0-1)

### Our Composite Features
- **Mood Score**: Combination of valence + energy
- **Grooviness**: Danceability + tempo
- **Focus Score**: Low speechiness + moderate energy
- **Context**: Workout, Party, Focus, Relaxation, General

---

## 7. Testing Your Changes

```bash
# After making changes, restart the app
# Ctrl+C to stop
streamlit run app/Home.py

# Check for errors in terminal
# Refresh browser to see changes
```

---

## 8. Common Issues

### "Module not found" Error
```bash
pip install [missing-module]
```

### "No data found" on Dashboard
- You need to authenticate first
- Click "Connect Spotify" on home page
- Wait for data sync to complete

### Environment Variables Not Loading
```bash
# Make sure .env file exists and has:
SPOTIFY_CLIENT_ID=xxx
SPOTIFY_CLIENT_SECRET=xxx
SPOTIFY_REDIRECT_URI=http://127.0.0.1:8501/
```

---

## 9. For Presentation Prep

### What You Should Know
1. **Phase 1** (Complete): Basic analytics dashboard
2. **Phase 2** (In Progress): Playlist intelligence
3. **Phase 3** (Demo Only): Machine learning predictions

### Key Achievements
- 3,200+ lines of production code
- Real Spotify integration
- Cloud storage (Cloudflare R2)
- 114k track enrichment database
- Multi-user support

### Your Contribution Focus
Pick ONE thing from Section 4 and do it well. Quality > Quantity.

---

## 10. Contact

**Questions?** Ask in team chat or:
- **Nicolo**: Project lead, knows all code
- **Repo**: github.com/nicodiferd/IME-565-CP-Spotify-API
- **Docs**: See `docs/` folder for detailed documentation

**Remember**: You don't need to understand everything. Pick one area and contribute there!