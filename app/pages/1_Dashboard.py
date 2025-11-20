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
from func.data_fetching import fetch_recently_played
from func.data_processing import process_recent_tracks, calculate_diversity_score
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

# ============================================================================
# DASHBOARD PAGE
# ============================================================================

st.header("📊 Dashboard")

# Fetch data
with st.spinner("Loading your listening data..."):
    recent_items = fetch_recently_played(sp, limit=50)
    recent_df = process_recent_tracks(recent_items, sp)

if recent_df.empty:
    st.warning("No recent listening data available. Try playing some music on Spotify!")
    st.stop()

# KPI metrics row 1
st.subheader("Overview")
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Total Tracks", len(recent_df))

with col2:
    unique_artists = recent_df['artist_name'].nunique()
    st.metric("Unique Artists", unique_artists)

with col3:
    total_minutes = recent_df['duration_min'].sum()
    st.metric("Total Listening", f"{total_minutes:.0f} min")

with col4:
    avg_popularity = recent_df['popularity'].mean()
    st.metric("Avg Popularity", f"{avg_popularity:.0f}")

# KPI metrics row 2 (advanced)
if 'mood_score' in recent_df.columns:
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        avg_mood = recent_df['mood_score'].mean()
        st.metric("Avg Mood Score", f"{avg_mood:.2f}")

    with col2:
        avg_energy = recent_df['energy'].mean()
        st.metric("Avg Energy", f"{avg_energy:.2f}")

    with col3:
        diversity = calculate_diversity_score(recent_df, 'artist_name')
        st.metric("Artist Diversity", f"{diversity:.0f}%")

    with col4:
        if 'context' in recent_df.columns:
            top_context = recent_df['context'].mode()[0]
            st.metric("Top Context", top_context.title())

st.markdown("---")

# Temporal patterns
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

# Artist analysis
st.subheader("🎤 Artist Analysis")
plot_top_artists(recent_df)
