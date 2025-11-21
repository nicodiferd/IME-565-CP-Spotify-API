"""
Utility functions for Spotify Analytics Dashboard
Exports all functions from function modules for easy importing
"""

# Authentication and credentials
from .auth import (
    initialize_session_state,
    get_credentials,
    validate_credentials,
    show_credential_configuration,
    get_spotify_oauth,
    authenticate,
    get_spotify_client
)

# Data fetching
from .data_fetching import (
    fetch_user_profile,
    fetch_recently_played,
    fetch_top_tracks,
    fetch_top_artists,
    fetch_playlists,
    fetch_audio_features
)

# Data processing
from .data_processing import (
    process_recent_tracks,
    process_top_tracks,
    calculate_diversity_score
)

# Visualizations
from .visualizations import (
    plot_audio_features_radar,
    plot_mood_distribution,
    plot_context_breakdown,
    plot_energy_valence_scatter,
    plot_temporal_heatmap,
    plot_recent_timeline,
    plot_listening_by_hour,
    plot_listening_by_day,
    plot_top_artists
)

# UI components
from .ui_components import (
    apply_page_config,
    get_custom_css
)

# Page authentication wrapper
from .page_auth import require_auth

# S3 storage (already exists)
from .s3_storage import *

# Data collection
from .data_collection import (
    collect_comprehensive_snapshot,
    should_refresh_data,
    collect_snapshot,  # Legacy function for backwards compatibility
    get_user_snapshot_count
)

# Dashboard helpers
from .dashboard_helpers import (
    load_current_snapshot,
    handle_missing_data,
    display_sync_status,
    get_recent_tracks,
    get_top_tracks,
    get_top_artists,
    get_metrics
)


__all__ = [
    # Auth
    'initialize_session_state',
    'get_credentials',
    'validate_credentials',
    'show_credential_configuration',
    'get_spotify_oauth',
    'authenticate',
    'get_spotify_client',
    'require_auth',  # Multi-page auth wrapper
    # Data fetching
    'fetch_user_profile',
    'fetch_recently_played',
    'fetch_top_tracks',
    'fetch_top_artists',
    'fetch_playlists',
    'fetch_audio_features',
    # Data processing
    'process_recent_tracks',
    'process_top_tracks',
    'calculate_diversity_score',
    # Visualizations
    'plot_audio_features_radar',
    'plot_mood_distribution',
    'plot_context_breakdown',
    'plot_energy_valence_scatter',
    'plot_temporal_heatmap',
    'plot_recent_timeline',
    'plot_listening_by_hour',
    'plot_listening_by_day',
    'plot_top_artists',
    # UI components
    'apply_page_config',
    'get_custom_css',
    # Data collection
    'collect_comprehensive_snapshot',
    'should_refresh_data',
    'collect_snapshot',  # Legacy
    'get_user_snapshot_count',
    # Dashboard helpers
    'load_current_snapshot',
    'handle_missing_data',
    'display_sync_status',
    'get_recent_tracks',
    'get_top_tracks',
    'get_top_artists',
    'get_metrics',
]
