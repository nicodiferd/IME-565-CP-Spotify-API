# Spotify Analytics Data Directory

## Required Datasets

Download the following datasets from Kaggle and place them in this directory:

### 1. Spotify Tracks Dataset (~114k tracks)
**URL**: https://www.kaggle.com/datasets/maharshipandya/-spotify-tracks-dataset
**Filename**: `spotify_tracks.csv` or `dataset.csv`
**Features**:
- Audio features: danceability, energy, valence, tempo, acousticness, instrumentalness, speechiness, liveness
- Track metadata: track_id, track_name, artists, album_name, track_genre
- Popularity metrics

### 2. Top Spotify Songs 2023
**URL**: https://www.kaggle.com/datasets/nelgiriyewithana/top-spotify-songs-2023
**Filename**: `spotify-2023.csv`
**Features**:
- Track details with streaming statistics
- Audio features
- Release dates and popularity metrics

### 3. Alternative: Spotify Dataset 1921-2020 (160k+ tracks)
**URL**: https://www.kaggle.com/datasets/yamaerenay/spotify-dataset-19212020-600k-tracks
**Filename**: `tracks.csv`
**Features**:
- Comprehensive historical dataset
- All audio features
- Temporal coverage from 1921-2020

## File Structure

Place downloaded CSV files directly in this directory:
```
data/
├── README.md (this file)
├── spotify_tracks.csv
├── spotify-2023.csv
├── tracks.csv (alternative)
└── (any other Spotify datasets)
```

## Notes

- You only need ONE of the main datasets to get started
- Files should be in CSV format
- The notebook will auto-detect common filenames
- Keep original filenames or rename to match the notebook expectations
