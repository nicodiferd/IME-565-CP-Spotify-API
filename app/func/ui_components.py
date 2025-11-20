"""
UI Components and Styling
Reusable UI components, CSS styling, and page configuration
"""

import streamlit as st


# ============================================================================
# PAGE CONFIGURATION
# ============================================================================

def apply_page_config():
    """Apply Streamlit page configuration"""
    st.set_page_config(
        page_title="Spotify Analytics",
        page_icon="🎵",
        layout="wide",
        initial_sidebar_state="expanded"
    )


# ============================================================================
# CUSTOM STYLING
# ============================================================================

def get_custom_css():
    """Return custom CSS for Spotify-like styling"""
    return """
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
    """
