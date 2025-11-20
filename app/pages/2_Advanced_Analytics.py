"""
Advanced Analytics Page
Detailed audio feature analysis, mood analysis, and feature distributions
"""

import streamlit as st
import plotly.graph_objects as go
import sys
import os

# Add parent directory to path to import from func
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from func.ui_components import apply_page_config, get_custom_css
from func.page_auth import require_auth
from func.data_fetching import fetch_recently_played
from func.data_processing import process_recent_tracks
from func.visualizations import (
    plot_audio_features_radar,
    plot_mood_distribution,
    plot_energy_valence_scatter,
    plot_context_breakdown
)

# Apply page configuration
apply_page_config()
st.markdown(get_custom_css(), unsafe_allow_html=True)

# Require authentication
sp, profile = require_auth()
if not sp:
    st.warning("Please connect your Spotify account to view analytics.")
    st.stop()

# ============================================================================
# ADVANCED ANALYTICS PAGE
# ============================================================================

st.header("📈 Advanced Analytics")

# Fetch data
with st.spinner("Analyzing your music..."):
    recent_items = fetch_recently_played(sp, limit=50)
    recent_df = process_recent_tracks(recent_items, sp)

if recent_df.empty:
    st.warning("No data available for analysis")
    st.stop()

# Check if audio features are available
has_audio_features = 'danceability' in recent_df.columns

if not has_audio_features:
    st.info("🎵 Audio features are being loaded. This may take a moment...")
    st.markdown("Audio features provide deeper insights into your music taste.")

# Audio feature profile
st.subheader("🎵 Your Audio Feature Profile")

col1, col2 = st.columns(2)

with col1:
    plot_audio_features_radar(recent_df)

with col2:
    if 'mood_score' in recent_df.columns:
        plot_mood_distribution(recent_df)
    else:
        st.info("Mood analysis requires audio features")

st.markdown("---")

# Mood quadrants
st.subheader("🎭 Mood Analysis")

col1, col2 = st.columns(2)

with col1:
    plot_energy_valence_scatter(recent_df)

with col2:
    plot_context_breakdown(recent_df)

st.markdown("---")

# Detailed audio features
if has_audio_features:
    st.subheader("📊 Audio Feature Distributions")

    features_to_plot = ['danceability', 'energy', 'valence', 'acousticness',
                       'speechiness', 'instrumentalness']
    available = [f for f in features_to_plot if f in recent_df.columns]

    if available:
        selected_features = st.multiselect(
            "Select features to visualize",
            available,
            default=available[:3]
        )

        if selected_features:
            fig = go.Figure()

            for feature in selected_features:
                fig.add_trace(go.Box(
                    y=recent_df[feature],
                    name=feature.capitalize(),
                    boxmean='sd'
                ))

            fig.update_layout(
                title='Audio Feature Distributions',
                yaxis_title='Value (0-1)',
                plot_bgcolor='#121212',
                paper_bgcolor='#121212',
                font_color='#FFFFFF',
                showlegend=True
            )

            st.plotly_chart(fig, use_container_width=True)
