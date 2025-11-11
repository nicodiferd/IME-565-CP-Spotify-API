# Spotify Listening Analytics Visualizer - Build Prompt

**Project**: IME 565 Spotify Analytics Platform
**Goal**: Create an interactive Streamlit dashboard for personalized music listening analytics

---

## Project Overview

Build a comprehensive Spotify analytics platform that provides deeper insights than Spotify's annual "Wrapped" feature. The platform should analyze listening patterns, track evolution, mood trajectories, and provide context-aware recommendations.

---

## Technical Architecture

### Data Sources

**Primary**: Spotify Web API (Behavioral Data)
- Recently played tracks (last 50 with timestamps)
- Top tracks/artists (short/medium/long term)
- User playlists
- Track metadata (name, artist, album, popularity, duration)

**Secondary**: Kaggle Audio Features Dataset (Enrichment Data)
- ~114,000 tracks with audio features
- Danceability, energy, valence, acousticness, instrumentalness, speechiness
- Tempo, loudness, key, mode, time signature

### Tech Stack

- **Backend**: Python 3.12+
- **API Integration**: Spotipy (Spotify Web API wrapper)
- **Dashboard**: Streamlit
- **Data Processing**: Pandas, NumPy
- **Visualization**: Plotly, Matplotlib, Seaborn
- **Machine Learning**: scikit-learn, XGBoost (Phase 3)
- **Storage**: Cloudflare R2/S3 (optional for persistence)

---

## Core Features to Build

### Phase 1: Authentication & Data Collection

#### 1. Spotify OAuth Authentication
**Requirements**:
- Session-based authentication (multi-user support)
- Token caching in `st.session_state` (NOT file-based)
- Automatic token refresh at 50-minute mark
- Clear authentication status display

**Implementation Pattern**:
```python
class SessionCacheHandler(CacheHandler):
    def get_cached_token(self):
        return st.session_state.get('token_info', None)

    def save_token_to_cache(self, token_info):
        st.session_state['token_info'] = token_info
```

**User Flow**:
1. User visits Streamlit app
2. "Connect Spotify" button displayed
3. OAuth redirect to Spotify login
4. User authorizes app
5. Redirect back to Streamlit with token
6. Token stored in session state
7. User profile displayed (name, account type)

#### 2. Data Fetching Layer
**Endpoints to Implement**:

```python
# Recently played tracks (last 50)
sp.current_user_recently_played(limit=50)

# Top tracks by time range
sp.current_user_top_tracks(time_range='short_term', limit=20)
sp.current_user_top_tracks(time_range='medium_term', limit=20)
sp.current_user_top_tracks(time_range='long_term', limit=20)

# Top artists
sp.current_user_top_artists(time_range='short_term', limit=20)

# User playlists
sp.current_user_playlists(limit=50)

# User profile
sp.current_user()
```

**Caching Strategy**:
```python
@st.cache_data(ttl=3600)  # Cache for 1 hour
def fetch_recently_played(sp):
    return sp.current_user_recently_played(limit=50)
```

**Error Handling**:
- HTTP 429 (Rate Limit): Display message, implement exponential backoff
- HTTP 401 (Unauthorized): Clear session, prompt re-authentication
- Connection errors: Retry with delay, show user-friendly message

---

### Phase 2: Visualizations & Analytics

#### 1. Recent Listening Timeline
**Visual**: Interactive timeline chart (Plotly)

**Data to Display**:
- X-axis: Time (played_at timestamps)
- Y-axis: Track names
- Hover info: Artist, album, duration, playback context
- Color coding: By artist or playlist source

**Insights**:
- Listening sessions (clustered timestamps)
- Late-night vs morning habits
- Repeat plays (same track multiple times)

**Code Pattern**:
```python
import plotly.express as px

df = pd.DataFrame(recent_tracks)
df['played_at'] = pd.to_datetime(df['played_at'])

fig = px.scatter(
    df,
    x='played_at',
    y='track_name',
    color='artist_name',
    hover_data=['album_name', 'duration_ms'],
    title='Your Recent Listening Timeline'
)
st.plotly_chart(fig)
```

#### 2. Top Tracks Evolution
**Visual**: Comparative bar charts or Sankey diagram

**Data to Display**:
- Top 10 tracks for each time range (short/medium/long)
- Side-by-side comparison
- Track position changes over time

**Insights**:
- Current obsessions vs all-time favorites
- Taste evolution
- Emerging artists

#### 3. Listening Patterns Analysis
**Visual**: Heatmap or distribution charts

**Metrics**:
- Hour-of-day distribution (0-23)
- Day-of-week distribution (Mon-Sun)
- Weekend vs weekday habits
- Listening frequency (tracks per day/week)

**Code Pattern**:
```python
df['hour'] = df['played_at'].dt.hour
df['day_of_week'] = df['played_at'].dt.day_name()

# Heatmap: Hour vs Day of Week
pivot = df.pivot_table(
    values='track_id',
    index='hour',
    columns='day_of_week',
    aggfunc='count',
    fill_value=0
)

fig = px.imshow(
    pivot,
    labels=dict(x="Day of Week", y="Hour of Day", color="Track Count"),
    title="Listening Patterns Heatmap"
)
st.plotly_chart(fig)
```

#### 4. Artist Diversity Metrics
**Visual**: Pie chart and bar chart

**Metrics**:
- Unique artists in last 50 plays
- Artist concentration (top artist play percentage)
- Genre diversity (if genre data available)
- New artist discovery rate

**Insights**:
- "You listened to 23 unique artists in your last 50 plays"
- "Drake accounts for 18% of your recent listening"
- "You discovered 3 new artists this week"

#### 5. Playlist Overview
**Visual**: Table with metrics + bar chart

**Data to Display**:
- Playlist name, track count, last modified
- Top playlists by size
- Playlist freshness score (tracks played recently)

**Interactions**:
- Click playlist to expand and see all tracks
- Filter by playlist size, activity, etc.

---

### Phase 3: Hybrid Audio Features (Spotify + Kaggle)

#### 1. Track Matching System
**Goal**: Match Spotify tracks to Kaggle dataset for audio features

**Matching Logic**:
```python
def match_track_to_kaggle(track_name, artist_name, kaggle_df):
    # Exact match first
    exact = kaggle_df[
        (kaggle_df['track_name'].str.lower() == track_name.lower()) &
        (kaggle_df['artists'].str.contains(artist_name, case=False))
    ]

    if not exact.empty:
        return exact.iloc[0]

    # Fuzzy match (remove special chars, normalize)
    # Use fuzzywuzzy or rapidfuzz for string similarity
    from fuzzywuzzy import fuzz

    kaggle_df['match_score'] = kaggle_df.apply(
        lambda row: fuzz.ratio(
            track_name.lower() + artist_name.lower(),
            row['track_name'].lower() + row['artists'].lower()
        ),
        axis=1
    )

    best_match = kaggle_df.loc[kaggle_df['match_score'].idxmax()]

    if best_match['match_score'] > 80:  # Threshold
        return best_match

    return None
```

#### 2. Mood Trajectory Visualization
**Visual**: Line chart over time

**Metrics**:
- Valence (musical positivity/happiness) over time
- Energy levels by hour/day
- Mood score (composite of valence + energy)

**Insights**:
- "Your music mood dipped on Wednesday (avg valence: 0.3)"
- "Evening listening is 40% more energetic than morning"

**Code Pattern**:
```python
df['mood_score'] = (df['valence'] * 0.5) + (df['energy'] * 0.3) - (df['acousticness'] * 0.2)

fig = px.line(
    df,
    x='played_at',
    y='mood_score',
    title='Your Music Mood Over Time',
    labels={'mood_score': 'Mood Score (0-1)'}
)
st.plotly_chart(fig)
```

#### 3. Context Classification
**Visual**: Pie chart + timeline with context labels

**Contexts to Detect**:
- **Workout**: energy > 0.7, danceability > 0.6, tempo > 120 BPM
- **Focus**: instrumentalness > 0.5, speechiness < 0.1, energy < 0.5
- **Relaxation**: acousticness > 0.6, energy < 0.4, valence > 0.5
- **Party**: energy > 0.8, valence > 0.6, danceability > 0.7
- **Podcast**: speechiness > 0.66

**Algorithm**:
```python
def classify_context(row):
    if row['energy'] > 0.7 and row['danceability'] > 0.6 and row['tempo'] > 120:
        return 'Workout'
    elif row['instrumentalness'] > 0.5 and row['speechiness'] < 0.1 and row['energy'] < 0.5:
        return 'Focus'
    elif row['acousticness'] > 0.6 and row['energy'] < 0.4 and row['valence'] > 0.5:
        return 'Relaxation'
    elif row['energy'] > 0.8 and row['valence'] > 0.6 and row['danceability'] > 0.7:
        return 'Party'
    elif row['speechiness'] > 0.66:
        return 'Podcast'
    else:
        return 'General'

df['context'] = df.apply(classify_context, axis=1)
```

#### 4. Audio Feature Distributions
**Visual**: Histograms or violin plots

**Features to Visualize**:
- Danceability distribution (0-1)
- Energy distribution (0-1)
- Valence distribution (0-1)
- Tempo distribution (BPM)
- Acousticness vs Instrumentalness (scatter plot)

**Insights**:
- "Your listening skews high-energy (avg: 0.72)"
- "You prefer danceable tracks (avg: 0.68)"
- "Mood range: 0.2-0.9 valence"

---

### Phase 4: Advanced Features (Optional)

#### 1. Playlist Health Score
**Metrics**:
- Freshness: % tracks played in last 30 days
- Diversity: Unique artists / total tracks
- Staleness: Days since last track added
- Size: Track count
- Engagement: Play count per track

**Visual**: Card dashboard with scores

#### 2. Recommendations Engine
**Approaches**:
- Content-based: Similar audio features (cosine similarity)
- Collaborative: Based on listening time patterns
- Hybrid: Combine both

**Display**:
- "Based on your 2 AM listening, you might like..."
- Show similar tracks from Kaggle dataset

#### 3. Listening Streaks
**Metrics**:
- Days with at least 1 play
- Longest streak
- Current streak
- Most active day of week

**Visual**: Calendar heatmap (GitHub-style)

---

## UI/UX Requirements

### Layout Structure

```
┌─────────────────────────────────────────────────────────┐
│  Header: Logo + "Spotify Analytics" + Profile Photo    │
├─────────────────────────────────────────────────────────┤
│  Sidebar:                                               │
│    - Connect Spotify (if not authenticated)            │
│    - User profile info                                  │
│    - Navigation menu                                    │
│      * Dashboard                                        │
│      * Recent Listening                                 │
│      * Top Tracks/Artists                               │
│      * Mood Analysis                                    │
│      * Playlists                                        │
│      * Settings                                         │
├─────────────────────────────────────────────────────────┤
│  Main Content:                                          │
│    - KPI cards (total tracks, unique artists, etc.)    │
│    - Interactive visualizations                         │
│    - Data tables (expandable)                           │
│    - Export buttons (CSV download)                      │
└─────────────────────────────────────────────────────────┘
```

### Design Principles

1. **Spotify Branding**: Use Spotify green (#1DB954) as primary color
2. **Dark Mode**: Match Spotify's dark theme
3. **Responsive**: Mobile-friendly layout
4. **Fast Loading**: Use caching, lazy loading
5. **Clear CTAs**: "Connect Spotify", "Refresh Data", "Export CSV"
6. **Tooltips**: Explain metrics on hover
7. **Error Messages**: User-friendly, actionable

---

## Data Processing Pipeline

### Step-by-Step Flow

```python
# 1. Authentication
if not st.session_state.get('token_info'):
    # Show login button
    auth_url = create_spotify_oauth().get_authorize_url()
    st.link_button("Connect Spotify", auth_url)
else:
    # User is authenticated
    sp = get_spotify_client()

    # 2. Fetch data
    recent = fetch_recently_played(sp)
    top_tracks = fetch_top_tracks(sp)
    playlists = fetch_playlists(sp)

    # 3. Process into DataFrame
    recent_df = process_recent_tracks(recent)

    # 4. Load Kaggle dataset
    kaggle_df = load_kaggle_data()

    # 5. Match and enrich
    enriched_df = match_and_enrich(recent_df, kaggle_df)

    # 6. Compute features
    enriched_df = compute_composite_features(enriched_df)
    enriched_df = classify_contexts(enriched_df)

    # 7. Visualize
    show_dashboard(enriched_df, top_tracks, playlists)
```

---

## Performance Optimization

### Caching Strategy

```python
# Cache data fetching (1 hour TTL)
@st.cache_data(ttl=3600)
def fetch_recently_played(sp):
    return sp.current_user_recently_played(limit=50)

# Cache resource (Spotify client)
@st.cache_resource
def get_spotify_client():
    return spotipy.Spotify(auth_manager=auth_manager)

# Cache Kaggle dataset loading (persist across sessions)
@st.cache_data
def load_kaggle_data():
    return pd.read_csv('data/raw/dataset.csv')
```

### Session State Management

```python
# Initialize session state keys on app start
if 'token_info' not in st.session_state:
    st.session_state.token_info = None

if 'user_profile' not in st.session_state:
    st.session_state.user_profile = None

if 'data_last_refreshed' not in st.session_state:
    st.session_state.data_last_refreshed = None
```

---

## Security Considerations

1. **Never commit credentials**: Use `.env` file (gitignored)
2. **Token storage**: Session-based only (not file-based for multi-user)
3. **Token refresh**: Automatic at 50-minute mark
4. **HTTPS only**: Ensure redirect URIs use HTTPS in production
5. **Scope minimization**: Only request necessary scopes
6. **User data privacy**: Don't persist sensitive data without consent

---

## Deployment Options

### Option 1: Streamlit Cloud (Recommended)
- **Pros**: Free, easy deployment, automatic scaling
- **Cons**: Limited resources, public unless paid plan
- **Setup**: Connect GitHub repo, set secrets in dashboard

### Option 2: Self-Hosted (Homelab)
- **Pros**: Full control, private network
- **Cons**: Requires server maintenance, SSL setup
- **Tools**: Docker, nginx reverse proxy, Cloudflare tunnel

### Option 3: Cloud Platform (AWS/GCP/Azure)
- **Pros**: Scalable, reliable
- **Cons**: Cost, complexity
- **Services**: EC2, Cloud Run, App Service

---

## Testing & Validation

### Unit Tests
```python
# Test track matching
def test_track_matching():
    kaggle_df = load_kaggle_data()
    match = match_track_to_kaggle("NOKIA", "Drake", kaggle_df)
    assert match is not None
    assert match['artist_name'] == "Drake"

# Test composite feature calculation
def test_mood_score():
    row = {'valence': 0.8, 'energy': 0.7, 'acousticness': 0.2}
    mood = (row['valence'] * 0.5) + (row['energy'] * 0.3) - (row['acousticness'] * 0.2)
    assert 0 <= mood <= 1
```

### Integration Tests
- Test OAuth flow end-to-end
- Test API rate limiting handling
- Test data fetching with mock responses

### User Acceptance Testing
- Test with all 3 team members
- Verify multi-user session isolation
- Check mobile responsiveness

---

## Success Metrics

**Technical Metrics**:
- Authentication success rate > 95%
- Page load time < 3 seconds
- API error rate < 1%
- Data refresh time < 10 seconds

**User Metrics**:
- 3 team members + 10 beta testers authenticated
- 50+ tracks analyzed per user
- 5+ visualizations implemented
- 80%+ track matching success rate (Spotify → Kaggle)

**Business Metrics**:
- Insights not available in Spotify Wrapped
- Actionable recommendations provided
- Weekly engagement (users return to check updates)

---

## Development Timeline

**Week 7** (Current):
- ✅ Spotify OAuth authentication
- ✅ API endpoint testing
- ✅ Kaggle dataset integration strategy
- 🔄 Basic Streamlit app structure

**Week 8**:
- Recent listening timeline visualization
- Top tracks evolution charts
- Temporal pattern analysis
- Playlist overview dashboard

**Week 9**:
- Kaggle track matching implementation
- Mood trajectory visualization
- Context classification
- Audio feature distributions

**Week 10**:
- Machine learning models (Random Forest, XGBoost)
- Recommendation engine
- Final polish and deployment
- Documentation and presentation

---

## References & Resources

### Spotify API Documentation
- [Web API Reference](https://developer.spotify.com/documentation/web-api)
- [Authorization Guide](https://developer.spotify.com/documentation/web-api/concepts/authorization)
- [Spotipy Library](https://spotipy.readthedocs.io/)

### Streamlit Resources
- [Streamlit Docs](https://docs.streamlit.io/)
- [Session State Guide](https://docs.streamlit.io/library/api-reference/session-state)
- [Caching Guide](https://docs.streamlit.io/library/advanced-features/caching)

### Data Visualization
- [Plotly Python](https://plotly.com/python/)
- [Seaborn Gallery](https://seaborn.pydata.org/examples/index.html)

### Machine Learning
- [scikit-learn User Guide](https://scikit-learn.org/stable/user_guide.html)
- [XGBoost Documentation](https://xgboost.readthedocs.io/)

---

## Getting Started

**Immediate Next Steps**:

1. **Set up Streamlit environment**
   ```bash
   pip install streamlit plotly spotipy python-dotenv pandas
   streamlit run app/main.py
   ```

2. **Implement OAuth authentication**
   - Create session-based cache handler
   - Add "Connect Spotify" button
   - Handle redirect callback

3. **Build first visualization**
   - Fetch recently played tracks
   - Display as timeline chart
   - Add basic metrics (total tracks, unique artists)

4. **Test with team members**
   - Add all 3 users to Spotify app allowlist
   - Verify multi-user session isolation
   - Gather feedback on UX

**Good luck building! 🎵**
