"""
Recent Listening Page
Detailed view of recently played tracks with timeline and downloadable data
"""

import streamlit as st
from datetime import datetime
import sys
import os

# Add parent directory to path to import from func
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from func.ui_components import apply_page_config, get_custom_css
from func.page_auth import require_auth
from func.data_fetching import fetch_recently_played
from func.data_processing import process_recent_tracks
from func.visualizations import plot_recent_timeline

# Apply page configuration
apply_page_config()
st.markdown(get_custom_css(), unsafe_allow_html=True)

# Require authentication
sp, profile = require_auth()
if not sp:
    st.warning("Please connect your Spotify account to view recent listening.")
    st.stop()

# ============================================================================
# RECENT LISTENING PAGE
# ============================================================================

st.header("🕒 Recent Listening")

# Fetch data
recent_items = fetch_recently_played(sp, limit=50)
recent_df = process_recent_tracks(recent_items, sp)

if recent_df.empty:
    st.warning("No recent listening data available.")
    st.stop()

# Timeline visualization
plot_recent_timeline(recent_df)

st.markdown("---")

# Data table
st.subheader("📋 Track List")

# Select columns to display
base_cols = ['played_at', 'track_name', 'artist_name', 'album_name', 'duration_min', 'popularity']

if 'context' in recent_df.columns:
    base_cols.append('context')
if 'mood_score' in recent_df.columns:
    base_cols.extend(['mood_score', 'energy', 'valence'])

display_df = recent_df[[col for col in base_cols if col in recent_df.columns]].copy()

# Format columns
display_df['played_at'] = display_df['played_at'].dt.strftime('%Y-%m-%d %H:%M')
display_df['duration_min'] = display_df['duration_min'].round(2)

if 'mood_score' in display_df.columns:
    display_df['mood_score'] = display_df['mood_score'].round(2)
if 'energy' in display_df.columns:
    display_df['energy'] = display_df['energy'].round(2)
if 'valence' in display_df.columns:
    display_df['valence'] = display_df['valence'].round(2)

# Rename columns
col_names = {
    'played_at': 'Played At',
    'track_name': 'Track',
    'artist_name': 'Artist',
    'album_name': 'Album',
    'duration_min': 'Duration (min)',
    'popularity': 'Popularity',
    'context': 'Context',
    'mood_score': 'Mood',
    'energy': 'Energy',
    'valence': 'Valence'
}
display_df.rename(columns=col_names, inplace=True)

st.dataframe(display_df, use_container_width=True, height=400)

# Download button
csv = display_df.to_csv(index=False)
st.download_button(
    label="📥 Download as CSV",
    data=csv,
    file_name=f"spotify_recent_listening_{datetime.now().strftime('%Y%m%d')}.csv",
    mime="text/csv"
)
