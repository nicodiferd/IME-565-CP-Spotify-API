"""
Spotify Listening Analytics Dashboard
IME 565 - Predictive Data Analytics for Engineers

A Streamlit app for personalized Spotify listening insights with advanced analytics
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import os
import sys
from dotenv import load_dotenv

# Spotipy imports
import spotipy
from spotipy.oauth2 import SpotifyOAuth

# Import src modules for feature engineering
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
try:
    from src.feature_engineering import create_composite_features, classify_context
except ImportError:
    # Fallback if src modules not available
    create_composite_features = None
    classify_context = None

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
    .stTextInput>div>div>input {
        background-color: #282828;
        color: #FFFFFF;
    }
    .config-section {
        background-color: #282828;
        padding: 15px;
        border-radius: 10px;
        margin: 10px 0;
    }
    </style>
""", unsafe_allow_html=True)


# ============================================================================
# SESSION STATE INITIALIZATION
# ============================================================================

def initialize_session_state():
    """Initialize all session state variables"""
    if 'token_info' not in st.session_state:
        st.session_state.token_info = None
    if 'auth_code' not in st.session_state:
        st.session_state.auth_code = None
    if 'credential_mode' not in st.session_state:
        st.session_state.credential_mode = None  # 'env' or 'manual'
    if 'manual_client_id' not in st.session_state:
        st.session_state.manual_client_id = ""
    if 'manual_client_secret' not in st.session_state:
        st.session_state.manual_client_secret = ""
    if 'manual_redirect_uri' not in st.session_state:
        st.session_state.manual_redirect_uri = "http://127.0.0.1:8501/"
    if 'credentials_configured' not in st.session_state:
        st.session_state.credentials_configured = False
    if 'auth_error' not in st.session_state:
        st.session_state.auth_error = None
    if 'is_connecting' not in st.session_state:
        st.session_state.is_connecting = False


# ============================================================================
# CREDENTIAL MANAGEMENT
# ============================================================================

def get_credentials():
    """Get credentials based on selected mode"""
    if st.session_state.credential_mode == 'env':
        return {
            'client_id': os.getenv('SPOTIFY_CLIENT_ID'),
            'client_secret': os.getenv('SPOTIFY_CLIENT_SECRET'),
            'redirect_uri': os.getenv('SPOTIFY_REDIRECT_URI', 'http://127.0.0.1:8501/')
        }
    elif st.session_state.credential_mode == 'manual':
        return {
            'client_id': st.session_state.manual_client_id,
            'client_secret': st.session_state.manual_client_secret,
            'redirect_uri': st.session_state.manual_redirect_uri
        }
    return None


def validate_credentials(creds):
    """Validate that credentials are not empty"""
    if not creds:
        return False
    return all([
        creds.get('client_id'),
        creds.get('client_secret'),
        creds.get('redirect_uri')
    ])


def show_credential_configuration():
    """Show credential configuration UI"""
    st.sidebar.markdown("### 🔐 Configuration")

    # Mode selection buttons
    col1, col2 = st.sidebar.columns(2)

    with col1:
        if st.button("📁 Use .env", use_container_width=True):
            st.session_state.credential_mode = 'env'
            creds = get_credentials()
            if validate_credentials(creds):
                st.session_state.credentials_configured = True
                st.rerun()
            else:
                st.error("⚠️ .env file not found or incomplete")

    with col2:
        if st.button("⌨️ Manual Input", use_container_width=True):
            st.session_state.credential_mode = 'manual'
            st.session_state.credentials_configured = False

    # Show manual input fields if manual mode selected
    if st.session_state.credential_mode == 'manual':
        st.sidebar.markdown("---")
        st.sidebar.markdown("**Enter Spotify API Credentials:**")

        st.session_state.manual_client_id = st.sidebar.text_input(
            "Client ID",
            value=st.session_state.manual_client_id,
            type="password",
            help="From Spotify Developer Dashboard"
        )

        st.session_state.manual_client_secret = st.sidebar.text_input(
            "Client Secret",
            value=st.session_state.manual_client_secret,
            type="password",
            help="From Spotify Developer Dashboard"
        )

        st.session_state.manual_redirect_uri = st.sidebar.text_input(
            "Redirect URI",
            value=st.session_state.manual_redirect_uri,
            help="Must match Spotify app settings"
        )

        if st.sidebar.button("✓ Save Credentials", use_container_width=True):
            creds = get_credentials()
            if validate_credentials(creds):
                st.session_state.credentials_configured = True
                st.sidebar.success("✓ Credentials saved!")
                st.rerun()
            else:
                st.sidebar.error("⚠️ All fields are required")

    elif st.session_state.credential_mode == 'env':
        creds = get_credentials()
        if validate_credentials(creds):
            st.sidebar.success("✓ Using .env credentials")
        else:
            st.sidebar.error("⚠️ .env credentials incomplete")

    st.sidebar.markdown("---")

    # Show help
    with st.sidebar.expander("ℹ️ How to get credentials"):
        st.markdown("""
        1. Go to [Spotify Developer Dashboard](https://developer.spotify.com/dashboard)
        2. Create a new app (or use existing)
        3. Click "Edit Settings"
        4. Add this **exact** Redirect URI:
           ```
           http://127.0.0.1:8501/
           ```
        5. Copy Client ID and Client Secret
        6. Paste them above

        ⚠️ **Important**: The Redirect URI must match exactly (including the trailing slash)!
        """)


# ============================================================================
# SPOTIFY AUTHENTICATION
# ============================================================================

def get_spotify_oauth():
    """Create SpotifyOAuth object with dynamic credentials"""
    creds = get_credentials()

    if not validate_credentials(creds):
        return None

    return SpotifyOAuth(
        client_id=creds['client_id'],
        client_secret=creds['client_secret'],
        redirect_uri=creds['redirect_uri'],
        scope=' '.join([
            'user-read-recently-played',
            'user-top-read',
            'playlist-read-private',
            'user-read-private',
            'user-library-read'
        ]),
        show_dialog=True,  # Always show dialog for clarity
        open_browser=False,
        cache_handler=None  # Disable file caching, use session state only
    )


def authenticate():
    """Handle Spotify authentication flow with improved error handling"""
    sp_oauth = get_spotify_oauth()

    if not sp_oauth:
        st.session_state.auth_error = "OAuth configuration failed. Check your credentials."
        return None

    # Check if we have a code in the URL (callback from Spotify)
    query_params = st.query_params

    # Check for error in OAuth callback
    if 'error' in query_params:
        error = query_params.get('error', 'unknown_error')
        st.session_state.auth_error = f"Spotify authorization failed: {error}"
        st.session_state.is_connecting = False
        st.query_params.clear()
        return None

    if 'code' in query_params:
        code = query_params['code']

        # Exchange code for token (only if we haven't already)
        if code != st.session_state.get('auth_code'):
            st.session_state.is_connecting = True
            try:
                with st.spinner("🔐 Connecting to Spotify..."):
                    token_info = sp_oauth.get_access_token(code, check_cache=False)
                    st.session_state.token_info = token_info
                    st.session_state.auth_code = code
                    st.session_state.auth_error = None
                    st.session_state.is_connecting = False

                # Clear the URL parameters
                st.query_params.clear()
                st.rerun()

            except Exception as e:
                error_msg = str(e)
                if "invalid_client" in error_msg.lower():
                    st.session_state.auth_error = "Invalid Client ID or Client Secret. Please check your credentials."
                elif "redirect_uri" in error_msg.lower():
                    st.session_state.auth_error = f"Redirect URI mismatch. Make sure '{st.session_state.manual_redirect_uri}' is added to your Spotify app settings."
                else:
                    st.session_state.auth_error = f"Authentication failed: {error_msg}"

                st.session_state.token_info = None
                st.session_state.is_connecting = False
                st.query_params.clear()
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
                st.session_state.auth_error = None
            except Exception as e:
                st.session_state.auth_error = f"Token refresh failed: {e}"
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


@st.cache_data(ttl=1800)
def fetch_recently_played(_sp, limit=50):
    """Fetch recently played tracks"""
    try:
        results = _sp.current_user_recently_played(limit=limit)
        return results.get('items', [])
    except Exception as e:
        st.error(f"Error fetching recently played: {e}")
        return []


@st.cache_data(ttl=1800)
def fetch_top_tracks(_sp, time_range='short_term', limit=20):
    """Fetch top tracks for a given time range"""
    try:
        results = _sp.current_user_top_tracks(time_range=time_range, limit=limit)
        return results.get('items', [])
    except Exception as e:
        st.error(f"Error fetching top tracks ({time_range}): {e}")
        return []


@st.cache_data(ttl=1800)
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


@st.cache_data(ttl=1800)
def fetch_audio_features(_sp, track_ids):
    """Fetch audio features for multiple tracks"""
    try:
        if not track_ids:
            return []

        # Spotify allows max 100 tracks per request
        all_features = []
        for i in range(0, len(track_ids), 100):
            batch = track_ids[i:i+100]
            features = _sp.audio_features(batch)
            all_features.extend([f for f in features if f is not None])

        return all_features
    except Exception as e:
        st.warning(f"Could not fetch audio features: {e}")
        return []


# ============================================================================
# DATA PROCESSING FUNCTIONS
# ============================================================================

def process_recent_tracks(recent_items, sp=None):
    """Convert recently played items to DataFrame with audio features"""
    if not recent_items:
        return pd.DataFrame()

    # Basic track data
    data = []
    track_ids = []

    for item in recent_items:
        track = item.get('track', {})
        track_id = track.get('id')

        if track_id:
            track_ids.append(track_id)
            data.append({
                'track_id': track_id,
                'track_name': track.get('name'),
                'artist_name': track.get('artists', [{}])[0].get('name'),
                'album_name': track.get('album', {}).get('name'),
                'played_at': item.get('played_at'),
                'duration_ms': track.get('duration_ms'),
                'popularity': track.get('popularity'),
                'explicit': track.get('explicit'),
                'preview_url': track.get('preview_url')
            })

    if not data:
        return pd.DataFrame()

    df = pd.DataFrame(data)

    # Convert timestamps
    df['played_at'] = pd.to_datetime(df['played_at'])
    df['duration_min'] = df['duration_ms'] / 60000
    df['hour'] = df['played_at'].dt.hour
    df['day_of_week'] = df['played_at'].dt.day_name()
    df['date'] = df['played_at'].dt.date
    df['is_weekend'] = df['played_at'].dt.dayofweek >= 5

    # Fetch audio features if Spotify client provided
    if sp and track_ids:
        with st.spinner("Fetching audio features..."):
            audio_features = fetch_audio_features(sp, track_ids)

            if audio_features:
                # Create audio features dataframe
                af_df = pd.DataFrame(audio_features)
                af_df.rename(columns={'id': 'track_id'}, inplace=True)

                # Merge with main dataframe
                df = df.merge(af_df, on='track_id', how='left')

                # Add composite features if module available
                if create_composite_features and 'danceability' in df.columns:
                    try:
                        df = create_composite_features(df)
                    except Exception as e:
                        st.warning(f"Could not create composite features: {e}")

                # Add context classification if module available
                if classify_context and 'energy' in df.columns:
                    try:
                        df = classify_context(df)
                    except Exception as e:
                        st.warning(f"Could not classify context: {e}")

    return df


def process_top_tracks(top_tracks, sp=None):
    """Convert top tracks to DataFrame with audio features"""
    if not top_tracks:
        return pd.DataFrame()

    data = []
    track_ids = []

    for track in top_tracks:
        track_id = track.get('id')
        if track_id:
            track_ids.append(track_id)
            data.append({
                'track_id': track_id,
                'track_name': track.get('name'),
                'artist_name': track.get('artists', [{}])[0].get('name'),
                'album_name': track.get('album', {}).get('name'),
                'popularity': track.get('popularity'),
                'duration_ms': track.get('duration_ms'),
                'duration_min': track.get('duration_ms', 0) / 60000,
                'preview_url': track.get('preview_url')
            })

    if not data:
        return pd.DataFrame()

    df = pd.DataFrame(data)

    # Fetch audio features
    if sp and track_ids:
        audio_features = fetch_audio_features(sp, track_ids)

        if audio_features:
            af_df = pd.DataFrame(audio_features)
            af_df.rename(columns={'id': 'track_id'}, inplace=True)
            df = df.merge(af_df, on='track_id', how='left')

            # Add composite features
            if create_composite_features and 'danceability' in df.columns:
                try:
                    df = create_composite_features(df)
                except:
                    pass

            # Add context
            if classify_context and 'energy' in df.columns:
                try:
                    df = classify_context(df)
                except:
                    pass

    return df


def calculate_diversity_score(df, column='artist_name'):
    """Calculate diversity using Shannon entropy"""
    if df.empty or column not in df.columns:
        return 0

    value_counts = df[column].value_counts()
    proportions = value_counts / len(df)
    entropy = -np.sum(proportions * np.log2(proportions))

    # Normalize to 0-100 scale
    max_entropy = np.log2(len(value_counts))
    if max_entropy == 0:
        return 0

    return (entropy / max_entropy) * 100


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
# ORIGINAL VISUALIZATION FUNCTIONS (ENHANCED)
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
        labels={'played_at': 'Time', 'track_name': 'Track', color_col: color_col.replace('_', ' ').title()},
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


# ============================================================================
# PAGE FUNCTIONS
# ============================================================================

def show_dashboard_page(sp):
    """Enhanced dashboard overview page"""
    st.header("📊 Dashboard")

    # Fetch data
    with st.spinner("Loading your listening data..."):
        recent_items = fetch_recently_played(sp, limit=50)
        recent_df = process_recent_tracks(recent_items, sp)

    if recent_df.empty:
        st.warning("No recent listening data available. Try playing some music on Spotify!")
        return

    # KPI metrics row 1
    st.subheader("Overview")
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Total Tracks", len(recent_df))

    with col2:
        unique_artists = recent_df['artist_name'].nunique()
        st.metric("Unique Artists", unique_artists)

    with col3:
        total_minutes = recent_df['duration_min'].sum()
        st.metric("Total Listening", f"{total_minutes:.0f} min")

    with col4:
        avg_popularity = recent_df['popularity'].mean()
        st.metric("Avg Popularity", f"{avg_popularity:.0f}")

    # KPI metrics row 2 (advanced)
    if 'mood_score' in recent_df.columns:
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            avg_mood = recent_df['mood_score'].mean()
            st.metric("Avg Mood Score", f"{avg_mood:.2f}")

        with col2:
            avg_energy = recent_df['energy'].mean()
            st.metric("Avg Energy", f"{avg_energy:.2f}")

        with col3:
            diversity = calculate_diversity_score(recent_df, 'artist_name')
            st.metric("Artist Diversity", f"{diversity:.0f}%")

        with col4:
            if 'context' in recent_df.columns:
                top_context = recent_df['context'].mode()[0]
                st.metric("Top Context", top_context.title())

    st.markdown("---")

    # Temporal patterns
    st.subheader("⏰ Temporal Patterns")
    col_left, col_right = st.columns(2)

    with col_left:
        plot_listening_by_hour(recent_df)

    with col_right:
        plot_listening_by_day(recent_df)

    # Heatmap
    if 'hour' in recent_df.columns and 'day_of_week' in recent_df.columns:
        plot_temporal_heatmap(recent_df)

    st.markdown("---")

    # Artist analysis
    st.subheader("🎤 Artist Analysis")
    plot_top_artists(recent_df)


def show_analytics_page(sp):
    """Advanced analytics page"""
    st.header("📈 Advanced Analytics")

    # Fetch data
    with st.spinner("Analyzing your music..."):
        recent_items = fetch_recently_played(sp, limit=50)
        recent_df = process_recent_tracks(recent_items, sp)

    if recent_df.empty:
        st.warning("No data available for analysis")
        return

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


def show_recent_listening_page(sp):
    """Recent listening detailed page"""
    st.header("🕒 Recent Listening")

    # Fetch data
    recent_items = fetch_recently_played(sp, limit=50)
    recent_df = process_recent_tracks(recent_items, sp)

    if recent_df.empty:
        st.warning("No recent listening data available.")
        return

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


def show_top_tracks_page(sp):
    """Enhanced top tracks page with time range comparison"""
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
        return

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


def show_playlists_page(sp):
    """Playlists overview page"""
    st.header("🎵 Your Playlists")

    # Fetch data
    playlists = fetch_playlists(sp, limit=50)

    if not playlists:
        st.warning("No playlists found.")
        return

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


def show_welcome_page():
    """Welcome page for non-authenticated users"""
    st.markdown("## Welcome to Spotify Analytics! 👋")
    st.markdown("""
    This advanced dashboard provides deeper insights into your Spotify listening habits
    than the annual Wrapped feature.

    ### 🎯 Features:

    #### 📊 Dashboard
    - Key metrics: tracks played, unique artists, listening time
    - Temporal patterns: hour-by-hour and day-by-day analysis
    - Activity heatmap showing when you listen most

    #### 📈 Advanced Analytics
    - **Audio Feature Profile**: See your taste across danceability, energy, valence, etc.
    - **Mood Analysis**: Understand your emotional music preferences
    - **Context Classification**: Workout, focus, party, relaxation patterns
    - **Energy-Valence Quadrants**: Visualize your music mood distribution

    #### 🕒 Recent Listening
    - Detailed timeline of your last 50 tracks
    - Full track information with audio features
    - Export data as CSV for further analysis

    #### 🏆 Top Tracks
    - Your favorites across different time periods
    - Audio profile of your top tracks
    - Context classification for each track

    #### 🎵 Playlists
    - Overview of all your playlists
    - Track counts and metadata
    - Quick access to open in Spotify

    ### 🚀 Getting Started:

    1. **Configure Credentials** in the sidebar (Use .env or Manual Input)
    2. **Add Redirect URI** to your Spotify app: `http://127.0.0.1:8501/`
    3. **Click "Connect Spotify"** to authorize the app
    4. **Explore your personalized analytics!**

    ---

    ### 🔧 Troubleshooting:

    **"Page not found" or "Connection failed"**
    - Ensure Redirect URI is **exactly**: `http://127.0.0.1:8501/`
    - Include the trailing slash `/` - it's important!
    - Check it's added in Spotify Developer Dashboard → Edit Settings
    - Verify Client ID and Secret are correct

    **"Invalid Client ID or Secret"**
    - Double-check credentials from Spotify Dashboard
    - Make sure there are no extra spaces
    - Try regenerating the Client Secret

    **"Redirect URI mismatch"**
    - The URI in your app must match Spotify settings exactly
    - Use `127.0.0.1` NOT `localhost` (they're different)
    - Include the port number `:8501` and trailing slash `/`
    - Format: `http://127.0.0.1:8501/`

    ---

    ### 🔒 Privacy & Security:
    - This app only reads your listening data
    - No data is stored or shared
    - All processing happens in your browser session
    - You can disconnect at any time

    ---

    **Note**: This app is in Development Mode and can only be used by allowlisted users.
    To add your Spotify account, go to the [Spotify Developer Dashboard](https://developer.spotify.com/dashboard).
    """)


# ============================================================================
# MAIN APP
# ============================================================================

def main():
    """Main application logic"""

    # Initialize session state
    initialize_session_state()

    # Header
    st.title("🎵 Spotify Listening Analytics")
    st.markdown("*Advanced insights into your music habits powered by ML*")

    # Sidebar
    with st.sidebar:
        st.image("https://storage.googleapis.com/pr-newsroom-wp/1/2018/11/Spotify_Logo_RGB_Green.png", width=150)
        st.markdown("---")

        # Show credential configuration if not authenticated
        if not st.session_state.token_info:
            show_credential_configuration()

        # Authentication status
        if st.session_state.credentials_configured:
            # Authenticate
            token_info = authenticate()

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
                        if st.button("🚪 Disconnect", use_container_width=True):
                            st.session_state.token_info = None
                            st.session_state.auth_code = None
                            st.session_state.credentials_configured = False
                            st.session_state.credential_mode = None
                            st.rerun()

                        st.markdown("---")

                        # Navigation
                        st.subheader("📍 Navigation")
                        page = st.radio(
                            "Select Page",
                            ["Dashboard", "Advanced Analytics", "Recent Listening", "Top Tracks", "Playlists"],
                            label_visibility="collapsed"
                        )

                        st.markdown("---")

                        # Data refresh
                        if st.button("🔄 Refresh Data", use_container_width=True):
                            st.cache_data.clear()
                            st.rerun()

                        st.caption("Last updated: " + datetime.now().strftime("%H:%M:%S"))
                    else:
                        st.error("Could not load user profile")
                        page = "Welcome"
                        sp = None
                else:
                    st.error("Could not create Spotify client")
                    page = "Welcome"
                    sp = None
            else:
                # Not authenticated but credentials configured - show connect button

                # Display any authentication errors
                if st.session_state.auth_error:
                    st.error(f"⚠️ {st.session_state.auth_error}")

                    # Reset credentials button
                    if st.button("🔄 Reset Credentials", use_container_width=True):
                        st.session_state.credentials_configured = False
                        st.session_state.credential_mode = None
                        st.session_state.auth_error = None
                        st.rerun()

                # Show connecting state
                elif st.session_state.is_connecting:
                    st.info("🔐 Connecting to Spotify...")
                    st.spinner("Please wait...")

                else:
                    st.info("Ready to connect!")

                    sp_oauth = get_spotify_oauth()
                    if sp_oauth:
                        auth_url = sp_oauth.get_authorize_url()

                        st.markdown(f"""
                            <a href="{auth_url}" target="_self">
                                <button style="
                                    background-color: #1DB954;
                                    color: white;
                                    border-radius: 20px;
                                    border: none;
                                    padding: 12px 24px;
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

                        st.markdown("---")
                        st.caption(f"📍 Redirect URI: `{get_credentials().get('redirect_uri', 'N/A')}`")

                page = "Welcome"
                sp = None
        else:
            # Credentials not configured
            st.info("👆 Configure credentials above to get started")
            page = "Welcome"
            sp = None

    # Main content area
    if not st.session_state.token_info or not st.session_state.credentials_configured:
        show_welcome_page()
    else:
        # User is authenticated - show selected page
        if page == "Dashboard":
            show_dashboard_page(sp)
        elif page == "Advanced Analytics":
            show_analytics_page(sp)
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
