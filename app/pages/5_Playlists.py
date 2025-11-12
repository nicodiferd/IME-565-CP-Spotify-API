"""
Playlists Page
Overview of user's Spotify playlists with metadata and quick access
"""

import streamlit as st
import sys
import os

# Add parent directory to path to import from func
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from func.ui_components import apply_page_config, get_custom_css
from func.page_auth import require_auth
from func.data_fetching import fetch_playlists

# Apply page configuration
apply_page_config()
st.markdown(get_custom_css(), unsafe_allow_html=True)

# Require authentication
sp, profile = require_auth()
if not sp:
    st.warning("Please connect your Spotify account to view playlists.")
    st.stop()

# ============================================================================
# PLAYLISTS PAGE
# ============================================================================

st.header("🎵 Your Playlists")

# Fetch data
playlists = fetch_playlists(sp, limit=50)

if not playlists:
    st.warning("No playlists found.")
    st.stop()

# Summary metrics
total_playlists = len(playlists)
total_tracks = sum(p.get('tracks', {}).get('total', 0) for p in playlists)

col1, col2, col3 = st.columns(3)

with col1:
    st.metric("Total Playlists", total_playlists)

with col2:
    st.metric("Total Tracks", total_tracks)

with col3:
    avg_tracks = total_tracks / total_playlists if total_playlists > 0 else 0
    st.metric("Avg Tracks/Playlist", f"{avg_tracks:.0f}")

st.markdown("---")

# Display playlists
for playlist in playlists:
    with st.expander(f"🎵 {playlist.get('name', 'Unnamed')} ({playlist.get('tracks', {}).get('total', 0)} tracks)"):
        col_a, col_b = st.columns([1, 3])

        with col_a:
            # Playlist image
            images = playlist.get('images', [])
            if images:
                st.image(images[0].get('url'), width=150)

        with col_b:
            st.write(f"**Owner**: {playlist.get('owner', {}).get('display_name', 'Unknown')}")
            st.write(f"**Public**: {'Yes' if playlist.get('public') else 'No'}")
            st.write(f"**Tracks**: {playlist.get('tracks', {}).get('total', 0)}")

            if playlist.get('description'):
                st.caption(playlist.get('description'))

            # Link to open in Spotify
            playlist_url = playlist.get('external_urls', {}).get('spotify')
            if playlist_url:
                st.link_button("Open in Spotify", playlist_url)
