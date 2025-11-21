"""
Data Sync Page - First-Time User Optimized
Comprehensive data collection for instant dashboard value
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
from func.page_auth import require_auth
from func.data_collection import should_refresh_data, collect_comprehensive_snapshot

# Apply page configuration
apply_page_config()
st.markdown(get_custom_css(), unsafe_allow_html=True)

# ============================================================================
# AUTHENTICATION CHECK
# ============================================================================

sp, profile = require_auth()
if not sp:
    st.warning("Please connect your Spotify account to continue.")
    st.stop()

user_id = profile['id']

# ============================================================================
# LOAD SPOTIFY FACTS
# ============================================================================

facts_path = Path(__file__).parent.parent / "data" / "spotify_facts.json"
try:
    with open(facts_path, 'r') as f:
        spotify_facts = json.load(f)
except Exception as e:
    spotify_facts = [
        "Spotify has over 100 million tracks in its library.",
        "The average song is 3 minutes and 30 seconds long.",
        "Music can reduce stress and anxiety levels.",
        "Listening to music releases dopamine in the brain.",
        "Your music taste says a lot about your personality!",
        "Different genres affect your brain in unique ways.",
        "We're analyzing your unique listening patterns...",
        "Almost there! Your dashboard is being prepared..."
    ]

# ============================================================================
# CHECK IF REFRESH NEEDED
# ============================================================================

st.title("📊 Data Sync")

# Check for force sync flag
force_sync = st.session_state.get('force_sync', False)
refresh_needed = force_sync or should_refresh_data(user_id)

if not refresh_needed:
    # Data is up to date
    st.success("✅ Your data is up to date!")
    st.info("We automatically refresh your data every 24 hours to keep your insights current.")

    st.markdown("---")

    # Show last sync info
    try:
        from func.s3_storage import get_s3_client, get_bucket_name
        bucket_name = get_bucket_name()
        s3_client = get_s3_client()

        metadata_key = f'users/{user_id}/current/metadata.json'
        response = s3_client.get_object(Bucket=bucket_name, Key=metadata_key)
        metadata_content = response['Body'].read().decode('utf-8')
        metadata = json.loads(metadata_content)

        last_sync_time = metadata.get('last_sync', 'Unknown')

        from datetime import datetime, timezone
        try:
            last_sync = datetime.fromisoformat(last_sync_time)
            time_ago = datetime.now(timezone.utc) - last_sync
            hours_ago = int(time_ago.total_seconds() / 3600)

            st.caption(f"Last synced: {hours_ago} hours ago")
        except:
            st.caption(f"Last synced: Recently")
    except:
        pass

    st.markdown("### What's Available")
    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("**📈 Top Tracks**")
        st.caption("Your favorite songs across 3 time ranges")

    with col2:
        st.markdown("**👥 Top Artists**")
        st.caption("Artists you listen to most")

    with col3:
        st.markdown("**🎵 Recent Listening**")
        st.caption("Your last 50 played tracks")

    st.markdown("---")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔄 Force Refresh Now", type="secondary", use_container_width=True):
            st.session_state['force_sync'] = True
            st.rerun()

    with col2:
        if st.button("➡️ Go to Dashboard", type="primary", use_container_width=True):
            st.switch_page("pages/1_Dashboard.py")

    st.stop()

# ============================================================================
# DATA SYNC NEEDED - SHOW INFO
# ============================================================================

st.markdown("""
<div style='text-align: center; padding: 2rem 0;'>
    <h1 style='font-size: 3rem; margin-bottom: 0.5rem;'>🎵</h1>
    <h2 style='margin-top: 0;'>Collecting Your Music Data</h2>
    <p style='color: #b3b3b3; font-size: 1.1rem;'>
        We're fetching your listening history from Spotify to create personalized insights.
        <br>This takes about 30-60 seconds.
    </p>
</div>
""", unsafe_allow_html=True)

st.markdown("---")

st.info("⏳ **What we're collecting:**")
st.markdown("""
- **Top 50 tracks** (last 4 weeks, 6 months, and all-time)
- **Top 50 artists** (last 4 weeks, 6 months, and all-time)
- **50 most recently played tracks** with timestamps
""")

st.markdown("---")

# ============================================================================
# PROGRESS TRACKING
# ============================================================================

progress_bar = st.progress(0)
status_text = st.empty()
fact_container = st.empty()
stage_container = st.empty()

# Define precise steps matching our collection function
steps = [
    ("Connecting to Spotify API...", 0.05),
    ("Fetching user profile...", 0.10),
    ("Fetching recently played tracks...", 0.20),
    ("Fetching top tracks (last 4 weeks)...", 0.30),
    ("Fetching top tracks (last 6 months)...", 0.40),
    ("Fetching top tracks (all-time)...", 0.50),
    ("Fetching top artists (last 4 weeks)...", 0.60),
    ("Fetching top artists (last 6 months)...", 0.70),
    ("Fetching top artists (all-time)...", 0.80),
    ("Computing analytics metrics...", 0.88),
    ("Saving to current/ directory...", 0.94),
    ("Archiving snapshot for historical analysis...", 0.98),
    ("Finalizing...", 1.0)
]

# Initialize fact rotation
fact_index = random.randint(0, len(spotify_facts) - 1)
last_fact_time = time.time()

# ============================================================================
# RUN SYNC WITH SIMULATED PROGRESS
# ============================================================================

# Show initial fact
fact_container.markdown(f"""
<div style='background-color: #282828; padding: 1.5rem; border-radius: 10px; margin: 2rem 0; text-align: center;'>
    <p style='color: #1DB954; font-weight: bold; margin-bottom: 0.5rem;'>DID YOU KNOW?</p>
    <p style='font-size: 1.1rem; line-height: 1.6;'>{spotify_facts[fact_index]}</p>
</div>
""", unsafe_allow_html=True)

try:
    # Run sync in "background" while showing progress
    # We'll simulate progress updates since the actual collection happens synchronously

    # Start the actual collection in a way that we can show progress
    import threading
    sync_result = {'success': False, 'timestamp': None, 'error': None}

    def run_collection():
        """Run collection in thread"""
        try:
            success, timestamp = collect_comprehensive_snapshot(sp, user_id, force=force_sync)
            sync_result['success'] = success
            sync_result['timestamp'] = timestamp
        except Exception as e:
            sync_result['error'] = str(e)

    # Start collection thread
    collection_thread = threading.Thread(target=run_collection)
    collection_thread.start()

    # Show progress updates while collection runs
    for step_text, progress in steps:
        status_text.text(step_text)
        progress_bar.progress(progress)

        # Determine stage emoji based on progress
        if progress < 0.2:
            stage_emoji = "🔗"
        elif progress < 0.5:
            stage_emoji = "🎵"
        elif progress < 0.8:
            stage_emoji = "👥"
        elif progress < 0.95:
            stage_emoji = "📊"
        else:
            stage_emoji = "💾"

        stage_container.markdown(f"<h2 style='text-align: center;'>{stage_emoji}</h2>", unsafe_allow_html=True)

        # Rotate facts periodically
        if time.time() - last_fact_time >= 3:
            fact_index = (fact_index + 1) % len(spotify_facts)
            last_fact_time = time.time()

            fact_container.markdown(f"""
            <div style='background-color: #282828; padding: 1.5rem; border-radius: 10px; margin: 2rem 0; text-align: center;'>
                <p style='color: #1DB954; font-weight: bold; margin-bottom: 0.5rem;'>DID YOU KNOW?</p>
                <p style='font-size: 1.1rem; line-height: 1.6;'>{spotify_facts[fact_index]}</p>
            </div>
            """, unsafe_allow_html=True)

        # Wait for this step duration (total ~40 seconds for UI)
        time.sleep(3.0)

    # Wait for collection thread to complete
    collection_thread.join(timeout=30)  # Max 30 more seconds

    # Check results
    if sync_result['error']:
        raise Exception(sync_result['error'])

    if not sync_result['success']:
        raise Exception("Data collection failed")

    # Success!
    progress_bar.progress(1.0)
    status_text.text("✅ Sync complete!")
    stage_container.markdown("<h2 style='text-align: center;'>🎉</h2>", unsafe_allow_html=True)

    st.success("🎉 **All set!** Your personalized insights are ready.")

    # Clear force sync flag if it was set
    if 'force_sync' in st.session_state:
        del st.session_state['force_sync']

    # Mark sync as completed this session
    st.session_state['sync_completed_this_session'] = True

    st.balloons()
    time.sleep(2)

    # Redirect to dashboard
    st.switch_page("pages/1_Dashboard.py")

except Exception as e:
    progress_bar.progress(0)
    status_text.text("")
    stage_container.empty()
    fact_container.empty()

    st.error(f"❌ **Sync failed:** {str(e)}")

    st.markdown("""
    <div style='background-color: #3a0f0f; padding: 1rem; border-radius: 5px; margin: 1rem 0;'>
        <p><strong>Possible causes:</strong></p>
        <ul>
            <li>Network connectivity issues</li>
            <li>Spotify API rate limiting (try again in a few minutes)</li>
            <li>Cloud storage unavailable</li>
            <li>Invalid authentication token (try re-authenticating)</li>
        </ul>
        <p>Please try again. If the problem persists, check your internet connection and Spotify API credentials.</p>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        if st.button("🔄 Retry Sync", use_container_width=True, type="primary"):
            st.rerun()
