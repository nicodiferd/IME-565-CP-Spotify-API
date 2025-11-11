"""
Deep User Page
Explore aggregated historical listening data and trends over time
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import numpy as np

from app.func.s3_storage import load_all_user_data, get_bucket_name
from app.func.data_collection import get_user_snapshot_count


def show_deep_user_page(sp, user_id):
    """
    Main Deep User page function

    Args:
        sp: Authenticated Spotipy client
        user_id: Spotify user ID
    """
    st.header("🔍 Deep User Analytics")
    st.markdown("Explore your listening history and trends over time")

    bucket_name = get_bucket_name()

    if not bucket_name:
        st.error("S3 bucket not configured. Please add S3_BUCKET_NAME to your .env file.")
        return

    # Check if user has any data
    snapshot_count = get_user_snapshot_count(sp, user_id)

    if snapshot_count == 0:
        st.info("📸 No historical data found. Data collection will start automatically on your next login!")
        st.markdown("""
        ### What is Deep User Analytics?

        Deep User Analytics tracks your listening habits over time, allowing you to:
        - See how your music taste evolves
        - Track your top artists and genres across weeks/months
        - Analyze listening patterns and behaviors
        - Compare your taste with team members

        **Data is collected automatically** every time you use the app.
        """)
        return

    st.success(f"📊 Found {snapshot_count} historical snapshots")

    # Tabs for different analyses
    tab1, tab2, tab3, tab4 = st.tabs([
        "🎵 Artist Evolution",
        "⏰ Listening Patterns",
        "👥 Team Comparison",
        "📈 Metrics Over Time"
    ])

    with tab1:
        show_artist_evolution(bucket_name, user_id)

    with tab2:
        show_listening_patterns(bucket_name, user_id)

    with tab3:
        show_team_comparison(bucket_name, user_id)

    with tab4:
        show_metrics_over_time(bucket_name, user_id)


def show_artist_evolution(bucket_name, user_id):
    """Show how top artists change over time"""
    st.subheader("Artist & Genre Evolution")

    with st.spinner("Loading artist data..."):
        # Load top artists data
        top_artists = load_all_user_data(bucket_name, user_id, 'top_artists')

        if top_artists.empty:
            st.warning("No artist data available yet")
            return

    # Convert snapshot_timestamp to datetime
    top_artists['timestamp'] = pd.to_datetime(top_artists['snapshot_timestamp'])
    top_artists = top_artists.sort_values('timestamp')

    # Filter by time range
    time_range = st.selectbox(
        "Select time range to analyze",
        ["short_term", "medium_term", "long_term"],
        format_func=lambda x: {"short_term": "Last 4 Weeks", "medium_term": "Last 6 Months", "long_term": "All Time"}[x]
    )

    filtered_artists = top_artists[top_artists['time_range'] == time_range]

    if filtered_artists.empty:
        st.warning(f"No data for {time_range}")
        return

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
        genres = row['genres'].split(', ')
        timestamp = row['timestamp']
        for genre in genres:
            if genre:
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


def show_listening_patterns(bucket_name, user_id):
    """Show temporal listening patterns"""
    st.subheader("Listening Patterns Over Time")

    with st.spinner("Loading listening data..."):
        # Load recent tracks data
        recent_tracks = load_all_user_data(bucket_name, user_id, 'recent_tracks')

        if recent_tracks.empty:
            st.warning("No listening data available yet")
            return

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
        labels={'date': 'Date', 'tracks': 'Tracks Played'},
        color_discrete_sequence=['#1DB954']
    )

    fig.update_layout(
        plot_bgcolor='#121212',
        paper_bgcolor='#121212',
        font_color='#FFFFFF'
    )

    st.plotly_chart(fig, use_container_width=True)

    # Hour-of-day pattern
    st.markdown("### Time-of-Day Listening Pattern")

    col1, col2 = st.columns(2)

    with col1:
        hourly_counts = recent_tracks['hour'].value_counts().sort_index()

        fig = go.Figure(data=[
            go.Bar(
                x=hourly_counts.index,
                y=hourly_counts.values,
                marker_color='#1DB954'
            )
        ])

        fig.update_layout(
            title='Listening by Hour',
            xaxis_title='Hour (24h)',
            yaxis_title='Number of Tracks',
            plot_bgcolor='#121212',
            paper_bgcolor='#121212',
            font_color='#FFFFFF'
        )

        st.plotly_chart(fig, use_container_width=True)

    with col2:
        # Day of week pattern
        day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        day_counts = recent_tracks['day_of_week'].value_counts().reindex(day_order, fill_value=0)

        fig = go.Figure(data=[
            go.Bar(
                x=day_counts.index,
                y=day_counts.values,
                marker_color='#1DB954'
            )
        ])

        fig.update_layout(
            title='Listening by Day of Week',
            xaxis_title='Day',
            yaxis_title='Number of Tracks',
            plot_bgcolor='#121212',
            paper_bgcolor='#121212',
            font_color='#FFFFFF',
            xaxis_tickangle=-45
        )

        st.plotly_chart(fig, use_container_width=True)


def show_team_comparison(bucket_name, user_id):
    """Compare listening habits with team members"""
    st.subheader("Team Comparison")

    st.info("🚧 Team comparison features coming soon! This will show:")
    st.markdown("""
    - **Taste Overlap**: Artists and tracks you have in common with team members
    - **Diversity Scores**: Compare artist/genre diversity across the team
    - **Listening Patterns**: Who listens the most, and when
    - **Music Explorer Score**: Who discovers new artists most frequently
    - **Mood Profiles**: Compare average energy, valence, and mood scores
    """)

    # Placeholder for team comparison
    st.markdown("### Your Listening Profile")

    with st.spinner("Analyzing your data..."):
        recent_tracks = load_all_user_data(bucket_name, user_id, 'recent_tracks')

        if not recent_tracks.empty:
            col1, col2, col3 = st.columns(3)

            with col1:
                unique_artists = recent_tracks['artist_name'].nunique()
                st.metric("Unique Artists", unique_artists)

            with col2:
                if 'energy' in recent_tracks.columns:
                    avg_energy = recent_tracks['energy'].mean()
                    st.metric("Avg Energy", f"{avg_energy:.2f}")

            with col3:
                if 'valence' in recent_tracks.columns:
                    avg_valence = recent_tracks['valence'].mean()
                    st.metric("Avg Mood", f"{avg_valence:.2f}")


def show_metrics_over_time(bucket_name, user_id):
    """Show computed metrics over time"""
    st.subheader("Metrics Evolution")

    with st.spinner("Loading metrics..."):
        # Load metrics data
        from app.func.s3_storage import load_all_user_data

        metrics = load_all_user_data(bucket_name, user_id, 'metrics')

        if metrics.empty:
            st.warning("No metrics data available yet")
            return

    # Convert timestamp
    metrics['timestamp'] = pd.to_datetime(metrics['snapshot_timestamp'])
    metrics = metrics.sort_values('timestamp')

    # Audio feature trends
    st.markdown("### Audio Feature Trends")

    audio_features = ['energy', 'valence', 'danceability', 'acousticness']
    available_features = [f'recent_avg_{f}' for f in audio_features if f'recent_avg_{f}' in metrics.columns]

    if available_features:
        selected_features = st.multiselect(
            "Select features to visualize",
            available_features,
            default=available_features[:2],
            format_func=lambda x: x.replace('recent_avg_', '').title()
        )

        if selected_features:
            fig = go.Figure()

            for feature in selected_features:
                fig.add_trace(go.Scatter(
                    x=metrics['timestamp'],
                    y=metrics[feature],
                    mode='lines+markers',
                    name=feature.replace('recent_avg_', '').title()
                ))

            fig.update_layout(
                title='Audio Features Over Time',
                xaxis_title='Date',
                yaxis_title='Value',
                plot_bgcolor='#121212',
                paper_bgcolor='#121212',
                font_color='#FFFFFF',
                hovermode='x unified'
            )

            st.plotly_chart(fig, use_container_width=True)

    # Diversity trends
    st.markdown("### Artist Diversity Over Time")

    if 'recent_artist_diversity' in metrics.columns:
        fig = px.line(
            metrics,
            x='timestamp',
            y='recent_artist_diversity',
            title='Artist Diversity Score',
            labels={'timestamp': 'Date', 'recent_artist_diversity': 'Diversity Score'},
            color_discrete_sequence=['#1DB954']
        )

        fig.update_layout(
            plot_bgcolor='#121212',
            paper_bgcolor='#121212',
            font_color='#FFFFFF'
        )

        st.plotly_chart(fig, use_container_width=True)

    # Context distribution over time
    st.markdown("### Listening Context Over Time")

    context_cols = [col for col in metrics.columns if col.startswith('recent_pct_')]

    if context_cols:
        context_df = metrics[['timestamp'] + context_cols].copy()

        # Reshape for plotting
        context_long = context_df.melt(
            id_vars=['timestamp'],
            value_vars=context_cols,
            var_name='context',
            value_name='percentage'
        )

        context_long['context'] = context_long['context'].str.replace('recent_pct_', '').str.title()

        fig = px.area(
            context_long,
            x='timestamp',
            y='percentage',
            color='context',
            title='Listening Context Distribution Over Time',
            labels={'timestamp': 'Date', 'percentage': 'Percentage', 'context': 'Context'},
            color_discrete_sequence=px.colors.sequential.Greens
        )

        fig.update_layout(
            plot_bgcolor='#121212',
            paper_bgcolor='#121212',
            font_color='#FFFFFF'
        )

        st.plotly_chart(fig, use_container_width=True)
