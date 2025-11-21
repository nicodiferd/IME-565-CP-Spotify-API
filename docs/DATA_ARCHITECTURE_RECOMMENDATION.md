# Data Architecture Recommendation for Spotify Analytics Dashboard

**Date**: November 20, 2025
**Purpose**: Design optimal data collection and storage strategy for personal Spotify analytics

---

## Executive Summary

**Recommended Approach**: **Parquet files in Cloudflare R2 with smart aggregations**

**Why?**
- ✅ Already implemented (R2 storage working)
- ✅ Cost-effective (no database hosting costs)
- ✅ Simple architecture (no server management)
- ✅ Perfect for single-user analytics workload
- ✅ Efficient for time-series analysis
- ✅ Easy to version and backup

**Not Recommended**: MongoDB, Supabase, or traditional databases
- ❌ Overkill for single-user dashboards
- ❌ Added complexity and costs
- ❌ Requires connection management
- ❌ No cross-user queries needed

---

## Table of Contents
1. [Architecture Options Analysis](#architecture-options-analysis)
2. [Recommended File Structure](#recommended-file-structure)
3. [Data Collection Strategy](#data-collection-strategy)
4. [What to Show Users (Unique Value)](#what-to-show-users-unique-value)
5. [Implementation Guide](#implementation-guide)
6. [Handling Audio Features](#handling-audio-features)
7. [Performance Optimization](#performance-optimization)

---

## Architecture Options Analysis

### Option 1: Database (MongoDB, Supabase, PostgreSQL)

**When to Use:**
- Multi-user applications with complex queries across users
- Real-time collaborative features
- Transactional workloads (e.g., user ratings, comments)
- Need for complex joins and aggregations
- User authentication and authorization requirements

**Pros:**
- Structured queries with SQL/NoSQL
- Built-in relationships and indexes
- Real-time updates
- User authentication integration
- ACID guarantees (SQL databases)

**Cons:**
- **Added complexity**: Server setup, connection pooling, credential management
- **Ongoing costs**: Database hosting ($10-50/month minimum)
- **Overkill**: You're building a single-user analytics dashboard, not a social platform
- **No cross-user queries**: Each user only sees their own data
- **Maintenance**: Backups, migrations, scaling, monitoring
- **Latency**: Network round-trips for every query

**Verdict for This Project**: ❌ **Not Recommended**
- You don't need multi-user queries
- Analytics workload (not transactional)
- Users only view their own data
- Historical snapshots more important than real-time updates

---

### Option 2: Flat Files in Object Storage (Parquet/JSON in R2)

**When to Use:**
- Single-user or user-scoped analytics
- Historical snapshots and time-series data
- Read-heavy analytics workloads
- Cost-sensitive projects
- Simple deployment (no database server)

**Pros:**
- ✅ **Already implemented**: Cloudflare R2 working in your app
- ✅ **Cost-effective**: R2 storage is ~$0.015/GB/month (vs $20+ for databases)
- ✅ **Simple architecture**: No server, no credentials, no connection pooling
- ✅ **Parquet efficiency**: Columnar format, compressed, perfect for analytics
- ✅ **Easy versioning**: Snapshots preserved, can rollback or reprocess
- ✅ **Pandas-native**: Load directly into DataFrames for analysis
- ✅ **No vendor lock-in**: S3-compatible, portable
- ✅ **Infinite scalability**: Object storage scales automatically

**Cons:**
- ⚠️ No real-time queries without loading data
- ⚠️ Need careful file structure design
- ⚠️ Updates require rewriting files (not an issue for append-only snapshots)

**Verdict for This Project**: ✅ **STRONGLY RECOMMENDED**
- Perfect fit for analytics dashboard
- Cost-effective and simple
- Already working in your codebase

---

### Option 3: Hybrid (Files + Lightweight DB)

**When to Use:**
- Need both historical snapshots and fast queries
- Want to avoid cloud database but need SQL
- Local-first applications

**Examples:**
- **DuckDB**: In-process SQL database, can query Parquet files directly
- **SQLite**: Lightweight embedded database
- **MotherDuck**: Cloud DuckDB (serverless)

**Pros:**
- SQL queries on Parquet files
- No separate database server
- Best of both worlds

**Cons:**
- Added complexity over pure Parquet
- Still experimental for this use case
- Streamlit deployment complexity

**Verdict for This Project**: ⚠️ **Consider for Phase 3**
- Interesting for advanced queries
- Not needed for initial dashboard
- Revisit if query complexity grows

---

## Recommended File Structure

### Directory Layout

```
cloudflare-r2://ime565spotify/
├── reference_data/
│   ├── kaggle_tracks.parquet              # 114k Spotify tracks with audio features
│   └── kaggle_tracks_index.parquet        # Track ID → audio features lookup
│
└── users/
    └── {user_id}/                         # e.g., "nico_diferd"
        │
        ├── profile.json                   # Latest user profile metadata
        │
        ├── snapshots/                     # Point-in-time data collection
        │   ├── 2025-11-20T14-30-00Z/
        │   │   ├── metadata.json          # Snapshot info (timestamp, version, source)
        │   │   ├── recent_tracks.parquet  # 50 recently played tracks
        │   │   ├── top_tracks_short.parquet    # Top 50 (last 4 weeks)
        │   │   ├── top_tracks_medium.parquet   # Top 50 (last 6 months)
        │   │   ├── top_tracks_long.parquet     # Top 50 (several years)
        │   │   ├── top_artists_short.parquet   # Top 50 artists (last 4 weeks)
        │   │   ├── top_artists_medium.parquet  # Top 50 artists (last 6 months)
        │   │   ├── top_artists_long.parquet    # Top 50 artists (several years)
        │   │   └── computed_metrics.json       # Derived metrics (diversity, averages, etc.)
        │   │
        │   ├── 2025-11-21T10-15-00Z/
        │   │   └── ...                    # Next snapshot
        │   │
        │   └── ...
        │
        └── aggregated/                    # Pre-computed aggregations for fast loading
            ├── all_recent_tracks.parquet  # All historical recent tracks (deduplicated by played_at)
            ├── all_snapshots_metrics.parquet   # Time series of computed metrics
            ├── unique_tracks.parquet      # Deduplicated track library (all tracks user has listened to)
            ├── unique_artists.parquet     # Deduplicated artist library
            └── last_updated.json          # Timestamp of last aggregation
```

### Why This Structure?

1. **User-scoped directories** (`users/{user_id}/`)
   - Complete data isolation per user
   - Privacy-preserving
   - Easy to delete individual user data (GDPR compliance)

2. **Snapshots folder** (append-only)
   - Preserve point-in-time data
   - Never delete (can show "3 months ago you listened to...")
   - Can recompute metrics later if algorithm changes
   - Enables time-travel queries

3. **Aggregated folder** (derived data)
   - Pre-computed for fast dashboard loading
   - Rebuilt from snapshots when needed
   - Cacheable in Streamlit

4. **Parquet format**
   - Columnar storage (only read columns you need)
   - Compressed (smaller storage, faster transfer)
   - Typed schema (no parsing errors)
   - Direct pandas integration

5. **Reference data folder**
   - Shared across all users
   - Kaggle dataset with audio features
   - Track ID lookup table

---

## Data Collection Strategy

### When to Collect?

**Option A: On Every Session (Current)**
- User authenticates → trigger data sync
- Simple, guaranteed fresh data
- May annoy users with repeated syncs

**Option B: Smart Scheduling (Recommended)**
- Check `last_updated.json`
- Only collect if >24 hours since last snapshot
- User can manually trigger refresh
- Balance freshness vs API usage

**Option C: Background Collection (Future)**
- Periodic collection (daily/weekly)
- Requires server/cron job
- Not needed for personal dashboard

**Recommendation**: **Option B - Smart Scheduling**

```python
def should_collect_data(user_id):
    """Check if we need a new snapshot"""
    try:
        last_updated = load_from_r2(f'users/{user_id}/aggregated/last_updated.json')
        last_snapshot_time = datetime.fromisoformat(last_updated['timestamp'])
        hours_since = (datetime.now(timezone.utc) - last_snapshot_time).total_seconds() / 3600
        return hours_since >= 24  # Collect once per day
    except FileNotFoundError:
        return True  # No data yet, collect
```

### What to Collect Per Snapshot?

Based on API capabilities documentation:

```python
def collect_user_snapshot(sp, user_id):
    """Collect complete user snapshot"""
    timestamp = datetime.now(timezone.utc).isoformat().replace(':', '-')
    snapshot_dir = f'users/{user_id}/snapshots/{timestamp}'

    # 1. User Profile (lightweight JSON)
    profile = sp.current_user()
    save_to_r2(f'{snapshot_dir}/metadata.json', {
        'timestamp': timestamp,
        'user_id': user_id,
        'display_name': profile.get('display_name'),
        'country': profile.get('country'),
        'product': profile.get('product')
    })

    # 2. Recently Played (50 tracks with timestamps)
    recent = sp.current_user_recently_played(limit=50)
    recent_df = process_recent_tracks(recent)
    save_parquet_to_r2(f'{snapshot_dir}/recent_tracks.parquet', recent_df)

    # 3. Top Tracks (all time ranges)
    for time_range in ['short_term', 'medium_term', 'long_term']:
        top_tracks = sp.current_user_top_tracks(time_range=time_range, limit=50)
        tracks_df = process_top_tracks(top_tracks, time_range)
        save_parquet_to_r2(f'{snapshot_dir}/top_tracks_{time_range.split("_")[0]}.parquet', tracks_df)

    # 4. Top Artists (all time ranges)
    for time_range in ['short_term', 'medium_term', 'long_term']:
        top_artists = sp.current_user_top_artists(time_range=time_range, limit=50)
        artists_df = process_top_artists(top_artists, time_range)
        save_parquet_to_r2(f'{snapshot_dir}/top_artists_{time_range.split("_")[0]}.parquet', artists_df)

    # 5. Compute Derived Metrics
    metrics = compute_snapshot_metrics(recent_df, tracks_df, artists_df)
    save_to_r2(f'{snapshot_dir}/computed_metrics.json', metrics)

    # 6. Update Aggregated Data
    update_aggregated_data(user_id, timestamp)

    return snapshot_dir
```

---

## What to Show Users (Unique Value)

### The Core Question: What Does Spotify Wrapped NOT Show?

Spotify Wrapped is **annual** and focuses on **vanity metrics** (top 0.01% listener). Your dashboard should provide:

1. **Continuous insights** (not just once a year)
2. **Temporal patterns** (when, not just what)
3. **Trends over time** (evolution, not snapshots)
4. **Actionable insights** (discover new music, understand your habits)

---

### Tier 1: Always Available (No Audio Features Required)

These are **uniquely valuable** and unavailable elsewhere:

#### 1. **Temporal Listening Patterns**
*"When do you actually listen to music?"*

**Metrics:**
- Hour-of-day distribution (peak listening times)
- Day-of-week patterns (weekday vs weekend)
- Monthly trends (seasonal changes)
- Listening streaks (consecutive days)

**Visualizations:**
- Heatmap: Hour x Day of Week
- Line chart: Listening minutes per day over time
- Calendar view: Listening intensity per day

**Why Valuable:**
- Understand your actual habits (not just what you think you listen to)
- Identify music contexts (morning commute, work hours, evening wind-down)

**Example Insights:**
> "You listen most on Tuesday mornings (9-11am) and Friday evenings (6-10pm). Your weekday listening is 2.3x higher than weekends."

---

#### 2. **Artist Evolution & Loyalty**
*"How does your taste change over time?"*

**Metrics:**
- Top artist changes month-over-month
- Artist discovery rate (new artists per month)
- Artist loyalty score (% of listening to repeat artists)
- Genre drift (how genres shift over time)

**Visualizations:**
- Sankey diagram: Top artists migration (Month 1 → Month 2 → Month 3)
- Bar chart race: Top 10 artists over time (animated)
- Line chart: Artist diversity score over time

**Why Valuable:**
- See how your taste evolves (not just static "top artists")
- Identify phases (e.g., "your indie phase in March")

**Example Insights:**
> "In the past 3 months, 40% of your top artists changed. You discovered 12 new artists in November, up from 5 in October."

---

#### 3. **Discovery & Exploration Metrics**
*"How adventurous is your listening?"*

**Metrics:**
- **Artist diversity**: Unique artists / total listening events
- **Genre diversity**: Unique genres / total artists
- **Mainstream score**: Average artist popularity (0-100)
- **New release ratio**: % of tracks released in last year
- **Repeat rate**: % of tracks listened to multiple times

**Visualizations:**
- Spider chart: Exploration profile (diversity, mainstream, new releases)
- Scatter plot: Artist popularity vs your listen count
- Pie chart: New discoveries vs familiar favorites

**Why Valuable:**
- Quantify your music exploration behavior
- Compare short-term vs long-term (are you exploring or settling?)

**Example Insights:**
> "You're a Genre Explorer: 85% diversity score, listening to 23 different genres. Your mainstream score is 45/100, meaning you prefer niche artists. 30% of your listening is new releases from 2025."

---

#### 4. **Popularity Trajectory**
*"Is your taste becoming more mainstream or more niche?"*

**Metrics:**
- Average track popularity over time
- Average artist follower count over time
- % of top 40 hits in your library
- Obscurity index (inverse of popularity)

**Visualizations:**
- Line chart: Mainstream score over time
- Area chart: Distribution of popularity (mainstream vs niche)

**Why Valuable:**
- See if your taste is converging with mainstream or diverging
- Understand your music identity

**Example Insights:**
> "Your taste is becoming more niche: Your mainstream score dropped from 68 to 52 in 6 months. 78% of your top artists have <1M followers."

---

#### 5. **Release Year Preferences**
*"Do you prefer classics or new releases?"*

**Metrics:**
- Average release year of tracks
- Decade distribution (60s, 70s, 80s, 90s, 2000s, 2010s, 2020s)
- % of tracks released in last year
- Temporal range (oldest to newest)

**Visualizations:**
- Histogram: Release year distribution
- Line chart: Average release year over time
- Stacked bar: Decade proportions per month

**Why Valuable:**
- Understand your temporal music preference
- See if you're exploring music history or staying current

**Example Insights:**
> "You're a Nostalgia Listener: 45% of your music is from the 2010s, with an average release year of 2015. You rarely listen to tracks older than 2000."

---

#### 6. **Content Preferences**
*"What types of music do you gravitate toward?"*

**Metrics:**
- Explicit content ratio
- Album vs single preference
- Average track duration
- Track duration distribution

**Visualizations:**
- Pie chart: Explicit vs clean
- Bar chart: Album vs single vs compilation
- Histogram: Track duration distribution

**Why Valuable:**
- Understand your listening style (full albums vs singles)
- See if preferences change over time

**Example Insights:**
> "You're an Album Listener: 78% of your listening is from full albums, not singles. You prefer longer tracks (avg 4:12), skewing toward deep cuts over radio edits."

---

#### 7. **Comparative Analysis**
*"How does your current taste compare to your past?"*

**Metrics:**
- Top tracks: Short-term vs long-term overlap
- Top artists: How many from your all-time favorites are still in your current rotation?
- Genre shift: Current genres vs 6 months ago
- Discovery vs loyalty ratio

**Visualizations:**
- Venn diagram: Short-term top tracks ∩ Long-term top tracks
- Side-by-side bar charts: Top artists now vs 6 months ago
- Flow diagram: Genre changes

**Why Valuable:**
- See if you're sticking with old favorites or exploring
- Identify music phases vs enduring preferences

**Example Insights:**
> "Musical Consistency: 70% of your short-term top tracks are also in your all-time favorites. You're loyal to your core taste."
>
> "Musical Explorer: Only 20% overlap between short-term and long-term. You're constantly discovering new music."

---

### Tier 2: Enhanced Insights (With Audio Features from Kaggle Dataset)

If track is in Kaggle dataset, show:

#### 8. **Audio Feature Profiles**
*"What does your music actually sound like?"*

**Metrics:**
- Average danceability, energy, valence
- Mood score (composite of valence, energy, acousticness)
- Acoustic vs electronic preference
- Instrumental vs vocal preference

**Visualizations:**
- Radar chart: Your audio feature profile
- Violin plot: Feature distributions
- Line chart: Mood score over time

**Example Insights:**
> "Your music is High Energy (0.78) and Moderately Happy (valence: 0.65). You prefer vocal-driven tracks (low instrumentalness) with electronic production (low acousticness)."

---

#### 9. **Context Detection**
*"What activities do you listen to music for?"*

**Metrics:**
- Workout music (high energy, high tempo)
- Focus music (low speechiness, moderate energy, high instrumentalness)
- Party music (high danceability, high energy)
- Relaxation music (low energy, high acousticness)

**Visualizations:**
- Pie chart: Context distribution
- Stacked area chart: Context over time

**Example Insights:**
> "You're a Focus Listener: 45% of your music is optimal for concentration (low speechiness, instrumental). Workout music makes up only 15%."

---

### Tier 3: Future Enhancements (Requires Extended API Access)

Once you get audio features for all tracks:
- Real-time mood trajectory
- Personalized playlist optimization
- Predictive recommendations based on current mood

---

## Implementation Guide

### Step 1: Refactor `data_collection.py`

```python
# app/func/data_collection.py

import pandas as pd
from datetime import datetime, timezone, timedelta
import json
from .s3_storage import save_to_r2, load_from_r2, save_parquet_to_r2, load_parquet_from_r2

def should_collect_snapshot(user_id):
    """
    Check if we need a new snapshot (once per 24 hours)
    """
    try:
        last_updated = load_from_r2(f'users/{user_id}/aggregated/last_updated.json')
        last_time = datetime.fromisoformat(last_updated['timestamp'])
        hours_since = (datetime.now(timezone.utc) - last_time).total_seconds() / 3600
        return hours_since >= 24
    except:
        return True  # No data yet, collect

def collect_user_snapshot(sp, user_id, force=False):
    """
    Collect complete user snapshot

    Args:
        sp: Authenticated Spotipy client
        user_id: Spotify user ID
        force: Force collection even if recent snapshot exists

    Returns:
        snapshot_dir: Path to snapshot directory in R2
    """
    if not force and not should_collect_snapshot(user_id):
        print(f"Snapshot already collected in last 24h, skipping")
        return None

    timestamp = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H-%M-%S')
    snapshot_dir = f'users/{user_id}/snapshots/{timestamp}'

    print(f"Collecting snapshot for {user_id} at {timestamp}")

    # 1. Metadata
    profile = sp.current_user()
    metadata = {
        'timestamp': timestamp,
        'user_id': user_id,
        'display_name': profile.get('display_name'),
        'country': profile.get('country'),
        'product': profile.get('product'),
        'api_version': '2025-11'
    }
    save_to_r2(f'{snapshot_dir}/metadata.json', metadata)

    # 2. Recently Played
    recent = sp.current_user_recently_played(limit=50)
    recent_df = process_recent_tracks(recent)
    save_parquet_to_r2(f'{snapshot_dir}/recent_tracks.parquet', recent_df)

    # 3. Top Tracks (all time ranges)
    for time_range in ['short_term', 'medium_term', 'long_term']:
        top_tracks = sp.current_user_top_tracks(time_range=time_range, limit=50)
        tracks_df = process_top_tracks(top_tracks)
        tracks_df['time_range'] = time_range
        save_parquet_to_r2(
            f'{snapshot_dir}/top_tracks_{time_range.split("_")[0]}.parquet',
            tracks_df
        )

    # 4. Top Artists (all time ranges)
    for time_range in ['short_term', 'medium_term', 'long_term']:
        top_artists = sp.current_user_top_artists(time_range=time_range, limit=50)
        artists_df = process_top_artists(top_artists)
        artists_df['time_range'] = time_range
        save_parquet_to_r2(
            f'{snapshot_dir}/top_artists_{time_range.split("_")[0]}.parquet',
            artists_df
        )

    # 5. Compute Metrics
    metrics = compute_snapshot_metrics(
        recent_df,
        tracks_df,  # Use one of the top tracks dataframes
        artists_df   # Use one of the top artists dataframes
    )
    save_to_r2(f'{snapshot_dir}/computed_metrics.json', metrics)

    # 6. Update Aggregated Data
    update_aggregated_data(user_id, timestamp)

    print(f"Snapshot collected: {snapshot_dir}")
    return snapshot_dir


def process_recent_tracks(recent_response):
    """Convert recent tracks API response to DataFrame"""
    tracks = []
    for item in recent_response['items']:
        track = item['track']
        tracks.append({
            'played_at': item['played_at'],
            'track_id': track['id'],
            'track_name': track['name'],
            'artist_id': track['artists'][0]['id'],
            'artist_name': track['artists'][0]['name'],
            'album_id': track['album']['id'],
            'album_name': track['album']['name'],
            'album_type': track['album']['album_type'],
            'release_date': track['album']['release_date'],
            'popularity': track['popularity'],
            'duration_ms': track['duration_ms'],
            'explicit': track['explicit'],
            'uri': track['uri']
        })

    df = pd.DataFrame(tracks)

    # Add derived columns
    df['played_at_dt'] = pd.to_datetime(df['played_at'])
    df['hour_of_day'] = df['played_at_dt'].dt.hour
    df['day_of_week'] = df['played_at_dt'].dt.dayofweek
    df['duration_seconds'] = df['duration_ms'] / 1000
    df['release_year'] = df['release_date'].str[:4].astype(int)

    return df


def process_top_tracks(top_tracks_response):
    """Convert top tracks API response to DataFrame"""
    tracks = []
    for idx, track in enumerate(top_tracks_response['items']):
        tracks.append({
            'rank': idx + 1,
            'track_id': track['id'],
            'track_name': track['name'],
            'artist_id': track['artists'][0]['id'],
            'artist_name': track['artists'][0]['name'],
            'album_id': track['album']['id'],
            'album_name': track['album']['name'],
            'album_type': track['album']['album_type'],
            'release_date': track['album']['release_date'],
            'popularity': track['popularity'],
            'duration_ms': track['duration_ms'],
            'explicit': track['explicit'],
            'uri': track['uri']
        })

    df = pd.DataFrame(tracks)
    df['duration_seconds'] = df['duration_ms'] / 1000
    df['release_year'] = df['release_date'].str[:4].astype(int)

    return df


def process_top_artists(top_artists_response):
    """Convert top artists API response to DataFrame"""
    artists = []
    for idx, artist in enumerate(top_artists_response['items']):
        artists.append({
            'rank': idx + 1,
            'artist_id': artist['id'],
            'artist_name': artist['name'],
            'genres': ','.join(artist['genres']) if artist['genres'] else '',
            'genre_list': artist['genres'],
            'popularity': artist['popularity'],
            'followers': artist['followers']['total'],
            'uri': artist['uri']
        })

    return pd.DataFrame(artists)


def compute_snapshot_metrics(recent_df, top_tracks_df, top_artists_df):
    """
    Compute derived metrics from snapshot data

    Returns dict of metrics for saving to JSON
    """
    metrics = {
        'recent_tracks': {
            'count': len(recent_df),
            'unique_tracks': recent_df['track_id'].nunique(),
            'unique_artists': recent_df['artist_id'].nunique(),
            'avg_popularity': float(recent_df['popularity'].mean()),
            'explicit_ratio': float(recent_df['explicit'].mean()),
            'avg_duration_seconds': float(recent_df['duration_seconds'].mean()),
            'avg_release_year': float(recent_df['release_year'].mean()),
        },
        'top_tracks': {
            'avg_popularity': float(top_tracks_df['popularity'].mean()),
            'explicit_ratio': float(top_tracks_df['explicit'].mean()),
            'avg_duration_seconds': float(top_tracks_df['duration_seconds'].mean()),
            'album_vs_single': {
                'album': int((top_tracks_df['album_type'] == 'album').sum()),
                'single': int((top_tracks_df['album_type'] == 'single').sum()),
            }
        },
        'top_artists': {
            'count': len(top_artists_df),
            'avg_popularity': float(top_artists_df['popularity'].mean()),
            'avg_followers': float(top_artists_df['followers'].mean()),
            'total_genres': len([g for genres in top_artists_df['genre_list'] for g in genres]),
            'unique_genres': len(set([g for genres in top_artists_df['genre_list'] for g in genres])),
        },
        'diversity': {
            'artist_diversity': float(recent_df['artist_id'].nunique() / len(recent_df)),
            'mainstream_score': float(recent_df['popularity'].mean()),
        }
    }

    return metrics


def update_aggregated_data(user_id, timestamp):
    """
    Update aggregated files from all snapshots

    This combines all historical snapshots into queryable aggregated files
    """
    # Load all snapshots
    # This is a simplified version - you'd implement full snapshot loading

    # Update last_updated.json
    save_to_r2(f'users/{user_id}/aggregated/last_updated.json', {
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'last_snapshot': timestamp
    })

    # TODO: Implement full aggregation logic
    # - Load all snapshot recent_tracks → deduplicate → save to all_recent_tracks.parquet
    # - Load all snapshot metrics → time series → save to all_snapshots_metrics.parquet
```

---

### Step 2: Update `0_Data_Sync.py`

```python
# app/pages/0_Data_Sync.py

import streamlit as st
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from func.ui_components import apply_page_config, get_custom_css
from func.page_auth import require_auth
from func.data_collection import should_collect_snapshot, collect_user_snapshot
import time

apply_page_config()
st.markdown(get_custom_css(), unsafe_allow_html=True)

sp, profile = require_auth()
if not sp:
    st.warning("Please connect your Spotify account to continue.")
    st.stop()

user_id = profile['id']

st.title("📊 Data Sync")

# Check if sync needed
if not should_collect_snapshot(user_id):
    st.success("✅ Your data is up to date!")
    st.info("We collect a new snapshot every 24 hours to track your listening trends.")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Force Refresh", type="secondary"):
            st.session_state['force_sync'] = True
            st.rerun()
    with col2:
        if st.button("Go to Dashboard", type="primary"):
            st.switch_page("pages/1_Dashboard.py")
    st.stop()

# Sync needed
st.info("⏳ Collecting your latest listening data...")

progress_bar = st.progress(0)
status_text = st.empty()

steps = [
    "Fetching recently played tracks...",
    "Fetching top tracks (short-term)...",
    "Fetching top tracks (medium-term)...",
    "Fetching top tracks (long-term)...",
    "Fetching top artists (short-term)...",
    "Fetching top artists (medium-term)...",
    "Fetching top artists (long-term)...",
    "Computing metrics...",
    "Saving to cloud storage...",
]

for i, step in enumerate(steps):
    status_text.text(step)
    progress_bar.progress((i + 1) / len(steps))
    time.sleep(0.5)  # Simulate progress (actual collection happens in background)

# Actually collect data
force = st.session_state.get('force_sync', False)
snapshot_dir = collect_user_snapshot(sp, user_id, force=force)

if snapshot_dir:
    st.success("✅ Data sync complete!")
    st.balloons()
    time.sleep(1)
    st.switch_page("pages/1_Dashboard.py")
else:
    st.error("❌ Data sync failed. Please try again.")
```

---

## Handling Audio Features

Since `sp.audio_features()` returns HTTP 403, use a **lookup strategy**:

### Step 1: Pre-load Kaggle Dataset to R2

```python
# One-time setup script

import pandas as pd
from app.func.s3_storage import save_parquet_to_r2

# Load Kaggle dataset
df_kaggle = pd.read_csv('data/raw/dataset.csv')

# Create lookup table: track_id → audio features
audio_features = df_kaggle[[
    'track_id', 'danceability', 'energy', 'valence',
    'acousticness', 'instrumentalness', 'speechiness',
    'tempo', 'loudness', 'key', 'mode', 'time_signature'
]]

# Save to R2
save_parquet_to_r2('reference_data/kaggle_tracks_audio_features.parquet', audio_features)
```

### Step 2: Enrich User Tracks with Audio Features

```python
def enrich_tracks_with_audio_features(tracks_df):
    """
    Enrich user tracks with audio features from Kaggle dataset

    Returns:
        tracks_df with audio features added (NaN if not in dataset)
    """
    # Load reference data (cache this)
    audio_features = load_parquet_from_r2('reference_data/kaggle_tracks_audio_features.parquet')

    # Merge
    enriched = tracks_df.merge(
        audio_features,
        on='track_id',
        how='left'
    )

    # Add flag for availability
    enriched['has_audio_features'] = ~enriched['danceability'].isna()

    return enriched
```

### Step 3: Conditional Visualizations

```python
# In dashboard page

enriched_tracks = enrich_tracks_with_audio_features(top_tracks_df)

availability = enriched_tracks['has_audio_features'].mean() * 100

st.metric("Audio Features Available", f"{availability:.0f}%")

if availability > 50:
    # Show audio feature charts
    plot_audio_features_radar(enriched_tracks)
else:
    st.warning("Audio features are unavailable for most of your tracks. Showing alternative metrics.")
    # Show popularity-based metrics instead
```

---

## Performance Optimization

### 1. Lazy Loading

Don't load all snapshots on page load:

```python
@st.cache_data(ttl=3600)
def load_latest_snapshot(user_id):
    """Load only the most recent snapshot"""
    # List snapshots, get latest
    # Load only that snapshot
    pass

@st.cache_data(ttl=3600)
def load_aggregated_metrics(user_id):
    """Load pre-computed aggregated metrics"""
    return load_parquet_from_r2(f'users/{user_id}/aggregated/all_snapshots_metrics.parquet')
```

### 2. Pre-compute Aggregations

Run aggregation after each snapshot collection:

```python
def update_aggregated_data(user_id, timestamp):
    """Update aggregated files"""
    # Load all snapshots
    all_snapshots = list_snapshots(user_id)

    # Combine all recent_tracks
    all_recent_tracks = []
    for snapshot in all_snapshots:
        df = load_parquet_from_r2(f'{snapshot}/recent_tracks.parquet')
        df['snapshot_timestamp'] = snapshot
        all_recent_tracks.append(df)

    combined = pd.concat(all_recent_tracks, ignore_index=True)

    # Deduplicate by played_at
    combined = combined.drop_duplicates(subset=['played_at', 'track_id'])

    # Save
    save_parquet_to_r2(
        f'users/{user_id}/aggregated/all_recent_tracks.parquet',
        combined
    )
```

### 3. Parquet Partitioning

For large historical data, partition by month:

```
users/{user_id}/aggregated/recent_tracks/
    year=2025/month=11/data.parquet
    year=2025/month=10/data.parquet
    ...
```

---

## Summary & Next Steps

### ✅ Recommended Architecture

**Storage**: Parquet files in Cloudflare R2
**Structure**: User-scoped snapshots + pre-computed aggregations
**Collection**: Once per 24 hours, user-triggered refresh option
**Format**: Parquet for analytics, JSON for metadata

### 🎯 Unique Value Propositions

1. **Temporal Intelligence**: Hour/day/week patterns over time
2. **Artist Evolution**: How your taste changes month-to-month
3. **Discovery Metrics**: Quantify your exploration behavior
4. **Comparative Analysis**: Short-term vs long-term preferences
5. **Continuous Insights**: Weekly engagement, not just annual Wrapped

### 🚀 Implementation Priority

**Phase 1 (Week 6-7)**: ✅ Already Complete
- Data collection working
- Basic metrics computed
- Dashboard showing recent/top tracks

**Phase 2 (Week 8-9)**: 🔨 Recommended Next Steps
1. Refactor `data_collection.py` with smart scheduling
2. Implement aggregated data files
3. Build temporal analysis visualizations
4. Add artist evolution tracking
5. Build discovery metrics dashboard

**Phase 3 (Week 10+)**: 🎯 Advanced Features
1. Audio features enrichment from Kaggle
2. Predictive modeling (if audio features available)
3. Playlist optimization recommendations
4. Export data to CSV/JSON for users

---

## Decision Matrix

| Requirement | Database | Parquet Files | Hybrid |
|-------------|----------|---------------|--------|
| Single-user analytics | ❌ Overkill | ✅ Perfect | ⚠️ Complex |
| Time-series data | ⚠️ OK | ✅ Excellent | ✅ Excellent |
| Cost | ❌ $20-50/mo | ✅ $0.50/mo | ⚠️ Varies |
| Simplicity | ❌ Complex | ✅ Simple | ⚠️ Moderate |
| Already implemented | ❌ No | ✅ Yes (R2) | ❌ No |
| Query speed | ✅ Fast | ⚠️ Load time | ✅ Fast |
| Scalability | ✅ High | ✅ High | ✅ High |

**Winner**: **Parquet Files in R2** 🏆

---

## Questions to Answer Before Implementing

1. ✅ **Storage backend**: Cloudflare R2 (already working)
2. ✅ **File format**: Parquet for data, JSON for metadata
3. ✅ **Collection frequency**: Once per 24 hours
4. ✅ **Aggregation strategy**: Pre-compute on collection
5. ⏳ **Retention policy**: Keep all snapshots? (Recommend: Yes, storage is cheap)
6. ⏳ **Audio features**: Kaggle lookup table + request extended API access
7. ⏳ **User quotas**: Unlimited storage per user? (Recommend: Yes for now)

Let me know if you want me to implement any specific part of this architecture!
