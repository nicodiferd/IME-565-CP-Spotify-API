"""
Data Collection Functions
Collect user listening data and prepare for storage
"""

import pandas as pd
import streamlit as st
from datetime import datetime
import os
import sys

# Import data fetching and processing functions
from app.func.data_fetching import (
    fetch_recently_played,
    fetch_top_tracks,
    fetch_top_artists,
    fetch_user_profile
)
from app.func.data_processing import (
    process_recent_tracks,
    process_top_tracks,
    calculate_diversity_score
)
from app.func.s3_storage import upload_dataframe_to_s3, get_bucket_name

# Import feature engineering from src
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
try:
    from src.feature_engineering import create_composite_features, classify_context
except ImportError:
    create_composite_features = None
    classify_context = None


def collect_snapshot(sp, user_id):
    """
    Collect a complete data snapshot for a user

    Args:
        sp: Authenticated Spotipy client
        user_id: Spotify user ID

    Returns:
        dict: Dictionary containing all collected DataFrames and metadata
    """
    snapshot_timestamp = datetime.now().isoformat()

    snapshot_data = {
        'user_id': user_id,
        'snapshot_timestamp': snapshot_timestamp,
        'recent_tracks': None,
        'top_tracks_short': None,
        'top_tracks_medium': None,
        'top_tracks_long': None,
        'top_artists_short': None,
        'top_artists_medium': None,
        'top_artists_long': None,
        'metrics': None
    }

    with st.spinner("📸 Collecting your listening snapshot..."):

        # Recently played tracks
        st.write("Fetching recently played tracks...")
        recent_items = fetch_recently_played(sp, limit=50)
        if recent_items:
            recent_df = process_recent_tracks(recent_items, sp)
            if not recent_df.empty:
                recent_df['snapshot_timestamp'] = snapshot_timestamp
                recent_df['user_id'] = user_id
                snapshot_data['recent_tracks'] = recent_df

        # Top tracks - all time ranges
        for time_range, label in [('short_term', 'short'), ('medium_term', 'medium'), ('long_term', 'long')]:
            st.write(f"Fetching top tracks ({label} term)...")
            top_tracks = fetch_top_tracks(sp, time_range=time_range, limit=50)
            if top_tracks:
                top_df = process_top_tracks(top_tracks, sp)
                if not top_df.empty:
                    top_df['snapshot_timestamp'] = snapshot_timestamp
                    top_df['user_id'] = user_id
                    top_df['time_range'] = time_range
                    snapshot_data[f'top_tracks_{label}'] = top_df

        # Top artists - all time ranges
        for time_range, label in [('short_term', 'short'), ('medium_term', 'medium'), ('long_term', 'long')]:
            st.write(f"Fetching top artists ({label} term)...")
            top_artists = fetch_top_artists(sp, time_range=time_range, limit=50)
            if top_artists:
                artists_data = []
                for idx, artist in enumerate(top_artists):
                    artists_data.append({
                        'artist_id': artist.get('id'),
                        'artist_name': artist.get('name'),
                        'genres': ', '.join(artist.get('genres', [])),
                        'popularity': artist.get('popularity'),
                        'followers': artist.get('followers', {}).get('total'),
                        'rank': idx + 1,
                        'time_range': time_range,
                        'snapshot_timestamp': snapshot_timestamp,
                        'user_id': user_id
                    })

                if artists_data:
                    snapshot_data[f'top_artists_{label}'] = pd.DataFrame(artists_data)

        # Calculate aggregated metrics
        st.write("Computing metrics...")
        snapshot_data['metrics'] = calculate_snapshot_metrics(snapshot_data)

    return snapshot_data


def calculate_snapshot_metrics(snapshot_data):
    """
    Calculate aggregated metrics from snapshot data

    Args:
        snapshot_data: Dictionary containing collected DataFrames

    Returns:
        pd.DataFrame: Single-row DataFrame with computed metrics
    """
    metrics = {
        'snapshot_timestamp': snapshot_data['snapshot_timestamp'],
        'user_id': snapshot_data['user_id']
    }

    # Recent tracks metrics
    recent_df = snapshot_data.get('recent_tracks')
    if recent_df is not None and not recent_df.empty:
        metrics['recent_unique_artists'] = recent_df['artist_name'].nunique()
        metrics['recent_unique_tracks'] = recent_df['track_name'].nunique()
        metrics['recent_artist_diversity'] = calculate_diversity_score(recent_df, 'artist_name')

        # Audio feature averages
        audio_features = ['danceability', 'energy', 'valence', 'acousticness',
                         'instrumentalness', 'speechiness', 'liveness', 'tempo', 'loudness']
        for feature in audio_features:
            if feature in recent_df.columns:
                metrics[f'recent_avg_{feature}'] = recent_df[feature].mean()

        # Composite feature averages
        if 'mood_score' in recent_df.columns:
            metrics['recent_avg_mood'] = recent_df['mood_score'].mean()
        if 'grooviness' in recent_df.columns:
            metrics['recent_avg_grooviness'] = recent_df['grooviness'].mean()

        # Context distribution
        if 'context' in recent_df.columns:
            context_dist = recent_df['context'].value_counts(normalize=True)
            for context, pct in context_dist.items():
                metrics[f'recent_pct_{context}'] = pct

    # Top tracks metrics (short term)
    top_short = snapshot_data.get('top_tracks_short')
    if top_short is not None and not top_short.empty:
        metrics['top_short_avg_popularity'] = top_short['popularity'].mean()
        metrics['top_short_unique_artists'] = top_short['artist_name'].nunique()

        if 'energy' in top_short.columns:
            metrics['top_short_avg_energy'] = top_short['energy'].mean()
        if 'valence' in top_short.columns:
            metrics['top_short_avg_valence'] = top_short['valence'].mean()

    # Top artists metrics (short term)
    top_artists_short = snapshot_data.get('top_artists_short')
    if top_artists_short is not None and not top_artists_short.empty:
        metrics['top_short_unique_genres'] = len([g for genres in top_artists_short['genres']
                                                   for g in genres.split(', ') if g])
        metrics['top_short_avg_artist_popularity'] = top_artists_short['popularity'].mean()

    return pd.DataFrame([metrics])


def save_snapshot_to_s3(snapshot_data):
    """
    Save collected snapshot data to S3

    Args:
        snapshot_data: Dictionary containing collected DataFrames

    Returns:
        bool: True if all uploads successful
    """
    bucket_name = get_bucket_name()
    if not bucket_name:
        st.error("S3 bucket not configured")
        return False

    user_id = snapshot_data['user_id']
    timestamp = snapshot_data['snapshot_timestamp'].replace(':', '-').replace('.', '-')

    success_count = 0
    total_uploads = 0

    with st.spinner("☁️ Uploading to S3..."):

        # Upload each DataFrame
        data_types = [
            ('recent_tracks', 'recent_tracks'),
            ('top_tracks_short', 'top_tracks_short'),
            ('top_tracks_medium', 'top_tracks_medium'),
            ('top_tracks_long', 'top_tracks_long'),
            ('top_artists_short', 'top_artists_short'),
            ('top_artists_medium', 'top_artists_medium'),
            ('top_artists_long', 'top_artists_long'),
            ('metrics', 'metrics')
        ]

        for data_key, filename_prefix in data_types:
            df = snapshot_data.get(data_key)
            if df is not None and not df.empty:
                s3_key = f"users/{user_id}/snapshots/{timestamp}_{filename_prefix}.parquet"
                total_uploads += 1

                if upload_dataframe_to_s3(df, bucket_name, s3_key):
                    success_count += 1
                    st.write(f"✓ Uploaded {filename_prefix}")

    if success_count == total_uploads and total_uploads > 0:
        st.success(f"✓ Successfully saved snapshot to S3 ({success_count} files)")
        return True
    elif success_count > 0:
        st.warning(f"⚠️ Partially saved: {success_count}/{total_uploads} files uploaded")
        return False
    else:
        st.error("❌ Failed to save snapshot to S3")
        return False


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
    from app.func.s3_storage import list_user_snapshots

    bucket_name = get_bucket_name()
    if not bucket_name:
        return 0

    snapshots = list_user_snapshots(bucket_name, user_id)

    # Count unique timestamps
    unique_timestamps = set()
    for key in snapshots:
        # Extract timestamp from key
        parts = key.split('/')
        if len(parts) >= 4:
            filename = parts[3]
            timestamp = filename.split('_')[0]
            unique_timestamps.add(timestamp)

    return len(unique_timestamps)
