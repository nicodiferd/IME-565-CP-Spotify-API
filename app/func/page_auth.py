"""
Shared Authentication Wrapper for Multi-Page Streamlit App
Provides a common authentication check that all pages can use
"""

import streamlit as st
from datetime import datetime
from .auth import (
    initialize_session_state,
    get_credentials,
    authenticate,
    get_spotify_client,
    show_credential_configuration,
    get_spotify_oauth
)
from .data_fetching import fetch_user_profile


def require_auth():
    """
    Require authentication for a page.
    Returns (sp_client, profile) if authenticated, otherwise shows auth UI and returns (None, None).

    Usage in a page:
        sp, profile = require_auth()
        if not sp:
            st.stop()  # Stop execution if not authenticated

        # Page content here...
    """
    # Initialize session state
    initialize_session_state()

    # Handle authentication
    if st.session_state.credentials_configured:
        token_info = authenticate()

        if token_info:
            # User is authenticated
            sp = get_spotify_client(token_info)

            if sp:
                profile = fetch_user_profile(sp)

                if profile:
                    # Show compact user info
                    st.sidebar.success("✓ Connected to Spotify")
                    st.sidebar.write(f"**{profile.get('display_name')}**")
                    st.sidebar.caption(f"User ID: `{profile.get('id')}`")
                    st.sidebar.caption(f"Account: {profile.get('product', 'free').upper()}")

                    # Logout button
                    if st.sidebar.button("🚪 Disconnect", use_container_width=True):
                        st.session_state.token_info = None
                        st.session_state.auth_code = None
                        st.session_state.credentials_configured = False
                        st.session_state.credential_mode = None
                        st.rerun()

                    st.sidebar.markdown("---")

                    # Re-sync data button (redirects to sync page)
                    if st.sidebar.button("🔄 Re-sync Data", use_container_width=True, help="Collect fresh listening data from Spotify"):
                        st.session_state.redirect_to_sync = True
                        st.switch_page("pages/0_Data_Sync.py")

                    # Clear cache button
                    if st.sidebar.button("🗑️ Clear Cache", use_container_width=True, help="Clear cached data and reload from Spotify"):
                        st.cache_data.clear()
                        st.rerun()

                    st.sidebar.caption("Last updated: " + datetime.now().strftime("%H:%M:%S"))

                    # Show info about automatic data syncing
                    if st.session_state.get('sync_completed_this_session', False):
                        st.sidebar.success("✓ Data synced this session")
                    else:
                        st.sidebar.info("💡 Data is automatically synced on each login")

                    return sp, profile
                else:
                    st.sidebar.error("Could not load user profile")
                    return None, None
            else:
                st.sidebar.error("Could not create Spotify client")
                return None, None
        else:
            # Not authenticated but credentials configured - show connect button
            if st.session_state.auth_error:
                st.sidebar.error(f"⚠️ {st.session_state.auth_error}")

                # Reset credentials button
                if st.sidebar.button("🔄 Reset Credentials", use_container_width=True):
                    st.session_state.credentials_configured = False
                    st.session_state.credential_mode = None
                    st.session_state.auth_error = None
                    st.rerun()

            elif st.session_state.is_connecting:
                st.sidebar.info("🔐 Connecting to Spotify...")
                st.sidebar.spinner("Please wait...")

            else:
                st.sidebar.info("Ready to connect!")

                sp_oauth = get_spotify_oauth()
                if sp_oauth:
                    auth_url = sp_oauth.get_authorize_url()

                    st.sidebar.markdown(f"""
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

                    st.sidebar.markdown("---")
                    st.sidebar.caption("This app requires:")
                    st.sidebar.caption("• Spotify account (Free or Premium)")
                    st.sidebar.caption("• Permission to read listening history")

                    st.sidebar.markdown("---")
                    st.sidebar.caption(f"📍 Redirect URI: `{get_credentials().get('redirect_uri', 'N/A')}`")

            return None, None
    else:
        # Credentials not configured - show config in sidebar
        st.sidebar.markdown("---")
        st.sidebar.image("https://storage.googleapis.com/pr-newsroom-wp/1/2018/11/Spotify_Logo_RGB_Green.png", width=120)
        with st.sidebar.expander("🔐 Connect Spotify", expanded=True):
            show_credential_configuration()
        return None, None

    # If we get here and authenticated, show compact status
    st.sidebar.markdown("---")
    st.sidebar.image("https://storage.googleapis.com/pr-newsroom-wp/1/2018/11/Spotify_Logo_RGB_Green.png", width=120)
