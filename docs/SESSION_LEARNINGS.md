# Session Learnings: Spotify API Integration & Data Collection

**Date**: November 5, 2025
**Session Focus**: Setting up Spotify API authentication, testing data retrieval, understanding API limitations

---

## Overview

This session focused on establishing a robust data collection pipeline using the Spotify Web API for our IME 565 analytics platform. We successfully authenticated with Spotify, tested various endpoints, identified API limitations, and designed a hybrid approach to overcome quota restrictions.

---

## Key Achievements

### ✅ 1. Spotify Developer App Configuration

**Setup Details:**
- **App Name**: IME 565 Spotify Analytics
- **App Status**: Development Mode
- **Client ID**: `4f226b6e1e8c47f5996bae4cc5b48394`
- **Redirect URIs Configured**:
  - `http://127.0.0.1:8888/callback` (for local testing)
  - `https://n8n.diferdinando.com/rest/oauth2-credential/callback` (for n8n automation)

**Important Discovery:**
- Spotify requires explicit IP addresses (`127.0.0.1`) instead of `localhost` for redirect URIs
- Multiple redirect URIs can be registered simultaneously for different environments

### ✅ 2. OAuth Authentication System

**Implementation**: `scripts/spotify_auth.py`

Successfully implemented multi-user OAuth authentication with:
- Token caching in `.spotify_cache/` directory
- Per-user token management (`.cache-{username}`)
- Automatic token refresh (tokens expire after 60 minutes)
- Browser-based OAuth flow

**OAuth Scopes Required:**
```python
SCOPES = [
    'user-read-recently-played',
    'user-top-read',
    'playlist-read-private',
    'user-read-private',
    'user-library-read'
]
```

**Authentication Flow:**
```bash
python scripts/spotify_auth.py --user nicolo
# Opens browser → User logs in → Redirects to localhost → Token cached
```

### ✅ 3. Successful API Endpoints

We confirmed these endpoints work perfectly in Development Mode:

#### **Recently Played Tracks**
```python
sp.current_user_recently_played(limit=50)
```
**Returns:**
- Last 50 tracks with exact timestamps (`played_at`)
- Full track metadata (name, artists, album, duration, popularity)
- Playback context (which playlist/album)
- **Data Quality**: 100% - No missing fields detected

**Sample Data Quality Metrics:**
- Total tracks retrieved: 50
- All have timestamps: ✓
- Duration range: 120-351 seconds (reasonable)
- No tracks under 5 seconds (no obvious skips)

#### **Top Tracks & Artists**
```python
sp.current_user_top_tracks(time_range='short_term', limit=20)
sp.current_user_top_tracks(time_range='long_term', limit=20)
sp.current_user_top_artists(time_range='medium_term', limit=20)
```
**Returns:**
- Top 50 tracks/artists across 3 time ranges:
  - `short_term`: Last ~4 weeks
  - `medium_term`: Last ~6 months
  - `long_term`: All time
- Shows taste evolution and current obsessions

**Sample Results (Nicolo's Data):**
- Top track (4 weeks): "crystallized (feat. Inéz)" by John Summit
- Top track (all-time): "NOKIA" by Drake

#### **User Playlists**
```python
sp.current_user_playlists(limit=50)
```
**Returns:**
- All user playlists (up to 50)
- Playlist metadata: name, track count, ID, owner
- Can drill down into each playlist for full track lists

**Sample Results:**
- 50 playlists retrieved
- Largest playlist: 290 tracks
- Total across all playlists: 700+ unique tracks

### ✅ 4. User Profile Data

```python
profile = sp.current_user()
```
**Returns:**
- Display name: `nico_diferd`
- User ID: `nico_diferd`
- Account type: `PREMIUM` (important for API access)
- Followers count: 13

---

## Critical Limitations Discovered

### ❌ Audio Features API (HTTP 403 Error)

**Problem**: The `audio_features` endpoint consistently returns `403 Forbidden` errors.

**What We Tried:**
1. Direct API calls with Client Credentials flow → 403
2. User OAuth token with proper scopes → 403
3. Single track requests → 403
4. Batch requests (up to 100 tracks) → 403
5. Rate limiting delays (2-5 seconds between calls) → Still 403

**Root Cause**: Development Mode Restrictions

Despite Spotify's documentation stating "no endpoint restrictions" for Development Mode, we discovered undocumented limitations on the `audio_features` endpoint.

**Investigation Results:**
```bash
# Direct REST API Test
GET https://api.spotify.com/v1/audio-features/3F57PtOdqRpD6euFYqtKXX
Authorization: Bearer {valid_token}

Response: 403 Forbidden
{
  "error": {
    "status": 403
  }
}
```

### 🚫 Extended Quota Mode Not Available

**Requirements for Extended Quota Mode** (per Spotify docs):
- ❌ Company email (not personal/student accounts)
- ❌ Established business entity
- ❌ 250,000+ monthly active users
- ❌ Commercial viability proof
- ❌ Review process: up to 6 weeks

**Conclusion**: Extended Quota Mode is **not realistic for student projects**.

### ⚠️ Development Mode Constraints

**User Limit**: Maximum 25 authenticated users
- Must add each user to allowlist in Developer Dashboard
- Sufficient for our 3-person team + beta testers

**Rate Limits**: Lower than Extended Quota Mode
- Experienced HTTP 429 errors when making rapid successive calls
- Need delays between batch requests (recommended: 1-2 seconds)

---

## Hybrid Solution: Spotify API + Kaggle Audio Features

Since audio features are blocked, we designed a **hybrid data collection strategy**:

### Architecture

```
┌─────────────────────────────────────────────────────────┐
│  SPOTIFY API (Behavioral Data)                          │
│  ✓ Recently played tracks (timestamps, context)        │
│  ✓ Top tracks/artists (time ranges)                    │
│  ✓ User playlists                                       │
│  ✓ Track metadata (name, artist, album, popularity)    │
└────────────────┬────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────┐
│  MATCHING ENGINE                                        │
│  Match by: track_name + artist_name                     │
│  Fuzzy matching for variations                          │
└────────────────┬────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────┐
│  KAGGLE DATASET (Audio Features)                        │
│  ✓ 114,000+ tracks with full audio features            │
│  ✓ Danceability, energy, valence, tempo, etc.          │
│  ✓ No API rate limits                                   │
└─────────────────────────────────────────────────────────┘
```

### Advantages

1. **Real Behavioral Data**: Actual listening history with timestamps
2. **Comprehensive Audio Features**: Kaggle's massive pre-computed database
3. **No Rate Limits**: Process thousands of tracks without API throttling
4. **Better Historical Coverage**: Kaggle has older tracks not in recent API data
5. **Faster Processing**: No network latency for audio feature lookups

### Data Pipeline

```python
# Step 1: Fetch from Spotify API
recent_tracks = sp.current_user_recently_played(limit=50)

# Step 2: Extract track metadata
for item in recent_tracks['items']:
    track_id = item['track']['id']
    track_name = item['track']['name']
    artists = item['track']['artists'][0]['name']
    played_at = item['played_at']  # Timestamp

# Step 3: Match to Kaggle dataset
kaggle_df = pd.read_csv('data/raw/dataset.csv')
matched = kaggle_df[
    (kaggle_df['track_name'] == track_name) &
    (kaggle_df['artists'].str.contains(artists))
]

# Step 4: Enrich with audio features
if not matched.empty:
    danceability = matched.iloc[0]['danceability']
    energy = matched.iloc[0]['energy']
    valence = matched.iloc[0]['valence']
    # ... etc
```

---

## Data Quality Findings

### Track Duration Analysis

From 50 recently played tracks:
- **Minimum**: 120 seconds (2:00)
- **Maximum**: 351.9 seconds (5:52)
- **Average**: 187.4 seconds (3:07)

**Cleaning Rule**: No tracks under 5 seconds detected (no cleaning needed for skips)

### Missing Data

**Excellent data quality** in behavioral endpoints:
- ✓ All tracks have valid IDs
- ✓ All tracks have names and artists
- ✓ All recently played tracks have timestamps
- ✓ No null values in critical fields

**Potential Issues**:
- Top tracks don't have `played_at` timestamps (by design)
- Some tracks may have `preview_url: null` (not critical for our use case)

### Timestamp Format

```json
"played_at": "2025-11-06T06:53:51.539Z"
```
- ISO 8601 format
- UTC timezone
- Millisecond precision
- Easy to parse with `datetime`

---

## Technical Learnings

### 1. Spotipy Library Issues

**Deprecation Warning Encountered**:
```
DeprecationWarning: You're using 'as_dict = True'.
get_access_token will return the token string directly in future versions.
```
**Solution**: Use `get_cached_token()` instead for token info.

### 2. Rate Limiting Best Practices

**HTTP 429 Errors** occur when making too many requests:
- Spotify API limit: ~180 requests/minute
- Safe rate: 2 requests/second with delays

**Implementation**:
```python
import time

for batch in batches:
    response = sp.audio_features(batch)
    time.sleep(1.0)  # 1-second delay between batches
```

### 3. Error Handling Patterns

**Robust API Call Structure**:
```python
try:
    results = sp.current_user_recently_played(limit=50)
    items = results.get('items', [])
except spotipy.exceptions.SpotifyException as e:
    if e.http_status == 429:
        # Rate limited - wait and retry
        retry_after = e.headers.get('Retry-After', 5)
        time.sleep(int(retry_after))
    elif e.http_status == 401:
        # Token expired - refresh
        auth.authenticate(force_refresh=True)
    else:
        # Log and continue
        print(f"Error: {e}")
```

---

## Environment Configuration

### Local Development Setup

**File**: `.env`
```bash
SPOTIFY_CLIENT_ID=4f226b6e1e8c47f5996bae4cc5b48394
SPOTIFY_CLIENT_SECRET=32782d50d8b94f4b849e02a7afb77522
SPOTIFY_REDIRECT_URI=http://127.0.0.1:8888/callback
```

**Multi-User Pattern**: Create per-user env files
```
.env.nicolo
.env.joe
.env.rithvik
```

**Token Storage**: `.spotify_cache/.cache-{username}`
- Automatically managed by Spotipy
- Contains access token, refresh token, expiry
- **Security**: Added to `.gitignore`

---

## Features We Can Build (Despite Limitations)

### Tier 1: Pure Spotify API Features

1. **Recent Listening Timeline**
   - Last 50 tracks with exact timestamps
   - Visualize listening sessions
   - Detect late-night binges, morning routines

2. **Temporal Patterns**
   - Hour-of-day listening distribution
   - Weekday vs weekend habits
   - Listening streaks and frequency

3. **Artist/Track Evolution**
   - Top items across 3 time ranges
   - Taste drift over time
   - Current obsessions vs all-time favorites

4. **Playlist Management**
   - Playlist health metrics (size, age, diversity)
   - Track overlap detection across playlists
   - Stale playlist identification

5. **Discovery Metrics**
   - New artist discovery rate
   - Repeat vs exploration ratio
   - Playlist freshness scores

### Tier 2: Hybrid Features (Spotify + Kaggle)

6. **Mood Trajectory**
   - Emotional listening patterns (valence over time)
   - Mood dips and peaks by day/week

7. **Context Classification**
   - Workout sessions (high energy, tempo > 120 BPM)
   - Focus music (instrumental, low speechiness)
   - Relaxation (acoustic, low energy)

8. **Audio Feature Analytics**
   - Energy distribution by time of day
   - Danceability trends
   - Tempo preferences

9. **Smart Recommendations**
   - Based on listening time patterns
   - Audio similarity using Kaggle features
   - Context-aware suggestions

10. **Playlist Optimization**
    - Suggest tracks based on playlist mood/energy
    - Balance acoustic vs electronic content
    - Diversify artist representation

---

## Next Steps

### Immediate (Week 7)

1. **Add Team Members to Allowlist**
   - Go to Developer Dashboard → User Management
   - Add Spotify usernames: `nico_diferd`, `joe_username`, `rithvik_username`

2. **Build Streamlit Dashboard**
   - OAuth authentication flow
   - Session-based token management
   - Basic visualizations (recently played, top tracks)

3. **Implement Kaggle Matching**
   - Load Kaggle datasets into pandas
   - Create fuzzy matching algorithm (track name + artist)
   - Handle edge cases (remixes, featuring artists)

### Short-Term (Week 8)

4. **Data Collection Pipeline**
   - Automated weekly collection via n8n
   - Store in Cloudflare R2/S3 bucket
   - Merge team member data

5. **Enhanced Analytics**
   - Temporal visualizations (Plotly timeline charts)
   - Mood tracking dashboards
   - Context detection algorithms

### Long-Term (Week 9-10)

6. **Machine Learning Models**
   - Random Forest for preference prediction
   - XGBoost for recommendation ranking
   - Ensemble voting classifier

7. **Production Deployment**
   - Streamlit Cloud or self-hosted
   - Automated data refresh
   - Multi-user support (up to 25 users)

---

## Resources & References

### Documentation
- [Spotify Web API Reference](https://developer.spotify.com/documentation/web-api)
- [Quota Modes Documentation](https://developer.spotify.com/documentation/web-api/concepts/quota-modes)
- [Redirect URI Guide](https://developer.spotify.com/documentation/web-api/concepts/redirect_uri)
- [Spotipy Library Docs](https://spotipy.readthedocs.io/)

### Datasets
- **Kaggle**: [Spotify Tracks Dataset](https://www.kaggle.com/datasets/maharshipandya/-spotify-tracks-dataset) (~114k tracks)
- **Kaggle**: [Top Spotify Songs 2023](https://www.kaggle.com/datasets/nelgiriyewithana/top-spotify-songs-2023) (~50k tracks)

### Tools
- **Spotipy**: Python library for Spotify Web API
- **Streamlit**: Dashboard framework
- **n8n**: Workflow automation (n8n.diferdinando.com)
- **Cloudflare R2**: S3-compatible storage

---

## Lessons Learned

1. **Always test API endpoints early** - We discovered audio features limitation before building full pipeline
2. **Development Mode is sufficient for student projects** - 25-user limit is plenty
3. **Hybrid approaches can overcome API limitations** - Kaggle datasets provide missing features
4. **Rate limiting is real** - Always implement delays and retry logic
5. **Documentation isn't always accurate** - "No endpoint restrictions" claim was false
6. **OAuth is complex but manageable** - Token caching and refresh logic is critical
7. **Real user data > synthetic data** - Even 50 recent tracks provide rich insights

---

## Questions & Answers

**Q: Can we use audio features at all?**
A: No via API, but yes via Kaggle dataset matching.

**Q: Is 50 tracks enough for analysis?**
A: Yes! 50 recent tracks + top tracks across time ranges = ~150 data points per user.

**Q: Can we add more than 3 users?**
A: Yes, up to 25 users in Development Mode.

**Q: Do we need Extended Quota Mode?**
A: No - not available for student projects, and not necessary for our use case.

**Q: Can we automate data collection?**
A: Yes - n8n workflow with Cloudflare tunnel (n8n.diferdinando.com).

---

## Contact & Support

**Team Members**:
- Nicolo DiFerdinando (authenticated: `nico_diferd`)
- Joe Mascher
- Rithvik Shetty

**Spotify Developer App**: IME 565 Spotify Analytics
**Client ID**: 

---

**Last Updated**: November 5, 2025
**Session Duration**: 2 hours
**Status**: ✅ Authentication working, API tested, hybrid approach designed
