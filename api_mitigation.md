# API Rate Limiting Mitigation Strategy

## Objective
Transform initial data syncing from a technical bottleneck into an engaging onboarding experience. This is a **mandatory step** in the authentication flow that collects baseline data for the project before users can access the dashboard.

## User Flow

**Authentication → Data Sync → Dashboard Access**

1. User clicks "Authenticate with Spotify" on home page
2. Credentials provided via `.env` or manual input
3. OAuth callback completes authentication
4. **Redirect to mandatory data sync/loading screen** (this is where we collect data)
5. Once collection completes, user gains access to all dashboard pages

**Important:** This is NOT an optional snapshot feature - it's the required onboarding flow that happens once during first-time setup and syncs baseline data for the entire project.

## Technical Considerations

### Implementation Options
**Option A: Streamlit Page (Recommended)**
- Use a dedicated Streamlit page (e.g., `app/pages/0_Syncing.py` or `app/Sync.py`)
- After OAuth callback, redirect to this page automatically
- Use `st.session_state` to track sync completion
- Block access to other pages until sync completes
- Pros: Consistent UI, easier state management, native Streamlit components
- Cons: Page refresh during OAuth callback handling

**Option B: Non-Streamlit Page**
- Custom HTML/JavaScript page served during OAuth callback
- Redirect back to Streamlit after completion
- Pros: More control over loading UX, no page refresh issues
- Cons: Additional server setup, harder to maintain consistency

**Recommendation:** Start with Option A (Streamlit page) for simplicity and consistency with existing architecture.

## Core Requirements

### Data Collection
- Restore full data capture (50 items per endpoint, not 20)
- Implement exponential backoff with retry logic for 429 errors
- Add intelligent delays between batches (0.5-1s) to prevent rate limiting
- Gracefully handle and retry failed requests without user interruption

### User Experience During Sync
Create an engaging loading screen that users see immediately after authentication:

**Interactive Elements:**
- Mini-game (e.g., Spotify music quiz, artist matching game, or rhythm-based clicking game)
- Rotating Spotify facts dataset (~1000 unique facts about listening habits, artist trivia, music statistics)
- Progress indicator showing collection stages (Recent Tracks → Top Artists → Audio Features → Metrics)
- Fun loading animations synced to collection progress

**Goal:** Make 60-120 second initial sync feel like an engaging onboarding experience rather than a tedious wait. Users should want to play the game and read facts while the backend handles all API complexity with proper rate limiting delays.
