"""
Data Processing and Transformation Functions
Convert Spotify API responses into processed DataFrames with audio features
"""

import streamlit as st
import pandas as pd
import numpy as np
import os
import sys

# Import audio features and context classification from src
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
try:
    from src.feature_engineering import create_composite_features, classify_context
except ImportError:
    # Fallback if src modules not available
    create_composite_features = None
    classify_context = None

from .data_fetching import fetch_audio_features


# ============================================================================
# DATA PROCESSING FUNCTIONS
# ============================================================================

def process_recent_tracks(recent_items, sp=None):
    """Convert recently played items to DataFrame with audio features"""
    if not recent_items:
        return pd.DataFrame()

    # Basic track data
    data = []
    track_ids = []

    for item in recent_items:
        track = item.get('track', {})
        track_id = track.get('id')

        if track_id:
            track_ids.append(track_id)
            data.append({
                'track_id': track_id,
                'track_name': track.get('name'),
                'artist_name': track.get('artists', [{}])[0].get('name'),
                'album_name': track.get('album', {}).get('name'),
                'release_date': track.get('album', {}).get('release_date'),
                'played_at': item.get('played_at'),
                'duration_ms': track.get('duration_ms'),
                'popularity': track.get('popularity'),
                'explicit': track.get('explicit', False),
                'preview_url': track.get('preview_url')
            })

    if not data:
        return pd.DataFrame()

    df = pd.DataFrame(data)

    # Convert timestamps
    df['played_at'] = pd.to_datetime(df['played_at'])
    df['duration_min'] = df['duration_ms'] / 60000

    # Extract comprehensive temporal features for analytics
    df['hour'] = df['played_at'].dt.hour  # 0-23
    df['day_of_week'] = df['played_at'].dt.day_name()  # Monday-Sunday
    df['day_of_month'] = df['played_at'].dt.day  # 1-31
    df['week_of_year'] = df['played_at'].dt.isocalendar().week  # 1-52
    df['month'] = df['played_at'].dt.month  # 1-12
    df['month_name'] = df['played_at'].dt.month_name()  # January-December
    df['quarter'] = df['played_at'].dt.quarter  # 1-4
    df['year'] = df['played_at'].dt.year  # YYYY
    df['day_of_year'] = df['played_at'].dt.dayofyear  # 1-365/366
    df['date'] = df['played_at'].dt.date  # Date only (YYYY-MM-DD)
    df['is_weekend'] = df['played_at'].dt.dayofweek >= 5  # Boolean

    # Add season classification
    def get_season(month):
        if month in [12, 1, 2]:
            return 'Winter'
        elif month in [3, 4, 5]:
            return 'Spring'
        elif month in [6, 7, 8]:
            return 'Summer'
        else:  # 9, 10, 11
            return 'Fall'

    df['season'] = df['month'].apply(get_season)

    # Add derived fields
    if 'release_date' in df.columns:
        df['release_year'] = df['release_date'].str[:4].fillna('0').astype(int)

    # NOTE: Audio features endpoint returns HTTP 403 (not available for this app)
    # We use Kaggle dataset lookup instead - see dashboard_helpers.py for enrichment
    # Commenting out to avoid error noise and wasted API calls:
    #
    # if sp and track_ids:
    #     audio_features = fetch_audio_features(sp, track_ids)
    #     if audio_features:
    #         # Merge and add composite features...

    return df


def process_top_tracks(top_tracks, sp=None):
    """Convert top tracks to DataFrame with audio features"""
    if not top_tracks:
        return pd.DataFrame()

    data = []
    track_ids = []

    for track in top_tracks:
        track_id = track.get('id')
        if track_id:
            track_ids.append(track_id)
            data.append({
                'track_id': track_id,
                'track_name': track.get('name'),
                'artist_name': track.get('artists', [{}])[0].get('name'),
                'album_name': track.get('album', {}).get('name'),
                'release_date': track.get('album', {}).get('release_date'),
                'popularity': track.get('popularity'),
                'duration_ms': track.get('duration_ms'),
                'duration_min': track.get('duration_ms', 0) / 60000,
                'explicit': track.get('explicit', False),
                'preview_url': track.get('preview_url')
            })

    if not data:
        return pd.DataFrame()

    df = pd.DataFrame(data)

    # NOTE: Audio features endpoint returns HTTP 403 (not available for this app)
    # We use Kaggle dataset lookup instead - see dashboard_helpers.py for enrichment
    # Commenting out to avoid error noise and wasted API calls:
    #
    # if sp and track_ids:
    #     audio_features = fetch_audio_features(sp, track_ids)
    #     if audio_features:
    #         # Merge and add composite features...

    return df


def calculate_diversity_score(df, column='artist_name'):
    """Calculate diversity using Shannon entropy"""
    if df.empty or column not in df.columns:
        return 0

    value_counts = df[column].value_counts()
    proportions = value_counts / len(df)
    entropy = -np.sum(proportions * np.log2(proportions))

    # Normalize to 0-100 scale
    max_entropy = np.log2(len(value_counts))
    if max_entropy == 0:
        return 0

    return (entropy / max_entropy) * 100
