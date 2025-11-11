# Deep User Analytics Integration Guide

This guide shows how to integrate the automatic data collection and Deep User page into your existing Streamlit app.

## Setup Steps

### 1. Install Dependencies

```bash
pip install boto3 pyarrow
# or reinstall all requirements
pip install -r requirements-mac.txt
```

### 2. Configure Cloudflare R2 Credentials

Add to your `.env` file:

```env
# Cloudflare R2 Storage
R2_ACCESS_KEY_ID=your_access_key_here
R2_SECRET_ACCESS_KEY=your_secret_key_here
R2_BUCKET_NAME=ime565spotify

# If you have a custom domain configured (recommended):
R2_CUSTOM_DOMAIN=s3.diferdinando.com

# OR if no custom domain, use your account ID:
# CLOUDFLARE_ACCOUNT_ID=24df8bb5d20dca402dfc277d4c38cc80
```

**Getting R2 Credentials:**
1. Go to Cloudflare Dashboard → R2
2. Your bucket is already created: `ime565spotify` ✓
3. Go to "Manage R2 API Tokens"
4. Create new API token with **Admin Read & Write** permissions
5. Copy the Access Key ID and Secret Access Key
6. Use your custom domain `s3.diferdinando.com` in the config (already set up in R2)

### 3. Verify R2 Bucket Setup

Your R2 bucket is already configured:
- ✓ Bucket name: `ime565spotify`
- ✓ Location: Western North America (WNAM)
- ✓ Public Access: Disabled (correct - app uses API)
- ✓ Custom domain: `s3.diferdinando.com`

**Important**: Make sure your R2 API token has Admin Read & Write permissions for the bucket.

### 4. Integration into `app/main.py`

#### Step A: Add Imports

At the top of `spotify_dashboard.py`, add:

```python
# Import data collection functions
from app.func.data_collection import collect_snapshot, save_snapshot_to_s3
from app.func.s3_storage import get_bucket_name

# Import Deep User page
from app.pages.deep_user import show_deep_user_page
```

#### Step B: Trigger Data Collection on Login

Find your authentication success logic (after user successfully authenticates). Add this:

```python
# After successful authentication
if st.session_state.token_info:
    sp = get_spotify_client(st.session_state.token_info)
    profile = fetch_user_profile(sp)
    user_id = profile.get('id')

    # Check if we should collect data this session
    if 'data_collected_this_session' not in st.session_state:
        st.session_state.data_collected_this_session = False

    # Collect data once per session
    if not st.session_state.data_collected_this_session and get_bucket_name():
        with st.spinner("📸 Collecting listening snapshot..."):
            try:
                snapshot_data = collect_snapshot(sp, user_id)
                save_snapshot_to_s3(snapshot_data)
                st.session_state.data_collected_this_session = True
                st.success("✓ Snapshot saved!")
            except Exception as e:
                st.warning(f"Could not save snapshot: {e}")
```

#### Step C: Add Deep User Page to Navigation

Find your page navigation radio button. Add "Deep User" option:

```python
# In sidebar navigation
page = st.radio(
    "Select Page",
    ["Dashboard", "Advanced Analytics", "Recent Listening", "Top Tracks", "Playlists", "Deep User"],
    label_visibility="collapsed"
)
```

#### Step D: Add Deep User Page Route

In your main content area where pages are routed:

```python
# Main content area
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
elif page == "Deep User":
    show_deep_user_page(sp, profile.get('id'))
```

## File Structure

After integration, your `app/` directory should look like:

```
app/
├── main.py                      # Main Streamlit app (modified)
├── func/
│   ├── __init__.py
│   ├── s3_storage.py            # NEW: R2 upload/download
│   └── data_collection.py       # NEW: Snapshot collection
└── pages/
    ├── __init__.py
    └── deep_user.py             # NEW: Deep User analytics page
```

## Data Storage Structure in R2

Your R2 bucket will be organized as:

```
spotify-analytics-data/
└── users/
    ├── user_id_1/
    │   └── snapshots/
    │       ├── 2025-01-11T10-30-00_recent_tracks.parquet
    │       ├── 2025-01-11T10-30-00_top_tracks_short.parquet
    │       ├── 2025-01-11T10-30-00_top_tracks_medium.parquet
    │       ├── 2025-01-11T10-30-00_top_artists_short.parquet
    │       ├── 2025-01-11T10-30-00_metrics.parquet
    │       └── ... (more snapshots over time)
    ├── user_id_2/
    │   └── snapshots/
    └── user_id_3/
        └── snapshots/
```

## Testing

1. **Start the app:**
   ```bash
   streamlit run app/main.py
   ```

2. **Authenticate with Spotify**
   - You should see "📸 Collecting listening snapshot..." message
   - After collection: "✓ Snapshot saved!"

3. **Visit Deep User page**
   - Navigate to "Deep User" in sidebar
   - First visit will show "No historical data" message
   - After 2+ logins, you'll see trends and charts

4. **Verify data in R2**
   - Go to Cloudflare R2 Dashboard
   - Check bucket `spotify-analytics-data`
   - You should see `users/{your_spotify_id}/snapshots/` with .parquet files

## Troubleshooting

### "R2 credentials not found"
- Check `.env` file has all 4 R2 variables
- Restart Streamlit app after adding credentials

### "Failed to upload to S3"
- Verify R2 API token has read/write permissions
- Check bucket name matches `.env` exactly
- Verify Account ID is correct (12-digit number)

### "No such key" when loading data
- This is normal on first use (no historical data yet)
- Collect 2+ snapshots by logging in multiple times
- Charts will appear after you have time-series data

### boto3 import errors
- Run: `pip install boto3 pyarrow`
- Check Python environment is activated

## Optional: Manual Data Collection Button

If you want users to manually trigger data collection, add this to sidebar:

```python
# In sidebar, after authentication
if st.button("📸 Capture Snapshot Now"):
    with st.spinner("Collecting data..."):
        snapshot_data = collect_snapshot(sp, user_id)
        if save_snapshot_to_s3(snapshot_data):
            st.success("Snapshot saved!")
            st.cache_data.clear()  # Refresh cached data
```

## What Gets Collected

Every snapshot includes:
- **50 recently played tracks** with full audio features
- **Top 50 tracks** (short/medium/long term) with audio features
- **Top 50 artists** (short/medium/long term) with genres
- **Computed metrics**: diversity scores, average mood, energy, context distributions

**Estimated storage per user:**
- ~100KB per snapshot
- ~3MB per month (daily logins)
- ~36MB per year

## Next Steps

After setup:
1. **Collect data**: Use the app regularly (daily/weekly)
2. **Wait 1-2 weeks**: More snapshots = better trend analysis
3. **Explore Deep User page**: View your music taste evolution
4. **Team comparison** (Phase 2): Compare with team members' data

## Privacy Note

- Data is only stored for authenticated users (you and your team)
- R2 bucket is private (not publicly accessible)
- No data sharing outside your team
- You can delete snapshots anytime from R2 dashboard
