"""
Data Sync Page
Mandatory data collection onboarding flow after authentication
"""

import streamlit as st
import sys
import os
import json
import time
import random
from pathlib import Path

# Add parent directory to path to import from func
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from func.ui_components import apply_page_config, get_custom_css
from func.data_collection import collect_snapshot_with_progress

# Apply page configuration
apply_page_config()
st.markdown(get_custom_css(), unsafe_allow_html=True)

# ============================================================================
# DATA SYNC PAGE
# ============================================================================

# Check if user is authenticated
if 'token_info' not in st.session_state or st.session_state.token_info is None:
    st.error("❌ Authentication required. Redirecting to home page...")
    time.sleep(2)
    st.switch_page("Home.py")
    st.stop()

# Load Spotify facts
facts_path = Path(__file__).parent.parent / "data" / "spotify_facts.json"
try:
    with open(facts_path, 'r') as f:
        spotify_facts = json.load(f)
except Exception as e:
    spotify_facts = [
        "Syncing your Spotify data...",
        "This will take about 60-90 seconds...",
        "We're analyzing your music taste...",
        "Almost there..."
    ]

# Initialize sync state
if 'sync_in_progress' not in st.session_state:
    st.session_state.sync_in_progress = False
if 'sync_error' not in st.session_state:
    st.session_state.sync_error = None
if 'current_fact_index' not in st.session_state:
    st.session_state.current_fact_index = random.randint(0, len(spotify_facts) - 1)

# ============================================================================
# HEADER
# ============================================================================

st.markdown("""
<div style='text-align: center; padding: 2rem 0;'>
    <h1 style='font-size: 3rem; margin-bottom: 0.5rem;'>🎵</h1>
    <h2 style='margin-top: 0;'>Setting Up Your Music Analytics</h2>
    <p style='color: #b3b3b3; font-size: 1.1rem;'>
        We're collecting your listening data to create personalized insights.
        <br>This will take about 45-60 seconds.
        <br><span style='color: #FFA500; font-size: 0.9rem;'>⚠️ Development Mode: Slower to prevent rate limits</span>
    </p>
</div>
""", unsafe_allow_html=True)

st.markdown("---")

# ============================================================================
# SYNC LOGIC
# ============================================================================

def run_sync():
    """Execute the data sync with progress updates"""
    st.session_state.sync_in_progress = True
    st.session_state.sync_error = None

    # Get Spotify client from session
    from func.auth import get_spotify_client
    sp = get_spotify_client()

    if not sp:
        st.session_state.sync_error = "Failed to initialize Spotify client. Please try again."
        st.session_state.sync_in_progress = False
        return

    # Create progress containers
    progress_bar = st.progress(0)
    status_text = st.empty()
    fact_container = st.empty()
    stage_emoji = st.empty()

    # Define stages
    stages = [
        ("🎵 Fetching recent tracks", 0, 20),
        ("🎸 Loading top tracks", 20, 45),
        ("🎤 Analyzing top artists", 45, 70),
        ("📊 Computing metrics", 70, 85),
        ("☁️ Saving to storage", 85, 100)
    ]

    current_stage_idx = 0
    last_fact_time = time.time()
    fact_index = st.session_state.current_fact_index

    try:
        # Call the data collection function with progress tracking
        for progress_data in collect_snapshot_with_progress(sp):
            # Extract progress info
            percentage = progress_data.get('percentage', 0)
            stage_name = progress_data.get('stage', 'Processing...')

            # Update progress bar
            progress_bar.progress(percentage / 100)

            # Update stage based on percentage
            for idx, (emoji_stage, start, end) in enumerate(stages):
                if start <= percentage < end:
                    if idx != current_stage_idx:
                        current_stage_idx = idx
                        stage_emoji.markdown(f"<h2 style='text-align: center;'>{emoji_stage}</h2>", unsafe_allow_html=True)
                    break

            # Update status text
            status_text.markdown(f"<p style='text-align: center; font-size: 1.2rem;'>{stage_name}</p>", unsafe_allow_html=True)

            # Rotate facts every 4 seconds
            if time.time() - last_fact_time >= 4:
                fact_index = (fact_index + 1) % len(spotify_facts)
                st.session_state.current_fact_index = fact_index
                last_fact_time = time.time()

            # Display current fact
            fact_container.markdown(f"""
            <div style='background-color: #282828; padding: 1.5rem; border-radius: 10px; margin: 2rem 0; text-align: center;'>
                <p style='color: #1DB954; font-weight: bold; margin-bottom: 0.5rem;'>DID YOU KNOW?</p>
                <p style='font-size: 1.1rem; line-height: 1.6;'>{spotify_facts[fact_index]}</p>
            </div>
            """, unsafe_allow_html=True)

        # Success!
        progress_bar.progress(100)
        status_text.markdown("<p style='text-align: center; font-size: 1.2rem; color: #1DB954;'>✅ Sync complete!</p>", unsafe_allow_html=True)
        stage_emoji.markdown("<h2 style='text-align: center;'>🎉</h2>", unsafe_allow_html=True)

        time.sleep(1.5)

        # Mark sync as complete and redirect
        st.session_state.sync_completed_this_session = True
        st.switch_page("pages/1_Dashboard.py")

    except Exception as e:
        st.session_state.sync_error = str(e)
        st.session_state.sync_in_progress = False

# ============================================================================
# ERROR HANDLING
# ============================================================================

if st.session_state.sync_error:
    st.error(f"❌ Sync failed: {st.session_state.sync_error}")
    st.markdown("""
    <div style='background-color: #3a0f0f; padding: 1rem; border-radius: 5px; margin: 1rem 0;'>
        <p><strong>Possible causes:</strong></p>
        <ul>
            <li>Network connectivity issues</li>
            <li>Spotify API rate limiting</li>
            <li>Cloud storage unavailable</li>
            <li>Invalid authentication token</li>
        </ul>
        <p>Please try again. If the problem persists, check your internet connection and Spotify API credentials.</p>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        if st.button("🔄 Retry Sync", use_container_width=True, type="primary"):
            st.session_state.sync_error = None
            st.rerun()

    st.stop()

# ============================================================================
# START SYNC
# ============================================================================

if not st.session_state.sync_in_progress:
    # Auto-start sync
    st.session_state.sync_in_progress = True
    st.rerun()
else:
    # Run the sync
    run_sync()
