"""
S3 Storage Functions
Upload and retrieve user listening data from Cloudflare R2 (S3-compatible storage)
"""

import boto3
import pandas as pd
import io
import os
from botocore.exceptions import ClientError, NoCredentialsError
import streamlit as st
from dotenv import load_dotenv

# Load environment variables from .env file
# This is needed for Streamlit multi-page apps where each page runs independently
load_dotenv()


def get_s3_client():
    """Create and return S3 client configured for Cloudflare R2"""
    try:
        # Cloudflare R2 credentials
        access_key_id = os.getenv('R2_ACCESS_KEY_ID')
        secret_access_key = os.getenv('R2_SECRET_ACCESS_KEY')
        account_id = os.getenv('CLOUDFLARE_ACCOUNT_ID')

        if not all([access_key_id, secret_access_key]):
            st.error("Cloudflare R2 credentials not found. Please configure .env file.")
            return None

        if not account_id:
            st.error("CLOUDFLARE_ACCOUNT_ID not found. This is required for R2 API access.")
            return None

        # Use R2 API endpoint (account ID required)
        # Note: Custom domains are for public HTTP access only, not S3 API
        endpoint_url = f"https://{account_id}.r2.cloudflarestorage.com"

        # Configure S3 client for R2
        # IMPORTANT: R2 requires path-style addressing (not virtual-hosted-style)
        from botocore.config import Config

        s3_config = Config(
            signature_version='s3v4',
            s3={'addressing_style': 'path'}  # Required for R2 compatibility
        )

        s3_client = boto3.client(
            's3',
            endpoint_url=endpoint_url,
            aws_access_key_id=access_key_id,
            aws_secret_access_key=secret_access_key,
            region_name='auto',  # R2 uses 'auto' for region
            config=s3_config
        )

        return s3_client

    except NoCredentialsError:
        st.error("R2 credentials not found. Please configure .env file.")
        return None
    except Exception as e:
        st.error(f"Failed to create R2 client: {e}")
        return None


def upload_dataframe_to_s3(df, bucket_name, s3_key):
    """
    Upload a pandas DataFrame to S3 as a Parquet file

    Args:
        df: pandas DataFrame to upload
        bucket_name: S3 bucket name
        s3_key: S3 object key (path/filename)

    Returns:
        bool: True if successful, False otherwise
    """
    if df.empty:
        st.warning(f"Empty DataFrame, skipping upload to {s3_key}")
        return False

    s3_client = get_s3_client()
    if not s3_client:
        return False

    try:
        # Convert DataFrame to Parquet in memory
        parquet_buffer = io.BytesIO()
        df.to_parquet(parquet_buffer, engine='pyarrow', compression='snappy', index=False)
        parquet_buffer.seek(0)

        # Upload to S3
        s3_client.put_object(
            Bucket=bucket_name,
            Key=s3_key,
            Body=parquet_buffer.getvalue(),
            ContentType='application/octet-stream'
        )

        return True

    except ClientError as e:
        st.error(f"Failed to upload to S3: {e}")
        return False
    except Exception as e:
        st.error(f"Unexpected error during S3 upload: {e}")
        return False


def download_dataframe_from_s3(bucket_name, s3_key):
    """
    Download a Parquet file from S3 and return as pandas DataFrame

    Args:
        bucket_name: S3 bucket name
        s3_key: S3 object key (path/filename)

    Returns:
        pd.DataFrame or None if failed
    """
    s3_client = get_s3_client()
    if not s3_client:
        return None

    try:
        # Download from S3
        response = s3_client.get_object(Bucket=bucket_name, Key=s3_key)
        parquet_buffer = io.BytesIO(response['Body'].read())

        # Read Parquet into DataFrame
        df = pd.read_parquet(parquet_buffer, engine='pyarrow')
        return df

    except ClientError as e:
        if e.response['Error']['Code'] == 'NoSuchKey':
            st.warning(f"File not found in S3: {s3_key}")
        else:
            st.error(f"Failed to download from S3: {e}")
        return None
    except Exception as e:
        st.error(f"Unexpected error during S3 download: {e}")
        return None


def list_user_snapshots(bucket_name, user_id):
    """
    List all snapshot files for a given user

    Args:
        bucket_name: S3 bucket name
        user_id: Spotify user ID

    Returns:
        list: List of S3 keys for user's snapshots
    """
    s3_client = get_s3_client()
    if not s3_client:
        return []

    try:
        prefix = f"users/{user_id}/snapshots/"
        response = s3_client.list_objects_v2(Bucket=bucket_name, Prefix=prefix)

        if 'Contents' not in response:
            return []

        # Extract keys and sort by timestamp (newest first)
        keys = [obj['Key'] for obj in response['Contents']]
        keys.sort(reverse=True)

        return keys

    except ClientError as e:
        st.error(f"Failed to list snapshots: {e}")
        return []


def load_all_user_data(bucket_name, user_id, data_type='recent_tracks'):
    """
    Load and concatenate all historical data for a user

    Args:
        bucket_name: S3 bucket name
        user_id: Spotify user ID
        data_type: Type of data to load ('recent_tracks', 'top_tracks', 'top_artists')

    Returns:
        pd.DataFrame: Concatenated historical data
    """
    s3_client = get_s3_client()
    if not s3_client:
        return pd.DataFrame()

    try:
        prefix = f"users/{user_id}/snapshots/"
        response = s3_client.list_objects_v2(Bucket=bucket_name, Prefix=prefix)

        if 'Contents' not in response:
            return pd.DataFrame()

        # Filter for specific data type
        keys = [obj['Key'] for obj in response['Contents'] if data_type in obj['Key']]

        if not keys:
            return pd.DataFrame()

        # Load and concatenate all files
        dfs = []
        for key in keys:
            df = download_dataframe_from_s3(bucket_name, key)
            if df is not None and not df.empty:
                dfs.append(df)

        if not dfs:
            return pd.DataFrame()

        # Concatenate and remove duplicates
        combined_df = pd.concat(dfs, ignore_index=True)

        # Remove duplicates based on track_id and snapshot_timestamp
        if 'track_id' in combined_df.columns and 'snapshot_timestamp' in combined_df.columns:
            combined_df = combined_df.drop_duplicates(subset=['track_id', 'snapshot_timestamp'])

        return combined_df

    except Exception as e:
        st.error(f"Failed to load user data: {e}")
        return pd.DataFrame()


def get_bucket_name():
    """Get R2 bucket name from environment"""
    bucket = os.getenv('R2_BUCKET_NAME')
    if not bucket:
        st.warning("R2_BUCKET_NAME not configured in .env")
    return bucket
