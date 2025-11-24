# Temporal Features Guide

## Overview

This guide documents all temporal (time-based) features available in the Spotify Analytics dashboard for advanced analytics and visualization.

---

## Temporal Features Available

### Automatically Extracted from `played_at` Timestamp

When data is processed through `data_processing.py`, the following temporal features are automatically extracted from the `played_at` timestamp:

#### Hour-Level Features
- **`hour`** (int, 0-23): Hour of day in 24-hour format
  - Example: `14` for 2:00 PM
  - Use for: Hourly listening patterns, peak listening times

#### Day-Level Features
- **`day_of_week`** (string): Full day name
  - Values: Monday, Tuesday, Wednesday, Thursday, Friday, Saturday, Sunday
  - Use for: Weekday vs weekend patterns, day-of-week heatmaps

- **`day_of_month`** (int, 1-31): Day of the month
  - Example: `23` for the 23rd
  - Use for: Monthly activity patterns, paycheck day analysis

- **`day_of_year`** (int, 1-365/366): Day number within the year
  - Example: `327` for November 23rd
  - Use for: Seasonal trends, year-long patterns

- **`date`** (date): Date only (no time component)
  - Format: YYYY-MM-DD
  - Use for: Daily aggregations, date-based filtering

- **`is_weekend`** (bool): Whether the day is Saturday or Sunday
  - Values: True/False
  - Use for: Weekend vs weekday comparisons

#### Week-Level Features
- **`week_of_year`** (int, 1-52): ISO week number
  - Example: `47` for the 47th week of the year
  - Use for: Weekly trends, week-over-week comparisons

#### Month-Level Features
- **`month`** (int, 1-12): Month number
  - Values: 1=January, 2=February, ..., 12=December
  - Use for: Monthly aggregations, seasonal analysis

- **`month_name`** (string): Full month name
  - Values: January, February, March, ..., December
  - Use for: Human-readable month displays

#### Quarter-Level Features
- **`quarter`** (int, 1-4): Calendar quarter
  - Values: 1=Q1 (Jan-Mar), 2=Q2 (Apr-Jun), 3=Q3 (Jul-Sep), 4=Q4 (Oct-Dec)
  - Use for: Quarterly business analysis, seasonal patterns

#### Year-Level Features
- **`year`** (int): Four-digit year
  - Example: `2025`
  - Use for: Year-over-year comparisons, long-term trends

#### Season Features
- **`season`** (string): Meteorological season
  - Values: Winter (Dec-Feb), Spring (Mar-May), Summer (Jun-Aug), Fall (Sep-Nov)
  - Use for: Seasonal listening habits, mood changes by season

---

## Using Temporal Features in Analysis

### Example 1: Hourly Listening Patterns

```python
import pandas as pd
from app.func.data_processing import process_recent_tracks
from app.func.visualizations import plot_listening_by_hour

# Process data (temporal features auto-extracted)
recent_df = process_recent_tracks(recent_data)

# Visualize hourly pattern
plot_listening_by_hour(recent_df)

# Or manually aggregate
hourly_listens = recent_df.groupby('hour')['track_id'].count()
peak_hour = hourly_listens.idxmax()
print(f"Peak listening hour: {peak_hour}:00")
```

### Example 2: Weekday vs Weekend Analysis

```python
# Compare weekday vs weekend listening
weekend_tracks = recent_df[recent_df['is_weekend'] == True]
weekday_tracks = recent_df[recent_df['is_weekend'] == False]

print(f"Weekend tracks: {len(weekend_tracks)}")
print(f"Weekday tracks: {len(weekday_tracks)}")

# Average energy by weekend/weekday
if 'energy' in recent_df.columns:
    weekend_energy = weekend_tracks['energy'].mean()
    weekday_energy = weekday_tracks['energy'].mean()
    print(f"Weekend energy: {weekend_energy:.2f}")
    print(f"Weekday energy: {weekday_energy:.2f}")
```

### Example 3: Monthly Trends

```python
# Group by month for trend analysis
monthly_counts = recent_df.groupby(['year', 'month_name'])['track_id'].count()

# Or use the datetime_utils helper
from app.func.datetime_utils import aggregate_by_month
monthly_df = aggregate_by_month(recent_df, 'played_at', 'track_id')
```

### Example 4: Seasonal Music Preferences

```python
# Analyze genre preferences by season
seasonal_genres = recent_df.groupby(['season', 'track_genre']).size()

# Which genres are most popular in summer?
summer_genres = recent_df[recent_df['season'] == 'Summer']['track_genre'].value_counts().head(10)
```

### Example 5: Day-of-Week × Hour Heatmap

```python
from app.func.visualizations import plot_temporal_heatmap

# This function uses hour and day_of_week features
plot_temporal_heatmap(recent_df)
```

---

## Datetime Utilities Module

A new `datetime_utils.py` module provides standardized datetime formatting and aggregation helpers.

### Standardized Datetime Formats

```python
from app.func.datetime_utils import FORMATS, format_datetime

# Available formats:
# 'iso8601': Full ISO8601 with timezone
# 'display_datetime': Human-readable (2025-11-23 14:30)
# 'display_date': Date only (2025-11-23)
# 'display_time': Time only (14:30:45)
# 'filename_datetime': Compact for filenames (20251123_143045)
# 'filename_date': Date for filenames (20251123)
# 'month_year': Month Year (November 2025)
# 'short_month_year': Short Month Year (Nov 2025)
# 'year_month': ISO month (2025-11)

# Usage
from datetime import datetime
dt = datetime.now()
formatted = format_datetime(dt, 'display_datetime')
print(formatted)  # "2025-11-23 14:30"
```

### Standardized Axis Labels

```python
from app.func.datetime_utils import get_axis_label, AXIS_LABELS

# Get standardized labels for charts
hour_label = get_axis_label('hour')  # "Hour of Day"
day_label = get_axis_label('day_of_week')  # "Day of Week"
month_label = get_axis_label('month_name')  # "Month"

# Available labels:
# played_at → "Listening Time"
# timestamp → "Date"
# hour → "Hour of Day"
# day_of_week → "Day of Week"
# day_of_month → "Day of Month"
# week_of_year → "Week of Year"
# month → "Month"
# month_name → "Month"
# quarter → "Quarter"
# year → "Year"
# season → "Season"
# tracks → "Number of Tracks"
```

### Aggregation Helpers

```python
from app.func.datetime_utils import (
    aggregate_by_hour,
    aggregate_by_day_of_week,
    aggregate_by_month,
    aggregate_by_date
)

# Hourly aggregation
hourly_df = aggregate_by_hour(recent_df, 'played_at', 'track_id')
# Returns: DataFrame with 'hour' (0-23) and 'count'

# Daily aggregation (with proper day ordering)
daily_df = aggregate_by_day_of_week(recent_df, 'played_at', 'track_id')
# Returns: DataFrame with 'day_of_week' (Monday-Sunday) and 'count'

# Monthly aggregation
monthly_df = aggregate_by_month(recent_df, 'played_at', 'track_id')
# Returns: DataFrame with 'month' (YYYY-MM format) and 'count'

# Date-level aggregation
date_df = aggregate_by_date(recent_df, 'played_at', 'track_id')
# Returns: DataFrame with 'date' and 'count'
```

### Time Ago Utilities

```python
from app.func.datetime_utils import time_ago_string, get_freshness_indicator

# Human-readable "time ago"
from datetime import datetime, timezone
last_sync = datetime.now(timezone.utc)
time_str = time_ago_string(last_sync)
print(time_str)  # "2 hours ago", "3 days ago", etc.

# Freshness indicator for sync status
emoji, color, message = get_freshness_indicator(last_sync)
print(f"{emoji} {message}")  # "🟢 Fresh (synced 2 hours ago)"
```

---

## Best Practices

### 1. Always Use Standardized Labels

```python
# Good - uses standardized labels
fig = px.line(
    df,
    x='played_at',
    y='count',
    labels={
        'played_at': datetime_utils.get_axis_label('played_at'),
        'count': datetime_utils.get_axis_label('tracks')
    }
)

# Avoid - hard-coded labels
labels={'played_at': 'Time', 'count': 'Tracks'}
```

### 2. Use Day Ordering for Day-of-Week Charts

```python
# Good - ordered Monday-Sunday
day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
df['day_of_week'] = pd.Categorical(df['day_of_week'], categories=day_order, ordered=True)

# Or use the aggregation helper (handles ordering automatically)
daily_df = aggregate_by_day_of_week(df, 'played_at', 'track_id')
```

### 3. Ensure Timezone Awareness

All datetime operations use UTC timezone via `timezone.utc`:

```python
from datetime import datetime, timezone

# Good - timezone aware
now = datetime.now(timezone.utc)

# Avoid - naive datetime
now = datetime.now()
```

### 4. Use Aggregation Helpers

```python
# Good - uses helper (handles edge cases)
from app.func.datetime_utils import aggregate_by_hour
hourly_df = aggregate_by_hour(df, 'played_at', 'track_id')

# Avoid - manual aggregation (may miss hours with 0 tracks)
hourly_df = df.groupby(df['played_at'].dt.hour)['track_id'].count()
```

---

## Examples of Analytics You Can Now Build

### 1. Peak Listening Times
- Hour-of-day distribution
- Day-of-week patterns
- Weekend vs weekday behavior

### 2. Monthly Trends
- Tracks played per month
- Genre shifts by month
- Discovery rate (new artists per month)

### 3. Seasonal Analysis
- Summer vs winter music preferences
- Energy/valence changes by season
- Genre diversity by season

### 4. Long-Term Trends
- Year-over-year listening growth
- Artist loyalty over quarters
- Evolution of mainstream score

### 5. Activity Patterns
- Busiest day of the month
- Listening streaks (consecutive days)
- Consistency score (variance in daily listens)

### 6. Context Detection
- Work hours music (9 AM - 5 PM on weekdays)
- Weekend party music (Friday/Saturday nights)
- Morning commute patterns (7-9 AM on weekdays)

---

## Where Temporal Features Are Used

### Dashboard Pages

1. **Dashboard (1_Dashboard.py)**
   - Temporal Patterns section
   - Hour-of-day bar chart
   - Day-of-week bar chart
   - Hour × Day heatmap

2. **Recent Listening (3_Recent_Listening.py)**
   - Timeline scatter plot with `played_at`
   - Formatted timestamps in data table

3. **Deep User Analytics (6_Deep_User.py)**
   - Artist evolution over time
   - Genre distribution by month
   - Daily listening activity
   - Hour × Day heatmap
   - Metrics time series

### Visualization Functions

- `plot_temporal_heatmap()` - Uses `hour` and `day_of_week`
- `plot_listening_by_hour()` - Uses `hour`
- `plot_listening_by_day()` - Uses `day_of_week`
- `plot_recent_timeline()` - Uses `played_at`

---

## File Locations

- **Temporal feature extraction**: `app/func/data_processing.py` (Lines 65-89)
- **Datetime utilities**: `app/func/datetime_utils.py`
- **Visualization functions**: `app/func/visualizations.py`
- **Dashboard implementations**: `app/pages/*.py`

---

## Future Enhancements

Potential additions for Phase 2/3:

1. **Business day classification** (excludes holidays)
2. **Time-of-day buckets** (Morning, Afternoon, Evening, Night)
3. **Listening session detection** (continuous listening periods)
4. **Temporal anomaly detection** (unusual listening times)
5. **Predictive models** using temporal features
6. **Custom date ranges** for comparisons
7. **Rolling averages** (7-day, 30-day windows)

---

## Questions?

For implementation details, see:
- `CLAUDE.md` - Main development guide
- `DATA_ARCHITECTURE_RECOMMENDATION_REVISED.md` - Data storage strategy
- Source code in `app/func/` directory

Last Updated: November 23, 2025
