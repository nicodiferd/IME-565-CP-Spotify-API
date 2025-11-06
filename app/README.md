# Spotify Analytics Dashboard - Streamlit App

Interactive dashboard for visualizing your Spotify listening habits and gaining insights into your music preferences.

## Quick Start

### 1. Install Dependencies

```bash
# From project root
pip install streamlit plotly spotipy python-dotenv pandas
```

### 2. Configure Environment

Make sure your `.env` file in the project root has:

```bash
SPOTIFY_CLIENT_ID=your_client_id
SPOTIFY_CLIENT_SECRET=your_client_secret
SPOTIFY_REDIRECT_URI=http://127.0.0.1:8501/callback
```

**Important**: For Streamlit, the redirect URI must use port **8501** (Streamlit's default port).

### 3. Add Redirect URI to Spotify Dashboard

1. Go to https://developer.spotify.com/dashboard
2. Click on your app (IME 565 Spotify Analytics)
3. Click **Settings**
4. Under **Redirect URIs**, add: `http://127.0.0.1:8501/callback`
5. Click **Save**

### 4. Run the App

```bash
# From project root
streamlit run app/spotify_dashboard.py

# Or from app directory
cd app
streamlit run spotify_dashboard.py
```

The app will open in your browser at `http://localhost:8501`

## Features

### Dashboard Page
- **KPI Metrics**: Total tracks, unique artists, listening time, avg popularity
- **Listening by Hour**: Bar chart showing when you listen most
- **Listening by Day**: Bar chart showing day-of-week distribution
- **Top Artists**: Top 10 artists from recent listening

### Recent Listening Page
- **Timeline Visualization**: Interactive scatter plot of last 50 tracks
- **Track List Table**: Sortable/filterable table with all metadata
- **CSV Export**: Download your listening data

### Top Tracks Page
- **Time Range Selection**: Last 4 weeks, 6 months, or all-time
- **Ranked List**: Your top 20 tracks with artist and popularity

### Playlists Page
- **Playlist Overview**: All your playlists with track counts
- **Playlist Details**: Expandable cards with images and metadata
- **Quick Links**: Open playlists directly in Spotify

## Architecture

### Authentication Flow

1. User clicks "Connect Spotify"
2. Redirects to Spotify OAuth login
3. User authorizes app
4. Spotify redirects back to `http://127.0.0.1:8501/callback?code=...`
5. App exchanges code for access token
6. Token stored in `st.session_state` (session-based, not file)
7. User profile displayed

### Session State Management

```python
st.session_state.token_info  # OAuth token
st.session_state.user_profile  # User profile data
```

**Important**: Each user gets their own session, so tokens don't conflict between users.

### Caching Strategy

```python
@st.cache_data(ttl=3600)  # Data fetching functions (1-hour TTL)
@st.cache_resource  # Spotify client (persist across reruns)
```

Data is cached for 1 hour to reduce API calls. Click "Refresh Data" in sidebar to force update.

## Customization

### Change Theme Colors

Edit the custom CSS in `spotify_dashboard.py`:

```python
st.markdown("""
    <style>
    .stButton>button {
        background-color: #1DB954;  /* Spotify green */
        ...
    }
    </style>
""", unsafe_allow_html=True)
```

### Add New Visualizations

Create a new function in the "VISUALIZATION FUNCTIONS" section:

```python
def plot_my_custom_chart(df):
    fig = px.bar(df, x='column', y='value')
    st.plotly_chart(fig, use_container_width=True)
```

### Add New Pages

1. Add page to sidebar navigation:
   ```python
   page = st.radio(
       "Select Page",
       ["Dashboard", "Recent Listening", "Top Tracks", "Playlists", "New Page"]
   )
   ```

2. Create page function:
   ```python
   def show_new_page(sp):
       st.header("New Page")
       # Your content here
   ```

3. Add to main content routing:
   ```python
   elif page == "New Page":
       show_new_page(sp)
   ```

## Troubleshooting

### "INVALID_CLIENT: Invalid redirect URI"
- Make sure `http://127.0.0.1:8501/callback` is added to your Spotify app's Redirect URIs
- Check that `.env` file has `SPOTIFY_REDIRECT_URI=http://127.0.0.1:8501/callback`

### "Token expired" errors
- The app auto-refreshes tokens every 55 minutes
- If you see errors, click "Disconnect" and reconnect

### Caching issues
- Click "Refresh Data" in sidebar
- Or restart the Streamlit app with Ctrl+C and re-run

### Rate limiting (HTTP 429)
- Wait a few minutes and refresh
- The app has built-in caching to minimize API calls

### No data showing
- Make sure you've played music on Spotify recently
- Check that your account is on the app's allowlist in Spotify Developer Dashboard

## Development Mode Limitations

- **Max 25 users**: Must add each user to allowlist in Developer Dashboard
- **Lower rate limits**: ~180 requests/minute
- **Audio features blocked**: Use Kaggle dataset matching as workaround

## Next Steps

### Phase 2 Enhancements
- [ ] Add Kaggle dataset matching for audio features
- [ ] Implement mood trajectory charts
- [ ] Add context classification (workout, focus, etc.)
- [ ] Create playlist health scores

### Phase 3 ML Features
- [ ] Recommendation engine
- [ ] Preference prediction models
- [ ] Clustering for activity detection

## File Structure

```
app/
├── spotify_dashboard.py    # Main Streamlit app
├── README.md               # This file
├── components/             # Reusable UI components (future)
└── pages/                  # Multi-page app structure (future)
```

## Resources

- [Streamlit Docs](https://docs.streamlit.io/)
- [Plotly Python](https://plotly.com/python/)
- [Spotipy Documentation](https://spotipy.readthedocs.io/)
- [Spotify Web API Reference](https://developer.spotify.com/documentation/web-api)

## License

MIT License - IME 565 Student Project

---

**Built by**: Nicolo DiFerdinando, Joe Mascher, Rithvik Shetty
**Course**: IME 565 - Predictive Data Analytics for Engineers
**Quarter**: Fall 2025
