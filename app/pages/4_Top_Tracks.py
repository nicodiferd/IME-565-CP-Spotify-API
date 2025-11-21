"""
Top Tracks Page
Display top tracks across different time ranges with side-by-side comparisons and taste consistency analysis
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
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

# Apply page configuration
apply_page_config()
st.markdown(get_custom_css(), unsafe_allow_html=True)

# Require authentication
sp, profile = require_auth()
if not sp:
    st.warning("Please connect your Spotify account to view top tracks.")
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
# TOP TRACKS PAGE
# ============================================================================

st.header("🏆 Top Tracks")

# Show sync status
display_sync_status(data['metadata'])

# Load all time ranges
tracks_short = data['top_tracks']['short'].copy()
tracks_medium = data['top_tracks']['medium'].copy()
tracks_long = data['top_tracks']['long'].copy()

# Enrich with audio features
with st.spinner("Enriching with audio features..."):
    tracks_short = enrich_with_audio_features(tracks_short, verbose=False)
    tracks_medium = enrich_with_audio_features(tracks_medium, verbose=False)
    tracks_long = enrich_with_audio_features(tracks_long, verbose=False)

# ============================================================================
# TIME RANGE SELECTOR & COMPARISON
# ============================================================================

# Add tabs for different views
view_mode = st.radio(
    "View Mode",
    ["Single Time Range", "Side-by-Side Comparison", "Taste Evolution"],
    horizontal=True
)

st.markdown("---")

if view_mode == "Single Time Range":
    # ========================================================================
    # SINGLE TIME RANGE VIEW
    # ========================================================================

    time_range_map = {
        'Last 4 Weeks': ('short', tracks_short),
        'Last 6 Months': ('medium', tracks_medium),
        'All Time': ('long', tracks_long)
    }

    selected_range = st.selectbox("Select Time Range", list(time_range_map.keys()))
    time_range, top_df = time_range_map[selected_range]

    if top_df.empty:
        st.warning("No top tracks data available for this time range.")
        st.stop()

    # Audio feature summary
    coverage = get_audio_features_coverage(top_df)

    if coverage['coverage_pct'] > 0:
        st.subheader("📊 Audio Profile")

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            if 'energy' in top_df.columns:
                avg_energy = top_df['energy'].mean()
                st.metric("Avg Energy", f"{avg_energy:.2f}")

        with col2:
            if 'valence' in top_df.columns:
                avg_valence = top_df['valence'].mean()
                st.metric("Avg Valence", f"{avg_valence:.2f}")

        with col3:
            if 'danceability' in top_df.columns:
                avg_dance = top_df['danceability'].mean()
                st.metric("Avg Danceability", f"{avg_dance:.2f}")

        with col4:
            if 'tempo' in top_df.columns:
                avg_tempo = top_df['tempo'].mean()
                st.metric("Avg Tempo", f"{avg_tempo:.0f} BPM")

        st.markdown("---")

    # Display tracks
    st.subheader(f"Top 20 Tracks ({selected_range})")

    for idx, row in top_df.head(20).iterrows():
        col1, col2 = st.columns([1, 10])

        with col1:
            st.markdown(f"### {row.get('rank', idx + 1)}")

        with col2:
            st.markdown(f"**{row['track_name']}**")

            caption_parts = [
                f"{row['artist_name']}",
                f"{row.get('album_name', 'Unknown Album')}",
                f"Popularity: {row.get('popularity', 'N/A')}"
            ]

            if 'context' in row and pd.notna(row['context']):
                caption_parts.append(f"Context: {row['context'].title()}")

            st.caption(" • ".join(caption_parts))

        st.markdown("---")

elif view_mode == "Side-by-Side Comparison":
    # ========================================================================
    # SIDE-BY-SIDE COMPARISON
    # ========================================================================

    st.subheader("🔄 Time Range Comparison")

    # Show taste consistency metrics
    metrics = data['metrics']
    taste = metrics.get('taste_consistency', {})
    overlap = taste.get('short_vs_long_overlap', 0)
    overlap_pct = taste.get('short_vs_long_overlap_pct', 0)

    st.info(f"🎯 **Taste Consistency**: {overlap} tracks overlap between short-term and long-term ({overlap_pct:.1f}%)")

    # Three columns for three time ranges
    col_short, col_med, col_long = st.columns(3)

    with col_short:
        st.markdown("### 📅 Last 4 Weeks")
        if not tracks_short.empty:
            for idx, row in tracks_short.head(10).iterrows():
                st.caption(f"{row.get('rank', idx+1)}. {row['track_name']}")
                st.caption(f"   ↳ {row['artist_name']}")
        else:
            st.caption("No data")

    with col_med:
        st.markdown("### 📆 Last 6 Months")
        if not tracks_medium.empty:
            for idx, row in tracks_medium.head(10).iterrows():
                st.caption(f"{row.get('rank', idx+1)}. {row['track_name']}")
                st.caption(f"   ↳ {row['artist_name']}")
        else:
            st.caption("No data")

    with col_long:
        st.markdown("### 🗓️ All Time")
        if not tracks_long.empty:
            for idx, row in tracks_long.head(10).iterrows():
                st.caption(f"{row.get('rank', idx+1)}. {row['track_name']}")
                st.caption(f"   ↳ {row['artist_name']}")
        else:
            st.caption("No data")

    st.markdown("---")

    # Audio profile comparison
    st.subheader("📊 Audio Profile Comparison")

    # Calculate averages for each time range
    profile_data = []

    for name, df in [('Last 4 Weeks', tracks_short), ('Last 6 Months', tracks_medium), ('All Time', tracks_long)]:
        if not df.empty:
            coverage = get_audio_features_coverage(df)

            if coverage['coverage_pct'] > 0:
                profile_data.append({
                    'Time Range': name,
                    'Energy': df['energy'].mean() if 'energy' in df.columns else 0,
                    'Valence': df['valence'].mean() if 'valence' in df.columns else 0,
                    'Danceability': df['danceability'].mean() if 'danceability' in df.columns else 0,
                    'Acousticness': df['acousticness'].mean() if 'acousticness' in df.columns else 0
                })

    if profile_data:
        import plotly.express as px

        profile_df = pd.DataFrame(profile_data)

        # Melt for plotting
        melted = profile_df.melt(id_vars=['Time Range'], var_name='Feature', value_name='Score')

        fig = px.bar(
            melted,
            x='Feature',
            y='Score',
            color='Time Range',
            barmode='group',
            title='Audio Features by Time Range',
            labels={'Score': 'Average Score (0-1)'},
            color_discrete_sequence=['#1DB954', '#1ED760', '#1FDF64']
        )

        fig.update_layout(
            plot_bgcolor='#121212',
            paper_bgcolor='#121212',
            font_color='#FFFFFF',
            height=400
        )

        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Audio features not available for comparison")

else:
    # ========================================================================
    # TASTE EVOLUTION VIEW
    # ========================================================================

    st.subheader("📈 Musical Taste Evolution")

    # Analyze overlap between time ranges
    short_ids = set(tracks_short['track_id']) if not tracks_short.empty else set()
    medium_ids = set(tracks_medium['track_id']) if not tracks_medium.empty else set()
    long_ids = set(tracks_long['track_id']) if not tracks_long.empty else set()

    # Calculate overlaps
    short_medium_overlap = len(short_ids & medium_ids)
    short_long_overlap = len(short_ids & long_ids)
    medium_long_overlap = len(medium_ids & long_ids)
    all_three_overlap = len(short_ids & medium_ids & long_ids)

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Short ∩ Medium", short_medium_overlap)

    with col2:
        st.metric("Short ∩ Long", short_long_overlap)

    with col3:
        st.metric("Medium ∩ Long", medium_long_overlap)

    with col4:
        st.metric("All Three", all_three_overlap)

    st.markdown("---")

    # Taste consistency interpretation
    st.subheader("🎯 Interpretation")

    metrics = data['metrics']
    taste = metrics.get('taste_consistency', {})
    overlap_pct = taste.get('short_vs_long_overlap_pct', 0)
    consistency_type = taste.get('consistency_type', 'Unknown')

    if overlap_pct > 60:
        st.success(f"""
        ### 🎵 {consistency_type}
        {overlap_pct:.0f}% of your current favorites are also all-time classics for you!

        **What this means**:
        - You have well-defined musical preferences
        - Your taste is stable over time
        - You've found what you love and stick to it
        """)
    elif overlap_pct > 30:
        st.info(f"""
        ### 🔀 Balanced Explorer
        {overlap_pct:.0f}% overlap between current and all-time favorites.

        **What this means**:
        - You have core favorites but also explore new music
        - Good balance between consistency and discovery
        - Your taste evolves but maintains roots
        """)
    else:
        st.warning(f"""
        ### 🔍 {consistency_type}
        Only {overlap_pct:.0f}% overlap - you're always discovering new music!

        **What this means**:
        - You're adventurous in your musical tastes
        - Constantly exploring new artists and tracks
        - Your current favorites differ significantly from your long-term history
        """)

    st.markdown("---")

    # Show tracks that appear in all three ranges (core favorites)
    if all_three_overlap > 0:
        st.subheader("⭐ Core Favorites (In All Time Ranges)")

        all_three_tracks = tracks_short[tracks_short['track_id'].isin(short_ids & medium_ids & long_ids)].head(10)

        for idx, row in all_three_tracks.iterrows():
            st.markdown(f"**{row['track_name']}** by {row['artist_name']}")
            st.caption(f"Popularity: {row.get('popularity', 'N/A')}")
            st.markdown("---")
    else:
        st.info("No tracks appear in all three time ranges - you're a true musical explorer!")
