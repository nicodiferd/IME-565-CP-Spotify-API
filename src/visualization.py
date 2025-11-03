"""
Visualization Module

Reusable plotting functions for Spotify analytics.
"""

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from typing import List, Optional


def plot_feature_distributions(
    df: pd.DataFrame,
    features: List[str],
    figsize: tuple = (15, 12),
    bins: int = 50
) -> None:
    """
    Plot histograms for multiple audio features.

    Args:
        df: DataFrame containing features
        features: List of feature column names to plot
        figsize: Figure size as (width, height)
        bins: Number of bins for histograms
    """
    n_features = len(features)
    n_cols = 3
    n_rows = (n_features + n_cols - 1) // n_cols

    fig, axes = plt.subplots(n_rows, n_cols, figsize=figsize)
    axes = axes.flatten() if n_features > 1 else [axes]

    for idx, feature in enumerate(features):
        if feature not in df.columns:
            continue

        axes[idx].hist(df[feature].dropna(), bins=bins, edgecolor='black', alpha=0.7)
        axes[idx].set_title(f'{feature.replace("_", " ").title()} Distribution',
                           fontsize=12, fontweight='bold')
        axes[idx].set_xlabel(feature.replace('_', ' ').title())
        axes[idx].set_ylabel('Frequency')
        axes[idx].grid(True, alpha=0.3)

        # Add mean line
        mean_val = df[feature].mean()
        axes[idx].axvline(mean_val, color='red', linestyle='--',
                         linewidth=2, label=f'Mean: {mean_val:.3f}')
        axes[idx].legend()

    # Hide unused subplots
    for idx in range(len(features), len(axes)):
        axes[idx].set_visible(False)

    plt.tight_layout()
    plt.suptitle('Audio Feature Distributions', fontsize=16, fontweight='bold', y=1.001)
    plt.show()


def plot_correlation_matrix(
    df: pd.DataFrame,
    features: List[str],
    figsize: tuple = (12, 10)
) -> None:
    """
    Plot correlation matrix heatmap for audio features.

    Args:
        df: DataFrame containing features
        features: List of feature column names
        figsize: Figure size as (width, height)
    """
    if len(features) < 2:
        print("Need at least 2 features for correlation matrix")
        return

    plt.figure(figsize=figsize)
    correlation_matrix = df[features].corr()

    sns.heatmap(correlation_matrix, annot=True, fmt='.2f', cmap='coolwarm',
                center=0, square=True, linewidths=1, cbar_kws={"shrink": 0.8})

    plt.title('Audio Features Correlation Matrix', fontsize=16, fontweight='bold', pad=20)
    plt.tight_layout()
    plt.show()

    # Print strong correlations
    print("\nStrong Correlations (|r| > 0.5):")
    print("=" * 50)
    for i in range(len(correlation_matrix.columns)):
        for j in range(i+1, len(correlation_matrix.columns)):
            corr_val = correlation_matrix.iloc[i, j]
            if abs(corr_val) > 0.5:
                print(f"{correlation_matrix.columns[i]:20s} <-> "
                      f"{correlation_matrix.columns[j]:20s}: {corr_val:6.3f}")


def plot_top_items(
    df: pd.DataFrame,
    column: str,
    title: str,
    top_n: int = 20,
    figsize: tuple = (12, 8),
    color: str = 'skyblue',
    horizontal: bool = True
) -> None:
    """
    Plot bar chart of top N items from a column.

    Args:
        df: DataFrame containing the column
        column: Column name to analyze
        title: Plot title
        top_n: Number of top items to display
        figsize: Figure size as (width, height)
        color: Bar color
        horizontal: If True, use horizontal bars
    """
    if column not in df.columns:
        print(f"Column '{column}' not found in DataFrame")
        return

    top_items = df[column].value_counts().head(top_n)

    plt.figure(figsize=figsize)
    if horizontal:
        top_items.plot(kind='barh', color=color, edgecolor='black')
        plt.xlabel('Count', fontsize=12)
        plt.ylabel(column.replace('_', ' ').title(), fontsize=12)
        plt.gca().invert_yaxis()
    else:
        top_items.plot(kind='bar', color=color, edgecolor='black')
        plt.xlabel(column.replace('_', ' ').title(), fontsize=12)
        plt.ylabel('Count', fontsize=12)
        plt.xticks(rotation=45, ha='right')

    plt.title(title, fontsize=14, fontweight='bold')
    plt.tight_layout()
    plt.show()

    return top_items


def plot_context_distribution(df: pd.DataFrame, figsize: tuple = (10, 6)) -> None:
    """
    Plot distribution of listening contexts.

    Args:
        df: DataFrame with 'context' column
        figsize: Figure size as (width, height)
    """
    if 'context' not in df.columns:
        print("No 'context' column found in DataFrame")
        return

    context_counts = df['context'].value_counts()

    plt.figure(figsize=figsize)
    context_counts.plot(kind='bar', color='teal', edgecolor='black', alpha=0.7)
    plt.xlabel('Context', fontsize=12)
    plt.ylabel('Number of Tracks', fontsize=12)
    plt.title('Track Distribution by Listening Context', fontsize=14, fontweight='bold')
    plt.xticks(rotation=45)
    plt.grid(axis='y', alpha=0.3)
    plt.tight_layout()
    plt.show()


def print_summary_stats(
    df: pd.DataFrame,
    audio_features: List[str],
    columns: Optional[dict] = None
) -> None:
    """
    Print comprehensive summary statistics for the dataset.

    Args:
        df: Input DataFrame
        audio_features: List of audio feature columns
        columns: Dictionary with 'track', 'artist', 'genre', 'popularity' keys
    """
    print("=" * 70)
    print("DATASET SUMMARY")
    print("=" * 70)

    print(f"\nDataset Overview:")
    print(f"  Total tracks: {len(df):,}")
    print(f"  Total columns: {len(df.columns)}")
    print(f"  Audio features: {len(audio_features)}")

    if columns:
        if columns.get('artist') and columns['artist'] in df.columns:
            print(f"\nArtists:")
            print(f"  Unique artists: {df[columns['artist']].nunique():,}")
            if len(df[columns['artist']].value_counts()) > 0:
                top_artist = df[columns['artist']].value_counts().index[0]
                top_count = df[columns['artist']].value_counts().values[0]
                print(f"  Top artist: {top_artist} ({top_count:,} tracks)")

        if columns.get('genre') and columns['genre'] in df.columns:
            print(f"\nGenres:")
            print(f"  Unique genres: {df[columns['genre']].nunique():,}")
            if len(df[columns['genre']].value_counts()) > 0:
                top_genre = df[columns['genre']].value_counts().index[0]
                top_count = df[columns['genre']].value_counts().values[0]
                print(f"  Top genre: {top_genre} ({top_count:,} tracks)")

    if audio_features:
        print(f"\nAudio Characteristics:")
        if 'energy' in df.columns:
            print(f"  Average energy: {df['energy'].mean():.3f}")
        if 'valence' in df.columns:
            print(f"  Average valence (happiness): {df['valence'].mean():.3f}")
        if 'danceability' in df.columns:
            print(f"  Average danceability: {df['danceability'].mean():.3f}")
        if 'tempo' in df.columns:
            print(f"  Average tempo: {df['tempo'].mean():.1f} BPM")

    # Composite features
    composite_features = [col for col in ['mood_score', 'grooviness', 'focus_score', 'relaxation_score']
                         if col in df.columns]
    if composite_features:
        print(f"\nComposite Scores:")
        for feature in composite_features:
            print(f"  Average {feature.replace('_', ' ')}: {df[feature].mean():.3f}")

    # Context distribution
    if 'context' in df.columns:
        print(f"\nListening Contexts:")
        for context, count in df['context'].value_counts().items():
            pct = (count / len(df)) * 100
            print(f"  {context}: {count:,} tracks ({pct:.1f}%)")

    print("=" * 70)
