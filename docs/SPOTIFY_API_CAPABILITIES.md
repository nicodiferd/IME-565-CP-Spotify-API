# Spotify API Capabilities Documentation

**Last Updated**: November 20, 2025
**Testing Source**: `notebooks/api_testing.ipynb`
**Spotipy Version**: Latest as of Fall 2025

This document outlines the current capabilities and limitations of the Spotify Web API based on hands-on testing with our application's authentication flow.

---

## Table of Contents
1. [Authentication & Scopes](#authentication--scopes)
2. [Available Endpoints](#available-endpoints)
3. [Unavailable/Restricted Endpoints](#unavailablerestricted-endpoints)
4. [Data Schemas](#data-schemas)
5. [Rate Limits & Best Practices](#rate-limits--best-practices)
6. [Derived Metrics](#derived-metrics)

---

## Authentication & Scopes

### Required OAuth Scopes

The following scopes are tested and working for our application:

```python
SCOPES = [
    'user-read-recently-played',    # Access recently played tracks
    'user-top-read',                 # Access top artists and tracks
    'user-library-read',             # Access saved tracks and albums
    'playlist-read-private',         # Access private playlists
    'playlist-read-collaborative',   # Access collaborative playlists
    'user-read-playback-state',      # Read current playback state
    'user-read-currently-playing',   # Read currently playing track
]
```

### Authentication Flow
- **Method**: Authorization Code Flow with PKCE
- **Redirect URI**: `http://127.0.0.1:8501/` (Streamlit default)
- **Token Storage**: Session-based cache (Streamlit session_state)
- **Token Expiration**: 60 minutes (auto-refresh recommended at 50 minutes)

---

## Available Endpoints

### 1. User Profile (`sp.current_user()`)

**Endpoint**: `GET /v1/me`
**Status**: ✅ Working

**Returns**:
```python
{
    'display_name': str,      # User's display name (may be None)
    'id': str,                # Unique user ID
    'email': str,             # User email (requires user-read-email scope)
    'country': str,           # Country code (e.g., 'US')
    'product': str,           # Subscription level ('premium', 'free')
    'followers': {
        'total': int          # Number of followers
    },
    'external_urls': {
        'spotify': str        # Profile URL
    }
}
```

**Example Output**:
```
Display Name: nico_diferd
User ID: nico_diferd
Followers: 13
Profile URL: https://open.spotify.com/user/nico_diferd
```

---

### 2. Recently Played Tracks (`sp.current_user_recently_played()`)

**Endpoint**: `GET /v1/me/player/recently-played`
**Status**: ✅ Working
**Limit**: Up to 50 tracks per request

**Parameters**:
- `limit`: Number of tracks (max 50)
- `after`: Unix timestamp for pagination
- `before`: Unix timestamp for pagination

**Returns**:
```python
{
    'items': [
        {
            'track': {
                'id': str,
                'name': str,
                'artists': [{'name': str, 'id': str}],
                'album': {
                    'name': str,
                    'album_type': str,
                    'release_date': str
                },
                'duration_ms': int,
                'popularity': int,
                'explicit': bool,
                'uri': str,
                'external_urls': {'spotify': str}
            },
            'played_at': str,  # ISO 8601 timestamp
            'context': dict    # Playlist/album context (may be None)
        }
    ],
    'next': str,  # URL for next page
    'cursors': {'after': str, 'before': str}
}
```

**Example Output**:
```
1. CAN'T SAY - Travis Scott
   Played at: 2025-11-21T00:47:36.254Z

2. Folded - Kehlani
   Played at: 2025-11-21T00:44:32.925Z
```

---

### 3. Top Tracks (`sp.current_user_top_tracks()`)

**Endpoint**: `GET /v1/me/top/tracks`
**Status**: ✅ Working
**Limit**: Up to 50 tracks per request

**Parameters**:
- `limit`: Number of tracks (max 50)
- `offset`: Index for pagination
- `time_range`: One of:
  - `short_term` - Last 4 weeks
  - `medium_term` - Last 6 months (default)
  - `long_term` - Several years

**Returns**: Similar structure to recently played, but includes:
```python
{
    'items': [
        {
            'id': str,
            'name': str,
            'artists': [{'name': str, 'id': str}],
            'album': {...},
            'popularity': int,      # 0-100 score
            'duration_ms': int,
            'explicit': bool,
            'uri': str
        }
    ]
}
```

**Example Output**:
```
Top Tracks (Last 4 Weeks):
1. Flicker of Light - Lola Young (Popularity: 60/100)
2. Good Game - Dominic Fike (Popularity: 50/100)
3. Your Teeth In My Neck - Kali Uchis (Popularity: 68/100)
```

---

### 4. Top Artists (`sp.current_user_top_artists()`)

**Endpoint**: `GET /v1/me/top/artists`
**Status**: ✅ Working
**Limit**: Up to 50 artists per request

**Parameters**: Same as top tracks (limit, offset, time_range)

**Returns**:
```python
{
    'items': [
        {
            'id': str,
            'name': str,
            'genres': [str],        # List of genre tags
            'popularity': int,       # 0-100 score
            'followers': {
                'total': int
            },
            'images': [{'url': str, 'height': int, 'width': int}],
            'uri': str,
            'external_urls': {'spotify': str}
        }
    ]
}
```

---

### 5. Track Details (`sp.track(track_id)`)

**Endpoint**: `GET /v1/tracks/{id}`
**Status**: ✅ Working
**Use Case**: Get full metadata for a specific track

**Returns**:
```python
{
    'id': str,
    'name': str,
    'uri': str,
    'external_urls': {'spotify': str},
    'artists': [
        {
            'name': str,
            'id': str,
            'uri': str
        }
    ],
    'album': {
        'name': str,
        'album_type': str,         # 'album', 'single', 'compilation'
        'release_date': str,        # YYYY-MM-DD or YYYY
        'total_tracks': int,
        'images': [...]
    },
    'popularity': int,              # 0-100
    'duration_ms': int,
    'explicit': bool,
    'track_number': int,
    'disc_number': int,
    'is_playable': bool,
    'is_local': bool,
    'preview_url': str             # May be None
}
```

**Example Usage**:
```python
track_details = sp.track('27a1mYSG5tYg7dmEjWBcmL')
print(f"Track: {track_details['name']}")
print(f"Album: {track_details['album']['name']}")
print(f"Release Date: {track_details['album']['release_date']}")
```

---

### 6. Artist Details (`sp.artist(artist_id)`)

**Endpoint**: `GET /v1/artists/{id}`
**Status**: ✅ Working
**Use Case**: Get genre information and artist metadata

**Returns**:
```python
{
    'id': str,
    'name': str,
    'genres': [str],               # May be empty for some artists
    'popularity': int,              # 0-100
    'followers': {'total': int},
    'images': [...],
    'uri': str,
    'external_urls': {'spotify': str}
}
```

**Example Output**:
```
Artist: Travis Scott
Genres: rap
Popularity: 90/100
Followers: 41,378,957

Artist: Kehlani
Genres: (No genres listed)
Popularity: 80/100
Followers: 8,732,690
```

**Important Notes**:
- Not all artists have genres assigned
- Genre classification can be sparse or incomplete
- Use for general categorization, not precise genre analysis

---

### 7. User Playlists (`sp.current_user_playlists()`)

**Endpoint**: `GET /v1/me/playlists`
**Status**: ✅ Working
**Limit**: Up to 50 playlists per request

**Returns**:
```python
{
    'items': [
        {
            'id': str,
            'name': str,
            'description': str,
            'owner': {'display_name': str, 'id': str},
            'public': bool,
            'collaborative': bool,
            'tracks': {'total': int},
            'images': [...],
            'external_urls': {'spotify': str}
        }
    ]
}
```

---

### 8. Playlist Tracks (`sp.playlist_tracks(playlist_id)`)

**Endpoint**: `GET /v1/playlists/{playlist_id}/tracks`
**Status**: ✅ Working
**Limit**: Up to 100 tracks per request

**Returns**: Similar structure to recently played tracks

---

### 9. Search (`sp.search()`)

**Endpoint**: `GET /v1/search`
**Status**: ✅ Working

**Parameters**:
- `q`: Search query (e.g., 'artist:Drake', 'track:Hotline Bling')
- `type`: 'track', 'artist', 'album', 'playlist'
- `limit`: Number of results (max 50)
- `offset`: Pagination offset

**Example**:
```python
results = sp.search(q='artist:Drake', type='track', limit=2)
```

---

## Unavailable/Restricted Endpoints

### ❌ Audio Features (`sp.audio_features()`)

**Endpoint**: `GET /v1/audio-features`
**Status**: ⛔ **BLOCKED** (HTTP 403 Forbidden)
**Impact**: **CRITICAL** - Cannot access audio features directly

**Expected Data (Not Accessible)**:
- `danceability` (0.0-1.0)
- `energy` (0.0-1.0)
- `valence` (0.0-1.0) - happiness/positivity
- `acousticness` (0.0-1.0)
- `instrumentalness` (0.0-1.0)
- `speechiness` (0.0-1.0)
- `tempo` (BPM)
- `loudness` (dB)
- `key` (0-11, pitch class)
- `mode` (0=minor, 1=major)
- `time_signature` (e.g., 4/4)

**Error Message**:
```
HTTP Error for GET to https://api.spotify.com/v1/audio-features/?ids=3etbPFMXnAuShtcImz4UXW
returned 403 due to None
```

**Workaround**:
Since audio features are critical for our analytics (mood scores, context classification, etc.), we have two options:

1. **Use Kaggle Datasets**: Pre-computed audio features from public Spotify datasets
   - Spotify Tracks Dataset (~114k tracks with audio features)
   - Limitation: Only works for tracks in the dataset

2. **Request Extended Permissions**: Contact Spotify Developer Support for extended quota
   - Required for production use with real-time user data
   - May require Spotify Developer Extended Program enrollment

**Current Project Impact**:
- Phase 1 (Foundation Analytics): ✅ **No Impact** - Using Kaggle datasets
- Phase 2 (Playlist Intelligence): ⚠️ **Partial Impact** - Limited to dataset tracks
- Phase 3 (Predictive Modeling): ⚠️ **Partial Impact** - Training limited to dataset tracks
- Streamlit Dashboard: ⚠️ **Significant Impact** - Cannot show audio features for user's personal tracks

---

## Data Schemas

### Processed Track DataFrame

After fetching and processing track data, we typically convert to pandas DataFrames with this schema:

```python
{
    'track_id': str,
    'track_name': str,
    'artist_name': str,
    'artist_id': str,
    'album_name': str,
    'album_type': str,           # 'album', 'single', 'compilation'
    'release_date': str,          # YYYY-MM-DD
    'release_year': str,          # Extracted from release_date
    'popularity': int,            # 0-100
    'duration_ms': int,
    'duration_seconds': float,    # Computed from duration_ms
    'explicit': bool,
    'track_number': int,
    'played_at': str,             # ISO timestamp (for recent tracks only)
}
```

### Artist DataFrame

```python
{
    'artist_id': str,
    'artist_name': str,
    'genres': list[str],          # May be empty
    'popularity': int,            # 0-100
    'followers': int,
}
```

---

## Rate Limits & Best Practices

### Rate Limits
- **Typical Limit**: ~180 requests per minute (approximately 3 per second)
- **Extended Limit**: Higher for approved applications
- **HTTP 429**: Too Many Requests error when limit exceeded
  - Response includes `Retry-After` header (seconds to wait)

### Best Practices

1. **Batch Requests**:
   ```python
   # Good: Batch track requests
   track_ids = ['id1', 'id2', 'id3', ...]
   tracks = sp.tracks(track_ids)  # Up to 50 at once

   # Bad: Individual requests
   for track_id in track_ids:
       track = sp.track(track_id)
   ```

2. **Implement Retry Logic**:
   ```python
   import time
   from spotipy.exceptions import SpotifyException

   def fetch_with_retry(func, *args, max_retries=3, **kwargs):
       for attempt in range(max_retries):
           try:
               return func(*args, **kwargs)
           except SpotifyException as e:
               if e.http_status == 429:
                   retry_after = int(e.headers.get('Retry-After', 5))
                   time.sleep(retry_after)
               else:
                   raise
       raise Exception("Max retries exceeded")
   ```

3. **Cache Results**:
   ```python
   # Streamlit caching
   @st.cache_data(ttl=3600)  # Cache for 1 hour
   def fetch_top_tracks(time_range):
       return sp.current_user_top_tracks(time_range=time_range, limit=50)
   ```

4. **Pagination**:
   ```python
   # Fetch all playlists (more than 50)
   all_playlists = []
   offset = 0
   limit = 50

   while True:
       playlists = sp.current_user_playlists(limit=limit, offset=offset)
       all_playlists.extend(playlists['items'])
       if playlists['next'] is None:
           break
       offset += limit
   ```

---

## Derived Metrics

Since audio features are unavailable via API, here are metrics we **can** compute from available data:

### 1. Popularity-Based Metrics
```python
# Average popularity score
avg_popularity = df['popularity'].mean()

# Mainstream vs Niche score
# High popularity = mainstream, low = niche
mainstream_score = (avg_popularity / 100) * 100
```

### 2. Artist Diversity
```python
# Number of unique artists
unique_artists = df['artist_name'].nunique()
total_tracks = len(df)
artist_diversity = (unique_artists / total_tracks) * 100
```

### 3. Genre Diversity
```python
# From artist data
all_genres = []
for genres in df_artists['genres']:
    all_genres.extend(genres)

unique_genres = len(set(all_genres))
genre_diversity_score = unique_genres / len(df_artists) if len(df_artists) > 0 else 0
```

### 4. Temporal Patterns
```python
# From recent tracks with 'played_at' timestamps
df['played_at'] = pd.to_datetime(df['played_at'])
df['hour_of_day'] = df['played_at'].dt.hour
df['day_of_week'] = df['played_at'].dt.dayofweek

# Peak listening hours
peak_hours = df['hour_of_day'].value_counts().head(3)
```

### 5. Release Year Distribution
```python
# Extract year from release_date
df['release_year'] = df['release_date'].str[:4].astype(int)

# Temporal preference (new vs old music)
avg_release_year = df['release_year'].mean()
year_range = df['release_year'].max() - df['release_year'].min()
```

### 6. Content Type Distribution
```python
# Explicit vs Clean
explicit_ratio = df['explicit'].sum() / len(df)

# Album vs Single preference
album_type_dist = df['album_type'].value_counts(normalize=True)
```

### 7. Duration Preferences
```python
# Average track duration
avg_duration_seconds = df['duration_ms'].mean() / 1000
avg_duration_minutes = avg_duration_seconds / 60

# Short vs Long track preference
df['duration_category'] = pd.cut(
    df['duration_ms'] / 1000,
    bins=[0, 120, 240, 360, float('inf')],
    labels=['Short (<2min)', 'Medium (2-4min)', 'Long (4-6min)', 'Very Long (>6min)']
)
```

### 8. Artist Loyalty
```python
# Repeat artist rate
artist_counts = df['artist_name'].value_counts()
repeat_artists = (artist_counts > 1).sum()
artist_loyalty_score = (repeat_artists / len(artist_counts)) * 100
```

---

## Recommendations for Project

### For Phase 1 (Foundation Analytics)
✅ **Continue using Kaggle datasets** - Full audio features available

### For Phase 2 (Playlist Intelligence)
⚠️ **Hybrid approach**:
- Use available API data (track metadata, popularity, artists)
- Merge with Kaggle datasets using track IDs for audio features
- Document which metrics are unavailable for non-dataset tracks

### For Phase 3 (Predictive Modeling)
⚠️ **Training strategy**:
- Train models on Kaggle dataset (with audio features)
- Apply predictions to user data (without audio features) using available metadata
- Consider building a secondary model that works without audio features

### For Streamlit Dashboard
⚠️ **Two-tier experience**:
- **Basic Metrics**: Always available (popularity, artists, genres, temporal patterns)
- **Advanced Metrics**: Only for tracks in Kaggle dataset (audio features, mood scores, context classification)
- Display clear messaging when audio features unavailable

### Request API Access
📧 **Contact Spotify Developer Support**:
- URL: https://developer.spotify.com/support
- Request: Extended quota for audio features endpoint
- Justification: Academic research project for predictive analytics course
- Mention: Non-commercial, educational use case

---

## Testing Results Summary

**Tested Date**: November 20, 2025
**Testing Environment**: Streamlit app with Jupyter notebook

| Endpoint | Status | Limit | Notes |
|----------|--------|-------|-------|
| User Profile | ✅ Working | N/A | Basic user info |
| Recently Played | ✅ Working | 50 | Includes timestamps |
| Top Tracks | ✅ Working | 50 | 3 time ranges |
| Top Artists | ✅ Working | 50 | 3 time ranges |
| Track Details | ✅ Working | N/A | Full metadata |
| Artist Details | ✅ Working | N/A | Genres (may be sparse) |
| Playlists | ✅ Working | 50 | User's playlists |
| Playlist Tracks | ✅ Working | 100 | Tracks in playlist |
| Search | ✅ Working | 50 | Multi-type search |
| **Audio Features** | ❌ **403 Forbidden** | N/A | **CRITICAL LIMITATION** |

---

## Sample Code Snippets

### Fetch Complete User Profile
```python
def get_user_summary(sp):
    """Fetch comprehensive user data"""
    profile = sp.current_user()

    # Get top tracks and artists across all time ranges
    top_tracks_short = sp.current_user_top_tracks(time_range='short_term', limit=50)
    top_tracks_medium = sp.current_user_top_tracks(time_range='medium_term', limit=50)
    top_tracks_long = sp.current_user_top_tracks(time_range='long_term', limit=50)

    top_artists_short = sp.current_user_top_artists(time_range='short_term', limit=50)
    top_artists_medium = sp.current_user_top_artists(time_range='medium_term', limit=50)
    top_artists_long = sp.current_user_top_artists(time_range='long_term', limit=50)

    # Recent listening
    recent = sp.current_user_recently_played(limit=50)

    return {
        'profile': profile,
        'top_tracks': {
            'short_term': top_tracks_short,
            'medium_term': top_tracks_medium,
            'long_term': top_tracks_long
        },
        'top_artists': {
            'short_term': top_artists_short,
            'medium_term': top_artists_medium,
            'long_term': top_artists_long
        },
        'recent': recent
    }
```

### Build Track DataFrame
```python
def tracks_to_dataframe(tracks_response):
    """Convert Spotify tracks response to pandas DataFrame"""
    track_data = []

    for item in tracks_response['items']:
        # Handle both 'track' key (recent) and direct items (top tracks)
        track = item.get('track', item)

        track_data.append({
            'track_id': track['id'],
            'track_name': track['name'],
            'artist_name': track['artists'][0]['name'],
            'artist_id': track['artists'][0]['id'],
            'album_name': track['album']['name'],
            'album_type': track['album']['album_type'],
            'release_date': track['album']['release_date'],
            'popularity': track['popularity'],
            'duration_ms': track['duration_ms'],
            'explicit': track['explicit'],
            'track_number': track['track_number'],
            'played_at': item.get('played_at', None)  # Only for recent tracks
        })

    df = pd.DataFrame(track_data)

    # Add computed columns
    df['duration_seconds'] = df['duration_ms'] / 1000
    df['release_year'] = df['release_date'].str[:4]

    return df
```

---

## Conclusion

The Spotify Web API provides extensive metadata about user listening habits, but the **critical limitation** is the unavailability of audio features (danceability, energy, valence, etc.) due to HTTP 403 restrictions.

**Key Takeaways**:
1. ✅ User profile, listening history, and metadata are fully accessible
2. ✅ Artist and genre information available (though sparse for some artists)
3. ❌ Audio features require extended API access or alternative data sources
4. 🎯 Recommend hybrid approach: API + Kaggle datasets for complete analytics

**Next Steps**:
1. Update project documentation to reflect audio features limitation
2. Implement hybrid data pipeline (API + Kaggle merging)
3. Request extended API access from Spotify Developer Support
4. Design two-tier dashboard experience based on data availability
