"""
Spotify OAuth Authentication System
Handles authentication for multiple team members with token caching
"""

import os
import json
from pathlib import Path
from datetime import datetime, timedelta
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from dotenv import load_dotenv


class SpotifyAuthenticator:
    """
    Manages Spotify OAuth authentication with automatic token refresh
    and multi-user support
    """

    # Required scopes for data collection
    SCOPES = [
        'user-read-recently-played',
        'user-top-read',
        'playlist-read-private',
        'user-read-private',
        'user-library-read'
    ]

    def __init__(self, user_name=None, env_file=None):
        """
        Initialize authenticator for a specific user

        Args:
            user_name: Name of team member (nicolo, joe, rithvik)
            env_file: Path to .env file (default: .env.{user_name})
        """
        self.user_name = user_name or os.getenv('USER_NAME', 'default')

        # Load environment variables
        if env_file:
            load_dotenv(env_file)
        elif user_name:
            env_path = f'.env.{user_name}'
            if os.path.exists(env_path):
                load_dotenv(env_path)
                print(f"✓ Loaded credentials from {env_path}")
            else:
                print(f"⚠️  Warning: {env_path} not found, using default .env")
                load_dotenv()
        else:
            load_dotenv()

        # Get credentials from environment
        self.client_id = os.getenv('SPOTIFY_CLIENT_ID')
        self.client_secret = os.getenv('SPOTIFY_CLIENT_SECRET')
        self.redirect_uri = os.getenv('SPOTIFY_REDIRECT_URI', 'http://localhost:8888/callback')

        # Validate credentials
        if not self.client_id or not self.client_secret:
            raise ValueError(
                f"Missing Spotify credentials for user '{self.user_name}'. "
                f"Please check your .env.{self.user_name} file."
            )

        # Cache directory for tokens
        self.cache_dir = Path('.spotify_cache')
        self.cache_dir.mkdir(exist_ok=True)
        self.cache_path = self.cache_dir / f'.cache-{self.user_name}'

        # Initialize Spotify client
        self.sp = None
        self._auth_manager = None

    def authenticate(self, force_refresh=False):
        """
        Authenticate with Spotify and return authenticated client

        Args:
            force_refresh: Force re-authentication even if token exists

        Returns:
            spotipy.Spotify: Authenticated Spotify client
        """
        if force_refresh and self.cache_path.exists():
            self.cache_path.unlink()
            print(f"🔄 Cleared cached token for {self.user_name}")

        # Create auth manager
        self._auth_manager = SpotifyOAuth(
            client_id=self.client_id,
            client_secret=self.client_secret,
            redirect_uri=self.redirect_uri,
            scope=' '.join(self.SCOPES),
            cache_path=str(self.cache_path),
            open_browser=True  # Auto-open browser for auth
        )

        # Get or refresh token
        token_info = self._auth_manager.get_access_token(as_dict=True)

        if not token_info:
            raise RuntimeError(
                f"Authentication failed for {self.user_name}. "
                "Please check your credentials and try again."
            )

        # Create Spotify client
        self.sp = spotipy.Spotify(auth=token_info['access_token'])

        # Verify authentication by getting user profile
        try:
            user_profile = self.sp.current_user()
            print(f"✓ Successfully authenticated as: {user_profile['display_name']}")
            print(f"  User ID: {user_profile['id']}")
            print(f"  Followers: {user_profile['followers']['total']}")
            return self.sp
        except Exception as e:
            raise RuntimeError(f"Authentication verification failed: {e}")

    def get_client(self):
        """
        Get authenticated Spotify client, refreshing token if needed

        Returns:
            spotipy.Spotify: Authenticated Spotify client
        """
        if not self.sp:
            return self.authenticate()

        # Check if token needs refresh
        if self._auth_manager:
            token_info = self._auth_manager.get_cached_token()
            if token_info:
                # Check if token expires in next 5 minutes
                expires_at = token_info.get('expires_at', 0)
                if expires_at - datetime.now().timestamp() < 300:
                    print(f"🔄 Refreshing token for {self.user_name}")
                    token_info = self._auth_manager.refresh_access_token(
                        token_info['refresh_token']
                    )
                    self.sp = spotipy.Spotify(auth=token_info['access_token'])

        return self.sp

    def save_token_info(self, output_path=None):
        """
        Save token information (for debugging, NOT the actual token)

        Args:
            output_path: Path to save token info
        """
        if not self._auth_manager:
            print("⚠️  No authentication manager available")
            return

        token_info = self._auth_manager.get_cached_token()
        if not token_info:
            print("⚠️  No cached token available")
            return

        # Save metadata only (not the actual token)
        token_metadata = {
            'user_name': self.user_name,
            'scope': token_info.get('scope', ''),
            'expires_at': datetime.fromtimestamp(
                token_info.get('expires_at', 0)
            ).isoformat(),
            'token_type': token_info.get('token_type', ''),
            'created_at': datetime.now().isoformat()
        }

        output_path = output_path or self.cache_dir / f'token_metadata_{self.user_name}.json'
        with open(output_path, 'w') as f:
            json.dump(token_metadata, f, indent=2)

        print(f"✓ Saved token metadata to {output_path}")


class TeamAuthenticator:
    """
    Manages authentication for all team members
    """

    TEAM_MEMBERS = ['nicolo', 'joe', 'rithvik']

    def __init__(self):
        """Initialize team authenticator"""
        self.authenticators = {}

    def authenticate_all(self, members=None):
        """
        Authenticate all team members

        Args:
            members: List of member names to authenticate (default: all)

        Returns:
            dict: Dictionary of {member_name: authenticated_client}
        """
        members = members or self.TEAM_MEMBERS
        results = {}

        print(f"\n{'='*60}")
        print(f"AUTHENTICATING TEAM MEMBERS")
        print(f"{'='*60}\n")

        for member in members:
            print(f"\n--- Authenticating: {member.upper()} ---")
            try:
                auth = SpotifyAuthenticator(user_name=member)
                client = auth.authenticate()
                self.authenticators[member] = auth
                results[member] = client
                print(f"✓ {member} authentication successful\n")
            except Exception as e:
                print(f"✗ {member} authentication failed: {e}\n")
                results[member] = None

        # Summary
        successful = sum(1 for v in results.values() if v is not None)
        print(f"\n{'='*60}")
        print(f"AUTHENTICATION SUMMARY")
        print(f"{'='*60}")
        print(f"Successful: {successful}/{len(members)}")
        for member, client in results.items():
            status = "✓ SUCCESS" if client else "✗ FAILED"
            print(f"  {member}: {status}")
        print(f"{'='*60}\n")

        return results

    def get_client(self, member):
        """
        Get authenticated client for a specific team member

        Args:
            member: Team member name

        Returns:
            spotipy.Spotify: Authenticated client
        """
        if member not in self.authenticators:
            raise ValueError(f"Member '{member}' not authenticated yet")

        return self.authenticators[member].get_client()


# Command-line interface
if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Spotify Authentication for Team Members')
    parser.add_argument(
        '--user',
        type=str,
        help='Team member name (nicolo, joe, rithvik) or "all" for everyone'
    )
    parser.add_argument(
        '--force-refresh',
        action='store_true',
        help='Force re-authentication even if token exists'
    )

    args = parser.parse_args()

    if args.user == 'all':
        # Authenticate all team members
        team_auth = TeamAuthenticator()
        team_auth.authenticate_all()
    elif args.user:
        # Authenticate single user
        auth = SpotifyAuthenticator(user_name=args.user)
        auth.authenticate(force_refresh=args.force_refresh)
        auth.save_token_info()
    else:
        # Interactive mode
        print("\nSpotify Authentication")
        print("=" * 50)
        print("Available team members:")
        for i, member in enumerate(TeamAuthenticator.TEAM_MEMBERS, 1):
            print(f"  {i}. {member}")
        print(f"  {len(TeamAuthenticator.TEAM_MEMBERS) + 1}. All team members")

        choice = input("\nSelect option (1-4): ").strip()

        if choice == str(len(TeamAuthenticator.TEAM_MEMBERS) + 1):
            team_auth = TeamAuthenticator()
            team_auth.authenticate_all()
        elif choice.isdigit() and 1 <= int(choice) <= len(TeamAuthenticator.TEAM_MEMBERS):
            member = TeamAuthenticator.TEAM_MEMBERS[int(choice) - 1]
            auth = SpotifyAuthenticator(user_name=member)
            auth.authenticate(force_refresh=args.force_refresh)
            auth.save_token_info()
        else:
            print("Invalid choice")
