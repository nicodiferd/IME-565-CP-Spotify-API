"""
Dashboard Helper Functions
Utilities for loading current snapshot data in dashboard pages
"""

import streamlit as st
import pandas as pd
import json
from .s3_storage import get_s3_client, get_bucket_name


@st.cache_data(ttl=3600)  # Cache for 1 hour
def load_current_snapshot(user_id):
    """
    Load current snapshot data for dashboard display
    All dashboards (except Deep User) should use this function

    This loads from users/{user_id}/current/ directory which contains
    the most recent sync data.

    Args:
        user_id: Spotify user ID

    Returns:
        dict: Dictionary containing all snapshot data
            {
                'recent_tracks': DataFrame,
                'top_tracks': {
                    'short': DataFrame,
                    'medium': DataFrame,
                    'long': DataFrame
                },
                'top_artists': {
                    'short': DataFrame,
                    'medium': DataFrame,
                    'long': DataFrame
                },
                'metadata': dict,
                'metrics': dict
            }

    Raises:
        Exception: If data cannot be loaded (user needs to sync)
    """
    try:
        bucket_name = get_bucket_name()
        if not bucket_name:
            raise Exception("S3 bucket not configured")

        s3_client = get_s3_client()

        # Load metadata
        metadata = load_json_from_r2(s3_client, bucket_name, f'users/{user_id}/current/metadata.json')

        # Load all dataframes
        recent_tracks = load_parquet_from_r2(s3_client, bucket_name, f'users/{user_id}/current/recent_tracks.parquet')
        top_tracks_short = load_parquet_from_r2(s3_client, bucket_name, f'users/{user_id}/current/top_tracks_short.parquet')
        top_tracks_medium = load_parquet_from_r2(s3_client, bucket_name, f'users/{user_id}/current/top_tracks_medium.parquet')
        top_tracks_long = load_parquet_from_r2(s3_client, bucket_name, f'users/{user_id}/current/top_tracks_long.parquet')
        top_artists_short = load_parquet_from_r2(s3_client, bucket_name, f'users/{user_id}/current/top_artists_short.parquet')
        top_artists_medium = load_parquet_from_r2(s3_client, bucket_name, f'users/{user_id}/current/top_artists_medium.parquet')
        top_artists_long = load_parquet_from_r2(s3_client, bucket_name, f'users/{user_id}/current/top_artists_long.parquet')
        metrics = load_json_from_r2(s3_client, bucket_name, f'users/{user_id}/current/computed_metrics.json')

        return {
            'recent_tracks': recent_tracks,
            'top_tracks': {
                'short': top_tracks_short,
                'medium': top_tracks_medium,
                'long': top_tracks_long
            },
            'top_artists': {
                'short': top_artists_short,
                'medium': top_artists_medium,
                'long': top_artists_long
            },
            'metadata': metadata,
            'metrics': metrics
        }

    except Exception as e:
        raise Exception(f"Failed to load snapshot data: {e}")


def load_parquet_from_r2(s3_client, bucket_name, key):
    """Load parquet file from R2"""
    try:
        import io
        response = s3_client.get_object(Bucket=bucket_name, Key=key)
        # Read the full content into memory first (required for pandas.read_parquet)
        parquet_bytes = response['Body'].read()
        return pd.read_parquet(io.BytesIO(parquet_bytes))
    except Exception as e:
        raise Exception(f"Failed to load {key}: {e}")


def load_json_from_r2(s3_client, bucket_name, key):
    """Load JSON file from R2"""
    try:
        response = s3_client.get_object(Bucket=bucket_name, Key=key)
        content = response['Body'].read().decode('utf-8')
        return json.loads(content)
    except Exception as e:
        raise Exception(f"Failed to load {key}: {e}")


def handle_missing_data(redirect_to_sync=True):
    """
    Display error message when data is missing and optionally redirect to sync

    Args:
        redirect_to_sync: If True, show button to go to Data Sync page
    """
    st.error("❌ No data found")
    st.info("""
    **It looks like you haven't synced your data yet.**

    Please complete the Data Sync process to populate your dashboard with insights.
    """)

    if redirect_to_sync:
        if st.button("➡️ Go to Data Sync", type="primary"):
            st.switch_page("pages/0_Data_Sync.py")

    st.stop()


def display_sync_status(metadata):
    """
    Display last sync time and freshness indicator

    Args:
        metadata: Metadata dict from current snapshot
    """
    from datetime import datetime, timezone

    last_sync_str = metadata.get('last_sync')
    if not last_sync_str:
        return

    try:
        last_sync = datetime.fromisoformat(last_sync_str)
        time_ago = datetime.now(timezone.utc) - last_sync
        hours_ago = int(time_ago.total_seconds() / 3600)

        if hours_ago < 1:
            freshness = "🟢 Fresh (synced < 1 hour ago)"
        elif hours_ago < 12:
            freshness = f"🟢 Fresh (synced {hours_ago} hours ago)"
        elif hours_ago < 24:
            freshness = f"🟡 Recent (synced {hours_ago} hours ago)"
        else:
            days_ago = hours_ago // 24
            freshness = f"🟠 Stale (synced {days_ago} days ago)"

        st.caption(freshness)

    except:
        st.caption("🔵 Recently synced")


# ============================================================================
# Quick Access Functions
# ============================================================================

def get_recent_tracks(user_id):
    """Get just recent tracks DataFrame"""
    data = load_current_snapshot(user_id)
    return data['recent_tracks']


def get_top_tracks(user_id, time_range='short'):
    """
    Get top tracks for specific time range

    Args:
        user_id: Spotify user ID
        time_range: 'short', 'medium', or 'long'

    Returns:
        DataFrame: Top tracks for specified time range
    """
    data = load_current_snapshot(user_id)
    return data['top_tracks'][time_range]


def get_top_artists(user_id, time_range='short'):
    """
    Get top artists for specific time range

    Args:
        user_id: Spotify user ID
        time_range: 'short', 'medium', or 'long'

    Returns:
        DataFrame: Top artists for specified time range
    """
    data = load_current_snapshot(user_id)
    return data['top_artists'][time_range]


def get_metrics(user_id):
    """Get computed metrics dict"""
    data = load_current_snapshot(user_id)
    return data['metrics']


# ============================================================================
# Kaggle Audio Features Integration
# ============================================================================

@st.cache_data(ttl=86400)  # Cache for 24 hours
def load_kaggle_dataset():
    """
    Load Kaggle Spotify tracks dataset with audio features

    Returns:
        DataFrame with ~114k tracks and full audio features
        Columns: track_id, track_name, artists, popularity, duration_ms, explicit,
                danceability, energy, valence, acousticness, instrumentalness,
                speechiness, tempo, loudness, liveness, key, mode, time_signature, track_genre
    """
    import pandas as pd
    import os

    # Path to Kaggle dataset
    kaggle_path = os.path.join('data', 'raw', 'dataset.csv')

    if not os.path.exists(kaggle_path):
        print(f"⚠️ Kaggle dataset not found at: {kaggle_path}")
        return pd.DataFrame()

    try:
        # Load dataset - select only needed columns for performance
        df = pd.read_csv(kaggle_path, usecols=[
            'track_id', 'track_name', 'artists', 'album_name', 'track_genre',
            'popularity', 'duration_ms', 'explicit',
            'danceability', 'energy', 'valence', 'acousticness',
            'instrumentalness', 'speechiness', 'tempo', 'loudness',
            'liveness', 'key', 'mode', 'time_signature'
        ])

        print(f"✓ Loaded Kaggle dataset: {len(df):,} tracks with audio features")
        return df

    except Exception as e:
        print(f"❌ Failed to load Kaggle dataset: {e}")
        return pd.DataFrame()


def enrich_with_audio_features(user_df, verbose=True):
    """
    Enrich user's tracks with audio features from Kaggle dataset

    Args:
        user_df: DataFrame with user's tracks (must have 'track_id' column)
        verbose: Print enrichment statistics

    Returns:
        DataFrame with audio features merged and composite features added
        Includes: mood_score, grooviness, focus_score, relaxation_score, context
    """
    import pandas as pd
    import sys
    import os

    # Add src/ to path to import feature engineering functions
    src_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'src')
    if src_path not in sys.path:
        sys.path.insert(0, src_path)

    from feature_engineering import create_composite_features, add_context_classification

    if user_df.empty:
        return user_df

    if 'track_id' not in user_df.columns:
        if verbose:
            print("⚠️ Cannot enrich: 'track_id' column not found")
        return user_df

    # Load Kaggle dataset
    kaggle_df = load_kaggle_dataset()

    if kaggle_df.empty:
        if verbose:
            print("⚠️ Kaggle dataset not available - proceeding without audio features")
        return user_df

    # Track original row count
    original_count = len(user_df)

    # Merge with Kaggle dataset by track_id
    # Use left join to keep all user tracks, even if not in Kaggle dataset
    # Suffix '_kaggle' for any conflicting columns
    enriched_df = user_df.merge(
        kaggle_df,
        on='track_id',
        how='left',
        suffixes=('', '_kaggle')
    )

    # Count how many tracks got audio features
    audio_feature_cols = ['danceability', 'energy', 'valence', 'acousticness',
                         'instrumentalness', 'speechiness', 'tempo']
    tracks_with_features = enriched_df[audio_feature_cols[0]].notna().sum()
    coverage_pct = (tracks_with_features / original_count * 100) if original_count > 0 else 0

    if verbose:
        print(f"\n🎵 Audio Features Enrichment:")
        print(f"  Total tracks: {original_count}")
        print(f"  Tracks with audio features: {tracks_with_features} ({coverage_pct:.1f}%)")
        print(f"  Tracks without audio features: {original_count - tracks_with_features}")

    # Only create composite features if we have audio features
    if tracks_with_features > 0:
        # Create composite features (mood, grooviness, focus, relaxation)
        enriched_df = create_composite_features(enriched_df)

        # Add context classification (Workout, Focus, Party, Relaxation, General)
        enriched_df = add_context_classification(enriched_df)

        if verbose:
            print(f"  ✓ Added composite features and context classification")
    else:
        if verbose:
            print(f"  ⚠️ No audio features available - skipping composite features")

    return enriched_df


def get_audio_features_coverage(df):
    """
    Calculate percentage of tracks that have audio features

    Args:
        df: DataFrame with tracks

    Returns:
        dict with coverage statistics
    """
    if df.empty:
        return {'total_tracks': 0, 'tracks_with_features': 0, 'coverage_pct': 0}

    audio_feature_cols = ['danceability', 'energy', 'valence']

    if not any(col in df.columns for col in audio_feature_cols):
        return {'total_tracks': len(df), 'tracks_with_features': 0, 'coverage_pct': 0}

    # Use first available audio feature column to check coverage
    check_col = next((col for col in audio_feature_cols if col in df.columns), None)

    if check_col:
        tracks_with_features = df[check_col].notna().sum()
        coverage_pct = (tracks_with_features / len(df) * 100)

        return {
            'total_tracks': len(df),
            'tracks_with_features': int(tracks_with_features),
            'coverage_pct': float(coverage_pct)
        }

    return {'total_tracks': len(df), 'tracks_with_features': 0, 'coverage_pct': 0}


# ============================================================================
# Example Usage in Dashboard Pages
# ============================================================================

"""
Example dashboard page implementation:

```python
import streamlit as st
from func.page_auth import require_auth
from func.dashboard_helpers import load_current_snapshot, handle_missing_data, display_sync_status

# Authenticate
sp, profile = require_auth()
if not sp:
    st.stop()

user_id = profile['id']

# Load current snapshot
try:
    data = load_current_snapshot(user_id)
except Exception as e:
    handle_missing_data(redirect_to_sync=True)

# Show sync status
display_sync_status(data['metadata'])

# Use the data
st.header("🎵 Your Music Dashboard")

# Example: Top artists
st.subheader("Top Artists This Month")
top_5 = data['top_artists']['short'].head(5)
st.dataframe(top_5[['rank', 'artist_name', 'popularity', 'genres']])

# Example: Taste consistency
overlap_pct = data['metrics']['taste_consistency']['short_vs_long_overlap_pct']
if overlap_pct > 60:
    st.success(f"Musical Consistency: {overlap_pct:.0f}% overlap between current and all-time favorites!")
else:
    st.info(f"Musical Explorer: Only {overlap_pct:.0f}% overlap - you're always discovering new music!")

# Example: Recent listening
st.subheader("Recent Listening Patterns")
recent = data['recent_tracks']
st.write(f"You've listened to {len(recent)} tracks recently")
st.write(f"From {recent['artist_name'].nunique()} different artists")
```
"""
