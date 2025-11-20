"""
Authentication and Credential Management for Spotify Analytics
Handles OAuth flow, credential configuration, and session state management
"""

import streamlit as st
import os
from datetime import datetime
from spotipy.oauth2 import SpotifyOAuth
import spotipy


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
    if 'snapshot_collected_this_session' not in st.session_state:
        st.session_state.snapshot_collected_this_session = False
    if 'redirect_to_sync' not in st.session_state:
        st.session_state.redirect_to_sync = False
    if 'sync_completed_this_session' not in st.session_state:
        st.session_state.sync_completed_this_session = False

    # Auto-detect and configure credentials from .env if available
    if not st.session_state.credentials_configured and st.session_state.credential_mode is None:
        env_creds = {
            'client_id': os.getenv('SPOTIFY_CLIENT_ID'),
            'client_secret': os.getenv('SPOTIFY_CLIENT_SECRET'),
            'redirect_uri': os.getenv('SPOTIFY_REDIRECT_URI', 'http://127.0.0.1:8501/')
        }
        if validate_credentials(env_creds):
            st.session_state.credential_mode = 'env'
            st.session_state.credentials_configured = True

    # Re-validate credentials if mode is set but not marked as configured
    # This handles cases where session state partially persists after OAuth redirect
    if st.session_state.credential_mode and not st.session_state.credentials_configured:
        creds = get_credentials()
        if validate_credentials(creds):
            st.session_state.credentials_configured = True


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
    # Check if we have a code in the URL (callback from Spotify) FIRST
    # This ensures we preserve credentials before checking OAuth
    query_params = st.query_params

    # If we're returning from OAuth, ensure credentials are configured
    if 'code' in query_params and not st.session_state.credentials_configured:
        # Try to re-configure credentials based on mode or auto-detect
        if st.session_state.credential_mode:
            # Re-validate existing credentials
            creds = get_credentials()
            if validate_credentials(creds):
                st.session_state.credentials_configured = True
        else:
            # Auto-detect from .env if no mode set
            env_creds = {
                'client_id': os.getenv('SPOTIFY_CLIENT_ID'),
                'client_secret': os.getenv('SPOTIFY_CLIENT_SECRET'),
                'redirect_uri': os.getenv('SPOTIFY_REDIRECT_URI', 'http://127.0.0.1:8501/')
            }
            if validate_credentials(env_creds):
                st.session_state.credential_mode = 'env'
                st.session_state.credentials_configured = True

    sp_oauth = get_spotify_oauth()

    if not sp_oauth:
        st.session_state.auth_error = "OAuth configuration failed. Check your credentials."
        return None

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

                    # Set flag to redirect to sync page (happens every login)
                    st.session_state.redirect_to_sync = True

                # Clear the URL parameters
                st.query_params.clear()
                st.rerun()

            except Exception as e:
                error_msg = str(e)
                if "invalid_client" in error_msg.lower():
                    st.session_state.auth_error = "Invalid Client ID or Client Secret. Please check your credentials."
                elif "redirect_uri" in error_msg.lower():
                    redirect_uri = get_credentials().get('redirect_uri', 'unknown')
                    st.session_state.auth_error = f"Redirect URI mismatch. Make sure '{redirect_uri}' is added to your Spotify app settings."
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


def get_spotify_client(token_info=None):
    """Create authenticated Spotify client"""
    if token_info is None:
        token_info = st.session_state.get('token_info')
    if not token_info:
        return None
    return spotipy.Spotify(auth=token_info['access_token'])
