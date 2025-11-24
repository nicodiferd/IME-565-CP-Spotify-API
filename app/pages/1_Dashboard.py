"""
Dashboard Page
Overview page with key metrics, temporal patterns, and artist analysis
"""

import streamlit as st
import sys
import os

# Add parent directory to path to import from func
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from func.ui_components import apply_page_config, get_custom_css
from func.page_auth import require_auth
from func.dashboard_helpers import (
    load_current_snapshot,
    handle_missing_data,
    display_sync_status,
    enrich_with_audio_features,
    get_audio_features_coverage
)
from func.data_processing import calculate_diversity_score
from func.visualizations import (
    plot_listening_by_hour,
    plot_listening_by_day,
    plot_temporal_heatmap,
    plot_top_artists
)

# Apply page configuration
apply_page_config()
st.markdown(get_custom_css(), unsafe_allow_html=True)

# Require authentication
sp, profile = require_auth()
if not sp:
    st.warning("Please connect your Spotify account to view the dashboard.")
    st.stop()

user_id = profile['id']

# ============================================================================
# LOAD SNAPSHOT DATA
# ============================================================================

try:
    data = load_current_snapshot(user_id)
except Exception as e:
    handle_missing_data(redirect_to_sync=True)

# ============================================================================
# DASHBOARD PAGE
# ============================================================================

st.header("📊 Dashboard")

# Show sync status
display_sync_status(data['metadata'])

# Load recent tracks and enrich with audio features
recent_df = data['recent_tracks'].copy()

if recent_df.empty:
    st.warning("No recent listening data available. Try playing some music on Spotify!")
    st.stop()

# Enrich with Kaggle audio features (adds mood, grooviness, context, etc.)
with st.spinner("Enriching with audio features..."):
    recent_df = enrich_with_audio_features(recent_df, verbose=False)

# Get audio features coverage
coverage = get_audio_features_coverage(recent_df)

# ============================================================================
# KPI METRICS - ROW 1 (BASIC)
# ============================================================================

st.subheader("Overview")
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Total Tracks", len(recent_df))

with col2:
    unique_artists = recent_df['artist_name'].nunique()
    st.metric("Unique Artists", unique_artists)

with col3:
    total_minutes = recent_df['duration_min'].sum() if 'duration_min' in recent_df.columns else 0
    st.metric("Total Listening", f"{total_minutes:.0f} min")

with col4:
    avg_popularity = recent_df['popularity'].mean() if 'popularity' in recent_df.columns else 0
    st.metric("Avg Popularity", f"{avg_popularity:.0f}")

# ============================================================================
# KPI METRICS - ROW 2 (AUDIO FEATURES)
# ============================================================================

if coverage['coverage_pct'] > 0:
    st.caption(f"🎵 Audio features available for {coverage['coverage_pct']:.1f}% of tracks")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        if 'mood_score' in recent_df.columns:
            avg_mood = recent_df['mood_score'].mean()
            st.metric("Avg Mood Score", f"{avg_mood:.2f}")
        else:
            st.metric("Avg Mood Score", "N/A")

    with col2:
        if 'energy' in recent_df.columns:
            avg_energy = recent_df['energy'].mean()
            st.metric("Avg Energy", f"{avg_energy:.2f}")
        else:
            st.metric("Avg Energy", "N/A")

    with col3:
        diversity = calculate_diversity_score(recent_df, 'artist_name')
        st.metric("Artist Diversity", f"{diversity:.0f}%")

    with col4:
        if 'context' in recent_df.columns:
            top_context = recent_df['context'].mode()[0] if not recent_df['context'].isna().all() else "Unknown"
            st.metric("Top Context", top_context.title())
        else:
            st.metric("Top Context", "N/A")
else:
    st.info("💡 Audio features not available. Connect to a Spotify Premium account or use our Kaggle dataset enrichment for mood, energy, and context analysis.")

st.markdown("---")

# ============================================================================
# TEMPORAL PATTERNS
# ============================================================================

st.subheader("⏰ Temporal Patterns")
col_left, col_right = st.columns(2)

with col_left:
    plot_listening_by_hour(recent_df)

with col_right:
    plot_listening_by_day(recent_df)

# Heatmap
if 'hour' in recent_df.columns and 'day_of_week' in recent_df.columns:
    plot_temporal_heatmap(recent_df)

st.markdown("---")

# ============================================================================
# ARTIST ANALYSIS
# ============================================================================

st.subheader("🎤 Artist Analysis")
plot_top_artists(recent_df)

st.markdown("---")

# ============================================================================
# TASTE CONSISTENCY (NEW)
# ============================================================================

st.subheader("🎯 Taste Consistency")

# Get metrics from snapshot
metrics = data['metrics']
taste = metrics.get('taste_consistency', {})
overlap_pct = taste.get('short_vs_long_overlap_pct', 0)
consistency_type = taste.get('consistency_type', 'Unknown')

col1, col2 = st.columns([2, 1])

with col1:
    st.metric(
        label="Short vs Long Term Overlap",
        value=f"{overlap_pct:.0f}%",
        help="Percentage of your current favorite tracks that are also in your all-time favorites"
    )

    if overlap_pct > 60:
        st.success(f"🎵 **{consistency_type}**: You have consistent musical taste! {overlap_pct:.0f}% of your recent favorites are also all-time favorites.")
    else:
        st.info(f"🔍 **{consistency_type}**: You're always discovering new music! Only {overlap_pct:.0f}% overlap between current and all-time favorites.")

with col2:
    # Diversity metrics
    diversity_metrics = metrics.get('diversity', {})
    unique_genres = diversity_metrics.get('unique_genres', 0)
    mainstream_score = diversity_metrics.get('mainstream_score', 0)

    st.metric("Unique Genres", unique_genres)
    st.metric("Mainstream Score", f"{mainstream_score:.0f}/100")

st.markdown("---")

# ============================================================================
# GENRE BREAKDOWN (NEW)
# ============================================================================

if 'track_genre' in recent_df.columns and recent_df['track_genre'].notna().any():
    st.subheader("🎸 Genre Breakdown")

    # Get top genres
    genre_counts = recent_df['track_genre'].value_counts().head(10)

    col1, col2 = st.columns([2, 1])

    with col1:
        import plotly.express as px

        fig = px.bar(
            x=genre_counts.values,
            y=genre_counts.index,
            orientation='h',
            labels={'x': 'Track Count', 'y': 'Genre'},
            title='Top 10 Genres'
        )
        fig.update_layout(
            height=400,
            showlegend=False,
            yaxis={'categoryorder': 'total ascending'}
        )
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.caption("**Top Genres**")
        for idx, (genre, count) in enumerate(genre_counts.head(5).items(), 1):
            pct = (count / len(recent_df)) * 100
            st.write(f"{idx}. {genre.title()}: {count} ({pct:.1f}%)")
