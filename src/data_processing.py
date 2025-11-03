"""
Data Processing Module

Functions for loading, cleaning, and preprocessing Spotify track data.
"""

import pandas as pd
from pathlib import Path
from typing import List, Optional, Tuple


def load_spotify_data(
    data_dir: str = 'data/raw',
    skip_large_files: bool = True,
    size_threshold_mb: float = 50.0
) -> Tuple[pd.DataFrame, str]:
    """
    Load Spotify dataset from CSV files with automatic encoding detection.

    Args:
        data_dir: Directory containing CSV files
        skip_large_files: Whether to skip files larger than threshold
        size_threshold_mb: Size threshold in MB for skipping files

    Returns:
        Tuple of (DataFrame, filename) for the loaded dataset

    Raises:
        FileNotFoundError: If no valid CSV files found
        ValueError: If no files could be loaded
    """
    data_path = Path(data_dir)
    csv_files = list(data_path.glob('*.csv'))

    if not csv_files:
        raise FileNotFoundError(f"No CSV files found in {data_dir}")

    # Sort files to prioritize dataset.csv
    csv_files = sorted(csv_files, key=lambda x: (x.name != 'dataset.csv', x.name))

    print(f"Found {len(csv_files)} CSV files in {data_dir}:")
    for i, file in enumerate(csv_files, 1):
        file_size = file.stat().st_size / (1024 * 1024)
        print(f"  {i}. {file.name} ({file_size:.2f} MB)")

    # Try to load files
    for selected_file in csv_files:
        # Skip large files if requested
        if skip_large_files:
            file_size_mb = selected_file.stat().st_size / (1024 * 1024)
            if 'artist' in selected_file.name.lower() and file_size_mb > size_threshold_mb:
                print(f"\nSkipping {selected_file.name} (will use in Phase 2)")
                continue

        print(f"\nAttempting to load: {selected_file.name}...")

        # Try different encodings
        encodings = ['utf-8', 'latin-1', 'iso-8859-1', 'cp1252']

        for encoding in encodings:
            try:
                df = pd.read_csv(selected_file, encoding=encoding)
                print(f"✓ Successfully loaded with {encoding} encoding")
                print(f"  {len(df):,} rows and {len(df.columns)} columns")
                return df, selected_file.name
            except UnicodeDecodeError:
                if encoding == encodings[-1]:
                    print(f"✗ Failed to load {selected_file.name} with all encodings")
                continue
            except Exception as e:
                print(f"✗ Error loading {selected_file.name}: {e}")
                break

    raise ValueError("Could not load any CSV files from the directory")


def identify_audio_features(df: pd.DataFrame) -> List[str]:
    """
    Identify which Spotify audio features are present in the dataset.

    Args:
        df: Input DataFrame

    Returns:
        List of audio feature column names present in the dataset
    """
    audio_features = [
        'danceability', 'energy', 'loudness', 'speechiness',
        'acousticness', 'instrumentalness', 'liveness', 'valence',
        'tempo', 'duration_ms', 'key', 'mode', 'time_signature'
    ]

    available_features = [col for col in audio_features if col in df.columns]

    print(f"\nAvailable Audio Features ({len(available_features)}):")
    for feature in available_features:
        print(f"  - {feature}")

    return available_features


def clean_dataset(
    df: pd.DataFrame,
    audio_features: Optional[List[str]] = None,
    remove_duplicates: bool = True,
    min_duration_ms: int = 5000
) -> pd.DataFrame:
    """
    Clean Spotify dataset by removing invalid/problematic records.

    Args:
        df: Input DataFrame
        audio_features: List of audio feature columns to check for missing values
        remove_duplicates: Whether to remove duplicate rows
        min_duration_ms: Minimum track duration in milliseconds

    Returns:
        Cleaned DataFrame
    """
    df_clean = df.copy()
    initial_count = len(df_clean)

    print(f"\nCleaning dataset...")
    print(f"Original dataset: {initial_count:,} rows")

    # Remove duplicates
    if remove_duplicates:
        before = len(df_clean)
        df_clean = df_clean.drop_duplicates()
        removed = before - len(df_clean)
        print(f"  Removed {removed:,} duplicate rows")

    # Handle missing values in audio features
    if audio_features:
        before = len(df_clean)
        df_clean = df_clean.dropna(subset=audio_features)
        removed = before - len(df_clean)
        print(f"  Removed {removed:,} rows with missing audio features")

    # Remove invalid loudness values (should be negative dB)
    if 'loudness' in df_clean.columns:
        before = len(df_clean)
        df_clean = df_clean[df_clean['loudness'] <= 0]
        removed = before - len(df_clean)
        print(f"  Removed {removed:,} rows with invalid loudness values (>0 dB)")

    # Remove extremely short durations
    if 'duration_ms' in df_clean.columns:
        before = len(df_clean)
        df_clean = df_clean[df_clean['duration_ms'] >= min_duration_ms]
        removed = before - len(df_clean)
        print(f"  Removed {removed:,} rows with duration < {min_duration_ms/1000:.0f} seconds")

    retention_pct = (len(df_clean) / initial_count) * 100
    print(f"\nFinal cleaned dataset: {len(df_clean):,} rows ({retention_pct:.1f}% retained)")

    return df_clean


def identify_column_names(df: pd.DataFrame) -> dict:
    """
    Identify common column names for tracks, artists, genres, and popularity.

    Args:
        df: Input DataFrame

    Returns:
        Dictionary with keys: 'track', 'artist', 'genre', 'popularity'
    """
    columns = {
        'track': None,
        'artist': None,
        'genre': None,
        'popularity': None
    }

    for col in df.columns:
        col_lower = col.lower()
        if 'track' in col_lower and 'name' in col_lower:
            columns['track'] = col
        elif 'artist' in col_lower and ('name' in col_lower or col_lower == 'artists'):
            columns['artist'] = col
        elif 'genre' in col_lower:
            columns['genre'] = col
        elif 'popular' in col_lower:
            columns['popularity'] = col

    print("\nIdentified columns:")
    for key, value in columns.items():
        print(f"  {key.capitalize()}: {value}")

    return columns


def get_dataset_summary(df: pd.DataFrame, audio_features: List[str]) -> dict:
    """
    Generate summary statistics for the dataset.

    Args:
        df: Input DataFrame
        audio_features: List of audio feature columns

    Returns:
        Dictionary with summary statistics
    """
    return {
        'total_rows': len(df),
        'total_columns': len(df.columns),
        'audio_features_count': len(audio_features),
        'missing_values': df.isnull().sum().sum(),
        'memory_usage_mb': df.memory_usage(deep=True).sum() / (1024 * 1024)
    }
