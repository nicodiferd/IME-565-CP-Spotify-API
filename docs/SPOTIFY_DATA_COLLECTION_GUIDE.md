# Spotify Real Data Collection Guide

**Date**: November 3, 2025
**Team**: Nicolo DiFerdinando, Joe Mascher, Rithvik Shetty
**Purpose**: Collect authentic listening data from team members via Spotify API

---

## Overview

This guide walks through collecting **real listening data** from all team members to power your analytics platform. Unlike synthetic data, this gives you authentic temporal patterns, genuine context switching, and real user behavior.

### What You'll Collect

**Per Team Member**:
- ✅ Recently played tracks (last 50 plays)
- ✅ Top tracks (short/medium/long term)
- ✅ Top artists (short/medium/long term)
- ✅ User playlists (metadata only, not full contents initially)
- ✅ Audio features for all tracks
- ✅ Listening timestamps and contexts

**Expected Data Volume**:
- 3 team members × ~50-200 tracks each = **150-600 unique listening events**
- With repeated collection over weeks: **500-2000+ events**
- Merged with Kaggle audio features: **Complete analytical dataset**

---

## Prerequisites

### 1. Spotify Developer Account Setup

**Each team member needs to complete this ONCE**:

```bash
1. Go to: https://developer.spotify.com/dashboard
2. Log in with your Spotify account
3. Click "Create App"
   - App Name: "IME565 Spotify Analytics - [YourName]"
   - App Description: "Course project for IME 565 - music analytics"
   - Redirect URI: http://localhost:8888/callback
   - API: Web API
   - Check: "I understand and agree..."
4. Click "Save"
5. Click "Settings"
6. Copy your Client ID and Client Secret
```

### 2. Environment Variables

**Create separate .env files for each team member**:

```bash
# .env.nicolo
SPOTIFY_CLIENT_ID=your_client_id_here
SPOTIFY_CLIENT_SECRET=your_client_secret_here
SPOTIFY_REDIRECT_URI=http://localhost:8888/callback
USER_NAME=nicolo
USER_ID=1

# .env.joe
SPOTIFY_CLIENT_ID=joe_client_id_here
SPOTIFY_CLIENT_SECRET=joe_client_secret_here
SPOTIFY_REDIRECT_URI=http://localhost:8888/callback
USER_NAME=joe
USER_ID=2

# .env.rithvik
SPOTIFY_CLIENT_ID=rithvik_client_id_here
SPOTIFY_CLIENT_SECRET=rithvik_client_secret_here
SPOTIFY_REDIRECT_URI=http://localhost:8888/callback
USER_NAME=rithvik
USER_ID=3
```

**Security Note**: Add `.env.*` to `.gitignore` to prevent committing credentials!

---

## Spotify API Endpoints We'll Use

### 1. Recently Played Tracks
**Endpoint**: `GET /me/player/recently-played`
**Limit**: 50 tracks (last ~1-3 days depending on listening frequency)
**Returns**: Track info + played_at timestamps
**Use Case**: Core temporal analysis data

### 2. Top Tracks
**Endpoint**: `GET /me/top/tracks`
**Time Ranges**: short_term (4 weeks), medium_term (6 months), long_term (years)
**Limit**: 50 tracks per time range
**Returns**: Track info + popularity
**Use Case**: Long-term preference analysis

### 3. Top Artists
**Endpoint**: `GET /me/top/artists`
**Time Ranges**: short_term, medium_term, long_term
**Limit**: 50 artists per time range
**Returns**: Artist info + genres
**Use Case**: Genre preference evolution

### 4. User Playlists
**Endpoint**: `GET /me/playlists`
**Limit**: All user playlists
**Returns**: Playlist metadata (name, description, track count)
**Use Case**: Playlist intelligence features (Phase 2)

### 5. Audio Features
**Endpoint**: `GET /audio-features`
**Limit**: 100 tracks per request (batch)
**Returns**: Complete audio analysis
**Use Case**: Merge with listening history for analysis

---

## Data Collection Workflow

### Workflow Diagram
```
┌─────────────────────────────────────────────────────────────────┐
│                    SPOTIFY DATA COLLECTION                       │
└─────────────────────────────────────────────────────────────────┘

Step 1: AUTHENTICATION
┌──────────────┐
│ Each Team    │──► OAuth2 Flow ──► Generate Token ──► Save to Cache
│ Member       │
└──────────────┘

Step 2: DATA COLLECTION (Per Member)
┌────────────────────┐
│ Run Collector      │──► Recently Played (50 tracks)
│ Script             │──► Top Tracks (3 time ranges × 50 = 150)
│                    │──► Top Artists (3 time ranges × 50 = 150)
│                    │──► User Playlists (metadata)
└────────────────────┘
         │
         ▼
┌────────────────────┐
│ Save Raw JSON      │──► data/raw/nicolo_recently_played.json
│                    │──► data/raw/nicolo_top_tracks.json
│                    │──► data/raw/nicolo_playlists.json
└────────────────────┘

Step 3: ENRICHMENT
┌────────────────────┐
│ Extract Track IDs  │──► Batch Fetch Audio Features
│                    │──► Merge with Kaggle Database
│                    │──► Add Context Classification
└────────────────────┘
         │
         ▼
┌────────────────────┐
│ Save Processed     │──► data/processed/nicolo_listening_history.csv
└────────────────────┘

Step 4: MERGING
┌────────────────────┐
│ Combine All 3      │──► Unified Dataset
│ Team Members       │──► Deduplicate
│                    │──► Standardize Timestamps
└────────────────────┘
         │
         ▼
┌────────────────────┐
│ Final Dataset      │──► data/team_listening_history.csv
└────────────────────┘
```

---

## Critical Considerations

### 1. **Rate Limiting**
```
Spotify API Limits:
- Standard: ~180 requests per minute
- Extended: 1000 requests per day per app
- Burst: 20 requests per second (brief)

Our Strategy:
✓ Batch audio features (100 tracks per request)
✓ Add 0.5s delay between requests
✓ Use exponential backoff on 429 errors
✓ Cache results to avoid re-fetching
```

### 2. **Token Management**
```
OAuth Tokens:
- Access Token: Expires after 60 minutes
- Refresh Token: Used to get new access token
- Scope Required:
  • user-read-recently-played
  • user-top-read
  • playlist-read-private
  • user-read-private

Implementation:
✓ Check token expiration before each request
✓ Auto-refresh when <5 minutes remaining
✓ Store tokens securely (session state or encrypted file)
✓ Never commit tokens to git
```

### 3. **Data Privacy**
```
Team Member Privacy:
✓ Each member controls their own data
✓ Option to anonymize user IDs in final dataset
✓ Can exclude specific tracks/playlists
✓ No sharing of raw data outside team

Dataset Privacy:
✓ If sharing/publishing: Remove user_ids or use pseudonyms
✓ Aggregate statistics only
✓ No personally identifiable information
```

### 4. **Data Quality**

**Common Issues**:

| Issue | Cause | Solution |
|-------|-------|----------|
| Missing audio features | Track removed from Spotify | Skip track or use fallback |
| Duplicate tracks | Multiple plays | Keep all with timestamps for temporal analysis |
| Null values | API errors | Retry with exponential backoff |
| Wrong time zone | UTC vs local | Standardize all to UTC, convert for display |
| Podcasts in history | Non-music content | Filter by `track_type` or missing audio features |

### 5. **Temporal Data Richness**

**What You Get from API**:
```python
# Recently Played Response
{
  "played_at": "2025-11-03T14:23:45.000Z",  # ✅ Exact timestamp
  "track": {
    "id": "track_id",
    "name": "track_name",
    "artists": [...],
    "duration_ms": 240000
  },
  "context": {
    "type": "playlist",        # ✅ Context type
    "uri": "spotify:playlist:..." # ✅ Source playlist
  }
}
```

**What You Can Derive**:
```python
✓ Hour of day (0-23)
✓ Day of week (Mon-Sun)
✓ Weekend vs weekday
✓ Time since last play (session detection)
✓ Play order in session
✓ Morning/afternoon/evening/night period
✓ Month and season
✓ Listening velocity (plays per day)
```

### 6. **Context Classification**

**Automatic Context Detection**:
```python
# Rule-based context inference from temporal + audio features

Morning (6-9 AM) + High Energy → "Commute"
Weekday (10 AM-5 PM) + Low Speechiness → "Focus/Work"
Evening (6-9 PM) + Medium Energy → "Relaxation"
Friday/Saturday (9 PM-2 AM) + High Valence → "Party"
Late Night (11 PM-6 AM) + Low Energy → "Sleep"
Weekend Morning + High Danceability → "Workout"
```

**Playlist-Based Context**:
```python
Playlist Name Contains:
- "workout", "gym", "running" → "Workout"
- "focus", "study", "concentration" → "Focus"
- "chill", "relax", "calm" → "Relaxation"
- "party", "dance", "club" → "Party"
- "sleep", "ambient", "night" → "Sleep"
```

---

## Data Schema

### Raw Data (from Spotify API)

#### recently_played.json
```json
{
  "items": [
    {
      "track": {
        "id": "track_id",
        "name": "track_name",
        "artists": [{"name": "artist_name", "id": "artist_id"}],
        "album": {"name": "album_name", "id": "album_id"},
        "duration_ms": 240000,
        "popularity": 75,
        "explicit": false
      },
      "played_at": "2025-11-03T14:23:45.000Z",
      "context": {
        "type": "playlist",
        "uri": "spotify:playlist:37i9dQZF1DXcBWIGoYBM5M"
      }
    }
  ]
}
```

#### top_tracks.json
```json
{
  "items": [
    {
      "id": "track_id",
      "name": "track_name",
      "artists": [...],
      "popularity": 85,
      "album": {...}
    }
  ],
  "time_range": "short_term"
}
```

### Processed Data (for analysis)

#### team_listening_history.csv
```csv
user_id,user_name,timestamp,track_id,track_name,artist_name,album_name,duration_ms,played_duration_ms,context_type,context_uri,playlist_name,hour,day_of_week,is_weekend,time_period,inferred_context,danceability,energy,valence,acousticness,speechiness,instrumentalness,tempo,loudness,key,mode,time_signature,popularity
1,nicolo,2025-11-03 14:23:45,5SuOikwiRyPMVoIQDJUgSV,Comedy,Gen Hoshino,Comedy,230666,230666,playlist,spotify:playlist:...,Focus Vibes,14,Sunday,True,afternoon,focus,0.676,0.461,0.715,0.032,0.143,0.000001,87.917,-6.746,1,0,4,73
```

**Column Descriptions**:
- `user_id`: Integer ID (1, 2, 3)
- `user_name`: Team member name (nicolo, joe, rithvik)
- `timestamp`: UTC timestamp of play
- `track_id`: Spotify track ID
- `track_name`, `artist_name`, `album_name`: Track metadata
- `duration_ms`: Track length
- `played_duration_ms`: How much was played (null if unknown)
- `context_type`: playlist, album, artist, collection
- `context_uri`: Spotify URI of context
- `playlist_name`: Extracted playlist name (if available)
- `hour`: Hour of day (0-23)
- `day_of_week`: Monday, Tuesday, etc.
- `is_weekend`: Boolean
- `time_period`: morning, afternoon, evening, night
- `inferred_context`: workout, focus, relaxation, party, sleep, commute, general
- Audio features: danceability, energy, valence, etc. (from audio-features endpoint)
- `popularity`: Spotify popularity score (0-100)

---

## Expected Outcomes

### Data Volume Estimates

**Initial Collection (Week 7)**:
| Source | Per Member | Total (3 members) |
|--------|------------|-------------------|
| Recently Played | 50 tracks | 150 plays |
| Top Tracks (all ranges) | 150 unique | 450 unique |
| Total Unique Tracks | ~150 | ~400-500 |
| Total Events with Timestamps | 50 | 150 |

**After 4 Weeks of Collection**:
| Source | Per Member | Total (3 members) |
|--------|------------|-------------------|
| Cumulative Recently Played | 200-400 | 600-1200 plays |
| New Top Tracks | 50-100 | 150-300 |
| Total Dataset | ~300-500 | ~900-1500 events |

### Data Richness

**What Makes This Dataset Valuable**:
```
✓ Real human behavior (not synthetic)
✓ Authentic temporal patterns
✓ Genuine context switching
✓ Multiple personas (3 different listening styles)
✓ Complete audio features for all tracks
✓ Longitudinal data (can track changes over weeks)
✓ Publication-quality methodology
```

**Limitations to Acknowledge**:
```
⚠ Small sample size (3 users vs millions)
⚠ Short time span (weeks vs years)
⚠ Limited to recent Spotify API data (no full history yet)
⚠ May not capture all listening contexts
⚠ Dependent on team members' active listening
```

---

## Validation Checklist

Before using collected data for analysis:

### Data Completeness
- [ ] All team members successfully authenticated
- [ ] Recently played data collected for all members
- [ ] Audio features fetched for 95%+ of tracks
- [ ] Timestamps in correct format (ISO 8601)
- [ ] No missing critical fields (track_id, timestamp, user_id)

### Data Quality
- [ ] Timestamps span at least 1-3 days initially
- [ ] Hour-of-day distribution looks realistic (not all same hour)
- [ ] Multiple contexts represented (not all one type)
- [ ] Audio features in valid ranges (0-1 for most)
- [ ] No duplicate plays at exact same timestamp

### Temporal Patterns
- [ ] Weekday vs weekend patterns visible (if data spans both)
- [ ] Peak listening hours identified
- [ ] Session boundaries detectable (gaps between plays)
- [ ] At least 3-5 different days represented

### Audio Features
- [ ] Energy distribution not uniform
- [ ] Multiple genres represented
- [ ] Valence shows variation (not all happy or all sad)
- [ ] Tempo spans reasonable range (60-180 BPM mostly)

---

## Troubleshooting

### Common Issues

#### 1. "Invalid Redirect URI"
```
Error: INVALID_CLIENT: Invalid redirect URI
Solution:
- Go to Spotify Developer Dashboard
- Click Settings
- Ensure redirect URI is EXACTLY: http://localhost:8888/callback
- No trailing slash, correct port
```

#### 2. "Insufficient Scope"
```
Error: Insufficient client scope
Solution:
- Delete .cache file
- Re-run authentication
- Ensure script requests all scopes:
  - user-read-recently-played
  - user-top-read
  - playlist-read-private
```

#### 3. "No Recently Played Tracks"
```
Error: API returns empty list
Cause: User hasn't listened to Spotify recently
Solution:
- Play a few songs on Spotify
- Wait 5-10 minutes
- Try collecting again
```

#### 4. "Rate Limited (429)"
```
Error: 429 Too Many Requests
Solution:
- Script should handle this automatically
- If not, add time.sleep(1) between requests
- Check Retry-After header
- Reduce batch size
```

#### 5. "Missing Audio Features"
```
Error: Some tracks have null audio features
Cause: Track removed from Spotify or not analyzed
Solution:
- Skip tracks with missing features
- Use Kaggle database as fallback if track_id matches
- Document percentage of missing data
```

---

## Weekly Collection Strategy

### Recurring Data Collection

To build a rich dataset over the semester:

**Week 7 (Nov 3-9)**: Initial collection
```bash
python scripts/collect_team_data.py --all-members
# Expected: 150 recent plays + 450 top tracks
```

**Week 8 (Nov 10-16)**: First update
```bash
python scripts/collect_team_data.py --recently-played-only
# Expected: 100-150 new plays
```

**Week 9 (Nov 17-23)**: Second update
```bash
python scripts/collect_team_data.py --recently-played-only
# Expected: 100-150 new plays
```

**Week 10 (Nov 24-30)**: Final collection
```bash
python scripts/collect_team_data.py --all-members
# Expected: Full dataset ~500-1000 plays
```

### Automation (Optional)
```bash
# Add to crontab for daily collection
0 9 * * * cd /path/to/project && python scripts/collect_team_data.py --recently-played-only
```

---

## Next Steps

1. **Read this guide thoroughly**
2. **Each team member**: Set up Spotify Developer account
3. **Each team member**: Create personal .env file
4. **Run**: Authentication and initial data collection script
5. **Validate**: Check data quality with validation script
6. **Merge**: Combine all team members into unified dataset
7. **Analyze**: Update Spotify.ipynb with real data

---

## Resources

### Spotify API Documentation
- Main Docs: https://developer.spotify.com/documentation/web-api
- Spotipy Library: https://spotipy.readthedocs.io/
- Authentication Guide: https://developer.spotify.com/documentation/web-api/tutorials/getting-started

### Project-Specific
- Data Strategy Analysis: `docs/DATA_STRATEGY_ANALYSIS.md`
- CLAUDE.md: Project overview and architecture
- Proposal: `IME565_Project_Proposal_Final.md`

### Academic References
- Marey et al. (2024): Activity-driven listening patterns
- Used to validate temporal pattern realism
