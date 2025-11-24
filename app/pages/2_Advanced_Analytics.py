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
from func.dashboard_helpers import (
    load_current_snapshot,
    handle_missing_data,
    display_sync_status,
    enrich_with_audio_features,
    get_audio_features_coverage
)
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

user_id = profile['id']

# ============================================================================
# LOAD SNAPSHOT DATA
# ============================================================================

try:
    data = load_current_snapshot(user_id)
except Exception as e:
    handle_missing_data(redirect_to_sync=True)

# ============================================================================
# ADVANCED ANALYTICS PAGE
# ============================================================================

st.header("📈 Advanced Analytics")

# Show sync status
display_sync_status(data['metadata'])

# Load recent tracks and enrich with audio features
recent_df = data['recent_tracks'].copy()

if recent_df.empty:
    st.warning("No data available for analysis")
    st.stop()

# Enrich with Kaggle audio features
with st.spinner("Enriching with audio features from Kaggle dataset..."):
    recent_df = enrich_with_audio_features(recent_df, verbose=False)

# Get audio features coverage
coverage = get_audio_features_coverage(recent_df)

# Show coverage info
if coverage['coverage_pct'] > 0:
    st.success(f"🎵 Audio features available for {coverage['tracks_with_features']}/{coverage['total_tracks']} tracks ({coverage['coverage_pct']:.1f}%)")
else:
    st.warning("⚠️ Audio features not available for your tracks. Analysis will be limited.")
    st.info(f"""
    **Audio features are provided by the Kaggle Spotify dataset.**

    Coverage: {coverage['coverage_pct']:.1f}%

    If your tracks are very new or obscure, they may not be in our dataset yet.
    Premium users can access Spotify's Audio Features API for 100% coverage.
    """)

# ============================================================================
# AUDIO FEATURE PROFILE
# ============================================================================

st.subheader("🎵 Your Audio Feature Profile")

col1, col2 = st.columns(2)

with col1:
    if coverage['coverage_pct'] > 0:
        plot_audio_features_radar(recent_df)
    else:
        st.info("Audio features radar chart requires audio features from Kaggle dataset")

with col2:
    if 'mood_score' in recent_df.columns:
        plot_mood_distribution(recent_df)
    else:
        st.info("Mood analysis requires audio features from Kaggle dataset")

st.markdown("---")

# ============================================================================
# MOOD ANALYSIS
# ============================================================================

st.subheader("🎭 Mood Analysis")

col1, col2 = st.columns(2)

with col1:
    if coverage['coverage_pct'] > 0:
        plot_energy_valence_scatter(recent_df)
    else:
        st.info("Energy-Valence analysis requires audio features")

with col2:
    if 'context' in recent_df.columns:
        plot_context_breakdown(recent_df)
    else:
        st.info("Context classification requires audio features")

st.markdown("---")

# ============================================================================
# AUDIO FEATURE DISTRIBUTIONS
# ============================================================================

if coverage['coverage_pct'] > 0:
    st.subheader("📊 Audio Feature Distributions")

    features_to_plot = ['danceability', 'energy', 'valence', 'acousticness',
                       'speechiness', 'instrumentalness', 'liveness']
    available = [f for f in features_to_plot if f in recent_df.columns and recent_df[f].notna().any()]

    if available:
        selected_features = st.multiselect(
            "Select features to visualize",
            available,
            default=available[:3] if len(available) >= 3 else available
        )

        if selected_features:
            fig = go.Figure()

            for feature in selected_features:
                # Filter out NaN values for this feature
                valid_data = recent_df[feature].dropna()

                if len(valid_data) > 0:
                    fig.add_trace(go.Box(
                        y=valid_data,
                        name=feature.capitalize(),
                        boxmean='sd'
                    ))

            fig.update_layout(
                title='Audio Feature Distributions',
                yaxis_title='Value (0-1)',
                plot_bgcolor='#121212',
                paper_bgcolor='#121212',
                font_color='#FFFFFF',
                showlegend=True,
                height=500
            )

            st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")

    # ============================================================================
    # COMPOSITE FEATURES (NEW)
    # ============================================================================

    if any(col in recent_df.columns for col in ['mood_score', 'grooviness', 'focus_score', 'relaxation_score']):
        st.subheader("🎨 Composite Features")

        st.caption("""
        Composite features combine multiple audio features to create higher-level insights:
        - **Mood Score**: Happiness/positivity (valence + energy - acousticness)
        - **Grooviness**: Dance/upbeat quality (danceability + energy + tempo)
        - **Focus Score**: Concentration suitability (low speechiness + high instrumentalness)
        - **Relaxation Score**: Calmness/chill quality (low energy + high acousticness + low tempo)
        """)

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            if 'mood_score' in recent_df.columns:
                avg_mood = recent_df['mood_score'].mean()
                st.metric("Avg Mood Score", f"{avg_mood:.2f}")
                st.caption(f"Range: {recent_df['mood_score'].min():.2f} - {recent_df['mood_score'].max():.2f}")

        with col2:
            if 'grooviness' in recent_df.columns:
                avg_groovy = recent_df['grooviness'].mean()
                st.metric("Avg Grooviness", f"{avg_groovy:.2f}")
                st.caption(f"Range: {recent_df['grooviness'].min():.2f} - {recent_df['grooviness'].max():.2f}")

        with col3:
            if 'focus_score' in recent_df.columns:
                avg_focus = recent_df['focus_score'].mean()
                st.metric("Avg Focus Score", f"{avg_focus:.2f}")
                st.caption(f"Range: {recent_df['focus_score'].min():.2f} - {recent_df['focus_score'].max():.2f}")

        with col4:
            if 'relaxation_score' in recent_df.columns:
                avg_relax = recent_df['relaxation_score'].mean()
                st.metric("Avg Relaxation", f"{avg_relax:.2f}")
                st.caption(f"Range: {recent_df['relaxation_score'].min():.2f} - {recent_df['relaxation_score'].max():.2f}")

        # Composite feature comparison
        composite_features = [col for col in ['mood_score', 'grooviness', 'focus_score', 'relaxation_score']
                             if col in recent_df.columns]

        if composite_features:
            import plotly.express as px
            import pandas as pd

            # Create summary dataframe
            composite_data = []
            for feature in composite_features:
                feature_name = feature.replace('_score', '').replace('_', ' ').title()
                composite_data.append({
                    'Feature': feature_name,
                    'Average': recent_df[feature].mean(),
                    'Min': recent_df[feature].min(),
                    'Max': recent_df[feature].max()
                })

            composite_df = pd.DataFrame(composite_data)

            fig = px.bar(
                composite_df,
                x='Feature',
                y='Average',
                title='Composite Features Comparison',
                labels={'Average': 'Average Score (0-1)'},
                color='Average',
                color_continuous_scale='Viridis'
            )

            fig.update_layout(
                plot_bgcolor='#121212',
                paper_bgcolor='#121212',
                font_color='#FFFFFF',
                height=400
            )

            st.plotly_chart(fig, use_container_width=True)

else:
    st.info("""
    ### 💡 Audio Features Not Available

    Audio features provide deep insights into your music:
    - **Danceability**: How suitable for dancing (0-1)
    - **Energy**: Intensity and activity level (0-1)
    - **Valence**: Musical positiveness/happiness (0-1)
    - **Acousticness**: Likelihood of being acoustic (0-1)
    - **Instrumentalness**: Predicts lack of vocals (0-1)
    - **Speechiness**: Presence of spoken words (0-1)

    We enrich your tracks with features from the Kaggle Spotify dataset (~114k tracks).
    Coverage depends on track popularity and recency.
    """)
