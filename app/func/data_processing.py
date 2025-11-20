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
                'played_at': item.get('played_at'),
                'duration_ms': track.get('duration_ms'),
                'popularity': track.get('popularity'),
                'explicit': track.get('explicit'),
                'preview_url': track.get('preview_url')
            })

    if not data:
        return pd.DataFrame()

    df = pd.DataFrame(data)

    # Convert timestamps
    df['played_at'] = pd.to_datetime(df['played_at'])
    df['duration_min'] = df['duration_ms'] / 60000
    df['hour'] = df['played_at'].dt.hour
    df['day_of_week'] = df['played_at'].dt.day_name()
    df['date'] = df['played_at'].dt.date
    df['is_weekend'] = df['played_at'].dt.dayofweek >= 5

    # Fetch audio features if Spotify client provided (optional - may not be available in Development Mode)
    if sp and track_ids:
        audio_features = fetch_audio_features(sp, track_ids)

        if audio_features:
            # Create audio features dataframe
            af_df = pd.DataFrame(audio_features)
            af_df.rename(columns={'id': 'track_id'}, inplace=True)

            # Merge with main dataframe
            df = df.merge(af_df, on='track_id', how='left')

            # Add composite features if module available
            if create_composite_features and 'danceability' in df.columns:
                try:
                    df = create_composite_features(df)
                except Exception as e:
                    pass  # Silently continue - composite features are optional

            # Add context classification if module available
            if classify_context and 'energy' in df.columns:
                try:
                    df = classify_context(df)
                except Exception as e:
                    pass  # Silently continue - context classification is optional

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
                'popularity': track.get('popularity'),
                'duration_ms': track.get('duration_ms'),
                'duration_min': track.get('duration_ms', 0) / 60000,
                'preview_url': track.get('preview_url')
            })

    if not data:
        return pd.DataFrame()

    df = pd.DataFrame(data)

    # Fetch audio features
    if sp and track_ids:
        audio_features = fetch_audio_features(sp, track_ids)

        if audio_features:
            af_df = pd.DataFrame(audio_features)
            af_df.rename(columns={'id': 'track_id'}, inplace=True)
            df = df.merge(af_df, on='track_id', how='left')

            # Add composite features
            if create_composite_features and 'danceability' in df.columns:
                try:
                    df = create_composite_features(df)
                except:
                    pass

            # Add context
            if classify_context and 'energy' in df.columns:
                try:
                    df = classify_context(df)
                except:
                    pass

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
