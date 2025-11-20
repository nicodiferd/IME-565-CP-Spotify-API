"""
Top Tracks Page
Display top tracks across different time ranges with audio feature profiles
"""

import streamlit as st
import pandas as pd
import sys
import os

# Add parent directory to path to import from func
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from func.ui_components import apply_page_config, get_custom_css
from func.page_auth import require_auth
from func.data_fetching import fetch_top_tracks
from func.data_processing import process_top_tracks

# Apply page configuration
apply_page_config()
st.markdown(get_custom_css(), unsafe_allow_html=True)

# Require authentication
sp, profile = require_auth()
if not sp:
    st.warning("Please connect your Spotify account to view top tracks.")
    st.stop()

# ============================================================================
# TOP TRACKS PAGE
# ============================================================================

st.header("🏆 Top Tracks")

# Time range selector
time_range_map = {
    'Last 4 Weeks': 'short_term',
    'Last 6 Months': 'medium_term',
    'All Time': 'long_term'
}

selected_range = st.selectbox("Select Time Range", list(time_range_map.keys()))
time_range = time_range_map[selected_range]

# Fetch data
with st.spinner("Loading your top tracks..."):
    top_tracks = fetch_top_tracks(sp, time_range=time_range, limit=20)
    top_df = process_top_tracks(top_tracks, sp)

if top_df.empty:
    st.warning("No top tracks data available for this time range.")
    st.stop()

# Show audio feature summary if available
if 'energy' in top_df.columns:
    st.subheader("📊 Top Tracks Audio Profile")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        avg_energy = top_df['energy'].mean()
        st.metric("Avg Energy", f"{avg_energy:.2f}")

    with col2:
        avg_valence = top_df['valence'].mean()
        st.metric("Avg Valence", f"{avg_valence:.2f}")

    with col3:
        avg_danceability = top_df['danceability'].mean()
        st.metric("Avg Danceability", f"{avg_danceability:.2f}")

    with col4:
        avg_tempo = top_df['tempo'].mean()
        st.metric("Avg Tempo", f"{avg_tempo:.0f} BPM")

    st.markdown("---")

# Display as numbered list
st.subheader(f"Your Top 20 Tracks ({selected_range})")

for idx, row in top_df.iterrows():
    col1, col2 = st.columns([1, 10])

    with col1:
        st.markdown(f"### {idx + 1}")

    with col2:
        st.markdown(f"**{row['track_name']}**")

        caption_parts = [
            f"{row['artist_name']}",
            f"{row['album_name']}",
            f"Popularity: {row['popularity']}"
        ]

        if 'context' in row and pd.notna(row['context']):
            caption_parts.append(f"Context: {row['context'].title()}")

        st.caption(" • ".join(caption_parts))

    st.markdown("---")
