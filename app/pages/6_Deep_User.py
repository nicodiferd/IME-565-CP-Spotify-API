"""
Deep User Analytics Page - First-Time User Optimized
Show trends over time (requires multiple snapshots)
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import sys
import os
from datetime import datetime, timezone

# Add parent directory to path to import from func
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from func.ui_components import apply_page_config, get_custom_css
from func.page_auth import require_auth
from func.dashboard_helpers import load_current_snapshot
from func.data_collection import get_user_snapshot_count
from func.s3_storage import load_all_user_data, get_bucket_name

# Apply page configuration
apply_page_config()
st.markdown(get_custom_css(), unsafe_allow_html=True)

# Require authentication
sp, profile = require_auth()
if not sp:
    st.warning("Please connect your Spotify account to view deep user analytics.")
    st.stop()

# ============================================================================
# DEEP USER ANALYTICS PAGE
# ============================================================================

st.header("📊 Deep User Analytics")
st.caption("Track your listening evolution over time")

user_id = profile.get('id')
bucket_name = get_bucket_name()

if not bucket_name:
    st.error("S3 bucket not configured. Please add R2 credentials to your .env file.")
    st.stop()

# Check snapshot count
snapshot_count = get_user_snapshot_count(sp, user_id)

# ============================================================================
# FIRST-TIME USER EXPERIENCE (< 2 snapshots)
# ============================================================================

if snapshot_count < 2:
    st.info(f"📅 **Current Status**: {snapshot_count} snapshot collected")

    st.markdown("""
    <div style='background-color: #282828; padding: 2rem; border-radius: 10px; margin: 2rem 0;'>
        <h3 style='color: #1DB954; margin-top: 0;'>🔮 What is Deep User Analytics?</h3>
        <p style='line-height: 1.8; font-size: 1.05rem;'>
            Deep User Analytics tracks how your listening habits <strong>evolve over time</strong>.
            Since this requires multiple data snapshots, you'll need to return to see your musical journey unfold.
        </p>

        <h4 style='color: #1DB954; margin-top: 1.5rem;'>What you'll see with more data:</h4>
        <ul style='line-height: 2; font-size: 1.05rem;'>
            <li>📈 <strong>Artist Evolution</strong>: How your top artists change week-over-week</li>
            <li>🕐 <strong>Listening Patterns</strong>: Temporal shifts in your music habits</li>
            <li>🎯 <strong>Taste Trajectory</strong>: Are you becoming more mainstream or niche?</li>
            <li>🌍 <strong>Genre Drift</strong>: How your genre preferences evolve</li>
            <li>🔍 <strong>Discovery Trends</strong>: Your exploration rate over time</li>
        </ul>

        <h4 style='color: #1DB954; margin-top: 1.5rem;'>How it works:</h4>
        <p style='line-height: 1.8; font-size: 1.05rem;'>
            We automatically collect a snapshot every 24 hours when you visit the dashboard.
            <strong>Come back in a few days</strong> to see your musical journey unfold!
        </p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    # Show current snapshot preview
    st.subheader("📸 Current Snapshot Preview")
    st.caption("Here's what we captured today:")

    try:
        current_data = load_current_snapshot(user_id)

        # Create tabs for preview
        tab1, tab2, tab3 = st.tabs(["🎤 Top Artists", "🎵 Top Tracks", "⏱️ Recent Activity"])

        with tab1:
            st.markdown("**Top 10 Artists Right Now**")
            st.caption("(Last 4 weeks)")

            top_artists = current_data['top_artists']['short'].head(10)
            st.dataframe(
                top_artists[['rank', 'artist_name', 'popularity', 'genres']],
                use_container_width=True,
                hide_index=True
            )

        with tab2:
            st.markdown("**Top 10 Tracks Right Now**")
            st.caption("(Last 4 weeks)")

            top_tracks = current_data['top_tracks']['short'].head(10)
            st.dataframe(
                top_tracks[['rank', 'track_name', 'artist_name', 'popularity']],
                use_container_width=True,
                hide_index=True
            )

        with tab3:
            st.markdown("**Recent Listening Summary**")

            recent = current_data['recent_tracks']

            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Tracks Played", len(recent))
            with col2:
                st.metric("Unique Artists", recent['artist_name'].nunique())
            with col3:
                avg_pop = recent['popularity'].mean()
                st.metric("Avg Popularity", f"{avg_pop:.0f}/100")

            # Hour of day distribution
            if 'hour_of_day' in recent.columns:
                st.markdown("**Listening by Hour of Day**")

                hourly_counts = recent['hour_of_day'].value_counts().sort_index()

                fig = px.bar(
                    x=hourly_counts.index,
                    y=hourly_counts.values,
                    labels={'x': 'Hour of Day', 'y': 'Number of Tracks'},
                    title='When Do You Listen?'
                )

                fig.update_layout(
                    plot_bgcolor='#121212',
                    paper_bgcolor='#121212',
                    font_color='#FFFFFF',
                    xaxis=dict(tickmode='linear', tick0=0, dtick=2)
                )

                st.plotly_chart(fig, use_container_width=True)

    except Exception as e:
        st.error(f"Could not load current snapshot: {e}")

    st.markdown("---")

    # Show placeholder for future features
    st.info("💡 **Coming Soon (after multiple snapshots):**")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("""
        **📈 Artist Evolution Timeline**
        - Track rank changes over time
        - See which artists you're discovering
        - Identify your musical phases
        """)

    with col2:
        st.markdown("""
        **🎯 Taste Trajectory**
        - Mainstream score over time
        - Genre diversity trends
        - Musical explorer vs consistency score
        """)

    st.stop()

# ============================================================================
# RETURNING USER EXPERIENCE (2+ snapshots)
# ============================================================================

st.success(f"✅ {snapshot_count} snapshots collected - showing historical analysis")

# Tabs for different analyses
tab1, tab2, tab3, tab4 = st.tabs([
    "🎵 Artist Evolution",
    "⏰ Listening Patterns",
    "📈 Metrics Over Time",
    "🎯 Taste Trajectory"
])

# ============================================================================
# TAB 1: ARTIST EVOLUTION
# ============================================================================

with tab1:
    st.subheader("Artist & Genre Evolution")

    with st.spinner("Loading artist data..."):
        # Load top artists data from ALL snapshots
        top_artists = load_all_user_data(bucket_name, user_id, 'top_artists')

        if top_artists.empty:
            st.warning("No artist data available yet")
        else:
            # Convert snapshot_timestamp to datetime
            top_artists['timestamp'] = pd.to_datetime(top_artists['snapshot_timestamp'])
            top_artists = top_artists.sort_values('timestamp')

            # Filter by time range
            time_range = st.selectbox(
                "Select time range to analyze",
                ["short_term", "medium_term", "long_term"],
                format_func=lambda x: {
                    "short_term": "Last 4 Weeks",
                    "medium_term": "Last 6 Months",
                    "long_term": "All Time"
                }[x]
            )

            filtered_artists = top_artists[top_artists['time_range'] == time_range]

            if filtered_artists.empty:
                st.warning(f"No data for {time_range}")
            else:
                # Top artists over time
                st.markdown("### Top 5 Artists Over Time")

                # Get top 5 most frequent artists
                top_5_artists = filtered_artists['artist_name'].value_counts().head(5).index.tolist()

                # Filter for these artists
                top_5_data = filtered_artists[filtered_artists['artist_name'].isin(top_5_artists)]

                fig = px.line(
                    top_5_data,
                    x='timestamp',
                    y='rank',
                    color='artist_name',
                    title=f'Artist Rankings Over Time ({time_range.replace("_", " ").title()})',
                    labels={'timestamp': 'Date', 'rank': 'Rank', 'artist_name': 'Artist'},
                    color_discrete_sequence=px.colors.qualitative.Set2
                )

                fig.update_yaxes(autorange="reversed")  # Rank 1 at top
                fig.update_layout(
                    plot_bgcolor='#121212',
                    paper_bgcolor='#121212',
                    font_color='#FFFFFF'
                )

                st.plotly_chart(fig, use_container_width=True)

                # Genre distribution over time
                st.markdown("### Genre Evolution")

                # Extract genres
                all_genres = []
                for _, row in filtered_artists.iterrows():
                    genres_str = row.get('genres', '')
                    if pd.isna(genres_str) or genres_str == '':
                        continue

                    genres = genres_str.split(', ') if isinstance(genres_str, str) else []
                    timestamp = row['timestamp']
                    for genre in genres:
                        if genre and genre.strip():
                            all_genres.append({'genre': genre, 'timestamp': timestamp})

                if all_genres:
                    genre_df = pd.DataFrame(all_genres)
                    genre_df['month'] = genre_df['timestamp'].dt.to_period('M').astype(str)

                    # Get top 10 genres overall
                    top_genres = genre_df['genre'].value_counts().head(10).index.tolist()
                    genre_df_filtered = genre_df[genre_df['genre'].isin(top_genres)]

                    # Count by month
                    genre_counts = genre_df_filtered.groupby(['month', 'genre']).size().reset_index(name='count')

                    fig = px.bar(
                        genre_counts,
                        x='month',
                        y='count',
                        color='genre',
                        title='Top Genres by Month',
                        labels={'month': 'Month', 'count': 'Appearances', 'genre': 'Genre'},
                        color_discrete_sequence=px.colors.qualitative.Plotly
                    )

                    fig.update_layout(
                        plot_bgcolor='#121212',
                        paper_bgcolor='#121212',
                        font_color='#FFFFFF',
                        xaxis_tickangle=-45
                    )

                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("No genre data available for this time range")

# ============================================================================
# TAB 2: LISTENING PATTERNS
# ============================================================================

with tab2:
    st.subheader("Listening Patterns Over Time")

    with st.spinner("Loading listening data..."):
        # Load recent tracks data from ALL snapshots
        recent_tracks = load_all_user_data(bucket_name, user_id, 'recent_tracks')

        if recent_tracks.empty:
            st.warning("No listening data available yet")
        else:
            # Convert timestamps
            recent_tracks['timestamp'] = pd.to_datetime(recent_tracks['snapshot_timestamp'])
            recent_tracks['date'] = recent_tracks['timestamp'].dt.date
            recent_tracks['hour'] = recent_tracks['timestamp'].dt.hour
            recent_tracks['day_of_week'] = recent_tracks['timestamp'].dt.day_name()

            # Listening frequency over time
            st.markdown("### Listening Activity Over Time")

            daily_counts = recent_tracks.groupby('date').size().reset_index(name='tracks')
            daily_counts['date'] = pd.to_datetime(daily_counts['date'])

            fig = px.line(
                daily_counts,
                x='date',
                y='tracks',
                title='Daily Listening Activity',
                labels={'date': 'Date', 'tracks': 'Tracks Played'}
            )

            fig.update_layout(
                plot_bgcolor='#121212',
                paper_bgcolor='#121212',
                font_color='#FFFFFF'
            )

            st.plotly_chart(fig, use_container_width=True)

            # Hour of day heatmap
            st.markdown("### Listening by Hour & Day of Week")

            hourly_weekly = recent_tracks.groupby(['day_of_week', 'hour']).size().reset_index(name='count')

            # Order days
            day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
            hourly_weekly['day_of_week'] = pd.Categorical(hourly_weekly['day_of_week'], categories=day_order, ordered=True)

            # Create heatmap
            pivot_table = hourly_weekly.pivot(index='day_of_week', columns='hour', values='count').fillna(0)

            fig = px.imshow(
                pivot_table,
                title='Listening Heatmap (Hour x Day)',
                labels=dict(x="Hour of Day", y="Day of Week", color="Tracks"),
                color_continuous_scale='Viridis'
            )

            fig.update_layout(
                plot_bgcolor='#121212',
                paper_bgcolor='#121212',
                font_color='#FFFFFF'
            )

            st.plotly_chart(fig, use_container_width=True)

# ============================================================================
# TAB 3: METRICS OVER TIME
# ============================================================================

with tab3:
    st.subheader("Metrics Over Time")

    with st.spinner("Loading metrics..."):
        # Load metrics from ALL snapshots
        metrics = load_all_user_data(bucket_name, user_id, 'metrics')

        if metrics.empty:
            st.warning("No metrics data available yet")
        else:
            # Convert timestamp
            metrics['timestamp'] = pd.to_datetime(metrics['snapshot_timestamp'])
            metrics = metrics.sort_values('timestamp')

            # Artist diversity over time
            if 'recent_unique_artists' in metrics.columns and 'recent_unique_tracks' in metrics.columns:
                st.markdown("### Artist Diversity Score")

                metrics['artist_diversity'] = metrics['recent_unique_artists'] / metrics['recent_unique_tracks'].replace(0, 1)

                fig = px.line(
                    metrics,
                    x='timestamp',
                    y='artist_diversity',
                    title='Artist Diversity Over Time',
                    labels={'timestamp': 'Date', 'artist_diversity': 'Diversity Score'}
                )

                fig.update_layout(
                    plot_bgcolor='#121212',
                    paper_bgcolor='#121212',
                    font_color='#FFFFFF'
                )

                st.plotly_chart(fig, use_container_width=True)

            # Average popularity over time
            if 'recent_avg_popularity' in metrics.columns:
                st.markdown("### Mainstream Score Over Time")

                fig = px.line(
                    metrics,
                    x='timestamp',
                    y='recent_avg_popularity',
                    title='Average Track Popularity (Mainstream Score)',
                    labels={'timestamp': 'Date', 'recent_avg_popularity': 'Avg Popularity (0-100)'}
                )

                fig.update_layout(
                    plot_bgcolor='#121212',
                    paper_bgcolor='#121212',
                    font_color='#FFFFFF'
                )

                st.plotly_chart(fig, use_container_width=True)

                # Interpretation
                latest_pop = metrics['recent_avg_popularity'].iloc[-1]
                if latest_pop > 70:
                    st.info(f"📈 Mainstream Listener: Your average popularity is {latest_pop:.0f}/100. You prefer popular hits!")
                elif latest_pop < 40:
                    st.info(f"🎵 Indie Explorer: Your average popularity is {latest_pop:.0f}/100. You prefer underground/niche artists!")
                else:
                    st.info(f"⚖️ Balanced Taste: Your average popularity is {latest_pop:.0f}/100. You enjoy a mix of popular and niche music!")

# ============================================================================
# TAB 4: TASTE TRAJECTORY
# ============================================================================

with tab4:
    st.subheader("Taste Trajectory")
    st.caption("How your musical preferences are evolving")

    # Placeholder for future implementation
    st.info("📊 Coming soon: Comprehensive taste trajectory analysis")

    st.markdown("""
    **Features planned:**
    - Mainstream vs Niche trajectory
    - Genre diversity score over time
    - Musical Explorer vs Consistency classification
    - Discovery rate (new artists per month)
    - Mood score trends (if audio features available)
    """)
