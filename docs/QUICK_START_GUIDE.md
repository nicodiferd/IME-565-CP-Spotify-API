# Quick Start: Collecting Real Spotify Data

**Time Required**: 20-30 minutes (first time), 5 minutes (recurring)
**Team Coordination**: Each member does steps 1-2 once, then one person runs collection

---

## Step-by-Step Instructions

### 1. **Set Up Spotify Developer Account** (5 minutes per person)

**Each team member needs to do this individually**:

1. Go to: https://developer.spotify.com/dashboard
2. Log in with your Spotify account
3. Click "Create App"
   - App Name: `IME565 Spotify Analytics - [Your Name]`
   - App Description: `Course project - music analytics`
   - Redirect URI: `http://localhost:8888/callback`
   - API: Web API
4. Click "Save"
5. Click "Settings"
6. **Copy your Client ID and Client Secret** (you'll need these next)

---

### 2. **Create Your .env File** (2 minutes per person)

**Each team member creates their own .env file**:

```bash
# Navigate to project directory
cd "/Users/nicolodiferdinando/Desktop/School/Semesters/Fall25/IME 565/IME-565-CP-Spotify-API"

# Create your personal .env file
# Replace "nicolo" with your name (joe or rithvik)
cp .env.example .env.nicolo

# Edit the file with your credentials
nano .env.nicolo
```

**File contents** (.env.nicolo):
```bash
SPOTIFY_CLIENT_ID=your_client_id_from_step_1
SPOTIFY_CLIENT_SECRET=your_client_secret_from_step_1
SPOTIFY_REDIRECT_URI=http://localhost:8888/callback
USER_NAME=nicolo
USER_ID=1
```

**Save and exit**: Press `Ctrl+X`, then `Y`, then `Enter`

Repeat for Joe and Rithvik with `.env.joe` and `.env.rithvik`

---

### 3. **First-Time Authentication** (3 minutes per person)

**Each team member needs to authenticate once**:

```bash
# Activate virtual environment
source venv/bin/activate

# Authenticate (replace "nicolo" with your name)
python scripts/spotify_auth.py --user nicolo
```

**What happens**:
1. Browser will open automatically
2. Spotify will ask you to authorize the app
3. Click "Agree"
4. You'll be redirected to localhost (may show "can't connect" - that's OK!)
5. Terminal will show "✓ Successfully authenticated"

**Troubleshooting**:
- If browser doesn't open: Check the terminal for a URL, copy and paste it into browser
- If "Invalid Redirect URI": Go back to Spotify Dashboard → Settings → Make sure it's exactly `http://localhost:8888/callback`

---

### 4. **Collect Data** (5-10 minutes)

**One team member can run this for everyone** (after all have authenticated):

```bash
# Full collection (first time)
python scripts/collect_spotify_data.py --user all

# This fetches:
#   - Recently played tracks (last 50)
#   - Top tracks (3 time ranges = ~150 tracks)
#   - Top artists (3 time ranges)
#   - User playlists
```

**Quick collection** (for recurring updates):
```bash
# Just recently played (faster, for weekly updates)
python scripts/collect_spotify_data.py --user all --recently-played-only
```

---

### 5. **Enrich with Audio Features** (3-5 minutes)

```bash
# Add audio features from Spotify API + Kaggle database
python scripts/enrich_with_audio_features.py --user all
```

This adds:
- Danceability, energy, valence, tempo, etc.
- Composite scores (mood, grooviness, focus, relaxation)
- Temporal features (hour, day of week, time period)
- Context inference (workout, focus, party, etc.)

---

### 6. **Merge Team Data** (1 minute)

```bash
# Combine all 3 team members into one dataset
python scripts/merge_team_data.py
```

**Output**: `data/team_listening_history.csv`

This is your **final dataset** ready for analysis!

---

### 7. **Analyze in Jupyter Notebook** (10+ minutes)

```bash
# Start Jupyter
jupyter notebook Spotify.ipynb
```

**Update the notebook** to load your real data:
```python
# Replace this line:
df = pd.read_csv('data/processed_spotify_data.csv')

# With this:
df = pd.read_csv('data/team_listening_history.csv')
```

Now run all temporal analysis cells to see:
- When each team member listens to music
- Context patterns (workout, focus, relaxation)
- Mood trajectories over time
- Hour-of-day and day-of-week patterns

---

## Complete Command Sequence

**For copy-paste convenience** (after initial setup):

```bash
# Navigate to project
cd "/Users/nicolodiferdinando/Desktop/School/Semesters/Fall25/IME 565/IME-565-CP-Spotify-API"

# Activate environment
source venv/bin/activate

# Collect data from all team members
python scripts/collect_spotify_data.py --user all

# Enrich with audio features
python scripts/enrich_with_audio_features.py --user all

# Merge into unified dataset
python scripts/merge_team_data.py

# Open notebook
jupyter notebook Spotify.ipynb
```

**Time**: ~10 minutes total

---

## Weekly Collection Strategy

To build a rich dataset over the semester:

**Week 7 (Initial)**: Full collection
```bash
python scripts/collect_spotify_data.py --user all
python scripts/enrich_with_audio_features.py --user all
python scripts/merge_team_data.py
```

**Weeks 8-10 (Updates)**: Quick collection
```bash
python scripts/collect_spotify_data.py --user all --recently-played-only
python scripts/enrich_with_audio_features.py --user all
python scripts/merge_team_data.py
```

Each week adds ~100-150 new listening events!

---

## What You Get

### Initial Collection (Week 7)
- **150** recently played tracks (50 per person × 3)
- **~400-500** unique tracks total
- **Complete audio features** for all tracks
- **Temporal data** spanning last 1-3 days

### After 4 Weeks (Week 10)
- **600-1200** listening events with timestamps
- **Rich temporal patterns** across weeks
- **Context diversity** (weekday vs weekend, morning vs evening)
- **Publication-quality dataset**

---

## Troubleshooting

### "ModuleNotFoundError: No module named 'spotipy'"
```bash
# Install dependencies
pip install -r requirements-mac.txt
```

### "Authentication failed"
```bash
# Delete cached token and try again
rm -rf .spotify_cache
python scripts/spotify_auth.py --user nicolo --force-refresh
```

### "No recently played data"
- Play some songs on Spotify
- Wait 5-10 minutes
- Run collection again

### "Missing audio features"
- Normal for ~5-10% of tracks
- Fallback to Kaggle database will handle most
- See logs for which tracks are missing

---

## Expected Output

```
data/
├── raw/
│   ├── nicolo_recently_played.json
│   ├── nicolo_top_tracks_all.json
│   ├── nicolo_playlists.json
│   ├── joe_recently_played.json
│   ├── ...
├── processed/
│   ├── nicolo_listening_history.csv
│   ├── joe_listening_history.csv
│   ├── rithvik_listening_history.csv
└── team_listening_history.csv  ← **YOUR FINAL DATASET**
```

---

## Next Steps

1. **Week 7**: Complete initial collection (all team members)
2. **Week 8-9**: Weekly updates (just recently played)
3. **Week 10**: Final collection + analysis for presentation
4. **Optional**: Request full Spotify export for historical data (takes 3-30 days)

---

## Questions?

- Check: `docs/SPOTIFY_DATA_COLLECTION_GUIDE.md` for detailed info
- Check: Script comments for technical details
- Ask teammates if stuck on authentication

**Remember**: Each team member only needs to authenticate ONCE. After that, one person can run collections for everyone!
