"""
Spotify Data Collection Script
Collects listening history and preferences from team members via Spotify API
"""

import json
import time
from datetime import datetime
from pathlib import Path
import pandas as pd
from spotify_auth import SpotifyAuthenticator, TeamAuthenticator


class SpotifyDataCollector:
    """
    Collects various types of data from Spotify API
    """

    def __init__(self, user_name, output_dir='data/raw'):
        """
        Initialize data collector for a specific user

        Args:
            user_name: Team member name
            output_dir: Directory to save raw JSON data
        """
        self.user_name = user_name
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Authenticate
        self.auth = SpotifyAuthenticator(user_name=user_name)
        self.sp = self.auth.authenticate()

        # Collection stats
        self.stats = {
            'user_name': user_name,
            'collection_time': datetime.now().isoformat(),
            'recently_played_count': 0,
            'top_tracks_count': 0,
            'top_artists_count': 0,
            'playlists_count': 0,
            'errors': []
        }

    def collect_recently_played(self, limit=50):
        """
        Collect recently played tracks

        Args:
            limit: Number of recent tracks to fetch (max 50)

        Returns:
            dict: Recently played data
        """
        print(f"\n📊 Collecting recently played tracks for {self.user_name}...")

        try:
            results = self.sp.current_user_recently_played(limit=limit)

            # Save raw JSON
            output_path = self.output_dir / f'{self.user_name}_recently_played.json'
            with open(output_path, 'w') as f:
                json.dump(results, f, indent=2)

            self.stats['recently_played_count'] = len(results.get('items', []))
            print(f"✓ Collected {self.stats['recently_played_count']} recently played tracks")
            print(f"✓ Saved to: {output_path}")

            return results

        except Exception as e:
            error_msg = f"Error collecting recently played: {e}"
            print(f"✗ {error_msg}")
            self.stats['errors'].append(error_msg)
            return None

    def collect_top_tracks(self, time_ranges=None, limit=50):
        """
        Collect top tracks for different time ranges

        Args:
            time_ranges: List of time ranges ('short_term', 'medium_term', 'long_term')
            limit: Number of tracks per time range (max 50)

        Returns:
            dict: Top tracks by time range
        """
        time_ranges = time_ranges or ['short_term', 'medium_term', 'long_term']
        time_range_labels = {
            'short_term': '~4 weeks',
            'medium_term': '~6 months',
            'long_term': 'several years'
        }

        print(f"\n📊 Collecting top tracks for {self.user_name}...")

        all_results = {}

        for time_range in time_ranges:
            try:
                print(f"  Fetching top tracks ({time_range_labels.get(time_range, time_range)})...")
                results = self.sp.current_user_top_tracks(
                    limit=limit,
                    time_range=time_range
                )

                # Add time range to results
                results['time_range'] = time_range
                all_results[time_range] = results

                # Save individual JSON
                output_path = self.output_dir / f'{self.user_name}_top_tracks_{time_range}.json'
                with open(output_path, 'w') as f:
                    json.dump(results, f, indent=2)

                track_count = len(results.get('items', []))
                self.stats['top_tracks_count'] += track_count
                print(f"  ✓ Collected {track_count} tracks ({time_range})")

                # Rate limiting - be nice to API
                time.sleep(0.5)

            except Exception as e:
                error_msg = f"Error collecting top tracks ({time_range}): {e}"
                print(f"  ✗ {error_msg}")
                self.stats['errors'].append(error_msg)

        # Save combined JSON
        if all_results:
            output_path = self.output_dir / f'{self.user_name}_top_tracks_all.json'
            with open(output_path, 'w') as f:
                json.dump(all_results, f, indent=2)
            print(f"✓ Saved all top tracks to: {output_path}")

        return all_results

    def collect_top_artists(self, time_ranges=None, limit=50):
        """
        Collect top artists for different time ranges

        Args:
            time_ranges: List of time ranges ('short_term', 'medium_term', 'long_term')
            limit: Number of artists per time range (max 50)

        Returns:
            dict: Top artists by time range
        """
        time_ranges = time_ranges or ['short_term', 'medium_term', 'long_term']
        time_range_labels = {
            'short_term': '~4 weeks',
            'medium_term': '~6 months',
            'long_term': 'several years'
        }

        print(f"\n📊 Collecting top artists for {self.user_name}...")

        all_results = {}

        for time_range in time_ranges:
            try:
                print(f"  Fetching top artists ({time_range_labels.get(time_range, time_range)})...")
                results = self.sp.current_user_top_artists(
                    limit=limit,
                    time_range=time_range
                )

                # Add time range to results
                results['time_range'] = time_range
                all_results[time_range] = results

                # Save individual JSON
                output_path = self.output_dir / f'{self.user_name}_top_artists_{time_range}.json'
                with open(output_path, 'w') as f:
                    json.dump(results, f, indent=2)

                artist_count = len(results.get('items', []))
                self.stats['top_artists_count'] += artist_count
                print(f"  ✓ Collected {artist_count} artists ({time_range})")

                # Rate limiting
                time.sleep(0.5)

            except Exception as e:
                error_msg = f"Error collecting top artists ({time_range}): {e}"
                print(f"  ✗ {error_msg}")
                self.stats['errors'].append(error_msg)

        # Save combined JSON
        if all_results:
            output_path = self.output_dir / f'{self.user_name}_top_artists_all.json'
            with open(output_path, 'w') as f:
                json.dump(all_results, f, indent=2)
            print(f"✓ Saved all top artists to: {output_path}")

        return all_results

    def collect_playlists(self, limit=50):
        """
        Collect user's playlists (metadata only)

        Args:
            limit: Number of playlists to fetch

        Returns:
            dict: Playlist data
        """
        print(f"\n📊 Collecting playlists for {self.user_name}...")

        try:
            results = self.sp.current_user_playlists(limit=limit)

            # Save raw JSON
            output_path = self.output_dir / f'{self.user_name}_playlists.json'
            with open(output_path, 'w') as f:
                json.dump(results, f, indent=2)

            self.stats['playlists_count'] = len(results.get('items', []))
            print(f"✓ Collected {self.stats['playlists_count']} playlists")
            print(f"✓ Saved to: {output_path}")

            return results

        except Exception as e:
            error_msg = f"Error collecting playlists: {e}"
            print(f"✗ {error_msg}")
            self.stats['errors'].append(error_msg)
            return None

    def collect_all(self, include_recently_played=True, include_top_tracks=True,
                    include_top_artists=True, include_playlists=True):
        """
        Collect all available data

        Args:
            include_recently_played: Collect recently played tracks
            include_top_tracks: Collect top tracks
            include_top_artists: Collect top artists
            include_playlists: Collect playlists

        Returns:
            dict: Collection statistics
        """
        print(f"\n{'='*60}")
        print(f"COLLECTING DATA FOR: {self.user_name.upper()}")
        print(f"{'='*60}")

        if include_recently_played:
            self.collect_recently_played()

        if include_top_tracks:
            self.collect_top_tracks()

        if include_top_artists:
            self.collect_top_artists()

        if include_playlists:
            self.collect_playlists()

        # Save collection stats
        stats_path = self.output_dir / f'{self.user_name}_collection_stats.json'
        with open(stats_path, 'w') as f:
            json.dump(self.stats, f, indent=2)

        # Print summary
        print(f"\n{'='*60}")
        print(f"COLLECTION SUMMARY FOR: {self.user_name.upper()}")
        print(f"{'='*60}")
        print(f"Recently Played Tracks: {self.stats['recently_played_count']}")
        print(f"Top Tracks (all ranges): {self.stats['top_tracks_count']}")
        print(f"Top Artists (all ranges): {self.stats['top_artists_count']}")
        print(f"Playlists: {self.stats['playlists_count']}")

        if self.stats['errors']:
            print(f"\nErrors ({len(self.stats['errors'])}):")
            for error in self.stats['errors']:
                print(f"  - {error}")
        else:
            print(f"\n✓ No errors!")

        print(f"{'='*60}\n")

        return self.stats


class TeamDataCollector:
    """
    Collects data from all team members
    """

    def __init__(self, members=None, output_dir='data/raw'):
        """
        Initialize team data collector

        Args:
            members: List of team member names (default: all)
            output_dir: Directory to save raw data
        """
        self.members = members or TeamAuthenticator.TEAM_MEMBERS
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.team_stats = {}

    def collect_all(self, **kwargs):
        """
        Collect data from all team members

        Args:
            **kwargs: Arguments passed to SpotifyDataCollector.collect_all()

        Returns:
            dict: Collection statistics for all members
        """
        print(f"\n{'#'*60}")
        print(f"TEAM DATA COLLECTION")
        print(f"Members: {', '.join(self.members)}")
        print(f"{'#'*60}\n")

        for member in self.members:
            try:
                collector = SpotifyDataCollector(
                    user_name=member,
                    output_dir=self.output_dir
                )
                stats = collector.collect_all(**kwargs)
                self.team_stats[member] = stats

            except Exception as e:
                error_msg = f"Failed to collect data for {member}: {e}"
                print(f"\n✗ {error_msg}\n")
                self.team_stats[member] = {
                    'error': error_msg,
                    'collection_time': datetime.now().isoformat()
                }

        # Save team summary
        summary_path = self.output_dir / 'team_collection_summary.json'
        with open(summary_path, 'w') as f:
            json.dump(self.team_stats, f, indent=2)

        # Print team summary
        self._print_team_summary()

        return self.team_stats

    def _print_team_summary(self):
        """Print summary of team data collection"""
        print(f"\n{'#'*60}")
        print(f"TEAM COLLECTION SUMMARY")
        print(f"{'#'*60}\n")

        total_recently_played = 0
        total_top_tracks = 0
        total_top_artists = 0
        total_playlists = 0
        total_errors = 0

        for member, stats in self.team_stats.items():
            if 'error' in stats:
                print(f"❌ {member}: FAILED - {stats['error']}")
                total_errors += 1
            else:
                print(f"✓ {member}:")
                print(f"    Recently Played: {stats.get('recently_played_count', 0)}")
                print(f"    Top Tracks: {stats.get('top_tracks_count', 0)}")
                print(f"    Top Artists: {stats.get('top_artists_count', 0)}")
                print(f"    Playlists: {stats.get('playlists_count', 0)}")

                total_recently_played += stats.get('recently_played_count', 0)
                total_top_tracks += stats.get('top_tracks_count', 0)
                total_top_artists += stats.get('top_artists_count', 0)
                total_playlists += stats.get('playlists_count', 0)

                if stats.get('errors'):
                    print(f"    Errors: {len(stats['errors'])}")
                    total_errors += len(stats['errors'])

        print(f"\n{'─'*60}")
        print(f"TEAM TOTALS:")
        print(f"  Total Recently Played Tracks: {total_recently_played}")
        print(f"  Total Top Tracks: {total_top_tracks}")
        print(f"  Total Top Artists: {total_top_artists}")
        print(f"  Total Playlists: {total_playlists}")
        if total_errors > 0:
            print(f"  Total Errors: {total_errors}")
        print(f"{'#'*60}\n")


# Command-line interface
if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Collect Spotify Data from Team Members')
    parser.add_argument(
        '--user',
        type=str,
        help='Collect data for specific user (nicolo, joe, rithvik) or "all" for team'
    )
    parser.add_argument(
        '--recently-played-only',
        action='store_true',
        help='Only collect recently played tracks (faster)'
    )
    parser.add_argument(
        '--output-dir',
        type=str,
        default='data/raw',
        help='Output directory for raw data'
    )

    args = parser.parse_args()

    # Determine what to collect
    if args.recently_played_only:
        collect_options = {
            'include_recently_played': True,
            'include_top_tracks': False,
            'include_top_artists': False,
            'include_playlists': False
        }
    else:
        collect_options = {
            'include_recently_played': True,
            'include_top_tracks': True,
            'include_top_artists': True,
            'include_playlists': True
        }

    # Collect data
    if args.user == 'all' or not args.user:
        # Collect from all team members
        team_collector = TeamDataCollector(output_dir=args.output_dir)
        team_collector.collect_all(**collect_options)
    else:
        # Collect from single user
        collector = SpotifyDataCollector(
            user_name=args.user,
            output_dir=args.output_dir
        )
        collector.collect_all(**collect_options)

    print("\n✨ Data collection complete! ✨")
    print(f"\nRaw data saved to: {args.output_dir}/")
    print("Next steps:")
    print("  1. Run: python scripts/enrich_with_audio_features.py")
    print("  2. Run: python scripts/merge_team_data.py")
    print("  3. Update Spotify.ipynb with new data")
