"""
Data Collection Functions - First-Time User Optimized
Collect comprehensive user listening data for instant dashboard value
"""

import pandas as pd
import streamlit as st
from datetime import datetime, timezone, timedelta
import os
import sys
import time
import json

# Import data fetching and processing functions using relative imports
from .data_fetching import (
    fetch_recently_played,
    fetch_top_tracks,
    fetch_top_artists,
    fetch_user_profile
)
from .data_processing import (
    process_recent_tracks,
    process_top_tracks,
    calculate_diversity_score
)
from .s3_storage import upload_dataframe_to_s3, get_bucket_name, get_s3_client

# Import feature engineering from src
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
try:
    from src.feature_engineering import create_composite_features, classify_context
except ImportError:
    create_composite_features = None
    classify_context = None


def should_refresh_data(user_id):
    """
    Check if we need to refresh current snapshot
    Returns True if >24 hours since last sync OR no data exists

    Args:
        user_id: Spotify user ID

    Returns:
        bool: True if refresh needed
    """
    try:
        bucket_name = get_bucket_name()
        if not bucket_name:
            return True

        s3_client = get_s3_client()

        # Try to load metadata from current/ directory
        metadata_key = f'users/{user_id}/current/metadata.json'

        try:
            response = s3_client.get_object(Bucket=bucket_name, Key=metadata_key)
            metadata_content = response['Body'].read().decode('utf-8')
            metadata = json.loads(metadata_content)

            last_sync = datetime.fromisoformat(metadata['last_sync'])
            hours_since = (datetime.now(timezone.utc) - last_sync).total_seconds() / 3600

            return hours_since >= 24  # Refresh if >24 hours
        except:
            return True  # No metadata found, refresh needed

    except Exception as e:
        print(f"Error checking refresh status: {e}")
        return True  # Default to refresh on error


def collect_comprehensive_snapshot(sp, user_id, force=False):
    """
    Collect comprehensive snapshot for all dashboards - First-time user optimized

    Target: <90 seconds total
    API Calls: 8 total (well within 180/min rate limit)

    Collects:
    - 50 recently played tracks
    - Top 50 tracks (short/medium/long term)
    - Top 50 artists (short/medium/long term)

    Saves to:
    - users/{user_id}/current/ → Used by all dashboards
    - users/{user_id}/snapshots/{timestamp}/ → Used by Deep User page only

    Args:
        sp: Authenticated Spotipy client
        user_id: Spotify user ID
        force: Force refresh even if <24hrs

    Returns:
        tuple: (success: bool, snapshot_timestamp: str)
    """
    if not force and not should_refresh_data(user_id):
        return False, None  # Skip refresh

    print(f"🔄 Starting comprehensive data sync for {user_id}")
    start_time = time.time()

    timestamp = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H-%M-%S')
    timestamp_iso = datetime.now(timezone.utc).isoformat()

    try:
        # ========================================
        # Step 1: User Profile (1 API call)
        # ========================================
        print("  📋 Fetching user profile...")
        profile = fetch_user_profile(sp)
        if not profile:
            raise Exception("Failed to fetch user profile")

        metadata = {
            'last_sync': timestamp_iso,
            'snapshot_timestamp': timestamp,
            'user_id': user_id,
            'display_name': profile.get('display_name'),
            'country': profile.get('country'),
            'product': profile.get('product'),
            'api_version': '2025-11'
        }

        # ========================================
        # Step 2: Recently Played (1 API call)
        # ========================================
        print("  🎵 Fetching recently played tracks...")
        recent_items = fetch_recently_played(sp, limit=50)
        if not recent_items:
            raise Exception("Failed to fetch recent tracks")

        recent_df = process_recent_tracks(recent_items, sp)
        if recent_df.empty:
            raise Exception("No recent tracks data")

        recent_df['snapshot_timestamp'] = timestamp_iso
        recent_df['user_id'] = user_id
        time.sleep(0.5)  # Small delay between requests

        # ========================================
        # Step 3: Top Tracks - All Time Ranges (3 API calls)
        # ========================================
        print("  🏆 Fetching top tracks (short-term)...")
        top_tracks_short = fetch_top_tracks(sp, time_range='short_term', limit=50)
        tracks_short_df = process_top_tracks_data(top_tracks_short, sp, 'short_term', timestamp_iso, user_id)
        time.sleep(0.5)

        print("  🏆 Fetching top tracks (medium-term)...")
        top_tracks_medium = fetch_top_tracks(sp, time_range='medium_term', limit=50)
        tracks_medium_df = process_top_tracks_data(top_tracks_medium, sp, 'medium_term', timestamp_iso, user_id)
        time.sleep(0.5)

        print("  🏆 Fetching top tracks (long-term)...")
        top_tracks_long = fetch_top_tracks(sp, time_range='long_term', limit=50)
        tracks_long_df = process_top_tracks_data(top_tracks_long, sp, 'long_term', timestamp_iso, user_id)
        time.sleep(0.5)

        # ========================================
        # Step 4: Top Artists - All Time Ranges (3 API calls)
        # ========================================
        print("  👥 Fetching top artists (short-term)...")
        top_artists_short = fetch_top_artists(sp, time_range='short_term', limit=50)
        artists_short_df = process_top_artists_data(top_artists_short, 'short_term', timestamp_iso, user_id)
        time.sleep(0.5)

        print("  👥 Fetching top artists (medium-term)...")
        top_artists_medium = fetch_top_artists(sp, time_range='medium_term', limit=50)
        artists_medium_df = process_top_artists_data(top_artists_medium, 'medium_term', timestamp_iso, user_id)
        time.sleep(0.5)

        print("  👥 Fetching top artists (long-term)...")
        top_artists_long = fetch_top_artists(sp, time_range='long_term', limit=50)
        artists_long_df = process_top_artists_data(top_artists_long, 'long_term', timestamp_iso, user_id)

        # ========================================
        # Step 5: Compute Derived Metrics
        # ========================================
        print("  📊 Computing metrics...")
        metrics = compute_snapshot_metrics(
            recent_df,
            tracks_short_df, tracks_medium_df, tracks_long_df,
            artists_short_df, artists_medium_df, artists_long_df
        )

        # ========================================
        # Step 6: Save to R2 (current/ directory) - Used by ALL dashboards
        # ========================================
        print("  💾 Saving to current/ directory (for dashboards)...")
        bucket_name = get_bucket_name()
        if not bucket_name:
            raise Exception("S3 bucket not configured")

        # Save metadata
        save_json_to_r2(bucket_name, f'users/{user_id}/current/metadata.json', metadata)

        # Save all dataframes to current/
        save_parquet_to_r2(bucket_name, f'users/{user_id}/current/recent_tracks.parquet', recent_df)
        save_parquet_to_r2(bucket_name, f'users/{user_id}/current/top_tracks_short.parquet', tracks_short_df)
        save_parquet_to_r2(bucket_name, f'users/{user_id}/current/top_tracks_medium.parquet', tracks_medium_df)
        save_parquet_to_r2(bucket_name, f'users/{user_id}/current/top_tracks_long.parquet', tracks_long_df)
        save_parquet_to_r2(bucket_name, f'users/{user_id}/current/top_artists_short.parquet', artists_short_df)
        save_parquet_to_r2(bucket_name, f'users/{user_id}/current/top_artists_medium.parquet', artists_medium_df)
        save_parquet_to_r2(bucket_name, f'users/{user_id}/current/top_artists_long.parquet', artists_long_df)
        save_json_to_r2(bucket_name, f'users/{user_id}/current/computed_metrics.json', metrics)

        # ========================================
        # Step 7: Archive to snapshots/ (for Deep User page ONLY)
        # ========================================
        print("  📦 Archiving snapshot for historical analysis...")
        snapshot_dir = f'users/{user_id}/snapshots/{timestamp}'

        save_json_to_r2(bucket_name, f'{snapshot_dir}/metadata.json', metadata)
        save_parquet_to_r2(bucket_name, f'{snapshot_dir}/recent_tracks.parquet', recent_df)
        save_parquet_to_r2(bucket_name, f'{snapshot_dir}/top_tracks_short.parquet', tracks_short_df)
        save_parquet_to_r2(bucket_name, f'{snapshot_dir}/top_tracks_medium.parquet', tracks_medium_df)
        save_parquet_to_r2(bucket_name, f'{snapshot_dir}/top_tracks_long.parquet', tracks_long_df)
        save_parquet_to_r2(bucket_name, f'{snapshot_dir}/top_artists_short.parquet', artists_short_df)
        save_parquet_to_r2(bucket_name, f'{snapshot_dir}/top_artists_medium.parquet', artists_medium_df)
        save_parquet_to_r2(bucket_name, f'{snapshot_dir}/top_artists_long.parquet', artists_long_df)
        save_json_to_r2(bucket_name, f'{snapshot_dir}/computed_metrics.json', metrics)

        elapsed = time.time() - start_time
        print(f"  ✅ Sync complete in {elapsed:.1f} seconds")

        return True, timestamp

    except Exception as e:
        print(f"  ❌ Sync failed: {e}")
        import traceback
        traceback.print_exc()
        return False, None


def process_top_tracks_data(top_tracks, sp, time_range, timestamp_iso, user_id):
    """Process top tracks API response into DataFrame"""
    if not top_tracks:
        return pd.DataFrame()

    top_df = process_top_tracks(top_tracks, sp)
    if top_df.empty:
        return pd.DataFrame()

    top_df['snapshot_timestamp'] = timestamp_iso
    top_df['user_id'] = user_id
    top_df['time_range'] = time_range

    # Add derived columns
    if 'release_date' in top_df.columns:
        top_df['release_year'] = top_df['release_date'].str[:4].astype(int)

    if 'duration_ms' in top_df.columns:
        top_df['duration_seconds'] = top_df['duration_ms'] / 1000

    return top_df


def process_top_artists_data(top_artists, time_range, timestamp_iso, user_id):
    """Process top artists API response into DataFrame"""
    if not top_artists:
        return pd.DataFrame()

    artists_data = []
    for idx, artist in enumerate(top_artists):
        genre_list = artist.get('genres', [])
        artists_data.append({
            'rank': idx + 1,
            'artist_id': artist.get('id'),
            'artist_name': artist.get('name'),
            'genres': ', '.join(genre_list),
            'genre_list': genre_list,  # Keep as list for processing
            'popularity': artist.get('popularity'),
            'followers': artist.get('followers', {}).get('total'),
            'time_range': time_range,
            'snapshot_timestamp': timestamp_iso,
            'user_id': user_id
        })

    return pd.DataFrame(artists_data)


def compute_snapshot_metrics(recent_df, tracks_s, tracks_m, tracks_l, artists_s, artists_m, artists_l):
    """
    Compute derived metrics from snapshot data
    Returns dict suitable for JSON serialization
    """
    # Combine all top tracks for overall stats
    all_top_tracks = pd.concat([tracks_s, tracks_m, tracks_l]).drop_duplicates(subset=['track_id'])
    all_top_artists = pd.concat([artists_s, artists_m, artists_l]).drop_duplicates(subset=['artist_id'])

    # Get all genres from all time ranges
    all_genres = []
    for df in [artists_s, artists_m, artists_l]:
        if 'genre_list' in df.columns:
            for genres in df['genre_list']:
                all_genres.extend(genres)
    unique_genres = len(set(all_genres))

    # Calculate taste consistency (overlap between short-term and long-term)
    short_track_ids = set(tracks_s['track_id']) if not tracks_s.empty else set()
    long_track_ids = set(tracks_l['track_id']) if not tracks_l.empty else set()
    overlap = len(short_track_ids & long_track_ids)
    overlap_pct = (overlap / 50 * 100) if len(short_track_ids) > 0 else 0

    # Helper function to safely get column mean
    def safe_mean(df, column, default=0):
        """Safely calculate mean of a column, return default if column missing"""
        if df.empty or column not in df.columns:
            return default
        return float(df[column].mean())

    metrics = {
        'snapshot_timestamp': recent_df['snapshot_timestamp'].iloc[0] if not recent_df.empty and 'snapshot_timestamp' in recent_df.columns else None,
        'user_id': recent_df['user_id'].iloc[0] if not recent_df.empty and 'user_id' in recent_df.columns else None,

        # Recent listening metrics
        'recent_listening': {
            'total_tracks': len(recent_df),
            'unique_tracks': recent_df['track_id'].nunique() if not recent_df.empty else 0,
            'unique_artists': recent_df['artist_name'].nunique() if not recent_df.empty else 0,
            'avg_popularity': safe_mean(recent_df, 'popularity'),
            'explicit_ratio': safe_mean(recent_df, 'explicit'),
            'avg_duration_minutes': safe_mean(recent_df, 'duration_ms') / 1000 if 'duration_ms' in recent_df.columns else 0,
            'avg_release_year': safe_mean(recent_df, 'release_year'),
        },

        # Top tracks metrics by time range
        'top_tracks': {
            'short_term_avg_popularity': safe_mean(tracks_s, 'popularity'),
            'medium_term_avg_popularity': safe_mean(tracks_m, 'popularity'),
            'long_term_avg_popularity': safe_mean(tracks_l, 'popularity'),
            'short_explicit_ratio': safe_mean(tracks_s, 'explicit'),
            'medium_explicit_ratio': safe_mean(tracks_m, 'explicit'),
            'long_explicit_ratio': safe_mean(tracks_l, 'explicit'),
        },

        # Top artists metrics by time range
        'top_artists': {
            'short_term_avg_popularity': safe_mean(artists_s, 'popularity'),
            'medium_term_avg_popularity': safe_mean(artists_m, 'popularity'),
            'long_term_avg_popularity': safe_mean(artists_l, 'popularity'),
            'short_term_avg_followers': safe_mean(artists_s, 'followers'),
            'medium_term_avg_followers': safe_mean(artists_m, 'followers'),
            'long_term_avg_followers': safe_mean(artists_l, 'followers'),
        },

        # Diversity metrics
        'diversity': {
            'artist_diversity': float(recent_df['artist_name'].nunique() / len(recent_df)) if not recent_df.empty and len(recent_df) > 0 else 0,
            'mainstream_score': safe_mean(recent_df, 'popularity'),
            'unique_genres': unique_genres,
        },

        # Taste consistency (short vs long term)
        'taste_consistency': {
            'short_vs_long_overlap': overlap,
            'short_vs_long_overlap_pct': float(overlap_pct),
            'consistency_type': 'Musical Consistency' if overlap_pct > 60 else 'Musical Explorer'
        }
    }

    return metrics


def save_parquet_to_r2(bucket_name, key, df):
    """Save DataFrame to R2 as parquet"""
    if df.empty:
        print(f"  ⚠️ Skipping empty DataFrame: {key}")
        return False

    try:
        # Use existing upload function
        success = upload_dataframe_to_s3(df, bucket_name, key)
        if success:
            print(f"  ✓ Saved: {key}")
        return success
    except Exception as e:
        print(f"  ✗ Failed to save {key}: {e}")
        return False


def save_json_to_r2(bucket_name, key, data):
    """Save JSON data to R2"""
    try:
        s3_client = get_s3_client()
        json_str = json.dumps(data, indent=2, default=str)

        s3_client.put_object(
            Bucket=bucket_name,
            Key=key,
            Body=json_str.encode('utf-8'),
            ContentType='application/json'
        )
        print(f"  ✓ Saved: {key}")
        return True
    except Exception as e:
        print(f"  ✗ Failed to save {key}: {e}")
        return False


# ========================================
# Legacy Functions (Keep for compatibility)
# ========================================

def collect_snapshot(sp, user_id):
    """
    Legacy function - redirects to new comprehensive snapshot
    Kept for backwards compatibility

    Args:
        sp: Authenticated Spotipy client
        user_id: Spotify user ID

    Returns:
        dict: Dictionary containing all collected DataFrames and metadata
    """
    success, timestamp = collect_comprehensive_snapshot(sp, user_id, force=True)

    if success:
        # Return data in old format for compatibility
        bucket_name = get_bucket_name()
        snapshot_data = {
            'user_id': user_id,
            'snapshot_timestamp': timestamp,
            'recent_tracks': load_dataframe_from_r2(bucket_name, f'users/{user_id}/current/recent_tracks.parquet'),
            'top_tracks_short': load_dataframe_from_r2(bucket_name, f'users/{user_id}/current/top_tracks_short.parquet'),
            'top_tracks_medium': load_dataframe_from_r2(bucket_name, f'users/{user_id}/current/top_tracks_medium.parquet'),
            'top_tracks_long': load_dataframe_from_r2(bucket_name, f'users/{user_id}/current/top_tracks_long.parquet'),
            'top_artists_short': load_dataframe_from_r2(bucket_name, f'users/{user_id}/current/top_artists_short.parquet'),
            'top_artists_medium': load_dataframe_from_r2(bucket_name, f'users/{user_id}/current/top_artists_medium.parquet'),
            'top_artists_long': load_dataframe_from_r2(bucket_name, f'users/{user_id}/current/top_artists_long.parquet'),
            'metrics': None
        }
        return snapshot_data
    else:
        return None


def load_dataframe_from_r2(bucket_name, key):
    """Load DataFrame from R2"""
    try:
        s3_client = get_s3_client()
        response = s3_client.get_object(Bucket=bucket_name, Key=key)
        return pd.read_parquet(response['Body'])
    except:
        return None


@st.cache_data(ttl=300)  # Cache for 5 minutes
def get_user_snapshot_count(_sp, user_id):
    """
    Get count of existing snapshots for a user

    Args:
        _sp: Spotipy client (for cache key)
        user_id: Spotify user ID

    Returns:
        int: Number of snapshots
    """
    try:
        bucket_name = get_bucket_name()
        if not bucket_name:
            return 0

        s3_client = get_s3_client()

        # List objects in snapshots/ directory
        response = s3_client.list_objects_v2(
            Bucket=bucket_name,
            Prefix=f'users/{user_id}/snapshots/',
            Delimiter='/'
        )

        # Count unique snapshot directories
        if 'CommonPrefixes' in response:
            return len(response['CommonPrefixes'])
        else:
            return 0

    except Exception as e:
        print(f"Error counting snapshots: {e}")
        return 0
