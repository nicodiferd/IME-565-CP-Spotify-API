"""
Spotify Listening Analytics Dashboard
IME 565 - Predictive Data Analytics for Engineers

A Streamlit app for personalized Spotify listening insights
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import os
from dotenv import load_dotenv

# Spotipy imports
import spotipy
from spotipy.oauth2 import SpotifyOAuth

# Load environment variables
load_dotenv()

# Page configuration
st.set_page_config(
    page_title="Spotify Analytics",
    page_icon="🎵",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for Spotify-like styling
st.markdown("""
    <style>
    .main {
        background-color: #121212;
        color: #FFFFFF;
    }
    .stButton>button {
        background-color: #1DB954;
        color: white;
        border-radius: 20px;
        border: none;
        padding: 10px 24px;
        font-weight: bold;
    }
    .stButton>button:hover {
        background-color: #1ED760;
    }
    .metric-card {
        background-color: #282828;
        padding: 20px;
        border-radius: 10px;
        margin: 10px 0;
    }
    h1, h2, h3 {
        color: #1DB954;
    }
    </style>
""", unsafe_allow_html=True)


# ============================================================================
# SPOTIFY AUTHENTICATION
# ============================================================================

def get_spotify_oauth():
    """Create SpotifyOAuth object"""
    return SpotifyOAuth(
        client_id=os.getenv('SPOTIFY_CLIENT_ID'),
        client_secret=os.getenv('SPOTIFY_CLIENT_SECRET'),
        redirect_uri=os.getenv('SPOTIFY_REDIRECT_URI'),
        scope=' '.join([
            'user-read-recently-played',
            'user-top-read',
            'playlist-read-private',
            'user-read-private',
            'user-library-read'
        ]),
        show_dialog=False,
        open_browser=False
    )


def authenticate():
    """Handle Spotify authentication flow"""

    # Initialize session state
    if 'token_info' not in st.session_state:
        st.session_state.token_info = None
    if 'auth_code' not in st.session_state:
        st.session_state.auth_code = None

    sp_oauth = get_spotify_oauth()

    # Check if we have a code in the URL (callback from Spotify)
    query_params = st.query_params

    if 'code' in query_params:
        code = query_params['code']

        # Exchange code for token (only if we haven't already)
        if code != st.session_state.get('auth_code'):
            try:
                token_info = sp_oauth.get_access_token(code, check_cache=False)
                st.session_state.token_info = token_info
                st.session_state.auth_code = code

                # Clear the URL parameters
                st.query_params.clear()
                st.rerun()

            except Exception as e:
                st.error(f"Authentication failed: {e}")
                st.session_state.token_info = None
                return None

    # Check if we have a valid token
    token_info = st.session_state.get('token_info')

    if token_info:
        # Check if token is expired and refresh if needed
        now = datetime.now().timestamp()
        is_expired = token_info.get('expires_at', 0) - now < 300  # Refresh if < 5 min left

        if is_expired:
            try:
                token_info = sp_oauth.refresh_access_token(token_info['refresh_token'])
                st.session_state.token_info = token_info
            except:
                st.session_state.token_info = None
                return None

    return token_info


def get_spotify_client(token_info):
    """Create authenticated Spotify client"""
    if not token_info:
        return None
    return spotipy.Spotify(auth=token_info['access_token'])


# ============================================================================
# DATA FETCHING FUNCTIONS
# ============================================================================

@st.cache_data(ttl=3600)
def fetch_user_profile(_sp):
    """Fetch current user profile"""
    try:
        return _sp.current_user()
    except Exception as e:
        st.error(f"Error fetching profile: {e}")
        return None


@st.cache_data(ttl=3600)
def fetch_recently_played(_sp, limit=50):
    """Fetch recently played tracks"""
    try:
        results = _sp.current_user_recently_played(limit=limit)
        return results.get('items', [])
    except Exception as e:
        st.error(f"Error fetching recently played: {e}")
        return []


@st.cache_data(ttl=3600)
def fetch_top_tracks(_sp, time_range='short_term', limit=20):
    """Fetch top tracks for a given time range"""
    try:
        results = _sp.current_user_top_tracks(time_range=time_range, limit=limit)
        return results.get('items', [])
    except Exception as e:
        st.error(f"Error fetching top tracks ({time_range}): {e}")
        return []


@st.cache_data(ttl=3600)
def fetch_top_artists(_sp, time_range='short_term', limit=20):
    """Fetch top artists for a given time range"""
    try:
        results = _sp.current_user_top_artists(time_range=time_range, limit=limit)
        return results.get('items', [])
    except Exception as e:
        st.error(f"Error fetching top artists ({time_range}): {e}")
        return []


@st.cache_data(ttl=3600)
def fetch_playlists(_sp, limit=50):
    """Fetch user playlists"""
    try:
        results = _sp.current_user_playlists(limit=limit)
        return results.get('items', [])
    except Exception as e:
        st.error(f"Error fetching playlists: {e}")
        return []


# ============================================================================
# DATA PROCESSING FUNCTIONS
# ============================================================================

def process_recent_tracks(recent_items):
    """Convert recently played items to DataFrame"""
    if not recent_items:
        return pd.DataFrame()

    data = []
    for item in recent_items:
        track = item.get('track', {})
        data.append({
            'track_id': track.get('id'),
            'track_name': track.get('name'),
            'artist_name': track.get('artists', [{}])[0].get('name'),
            'album_name': track.get('album', {}).get('name'),
            'played_at': item.get('played_at'),
            'duration_ms': track.get('duration_ms'),
            'popularity': track.get('popularity'),
            'explicit': track.get('explicit'),
            'preview_url': track.get('preview_url')
        })

    df = pd.DataFrame(data)
    df['played_at'] = pd.to_datetime(df['played_at'])
    df['duration_min'] = df['duration_ms'] / 60000
    df['hour'] = df['played_at'].dt.hour
    df['day_of_week'] = df['played_at'].dt.day_name()
    df['date'] = df['played_at'].dt.date

    return df


def process_top_tracks(top_tracks):
    """Convert top tracks to DataFrame"""
    if not top_tracks:
        return pd.DataFrame()

    data = []
    for track in top_tracks:
        data.append({
            'track_name': track.get('name'),
            'artist_name': track.get('artists', [{}])[0].get('name'),
            'album_name': track.get('album', {}).get('name'),
            'popularity': track.get('popularity'),
            'duration_ms': track.get('duration_ms'),
            'preview_url': track.get('preview_url')
        })

    return pd.DataFrame(data)


# ============================================================================
# VISUALIZATION FUNCTIONS
# ============================================================================

def plot_recent_timeline(df):
    """Plot recent listening timeline"""
    if df.empty:
        st.warning("No recent listening data available")
        return

    fig = px.scatter(
        df,
        x='played_at',
        y='track_name',
        color='artist_name',
        hover_data=['album_name', 'duration_min'],
        title='Recent Listening Timeline',
        labels={'played_at': 'Time', 'track_name': 'Track'},
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
    if df.empty:
        st.warning("No data available")
        return

    hour_counts = df['hour'].value_counts().sort_index()

    fig = go.Figure(data=[
        go.Bar(
            x=hour_counts.index,
            y=hour_counts.values,
            marker_color='#1DB954'
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
    if df.empty:
        st.warning("No data available")
        return

    # Order days properly
    day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    day_counts = df['day_of_week'].value_counts().reindex(day_order, fill_value=0)

    fig = go.Figure(data=[
        go.Bar(
            x=day_counts.index,
            y=day_counts.values,
            marker_color='#1DB954'
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
    if df.empty:
        st.warning("No data available")
        return

    # Get top 10 artists
    artist_counts = df['artist_name'].value_counts().head(10)

    fig = go.Figure(data=[
        go.Bar(
            x=artist_counts.values,
            y=artist_counts.index,
            orientation='h',
            marker_color='#1DB954'
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


# ============================================================================
# PAGE FUNCTIONS
# ============================================================================

def show_dashboard_page(sp):
    """Dashboard overview page"""
    st.header("Dashboard")

    # Fetch data
    recent_items = fetch_recently_played(sp, limit=50)
    recent_df = process_recent_tracks(recent_items)

    if recent_df.empty:
        st.warning("No recent listening data available. Try playing some music on Spotify!")
        return

    # KPI metrics
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Total Tracks", len(recent_df))

    with col2:
        unique_artists = recent_df['artist_name'].nunique()
        st.metric("Unique Artists", unique_artists)

    with col3:
        total_minutes = recent_df['duration_min'].sum()
        st.metric("Total Listening Time", f"{total_minutes:.0f} min")

    with col4:
        avg_popularity = recent_df['popularity'].mean()
        st.metric("Avg Popularity", f"{avg_popularity:.0f}")

    st.markdown("---")

    # Visualizations
    col_left, col_right = st.columns(2)

    with col_left:
        plot_listening_by_hour(recent_df)

    with col_right:
        plot_listening_by_day(recent_df)

    st.markdown("---")

    plot_top_artists(recent_df)


def show_recent_listening_page(sp):
    """Recent listening detailed page"""
    st.header("Recent Listening")

    # Fetch data
    recent_items = fetch_recently_played(sp, limit=50)
    recent_df = process_recent_tracks(recent_items)

    if recent_df.empty:
        st.warning("No recent listening data available.")
        return

    # Timeline visualization
    plot_recent_timeline(recent_df)

    st.markdown("---")

    # Data table
    st.subheader("Track List")

    # Format for display
    display_df = recent_df[[
        'played_at', 'track_name', 'artist_name', 'album_name', 'duration_min', 'popularity'
    ]].copy()

    display_df['played_at'] = display_df['played_at'].dt.strftime('%Y-%m-%d %H:%M')
    display_df['duration_min'] = display_df['duration_min'].round(2)

    display_df.columns = ['Played At', 'Track', 'Artist', 'Album', 'Duration (min)', 'Popularity']

    st.dataframe(display_df, use_container_width=True, height=400)

    # Download button
    csv = display_df.to_csv(index=False)
    st.download_button(
        label="📥 Download as CSV",
        data=csv,
        file_name=f"spotify_recent_listening_{datetime.now().strftime('%Y%m%d')}.csv",
        mime="text/csv"
    )


def show_top_tracks_page(sp):
    """Top tracks page with time range comparison"""
    st.header("Top Tracks")

    # Time range selector
    time_range_map = {
        'Last 4 Weeks': 'short_term',
        'Last 6 Months': 'medium_term',
        'All Time': 'long_term'
    }

    selected_range = st.selectbox("Select Time Range", list(time_range_map.keys()))
    time_range = time_range_map[selected_range]

    # Fetch data
    top_tracks = fetch_top_tracks(sp, time_range=time_range, limit=20)
    top_df = process_top_tracks(top_tracks)

    if top_df.empty:
        st.warning("No top tracks data available for this time range.")
        return

    # Display as numbered list
    st.subheader(f"Your Top 20 Tracks ({selected_range})")

    for idx, row in top_df.iterrows():
        col1, col2 = st.columns([1, 10])

        with col1:
            st.markdown(f"### {idx + 1}")

        with col2:
            st.markdown(f"**{row['track_name']}**")
            st.caption(f"{row['artist_name']} • {row['album_name']} • Popularity: {row['popularity']}")

        st.markdown("---")


def show_playlists_page(sp):
    """Playlists overview page"""
    st.header("Your Playlists")

    # Fetch data
    playlists = fetch_playlists(sp, limit=50)

    if not playlists:
        st.warning("No playlists found.")
        return

    # Summary metrics
    total_playlists = len(playlists)
    total_tracks = sum(p.get('tracks', {}).get('total', 0) for p in playlists)

    col1, col2 = st.columns(2)
    with col1:
        st.metric("Total Playlists", total_playlists)
    with col2:
        st.metric("Total Tracks", total_tracks)

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


def show_welcome_page():
    """Welcome page for non-authenticated users"""
    st.markdown("## Welcome! 👋")
    st.markdown("""
    This dashboard provides deeper insights into your Spotify listening habits than
    the annual Wrapped feature.

    ### Features:
    - **Recent Listening Timeline**: See your last 50 played tracks with timestamps
    - **Temporal Patterns**: Discover when you listen most (by hour and day)
    - **Top Tracks & Artists**: View your favorites across different time periods
    - **Playlist Overview**: Analyze your playlists
    - **Artist Diversity**: See how varied your music taste is

    ### Getting Started:
    1. Click "Connect Spotify" in the sidebar
    2. Log in with your Spotify account
    3. Authorize this app to read your listening data
    4. Explore your personalized analytics!

    ---
    **Note**: This app is in Development Mode and can only be used by allowlisted users.
    """)


# ============================================================================
# MAIN APP
# ============================================================================

def main():
    """Main application logic"""

    # Header
    st.title("🎵 Spotify Listening Analytics")
    st.markdown("*Deeper insights into your music habits*")

    # Authenticate
    token_info = authenticate()

    # Sidebar
    with st.sidebar:
        st.image("https://storage.googleapis.com/pr-newsroom-wp/1/2018/11/Spotify_Logo_RGB_Green.png", width=150)
        st.markdown("---")

        # Authentication status
        if token_info:
            # User is authenticated
            sp = get_spotify_client(token_info)

            if sp:
                profile = fetch_user_profile(sp)

                if profile:
                    st.success("✓ Connected to Spotify")
                    st.write(f"**{profile.get('display_name')}**")
                    st.write(f"User ID: `{profile.get('id')}`")
                    st.write(f"Account: {profile.get('product', 'free').upper()}")

                    # Logout button
                    if st.button("Disconnect"):
                        st.session_state.token_info = None
                        st.session_state.auth_code = None
                        st.rerun()

                    st.markdown("---")

                    # Navigation
                    st.subheader("Navigation")
                    page = st.radio(
                        "Select Page",
                        ["Dashboard", "Recent Listening", "Top Tracks", "Playlists"],
                        label_visibility="collapsed"
                    )

                    st.markdown("---")

                    # Data refresh
                    if st.button("🔄 Refresh Data"):
                        st.cache_data.clear()
                        st.rerun()
                else:
                    st.error("Could not load user profile")
                    page = "Welcome"
                    sp = None
            else:
                st.error("Could not create Spotify client")
                page = "Welcome"
                sp = None
        else:
            # User not authenticated
            st.warning("Not connected to Spotify")
            st.write("Click below to connect your Spotify account and view your listening analytics.")

            # Login button
            sp_oauth = get_spotify_oauth()
            auth_url = sp_oauth.get_authorize_url()

            # Use markdown link instead of link_button for better compatibility
            st.markdown(f"""
                <a href="{auth_url}" target="_self">
                    <button style="
                        background-color: #1DB954;
                        color: white;
                        border-radius: 20px;
                        border: none;
                        padding: 10px 24px;
                        font-weight: bold;
                        cursor: pointer;
                        width: 100%;
                        font-size: 16px;
                    ">
                        🎵 Connect Spotify
                    </button>
                </a>
            """, unsafe_allow_html=True)

            st.markdown("---")
            st.caption("This app requires:")
            st.caption("• Spotify account (Free or Premium)")
            st.caption("• Permission to read listening history")

            page = "Welcome"
            sp = None

    # Main content area
    if not token_info or not sp:
        show_welcome_page()
    else:
        # User is authenticated - show selected page
        if page == "Dashboard":
            show_dashboard_page(sp)
        elif page == "Recent Listening":
            show_recent_listening_page(sp)
        elif page == "Top Tracks":
            show_top_tracks_page(sp)
        elif page == "Playlists":
            show_playlists_page(sp)


# ============================================================================
# RUN APP
# ============================================================================

if __name__ == "__main__":
    main()
