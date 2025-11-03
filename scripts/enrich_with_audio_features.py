"""
Audio Features Enrichment Pipeline
Fetches audio features for collected tracks and merges with Kaggle database
"""

import json
import time
from pathlib import Path
from datetime import datetime
import pandas as pd
import numpy as np
from spotify_auth import SpotifyAuthenticator


class AudioFeaturesEnricher:
    """
    Enriches track data with audio features from Spotify API and Kaggle database
    """

    def __init__(self, user_name, kaggle_db_path='data/processed_spotify_data.csv',
                 raw_data_dir='data/raw', output_dir='data/processed'):
        """
        Initialize audio features enricher

        Args:
            user_name: Team member name
            kaggle_db_path: Path to Kaggle database with audio features
            raw_data_dir: Directory with raw JSON data
            output_dir: Directory to save enriched data
        """
        self.user_name = user_name
        self.raw_data_dir = Path(raw_data_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Load Kaggle database for fallback audio features
        try:
            self.kaggle_db = pd.read_csv(kaggle_db_path)
            print(f"✓ Loaded Kaggle database: {len(self.kaggle_db):,} tracks")
        except Exception as e:
            print(f"⚠️  Could not load Kaggle database: {e}")
            self.kaggle_db = None

        # Authenticate for API access
        self.auth = SpotifyAuthenticator(user_name=user_name)
        self.sp = self.auth.get_client()

        # Stats
        self.stats = {
            'user_name': user_name,
            'enrichment_time': datetime.now().isoformat(),
            'total_tracks': 0,
            'features_from_api': 0,
            'features_from_kaggle': 0,
            'features_missing': 0,
            'errors': []
        }

    def extract_tracks_from_recently_played(self):
        """
        Extract track information from recently played JSON

        Returns:
            pd.DataFrame: Track data with timestamps
        """
        json_path = self.raw_data_dir / f'{self.user_name}_recently_played.json'

        if not json_path.exists():
            print(f"⚠️  No recently played data found for {self.user_name}")
            return pd.DataFrame()

        with open(json_path, 'r') as f:
            data = json.load(f)

        tracks = []
        for item in data.get('items', []):
            track = item.get('track', {})
            tracks.append({
                'track_id': track.get('id'),
                'track_name': track.get('name'),
                'artist_name': ', '.join([a['name'] for a in track.get('artists', [])]),
                'artist_id': track['artists'][0]['id'] if track.get('artists') else None,
                'album_name': track.get('album', {}).get('name'),
                'album_id': track.get('album', {}).get('id'),
                'duration_ms': track.get('duration_ms'),
                'popularity': track.get('popularity'),
                'explicit': track.get('explicit'),
                'timestamp': item.get('played_at'),
                'context_type': item.get('context', {}).get('type'),
                'context_uri': item.get('context', {}).get('uri'),
                'source': 'recently_played'
            })

        df = pd.DataFrame(tracks)
        print(f"✓ Extracted {len(df)} tracks from recently played")
        return df

    def extract_tracks_from_top_tracks(self):
        """
        Extract track information from top tracks JSON

        Returns:
            pd.DataFrame: Track data with time ranges
        """
        json_path = self.raw_data_dir / f'{self.user_name}_top_tracks_all.json'

        if not json_path.exists():
            print(f"⚠️  No top tracks data found for {self.user_name}")
            return pd.DataFrame()

        with open(json_path, 'r') as f:
            data = json.load(f)

        tracks = []
        for time_range, results in data.items():
            for track in results.get('items', []):
                tracks.append({
                    'track_id': track.get('id'),
                    'track_name': track.get('name'),
                    'artist_name': ', '.join([a['name'] for a in track.get('artists', [])]),
                    'artist_id': track['artists'][0]['id'] if track.get('artists') else None,
                    'album_name': track.get('album', {}).get('name'),
                    'album_id': track.get('album', {}).get('id'),
                    'duration_ms': track.get('duration_ms'),
                    'popularity': track.get('popularity'),
                    'explicit': track.get('explicit'),
                    'time_range': time_range,
                    'source': 'top_tracks'
                })

        df = pd.DataFrame(tracks)
        print(f"✓ Extracted {len(df)} tracks from top tracks")
        return df

    def fetch_audio_features_batch(self, track_ids, batch_size=100):
        """
        Fetch audio features from Spotify API in batches

        Args:
            track_ids: List of track IDs
            batch_size: Number of tracks per batch (max 100)

        Returns:
            dict: {track_id: audio_features}
        """
        print(f"\n📊 Fetching audio features from Spotify API...")

        all_features = {}
        track_ids = [tid for tid in track_ids if tid]  # Remove None values

        for i in range(0, len(track_ids), batch_size):
            batch = track_ids[i:i + batch_size]
            print(f"  Processing batch {i//batch_size + 1}/{(len(track_ids)-1)//batch_size + 1}...")

            try:
                features_list = self.sp.audio_features(batch)

                for track_id, features in zip(batch, features_list):
                    if features:
                        all_features[track_id] = features
                        self.stats['features_from_api'] += 1
                    else:
                        print(f"    ⚠️  No audio features for track: {track_id}")
                        self.stats['features_missing'] += 1

                # Rate limiting
                time.sleep(0.5)

            except Exception as e:
                error_msg = f"Error fetching audio features for batch: {e}"
                print(f"    ✗ {error_msg}")
                self.stats['errors'].append(error_msg)

        print(f"✓ Fetched audio features for {len(all_features)} tracks")
        return all_features

    def get_audio_features_from_kaggle(self, track_ids):
        """
        Get audio features from Kaggle database as fallback

        Args:
            track_ids: List of track IDs

        Returns:
            dict: {track_id: audio_features}
        """
        if self.kaggle_db is None:
            return {}

        print(f"\n📚 Looking up audio features in Kaggle database...")

        features_dict = {}
        kaggle_ids = set(self.kaggle_db['track_id'].values)

        for track_id in track_ids:
            if track_id in kaggle_ids:
                row = self.kaggle_db[self.kaggle_db['track_id'] == track_id].iloc[0]

                # Convert to Spotify API format
                features_dict[track_id] = {
                    'danceability': row.get('danceability'),
                    'energy': row.get('energy'),
                    'key': int(row.get('key', 0)),
                    'loudness': row.get('loudness'),
                    'mode': int(row.get('mode', 0)),
                    'speechiness': row.get('speechiness'),
                    'acousticness': row.get('acousticness'),
                    'instrumentalness': row.get('instrumentalness'),
                    'liveness': row.get('liveness'),
                    'valence': row.get('valence'),
                    'tempo': row.get('tempo'),
                    'time_signature': int(row.get('time_signature', 4)),
                    'source': 'kaggle_db'
                }
                self.stats['features_from_kaggle'] += 1

        print(f"✓ Found audio features for {len(features_dict)} tracks in Kaggle DB")
        return features_dict

    def enrich_tracks_with_features(self, tracks_df):
        """
        Enrich tracks DataFrame with audio features

        Args:
            tracks_df: DataFrame with track information

        Returns:
            pd.DataFrame: Enriched DataFrame with audio features
        """
        self.stats['total_tracks'] = len(tracks_df)

        # Get unique track IDs
        unique_track_ids = tracks_df['track_id'].dropna().unique().tolist()
        print(f"\n📊 Enriching {len(unique_track_ids)} unique tracks...")

        # Fetch from Spotify API
        api_features = self.fetch_audio_features_batch(unique_track_ids)

        # Get missing features from Kaggle DB
        missing_ids = [tid for tid in unique_track_ids if tid not in api_features]
        if missing_ids:
            kaggle_features = self.get_audio_features_from_kaggle(missing_ids)
            api_features.update(kaggle_features)

        # Merge features into DataFrame
        audio_feature_cols = [
            'danceability', 'energy', 'key', 'loudness', 'mode',
            'speechiness', 'acousticness', 'instrumentalness',
            'liveness', 'valence', 'tempo', 'time_signature'
        ]

        for col in audio_feature_cols:
            tracks_df[col] = tracks_df['track_id'].apply(
                lambda tid: api_features.get(tid, {}).get(col) if tid in api_features else None
            )

        # Add feature source
        tracks_df['feature_source'] = tracks_df['track_id'].apply(
            lambda tid: api_features.get(tid, {}).get('source', 'api') if tid in api_features else 'missing'
        )

        # Calculate derived features
        tracks_df = self._add_derived_features(tracks_df)

        return tracks_df

    def _add_derived_features(self, df):
        """Add composite and derived features"""

        print(f"\n📊 Calculating derived features...")

        # Mood Score
        if all(col in df.columns for col in ['valence', 'energy', 'acousticness']):
            df['mood_score'] = (
                0.5 * df['valence'] +
                0.3 * df['energy'] +
                0.2 * (1 - df['acousticness'])
            )

        # Grooviness Index
        if all(col in df.columns for col in ['danceability', 'energy', 'tempo']):
            tempo_norm = (df['tempo'] - df['tempo'].min()) / (df['tempo'].max() - df['tempo'].min())
            df['grooviness'] = (
                0.4 * df['danceability'] +
                0.3 * df['energy'] +
                0.3 * tempo_norm
            )

        # Focus Score
        if all(col in df.columns for col in ['speechiness', 'energy', 'instrumentalness']):
            df['focus_score'] = (
                0.4 * (1 - df['speechiness']) +
                0.3 * df['instrumentalness'] +
                0.3 * (1 - abs(df['energy'] - 0.5) * 2)
            )

        # Relaxation Score
        if all(col in df.columns for col in ['energy', 'acousticness', 'tempo']):
            tempo_norm = (df['tempo'] - df['tempo'].min()) / (df['tempo'].max() - df['tempo'].min())
            df['relaxation_score'] = (
                0.4 * (1 - df['energy']) +
                0.3 * df['acousticness'] +
                0.3 * (1 - tempo_norm)
            )

        # Add temporal features if timestamp exists
        if 'timestamp' in df.columns and df['timestamp'].notna().any():
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df['hour'] = df['timestamp'].dt.hour
            df['day_of_week'] = df['timestamp'].dt.day_name()
            df['is_weekend'] = df['timestamp'].dt.dayofweek >= 5
            df['date'] = df['timestamp'].dt.date

            # Time period
            df['time_period'] = df['hour'].apply(self._classify_time_period)

            # Infer context
            df['inferred_context'] = df.apply(self._infer_context, axis=1)

        print(f"✓ Added derived features")
        return df

    @staticmethod
    def _classify_time_period(hour):
        """Classify hour into time period"""
        if 6 <= hour < 12:
            return 'morning'
        elif 12 <= hour < 18:
            return 'afternoon'
        elif 18 <= hour < 23:
            return 'evening'
        else:
            return 'night'

    @staticmethod
    def _infer_context(row):
        """Infer listening context from audio features and time"""
        energy = row.get('energy', 0.5)
        danceability = row.get('danceability', 0.5)
        valence = row.get('valence', 0.5)
        speechiness = row.get('speechiness', 0.5)
        acousticness = row.get('acousticness', 0.5)
        instrumentalness = row.get('instrumentalness', 0)
        hour = row.get('hour', 12)
        is_weekend = row.get('is_weekend', False)

        # High energy + high danceability = Workout
        if energy > 0.7 and danceability > 0.6:
            return 'workout'

        # Low speechiness + high instrumental = Focus
        if speechiness < 0.2 and instrumentalness > 0.5:
            return 'focus'

        # Low energy + high acousticness = Relaxation/Sleep
        if energy < 0.4 and acousticness > 0.5:
            return 'relaxation' if hour < 22 else 'sleep'

        # High valence + high energy = Party (especially evenings/weekends)
        if valence > 0.6 and energy > 0.6 and (hour >= 20 or is_weekend):
            return 'party'

        # Morning commute
        if 6 <= hour <= 9 and not is_weekend and energy > 0.5:
            return 'commute'

        return 'general'

    def process_user_data(self):
        """
        Process all data for a user

        Returns:
            pd.DataFrame: Enriched listening history
        """
        print(f"\n{'='*60}")
        print(f"PROCESSING DATA FOR: {self.user_name.upper()}")
        print(f"{'='*60}")

        # Extract tracks from different sources
        recently_played_df = self.extract_tracks_from_recently_played()
        top_tracks_df = self.extract_tracks_from_top_tracks()

        # Combine all tracks
        all_tracks = pd.concat([recently_played_df, top_tracks_df], ignore_index=True)

        if len(all_tracks) == 0:
            print(f"⚠️  No tracks found for {self.user_name}")
            return pd.DataFrame()

        # Enrich with audio features
        enriched_df = self.enrich_tracks_with_features(all_tracks)

        # Add user information
        enriched_df['user_name'] = self.user_name

        # Save enriched data
        output_path = self.output_dir / f'{self.user_name}_listening_history.csv'
        enriched_df.to_csv(output_path, index=False)
        print(f"\n✓ Saved enriched data to: {output_path}")

        # Save stats
        stats_path = self.output_dir / f'{self.user_name}_enrichment_stats.json'
        with open(stats_path, 'w') as f:
            json.dump(self.stats, f, indent=2)

        # Print summary
        self._print_summary()

        return enriched_df

    def _print_summary(self):
        """Print enrichment summary"""
        print(f"\n{'='*60}")
        print(f"ENRICHMENT SUMMARY FOR: {self.user_name.upper()}")
        print(f"{'='*60}")
        print(f"Total Tracks: {self.stats['total_tracks']}")
        print(f"Features from Spotify API: {self.stats['features_from_api']}")
        print(f"Features from Kaggle DB: {self.stats['features_from_kaggle']}")
        print(f"Missing Features: {self.stats['features_missing']}")

        if self.stats['errors']:
            print(f"\nErrors ({len(self.stats['errors'])}):")
            for error in self.stats['errors']:
                print(f"  - {error}")

        print(f"{'='*60}\n")


# Command-line interface
if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Enrich tracks with audio features')
    parser.add_argument(
        '--user',
        type=str,
        required=True,
        help='Team member name (nicolo, joe, rithvik) or "all"'
    )
    parser.add_argument(
        '--kaggle-db',
        type=str,
        default='data/processed_spotify_data.csv',
        help='Path to Kaggle database'
    )

    args = parser.parse_args()

    if args.user == 'all':
        from spotify_auth import TeamAuthenticator

        for member in TeamAuthenticator.TEAM_MEMBERS:
            try:
                enricher = AudioFeaturesEnricher(
                    user_name=member,
                    kaggle_db_path=args.kaggle_db
                )
                enricher.process_user_data()
            except Exception as e:
                print(f"\n✗ Failed to process {member}: {e}\n")
    else:
        enricher = AudioFeaturesEnricher(
            user_name=args.user,
            kaggle_db_path=args.kaggle_db
        )
        enricher.process_user_data()

    print("\n✨ Audio features enrichment complete! ✨")
    print("\nNext step: python scripts/merge_team_data.py")
