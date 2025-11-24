"""
Datetime utilities for consistent temporal formatting across dashboards.

Provides standardized datetime formats, axis labels, and temporal aggregation helpers.
"""

from datetime import datetime, timezone
import pandas as pd


# ============================================================================
# STANDARD DATETIME FORMATS
# ============================================================================

# Common datetime string formats
FORMATS = {
    'iso8601': '%Y-%m-%dT%H:%M:%S%z',  # Full ISO8601 with timezone
    'display_datetime': '%Y-%m-%d %H:%M',  # Human-readable (2025-11-23 14:30)
    'display_date': '%Y-%m-%d',  # Date only (2025-11-23)
    'display_time': '%H:%M:%S',  # Time only (14:30:45)
    'filename_datetime': '%Y%m%d_%H%M%S',  # Compact for filenames (20251123_143045)
    'filename_date': '%Y%m%d',  # Date for filenames (20251123)
    'month_year': '%B %Y',  # Month Year (November 2025)
    'short_month_year': '%b %Y',  # Short Month Year (Nov 2025)
    'year_month': '%Y-%m',  # ISO month (2025-11)
}


def format_datetime(dt, format_name='display_datetime'):
    """
    Format datetime using standardized format.

    Args:
        dt: datetime object or timestamp string
        format_name: One of the format names from FORMATS dict

    Returns:
        Formatted datetime string
    """
    if isinstance(dt, str):
        dt = pd.to_datetime(dt)

    return dt.strftime(FORMATS.get(format_name, FORMATS['display_datetime']))


def parse_datetime(dt_string, format_name='iso8601'):
    """
    Parse datetime string using standardized format.

    Args:
        dt_string: String to parse
        format_name: Format to use for parsing (default: iso8601)

    Returns:
        datetime object
    """
    if format_name == 'iso8601' or 'T' in dt_string:
        # Use pandas for robust ISO8601 parsing
        return pd.to_datetime(dt_string, format='ISO8601')

    return datetime.strptime(dt_string, FORMATS.get(format_name))


# ============================================================================
# AXIS LABELS FOR VISUALIZATIONS
# ============================================================================

# Standardized axis labels for temporal visualizations
AXIS_LABELS = {
    # Time-based labels
    'played_at': 'Listening Time',
    'timestamp': 'Date',
    'datetime': 'Date & Time',

    # Hour labels
    'hour': 'Hour of Day',
    'hour_24h': 'Hour (24h format)',
    'hour_12h': 'Hour (12h format)',

    # Day labels
    'day_of_week': 'Day of Week',
    'day_of_month': 'Day of Month',
    'day_of_year': 'Day of Year',
    'date': 'Date',

    # Week labels
    'week_of_year': 'Week of Year',
    'week': 'Week',

    # Month labels
    'month': 'Month',
    'month_name': 'Month',
    'month_year': 'Month & Year',

    # Quarter labels
    'quarter': 'Quarter',

    # Year labels
    'year': 'Year',

    # Season labels
    'season': 'Season',

    # Count/metric labels
    'tracks': 'Number of Tracks',
    'count': 'Count',
    'plays': 'Plays',
    'listens': 'Listens',
}


def get_axis_label(column_name, fallback=None):
    """
    Get standardized axis label for a column.

    Args:
        column_name: Name of the column/feature
        fallback: Fallback label if not found (default: titleized column_name)

    Returns:
        Axis label string
    """
    if column_name in AXIS_LABELS:
        return AXIS_LABELS[column_name]

    if fallback:
        return fallback

    # Fallback: titleize and replace underscores
    return column_name.replace('_', ' ').title()


# ============================================================================
# TEMPORAL AGGREGATION HELPERS
# ============================================================================

def aggregate_by_hour(df, datetime_col='played_at', count_col='track_id'):
    """
    Aggregate data by hour of day (0-23).

    Args:
        df: DataFrame with datetime column
        datetime_col: Name of datetime column
        count_col: Column to count

    Returns:
        DataFrame with hour and count
    """
    if datetime_col not in df.columns:
        raise ValueError(f"Column '{datetime_col}' not found in DataFrame")

    hour_counts = df.groupby(df[datetime_col].dt.hour)[count_col].count()
    hour_counts = hour_counts.reindex(range(24), fill_value=0)

    return pd.DataFrame({
        'hour': hour_counts.index,
        'count': hour_counts.values
    })


def aggregate_by_day_of_week(df, datetime_col='played_at', count_col='track_id'):
    """
    Aggregate data by day of week (Monday-Sunday).

    Args:
        df: DataFrame with datetime column
        datetime_col: Name of datetime column
        count_col: Column to count

    Returns:
        DataFrame with day_of_week and count (ordered Monday-Sunday)
    """
    if datetime_col not in df.columns:
        raise ValueError(f"Column '{datetime_col}' not found in DataFrame")

    day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    day_counts = df.groupby(df[datetime_col].dt.day_name())[count_col].count()
    day_counts = day_counts.reindex(day_order, fill_value=0)

    return pd.DataFrame({
        'day_of_week': day_counts.index,
        'count': day_counts.values
    })


def aggregate_by_month(df, datetime_col='played_at', count_col='track_id'):
    """
    Aggregate data by month.

    Args:
        df: DataFrame with datetime column
        datetime_col: Name of datetime column
        count_col: Column to count

    Returns:
        DataFrame with month (YYYY-MM format) and count
    """
    if datetime_col not in df.columns:
        raise ValueError(f"Column '{datetime_col}' not found in DataFrame")

    df_copy = df.copy()
    df_copy['month'] = df_copy[datetime_col].dt.to_period('M').astype(str)
    month_counts = df_copy.groupby('month')[count_col].count().reset_index()
    month_counts.columns = ['month', 'count']

    return month_counts


def aggregate_by_date(df, datetime_col='played_at', count_col='track_id'):
    """
    Aggregate data by date (daily).

    Args:
        df: DataFrame with datetime column
        datetime_col: Name of datetime column
        count_col: Column to count

    Returns:
        DataFrame with date and count
    """
    if datetime_col not in df.columns:
        raise ValueError(f"Column '{datetime_col}' not found in DataFrame")

    df_copy = df.copy()
    df_copy['date'] = df_copy[datetime_col].dt.date
    date_counts = df_copy.groupby('date')[count_col].count().reset_index()
    date_counts.columns = ['date', 'count']
    date_counts['date'] = pd.to_datetime(date_counts['date'])

    return date_counts


# ============================================================================
# TIME AGO UTILITIES
# ============================================================================

def time_ago_string(dt, now=None):
    """
    Convert datetime to human-readable "time ago" string.

    Args:
        dt: datetime object or ISO8601 string
        now: Reference datetime (default: current UTC time)

    Returns:
        String like "2 hours ago", "3 days ago", etc.
    """
    if now is None:
        now = datetime.now(timezone.utc)

    if isinstance(dt, str):
        dt = pd.to_datetime(dt, format='ISO8601')

    # Ensure timezone-aware
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    if now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)

    delta = now - dt
    seconds = delta.total_seconds()

    if seconds < 60:
        return "just now"
    elif seconds < 3600:
        minutes = int(seconds / 60)
        return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
    elif seconds < 86400:
        hours = int(seconds / 3600)
        return f"{hours} hour{'s' if hours != 1 else ''} ago"
    elif seconds < 604800:
        days = int(seconds / 86400)
        return f"{days} day{'s' if days != 1 else ''} ago"
    elif seconds < 2592000:  # ~30 days
        weeks = int(seconds / 604800)
        return f"{weeks} week{'s' if weeks != 1 else ''} ago"
    elif seconds < 31536000:  # ~365 days
        months = int(seconds / 2592000)
        return f"{months} month{'s' if months != 1 else ''} ago"
    else:
        years = int(seconds / 31536000)
        return f"{years} year{'s' if years != 1 else ''} ago"


def get_freshness_indicator(last_sync, now=None):
    """
    Get freshness indicator with emoji for sync status.

    Args:
        last_sync: datetime or ISO8601 string of last sync
        now: Reference datetime (default: current UTC time)

    Returns:
        Tuple of (emoji, color, message)
    """
    if now is None:
        now = datetime.now(timezone.utc)

    if isinstance(last_sync, str):
        last_sync = pd.to_datetime(last_sync, format='ISO8601')

    # Ensure timezone-aware
    if last_sync.tzinfo is None:
        last_sync = last_sync.replace(tzinfo=timezone.utc)
    if now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)

    delta = now - last_sync
    hours_ago = delta.total_seconds() / 3600

    if hours_ago < 1:
        return '🟢', '#1DB954', f"Fresh (synced {time_ago_string(last_sync, now)})"
    elif hours_ago < 12:
        return '🟢', '#1DB954', f"Fresh (synced {time_ago_string(last_sync, now)})"
    elif hours_ago < 24:
        return '🟡', '#FFB000', f"Recent (synced {time_ago_string(last_sync, now)})"
    else:
        return '🔴', '#FF4444', f"Stale (synced {time_ago_string(last_sync, now)})"


# ============================================================================
# TEMPORAL FEATURE EXTRACTION
# ============================================================================

def extract_all_temporal_features(df, datetime_col='played_at'):
    """
    Extract all temporal features from a datetime column.

    This is a convenience function that adds all temporal features
    to a DataFrame in one call.

    Args:
        df: DataFrame with datetime column
        datetime_col: Name of datetime column to extract from

    Returns:
        DataFrame with added temporal feature columns
    """
    if datetime_col not in df.columns:
        raise ValueError(f"Column '{datetime_col}' not found in DataFrame")

    df = df.copy()

    # Ensure datetime
    if not pd.api.types.is_datetime64_any_dtype(df[datetime_col]):
        df[datetime_col] = pd.to_datetime(df[datetime_col])

    # Time features
    df['hour'] = df[datetime_col].dt.hour
    df['minute'] = df[datetime_col].dt.minute

    # Day features
    df['day_of_week'] = df[datetime_col].dt.day_name()
    df['day_of_month'] = df[datetime_col].dt.day
    df['day_of_year'] = df[datetime_col].dt.dayofyear
    df['date'] = df[datetime_col].dt.date

    # Week features
    df['week_of_year'] = df[datetime_col].dt.isocalendar().week
    df['is_weekend'] = df[datetime_col].dt.dayofweek >= 5

    # Month features
    df['month'] = df[datetime_col].dt.month
    df['month_name'] = df[datetime_col].dt.month_name()

    # Quarter and year features
    df['quarter'] = df[datetime_col].dt.quarter
    df['year'] = df[datetime_col].dt.year

    # Season
    def get_season(month):
        if month in [12, 1, 2]:
            return 'Winter'
        elif month in [3, 4, 5]:
            return 'Spring'
        elif month in [6, 7, 8]:
            return 'Summer'
        else:
            return 'Fall'

    df['season'] = df['month'].apply(get_season)

    return df
