"""
Visualization Functions for Spotify Analytics
All Plotly chart generation functions with Spotify-themed styling
"""

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from . import datetime_utils


# ============================================================================
# ADVANCED VISUALIZATION FUNCTIONS
# ============================================================================

def plot_audio_features_radar(df):
    """Plot radar chart of average audio features"""
    if df.empty:
        st.warning("No data available")
        return

    # Check if audio features exist
    features = ['danceability', 'energy', 'speechiness', 'acousticness',
                'instrumentalness', 'liveness', 'valence']

    available_features = [f for f in features if f in df.columns]

    if not available_features:
        st.info("Audio features not available. Enable API access to see this chart.")
        return

    # Calculate averages
    averages = df[available_features].mean()

    fig = go.Figure()

    fig.add_trace(go.Scatterpolar(
        r=averages.values,
        theta=[f.capitalize() for f in available_features],
        fill='toself',
        fillcolor='rgba(29, 185, 84, 0.5)',
        line=dict(color='#1DB954', width=2),
        name='Your Average'
    ))

    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 1],
                gridcolor='#404040'
            ),
            bgcolor='#121212'
        ),
        showlegend=False,
        title='Your Audio Feature Profile',
        plot_bgcolor='#121212',
        paper_bgcolor='#121212',
        font_color='#FFFFFF',
        height=500
    )

    st.plotly_chart(fig, use_container_width=True)


def plot_mood_distribution(df):
    """Plot mood score distribution"""
    if df.empty or 'mood_score' not in df.columns:
        st.info("Mood scores not available")
        return

    fig = px.histogram(
        df,
        x='mood_score',
        nbins=30,
        title='Mood Score Distribution',
        labels={'mood_score': 'Mood Score (Higher = Happier)', 'count': 'Number of Tracks'},
        color_discrete_sequence=['#1DB954']
    )

    fig.update_layout(
        plot_bgcolor='#121212',
        paper_bgcolor='#121212',
        font_color='#FFFFFF',
        showlegend=False
    )

    st.plotly_chart(fig, use_container_width=True)


def plot_context_breakdown(df):
    """Plot context distribution pie chart"""
    if df.empty or 'context' not in df.columns:
        st.info("Context classification not available")
        return

    context_counts = df['context'].value_counts()

    fig = px.pie(
        values=context_counts.values,
        names=context_counts.index,
        title='Listening Context Breakdown',
        color_discrete_sequence=px.colors.sequential.Greens
    )

    fig.update_layout(
        plot_bgcolor='#121212',
        paper_bgcolor='#121212',
        font_color='#FFFFFF'
    )

    st.plotly_chart(fig, use_container_width=True)


def plot_energy_valence_scatter(df):
    """Plot energy vs valence scatter plot"""
    if df.empty or 'energy' not in df.columns or 'valence' not in df.columns:
        st.info("Energy/valence data not available")
        return

    fig = px.scatter(
        df,
        x='valence',
        y='energy',
        color='popularity',
        hover_data=['track_name', 'artist_name'],
        title='Energy vs Valence (Mood Quadrants)',
        labels={'valence': 'Valence (Happy →)', 'energy': 'Energy (Energetic →)',
                'popularity': 'Popularity'},
        color_continuous_scale='Greens'
    )

    # Add quadrant lines
    fig.add_hline(y=0.5, line_dash="dash", line_color="#404040", opacity=0.5)
    fig.add_vline(x=0.5, line_dash="dash", line_color="#404040", opacity=0.5)

    # Add quadrant labels
    fig.add_annotation(x=0.75, y=0.75, text="Happy & Energetic",
                      showarrow=False, font=dict(color="#888888"))
    fig.add_annotation(x=0.25, y=0.75, text="Sad & Energetic",
                      showarrow=False, font=dict(color="#888888"))
    fig.add_annotation(x=0.75, y=0.25, text="Happy & Calm",
                      showarrow=False, font=dict(color="#888888"))
    fig.add_annotation(x=0.25, y=0.25, text="Sad & Calm",
                      showarrow=False, font=dict(color="#888888"))

    fig.update_layout(
        plot_bgcolor='#121212',
        paper_bgcolor='#121212',
        font_color='#FFFFFF'
    )

    st.plotly_chart(fig, use_container_width=True)


def plot_temporal_heatmap(df):
    """Plot heatmap of listening activity by hour and day"""
    if df.empty or 'hour' not in df.columns or 'day_of_week' not in df.columns:
        st.info("Temporal data not available")
        return

    # Create pivot table
    day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']

    pivot = df.pivot_table(
        values='track_id',
        index='day_of_week',
        columns='hour',
        aggfunc='count',
        fill_value=0
    )

    # Reorder days
    pivot = pivot.reindex([d for d in day_order if d in pivot.index])

    fig = px.imshow(
        pivot,
        labels=dict(x="Hour of Day", y="Day of Week", color="Tracks Played"),
        title="Listening Activity Heatmap",
        color_continuous_scale='Greens',
        aspect="auto"
    )

    fig.update_layout(
        plot_bgcolor='#121212',
        paper_bgcolor='#121212',
        font_color='#FFFFFF'
    )

    st.plotly_chart(fig, use_container_width=True)


# ============================================================================
# BASIC VISUALIZATION FUNCTIONS
# ============================================================================

def plot_recent_timeline(df):
    """Plot recent listening timeline"""
    if df.empty:
        st.warning("No recent listening data available")
        return

    # Color by context if available, otherwise by artist
    color_col = 'context' if 'context' in df.columns else 'artist_name'

    fig = px.scatter(
        df,
        x='played_at',
        y='track_name',
        color=color_col,
        hover_data=['artist_name', 'album_name', 'duration_min'],
        title='Recent Listening Timeline',
        labels={
            'played_at': datetime_utils.get_axis_label('played_at'),
            'track_name': 'Track',
            color_col: color_col.replace('_', ' ').title()
        },
        height=600
    )

    fig.update_layout(
        plot_bgcolor='#121212',
        paper_bgcolor='#121212',
        font_color='#FFFFFF',
        showlegend=True
    )

    st.plotly_chart(fig, use_container_width=True)


def plot_listening_by_hour(df):
    """Plot listening distribution by hour of day"""
    if df.empty or 'hour' not in df.columns:
        st.warning("No data available")
        return

    hour_counts = df['hour'].value_counts().sort_index()

    fig = go.Figure(data=[
        go.Bar(
            x=hour_counts.index,
            y=hour_counts.values,
            marker_color='#1DB954',
            hovertemplate='Hour %{x}: %{y} tracks<extra></extra>'
        )
    ])

    fig.update_layout(
        title='Listening Activity by Hour of Day',
        xaxis_title='Hour (24h format)',
        yaxis_title='Number of Tracks',
        plot_bgcolor='#121212',
        paper_bgcolor='#121212',
        font_color='#FFFFFF',
        xaxis=dict(tickmode='linear', tick0=0, dtick=2)
    )

    st.plotly_chart(fig, use_container_width=True)


def plot_listening_by_day(df):
    """Plot listening distribution by day of week"""
    if df.empty or 'day_of_week' not in df.columns:
        st.warning("No data available")
        return

    day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    day_counts = df['day_of_week'].value_counts().reindex(day_order, fill_value=0)

    fig = go.Figure(data=[
        go.Bar(
            x=day_counts.index,
            y=day_counts.values,
            marker_color='#1DB954',
            hovertemplate='%{x}: %{y} tracks<extra></extra>'
        )
    ])

    fig.update_layout(
        title='Listening Activity by Day of Week',
        xaxis_title='Day',
        yaxis_title='Number of Tracks',
        plot_bgcolor='#121212',
        paper_bgcolor='#121212',
        font_color='#FFFFFF'
    )

    st.plotly_chart(fig, use_container_width=True)


def plot_top_artists(df):
    """Plot top artists horizontal bar chart"""
    if df.empty or 'artist_name' not in df.columns:
        st.warning("No data available")
        return

    artist_counts = df['artist_name'].value_counts().head(10)

    fig = go.Figure(data=[
        go.Bar(
            x=artist_counts.values,
            y=artist_counts.index,
            orientation='h',
            marker_color='#1DB954',
            hovertemplate='%{y}: %{x} tracks<extra></extra>'
        )
    ])

    fig.update_layout(
        title='Top 10 Artists (Recent Listening)',
        xaxis_title='Number of Tracks',
        yaxis_title='Artist',
        plot_bgcolor='#121212',
        paper_bgcolor='#121212',
        font_color='#FFFFFF',
        height=500
    )

    st.plotly_chart(fig, use_container_width=True)
