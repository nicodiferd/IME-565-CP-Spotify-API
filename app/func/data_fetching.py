"""
Spotify API Data Fetching Functions
All functions that interact with the Spotify Web API
Uses Streamlit caching for performance
Includes retry logic with exponential backoff for rate limiting
"""

import streamlit as st
import time
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log
)
import logging

# Setup logging for retry attempts
logger = logging.getLogger(__name__)


# ============================================================================
# RETRY LOGIC FOR RATE LIMITING
# ============================================================================

def handle_rate_limit_error(exception):
    """Extract retry-after header from Spotify rate limit errors"""
    if hasattr(exception, 'response') and exception.response is not None:
        retry_after = exception.response.headers.get('Retry-After')
        if retry_after:
            sleep_time = int(retry_after)
            logger.warning(f"Rate limited. Sleeping for {sleep_time} seconds...")
            time.sleep(sleep_time)
    return True


def is_rate_limit_error(exception):
    """Check if exception is a rate limit error (429)"""
    return (
        hasattr(exception, 'http_status') and exception.http_status == 429
    ) or '429' in str(exception)


def is_retryable_error(exception):
    """Check if exception should trigger a retry"""
    # Retry on rate limit (429), server errors (5xx), and timeout errors
    if is_rate_limit_error(exception):
        handle_rate_limit_error(exception)
        return True
    if hasattr(exception, 'http_status'):
        return exception.http_status >= 500
    return False


# Retry decorator configuration
spotify_retry = retry(
    retry=retry_if_exception_type(Exception),
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    before_sleep=before_sleep_log(logger, logging.WARNING),
    reraise=True
)


# ============================================================================
# DATA FETCHING FUNCTIONS
# ============================================================================

@st.cache_data(ttl=3600)
def fetch_user_profile(_sp):
    """Fetch current user profile with retry logic"""
    @spotify_retry
    def _fetch():
        return _sp.current_user()

    try:
        return _fetch()
    except Exception as e:
        st.error(f"Error fetching profile: {e}")
        return None


@st.cache_data(ttl=300)
def fetch_recently_played(_sp, limit=50):
    """Fetch recently played tracks with retry logic"""
    @spotify_retry
    def _fetch():
        return _sp.current_user_recently_played(limit=limit)

    try:
        results = _fetch()
        return results.get('items', [])
    except Exception as e:
        st.error(f"Error fetching recently played: {e}")
        return []


@st.cache_data(ttl=300)
def fetch_top_tracks(_sp, time_range='short_term', limit=50):
    """Fetch top tracks for a given time range with retry logic"""
    @spotify_retry
    def _fetch():
        return _sp.current_user_top_tracks(time_range=time_range, limit=limit)

    try:
        results = _fetch()
        return results.get('items', [])
    except Exception as e:
        st.error(f"Error fetching top tracks ({time_range}): {e}")
        return []


@st.cache_data(ttl=300)
def fetch_top_artists(_sp, time_range='short_term', limit=50):
    """Fetch top artists for a given time range with retry logic"""
    @spotify_retry
    def _fetch():
        return _sp.current_user_top_artists(time_range=time_range, limit=limit)

    try:
        results = _fetch()
        return results.get('items', [])
    except Exception as e:
        st.error(f"Error fetching top artists ({time_range}): {e}")
        return []


@st.cache_data(ttl=3600)
def fetch_playlists(_sp, limit=50):
    """Fetch user playlists with retry logic"""
    @spotify_retry
    def _fetch():
        return _sp.current_user_playlists(limit=limit)

    try:
        results = _fetch()
        return results.get('items', [])
    except Exception as e:
        st.error(f"Error fetching playlists: {e}")
        return []


@st.cache_data(ttl=300)
def fetch_audio_features(_sp, track_ids):
    """
    Fetch audio features for multiple tracks with retry logic

    Note: Audio features require Spotify Extended Quota Mode.
    Returns empty list if unavailable (Development Mode).
    """
    if not track_ids:
        return []

    try:
        # Spotify allows max 100 tracks per request
        all_features = []
        for i in range(0, len(track_ids), 100):
            batch = track_ids[i:i+100]

            # Try to fetch without retry for 403 errors (permanent failures)
            try:
                features = _sp.audio_features(batch)
                all_features.extend([f for f in features if f is not None])
            except Exception as batch_error:
                error_msg = str(batch_error)

                # Handle 403 Forbidden (Development Mode - no retry)
                if '403' in error_msg or 'Forbidden' in error_msg:
                    # Silently skip - this is expected in Development Mode
                    return []

                # For other errors, raise to be handled by outer try-catch
                raise

        return all_features

    except Exception as e:
        error_msg = str(e)

        # Handle 403 Forbidden (Development Mode quota/permissions issue)
        if '403' in error_msg or 'Forbidden' in error_msg:
            # Don't show warning repeatedly - log once
            return []

        # Handle 429 Rate Limiting
        elif '429' in error_msg or 'rate limit' in error_msg.lower():
            st.warning("⚠️ Rate limit reached. Continuing without audio features...")
            return []

        # Other errors
        else:
            # Silently continue - audio features are optional
            return []
