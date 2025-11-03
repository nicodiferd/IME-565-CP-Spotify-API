"""
Team Data Merger
Combines listening history from all team members into unified dataset
"""

import json
from pathlib import Path
from datetime import datetime
import pandas as pd
import numpy as np


class TeamDataMerger:
    """
    Merges listening history from multiple team members
    """

    def __init__(self, processed_data_dir='data/processed', output_dir='data'):
        """
        Initialize team data merger

        Args:
            processed_data_dir: Directory with processed individual data
            output_dir: Directory to save merged data
        """
        self.processed_data_dir = Path(processed_data_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.stats = {
            'merge_time': datetime.now().isoformat(),
            'members_processed': [],
            'total_tracks': 0,
            'unique_tracks': 0,
            'total_plays': 0,
            'date_range': {},
            'errors': []
        }

    def load_user_data(self, user_name):
        """
        Load processed data for a single user

        Args:
            user_name: Team member name

        Returns:
            pd.DataFrame: User's listening history
        """
        file_path = self.processed_data_dir / f'{user_name}_listening_history.csv'

        if not file_path.exists():
            print(f"⚠️  No processed data found for {user_name}")
            return pd.DataFrame()

        try:
            df = pd.read_csv(file_path)
            print(f"✓ Loaded {len(df)} records for {user_name}")
            return df
        except Exception as e:
            error_msg = f"Error loading data for {user_name}: {e}"
            print(f"✗ {error_msg}")
            self.stats['errors'].append(error_msg)
            return pd.DataFrame()

    def load_all_team_data(self, members=None):
        """
        Load data from all team members

        Args:
            members: List of member names (default: all files in processed dir)

        Returns:
            list: List of DataFrames, one per member
        """
        if members:
            member_files = [f'{m}_listening_history.csv' for m in members]
        else:
            member_files = list(self.processed_data_dir.glob('*_listening_history.csv'))
            member_files = [f.name for f in member_files]

        print(f"\n📊 Loading data from team members...")

        dataframes = []
        for file_name in member_files:
            user_name = file_name.replace('_listening_history.csv', '')
            df = self.load_user_data(user_name)

            if not df.empty:
                dataframes.append(df)
                self.stats['members_processed'].append(user_name)

        return dataframes

    def merge_dataframes(self, dataframes):
        """
        Merge all team member DataFrames

        Args:
            dataframes: List of DataFrames

        Returns:
            pd.DataFrame: Merged DataFrame
        """
        if not dataframes:
            print("⚠️  No data to merge")
            return pd.DataFrame()

        print(f"\n📊 Merging data from {len(dataframes)} team members...")

        # Concatenate all DataFrames
        merged_df = pd.concat(dataframes, ignore_index=True)

        # Standardize column types
        if 'timestamp' in merged_df.columns:
            merged_df['timestamp'] = pd.to_datetime(merged_df['timestamp'], errors='coerce')

        # Sort by timestamp (if available)
        if 'timestamp' in merged_df.columns and merged_df['timestamp'].notna().any():
            merged_df = merged_df.sort_values('timestamp')

        print(f"✓ Merged {len(merged_df)} total records")
        return merged_df

    def add_user_ids(self, df):
        """
        Add numeric user IDs to DataFrame

        Args:
            df: DataFrame with user_name column

        Returns:
            pd.DataFrame: DataFrame with user_id column
        """
        if 'user_name' not in df.columns:
            return df

        # Create user_id mapping
        unique_users = sorted(df['user_name'].unique())
        user_id_map = {name: idx + 1 for idx, name in enumerate(unique_users)}

        df['user_id'] = df['user_name'].map(user_id_map)

        print(f"✓ Added user IDs for {len(unique_users)} team members")
        return df

    def deduplicate_tracks(self, df):
        """
        Handle duplicate tracks (keep most informative version)

        Args:
            df: DataFrame with potential duplicates

        Returns:
            pd.DataFrame: Deduplicated DataFrame
        """
        initial_count = len(df)

        # For recently played data, keep all plays (with timestamps)
        # These represent multiple listens of the same track
        recently_played = df[df['source'] == 'recently_played'].copy()

        # For top tracks, keep unique tracks per user and time_range
        top_tracks = df[df['source'] == 'top_tracks'].copy()
        if not top_tracks.empty:
            top_tracks = top_tracks.drop_duplicates(
                subset=['user_name', 'track_id', 'time_range'],
                keep='first'
            )

        # Combine
        df = pd.concat([recently_played, top_tracks], ignore_index=True)

        duplicates_removed = initial_count - len(df)
        print(f"✓ Removed {duplicates_removed} duplicate entries")

        return df

    def calculate_statistics(self, df):
        """
        Calculate statistics about the merged dataset

        Args:
            df: Merged DataFrame
        """
        self.stats['total_tracks'] = len(df)
        self.stats['unique_tracks'] = df['track_id'].nunique()

        # Count plays (recently_played entries have timestamps)
        if 'timestamp' in df.columns:
            self.stats['total_plays'] = df[df['timestamp'].notna()].shape[0]

        # Date range
        if 'timestamp' in df.columns and df['timestamp'].notna().any():
            self.stats['date_range'] = {
                'start': df['timestamp'].min().isoformat(),
                'end': df['timestamp'].max().isoformat(),
                'days': (df['timestamp'].max() - df['timestamp'].min()).days
            }

        # Per-user statistics
        self.stats['per_user'] = {}
        for user in df['user_name'].unique():
            user_df = df[df['user_name'] == user]
            self.stats['per_user'][user] = {
                'total_tracks': len(user_df),
                'unique_tracks': user_df['track_id'].nunique(),
                'plays': user_df[user_df['timestamp'].notna()].shape[0] if 'timestamp' in df.columns else 0
            }

        # Context distribution (if available)
        if 'inferred_context' in df.columns:
            self.stats['context_distribution'] = df['inferred_context'].value_counts().to_dict()

        # Audio feature statistics
        audio_features = [
            'danceability', 'energy', 'valence', 'acousticness',
            'speechiness', 'instrumentalness', 'tempo'
        ]
        self.stats['audio_features'] = {}
        for feature in audio_features:
            if feature in df.columns:
                self.stats['audio_features'][feature] = {
                    'mean': float(df[feature].mean()),
                    'std': float(df[feature].std()),
                    'min': float(df[feature].min()),
                    'max': float(df[feature].max())
                }

    def merge_and_save(self, members=None, output_filename='team_listening_history.csv'):
        """
        Complete merge pipeline

        Args:
            members: List of member names to merge (default: all)
            output_filename: Name of output file

        Returns:
            pd.DataFrame: Merged and processed DataFrame
        """
        print(f"\n{'='*60}")
        print(f"TEAM DATA MERGER")
        print(f"{'='*60}")

        # Load all data
        dataframes = self.load_all_team_data(members)

        if not dataframes:
            print("❌ No data to merge!")
            return pd.DataFrame()

        # Merge
        merged_df = self.merge_dataframes(dataframes)

        # Process
        merged_df = self.add_user_ids(merged_df)
        merged_df = self.deduplicate_tracks(merged_df)

        # Calculate statistics
        self.calculate_statistics(merged_df)

        # Save merged data
        output_path = self.output_dir / output_filename
        merged_df.to_csv(output_path, index=False)
        print(f"\n✓ Saved merged data to: {output_path}")

        # Save statistics
        stats_path = self.output_dir / 'team_merge_statistics.json'
        with open(stats_path, 'w') as f:
            json.dump(self.stats, f, indent=2)
        print(f"✓ Saved statistics to: {stats_path}")

        # Print summary
        self._print_summary(merged_df)

        return merged_df

    def _print_summary(self, df):
        """Print merge summary"""
        print(f"\n{'='*60}")
        print(f"MERGE SUMMARY")
        print(f"{'='*60}")

        print(f"\nTeam Members: {len(self.stats['members_processed'])}")
        for user in self.stats['members_processed']:
            user_stats = self.stats['per_user'][user]
            print(f"  - {user}: {user_stats['plays']} plays, {user_stats['unique_tracks']} unique tracks")

        print(f"\nDataset Overview:")
        print(f"  Total Records: {self.stats['total_tracks']:,}")
        print(f"  Unique Tracks: {self.stats['unique_tracks']:,}")
        print(f"  Total Plays (with timestamps): {self.stats['total_plays']:,}")

        if self.stats.get('date_range'):
            print(f"\nTemporal Coverage:")
            print(f"  Start: {self.stats['date_range']['start']}")
            print(f"  End: {self.stats['date_range']['end']}")
            print(f"  Duration: {self.stats['date_range']['days']} days")

        if self.stats.get('context_distribution'):
            print(f"\nContext Distribution:")
            for context, count in sorted(
                self.stats['context_distribution'].items(),
                key=lambda x: x[1],
                reverse=True
            ):
                print(f"  {context}: {count:,} ({count/self.stats['total_tracks']*100:.1f}%)")

        print(f"\nAudio Feature Averages:")
        for feature, stats in self.stats['audio_features'].items():
            print(f"  {feature}: {stats['mean']:.3f} (±{stats['std']:.3f})")

        if self.stats['errors']:
            print(f"\nErrors ({len(self.stats['errors'])}):")
            for error in self.stats['errors']:
                print(f"  - {error}")

        print(f"{'='*60}\n")

        # Data quality assessment
        self._print_data_quality_report(df)

    def _print_data_quality_report(self, df):
        """Print data quality assessment"""
        print(f"{'='*60}")
        print(f"DATA QUALITY REPORT")
        print(f"{'='*60}")

        # Completeness
        total_records = len(df)
        audio_features = [
            'danceability', 'energy', 'valence', 'acousticness',
            'speechiness', 'instrumentalness', 'tempo'
        ]

        print(f"\nFeature Completeness:")
        for feature in audio_features:
            if feature in df.columns:
                missing = df[feature].isna().sum()
                completeness = (1 - missing/total_records) * 100
                status = "✓" if completeness > 90 else "⚠️" if completeness > 70 else "✗"
                print(f"  {status} {feature}: {completeness:.1f}% complete")

        # Temporal data
        if 'timestamp' in df.columns:
            temporal_completeness = (df['timestamp'].notna().sum() / total_records) * 100
            status = "✓" if temporal_completeness > 30 else "⚠️"
            print(f"\n{status} Temporal Data: {temporal_completeness:.1f}% of records have timestamps")

        # Recommendations
        print(f"\nRecommendations:")
        if df['timestamp'].notna().sum() < total_records * 0.3:
            print(f"  ⚠️  Limited temporal data - consider collecting more recently played tracks")

        if df['track_id'].nunique() < 100:
            print(f"  ⚠️  Small dataset - aim for 200+ unique tracks for robust analysis")

        if len(df[df['timestamp'].notna()]) < 50:
            print(f"  ⚠️  Few timestamped plays - collect data over multiple days")

        print(f"{'='*60}\n")


# Command-line interface
if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Merge team member listening data')
    parser.add_argument(
        '--members',
        nargs='+',
        help='Specific team members to merge (default: all)'
    )
    parser.add_argument(
        '--output',
        type=str,
        default='team_listening_history.csv',
        help='Output filename'
    )

    args = parser.parse_args()

    merger = TeamDataMerger()
    merged_df = merger.merge_and_save(
        members=args.members,
        output_filename=args.output
    )

    if not merged_df.empty:
        print("\n✨ Team data merge complete! ✨")
        print(f"\nFinal dataset: data/{args.output}")
        print("\nNext steps:")
        print("  1. Open Spotify.ipynb")
        print("  2. Load data/team_listening_history.csv")
        print("  3. Run temporal analysis on real team data!")
    else:
        print("\n❌ Merge failed - check errors above")
