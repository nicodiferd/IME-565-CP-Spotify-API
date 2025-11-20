"""
Test Cloudflare R2 Connection
Run this script to verify your R2 credentials are configured correctly
"""

import os
from dotenv import load_dotenv
import boto3
from botocore.config import Config
from botocore.exceptions import ClientError, NoCredentialsError
import pandas as pd
import io

# Load environment variables
load_dotenv()

print("=" * 60)
print("Cloudflare R2 Connection Test")
print("=" * 60)

# Check environment variables
print("\n1. Checking environment variables...")
access_key_id = os.getenv('R2_ACCESS_KEY_ID')
secret_access_key = os.getenv('R2_SECRET_ACCESS_KEY')
bucket_name = os.getenv('R2_BUCKET_NAME')
custom_domain = os.getenv('R2_CUSTOM_DOMAIN')
account_id = os.getenv('CLOUDFLARE_ACCOUNT_ID')

if not access_key_id:
    print("   ✗ R2_ACCESS_KEY_ID not found")
else:
    print(f"   ✓ R2_ACCESS_KEY_ID: {access_key_id[:10]}...")

if not secret_access_key:
    print("   ✗ R2_SECRET_ACCESS_KEY not found")
else:
    print(f"   ✓ R2_SECRET_ACCESS_KEY: {secret_access_key[:10]}...")

if not bucket_name:
    print("   ✗ R2_BUCKET_NAME not found")
else:
    print(f"   ✓ R2_BUCKET_NAME: {bucket_name}")

if not account_id:
    print("   ✗ CLOUDFLARE_ACCOUNT_ID not found")
    print("\n   Please add this to your .env file:")
    print("   CLOUDFLARE_ACCOUNT_ID=24df8bb5d20dca402dfc277d4c38cc80")
    exit(1)
else:
    print(f"   ✓ CLOUDFLARE_ACCOUNT_ID: {account_id}")

# Custom domain is for public access only, not API
if custom_domain:
    print(f"   ℹ R2_CUSTOM_DOMAIN: {custom_domain} (used for public URLs only)")

# Always use account ID endpoint for API
endpoint_url = f"https://{account_id}.r2.cloudflarestorage.com"

if not all([access_key_id, secret_access_key, bucket_name, account_id]):
    print("\n✗ Missing required environment variables!")
    print("   Please check your .env file.")
    exit(1)

print(f"\n   Endpoint: {endpoint_url}")

# Create R2 client
print("\n2. Creating R2 client...")
try:
    s3_config = Config(
        signature_version='s3v4',
        s3={'addressing_style': 'path'}  # Required for R2
    )

    s3_client = boto3.client(
        's3',
        endpoint_url=endpoint_url,
        aws_access_key_id=access_key_id,
        aws_secret_access_key=secret_access_key,
        region_name='auto',
        config=s3_config
    )
    print("   ✓ R2 client created successfully")

except NoCredentialsError:
    print("   ✗ Credentials error - check your access keys")
    exit(1)
except Exception as e:
    print(f"   ✗ Failed to create client: {e}")
    exit(1)

# Test connection - list buckets
print("\n3. Testing connection (list objects)...")
try:
    response = s3_client.list_objects_v2(Bucket=bucket_name, MaxKeys=10)
    object_count = response.get('KeyCount', 0)
    print(f"   ✓ Successfully connected to bucket: {bucket_name}")
    print(f"   ✓ Objects in bucket: {object_count}")

    if object_count > 0:
        print("\n   First few objects:")
        for obj in response.get('Contents', [])[:5]:
            print(f"      - {obj['Key']} ({obj['Size']} bytes)")

except ClientError as e:
    error_code = e.response['Error']['Code']
    if error_code == 'NoSuchBucket':
        print(f"   ✗ Bucket '{bucket_name}' does not exist")
        print("      Make sure the bucket name is correct (case-sensitive)")
    elif error_code == 'AccessDenied':
        print("   ✗ Access denied - check API token permissions")
        print("      Token needs 'Admin Read & Write' permissions")
    else:
        print(f"   ✗ Error: {error_code} - {e.response['Error']['Message']}")
    exit(1)
except Exception as e:
    print(f"   ✗ Connection failed: {e}")
    exit(1)

# Test write operation
print("\n4. Testing write operation...")
try:
    # Create a small test DataFrame
    test_df = pd.DataFrame({
        'timestamp': [pd.Timestamp.now()],
        'test_value': ['connection_test'],
        'status': ['success']
    })

    # Convert to Parquet
    parquet_buffer = io.BytesIO()
    test_df.to_parquet(parquet_buffer, engine='pyarrow', compression='snappy', index=False)
    parquet_buffer.seek(0)

    # Upload to R2
    test_key = 'test/connection_test.parquet'
    s3_client.put_object(
        Bucket=bucket_name,
        Key=test_key,
        Body=parquet_buffer.getvalue(),
        ContentType='application/octet-stream'
    )
    print(f"   ✓ Successfully uploaded test file: {test_key}")

except Exception as e:
    print(f"   ✗ Write test failed: {e}")
    exit(1)

# Test read operation
print("\n5. Testing read operation...")
try:
    response = s3_client.get_object(Bucket=bucket_name, Key=test_key)
    parquet_buffer = io.BytesIO(response['Body'].read())
    df_read = pd.read_parquet(parquet_buffer, engine='pyarrow')

    print(f"   ✓ Successfully read test file")
    print(f"   ✓ Data matches: {df_read['status'].iloc[0] == 'success'}")

except Exception as e:
    print(f"   ✗ Read test failed: {e}")
    exit(1)

# Cleanup - delete test file
print("\n6. Cleaning up test file...")
try:
    s3_client.delete_object(Bucket=bucket_name, Key=test_key)
    print(f"   ✓ Test file deleted")

except Exception as e:
    print(f"   ⚠ Cleanup failed: {e}")
    print(f"      You may need to manually delete: {test_key}")

# Success!
print("\n" + "=" * 60)
print("✓ ALL TESTS PASSED!")
print("=" * 60)
print("\nYour R2 connection is configured correctly.")
print("You can now integrate the Deep User analytics into your app.")
print("\nNext steps:")
print("1. Follow docs/INTEGRATION_GUIDE.md to integrate into app/main.py")
print("2. Start the Streamlit app: streamlit run app/main.py")
print("3. Login to collect your first snapshot!")
print("=" * 60)
