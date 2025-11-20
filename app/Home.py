"""
Spotify Analytics Dashboard - Home Page
Welcome page and main entry point for the multi-page Streamlit app
"""

import streamlit as st
import sys
import os
from dotenv import load_dotenv

# Add current directory to path to enable imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from func.ui_components import apply_page_config, get_custom_css
from func.page_auth import require_auth

# Load environment variables
load_dotenv()

# Apply page configuration
apply_page_config()

# Apply custom CSS
st.markdown(get_custom_css(), unsafe_allow_html=True)

# ============================================================================
# MAIN PAGE
# ============================================================================

st.title("🎵 Spotify Listening Analytics")
st.markdown("*Advanced insights into your music habits powered by ML*")

# Check authentication (but don't require it for home page)
sp, profile = require_auth()

# Auto-redirect to sync page after successful OAuth
if sp and profile and st.session_state.get('redirect_to_sync', False):
    st.session_state.redirect_to_sync = False
    st.switch_page("pages/0_Data_Sync.py")

# Show welcome content
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

#### 🔬 Deep User Analytics
- Historical tracking of listening habits over time
- Artist evolution and genre trends
- Temporal pattern analysis across weeks/months
- Compare listening habits with team members

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
- Data is collected and stored securely in Cloudflare R2
- All processing happens in your browser session
- You can disconnect at any time

---

**Note**: This app is in Development Mode and can only be used by allowlisted users.
To add your Spotify account, please reach out to the owner (Nicolo DiFerdinando) and he will add you to the allowlist.
""")

# If authenticated, show quick stats
if sp and profile:
    st.markdown("---")
    st.success(f"✅ Connected as **{profile.get('display_name')}**")
    st.info("👈 Use the sidebar to navigate to different pages")
