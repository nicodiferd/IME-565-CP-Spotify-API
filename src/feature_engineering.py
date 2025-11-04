"""
Feature Engineering Module

Functions for creating composite features and classifying listening contexts.
"""

import pandas as pd
import numpy as np
from typing import List


def create_composite_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Create composite features based on audio characteristics.

    Composite features created:
    - mood_score: Overall happiness/energy (valence + energy + acousticness)
    - grooviness: Danceability/upbeat quality (danceability + energy + tempo)
    - focus_score: Suitability for concentration (low speechiness, high instrumentalness)
    - relaxation_score: Calmness/chill quality (low energy, high acousticness, low tempo)

    Args:
        df: DataFrame with audio features

    Returns:
        DataFrame with added composite feature columns
    """
    df = df.copy()
    features_created = []

    # 1. Mood Score (valence + energy + acousticness)
    if all(col in df.columns for col in ['valence', 'energy', 'acousticness']):
        df['mood_score'] = (
            0.5 * df['valence'] +
            0.3 * df['energy'] +
            0.2 * (1 - df['acousticness'])
        )
        features_created.append('mood_score')

    # 2. Grooviness Index (danceability + energy + tempo)
    if all(col in df.columns for col in ['danceability', 'energy', 'tempo']):
        tempo_normalized = (df['tempo'] - df['tempo'].min()) / (df['tempo'].max() - df['tempo'].min())
        df['grooviness'] = (
            0.4 * df['danceability'] +
            0.3 * df['energy'] +
            0.3 * tempo_normalized
        )
        features_created.append('grooviness')

    # 3. Focus Score (low speechiness, moderate energy, high instrumentalness)
    if all(col in df.columns for col in ['speechiness', 'energy', 'instrumentalness']):
        df['focus_score'] = (
            0.4 * (1 - df['speechiness']) +
            0.3 * df['instrumentalness'] +
            0.3 * (1 - abs(df['energy'] - 0.5) * 2)
        )
        features_created.append('focus_score')

    # 4. Relaxation Score (low energy, high acousticness, low tempo)
    if all(col in df.columns for col in ['energy', 'acousticness', 'tempo']):
        tempo_normalized = (df['tempo'] - df['tempo'].min()) / (df['tempo'].max() - df['tempo'].min())
        df['relaxation_score'] = (
            0.4 * (1 - df['energy']) +
            0.3 * df['acousticness'] +
            0.3 * (1 - tempo_normalized)
        )
        features_created.append('relaxation_score')

    if features_created:
        print(f"\n✓ Created {len(features_created)} composite features:")
        for feature in features_created:
            print(f"  - {feature}")
    else:
        print("\n⚠️ No composite features created (missing required audio features)")

    return df


def classify_context(row: pd.Series) -> str:
    """
    Classify a track's listening context based on audio features.

    Context categories:
    - Workout: High energy + high danceability
    - Focus: Low speechiness + high instrumentalness
    - Relaxation: Low energy + high acousticness
    - Party: High valence + high energy + high danceability
    - General: Default category

    Args:
        row: Single row from DataFrame with audio features

    Returns:
        Context label as string
    """
    # Workout: High energy, high danceability
    if row.get('energy', 0) > 0.7 and row.get('danceability', 0) > 0.6:
        return 'Workout'

    # Focus: Low speechiness, high instrumentalness
    if row.get('speechiness', 0) < 0.2 and row.get('instrumentalness', 0) > 0.5:
        return 'Focus'

    # Relaxation: Low energy, high acousticness
    if row.get('energy', 0) < 0.4 and row.get('acousticness', 0) > 0.5:
        return 'Relaxation'

    # Party: High valence, high energy, high danceability
    if (row.get('valence', 0) > 0.6 and
        row.get('energy', 0) > 0.6 and
        row.get('danceability', 0) > 0.6):
        return 'Party'

    return 'General'


def add_context_classification(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add listening context classification to all tracks in dataset.

    Args:
        df: DataFrame with audio features

    Returns:
        DataFrame with added 'context' column
    """
    df = df.copy()

    print("\nClassifying listening contexts...")
    df['context'] = df.apply(classify_context, axis=1)

    context_counts = df['context'].value_counts()
    print("\nContext Distribution:")
    for context, count in context_counts.items():
        pct = (count / len(df)) * 100
        print(f"  {context}: {count:,} tracks ({pct:.1f}%)")

    return df


def get_normalized_features(audio_features: List[str]) -> List[str]:
    """
    Filter audio features to only those on 0-1 scale.

    Args:
        audio_features: List of all audio feature column names

    Returns:
        List of normalized (0-1 scale) feature names
    """
    non_normalized = ['loudness', 'tempo', 'duration_ms', 'key', 'mode', 'time_signature']
    return [f for f in audio_features if f not in non_normalized]


def get_composite_features(df: pd.DataFrame) -> List[str]:
    """
    Get list of composite features that exist in the DataFrame.

    Args:
        df: Input DataFrame

    Returns:
        List of composite feature column names
    """
    possible_composites = ['mood_score', 'grooviness', 'focus_score', 'relaxation_score']
    return [col for col in possible_composites if col in df.columns]
