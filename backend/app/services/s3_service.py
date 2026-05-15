# backend/app/services/s3_service.py
#import boto3
#import os

#s3 = boto3.client(
#   "s3",
#    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
#    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
#    region_name=os.getenv("AWS_REGION")
#)

#def upload_file(file_name, file_bytes):
#    bucket = os.getenv("AWS_BUCKET_NAME")
#    s3.put_object(
#        Bucket=bucket,
#        Key=file_name,
#        Body=file_bytes
#    )
#    return f"https://{bucket}.s3.amazonaws.com/{file_name}"


# backend/app/services/s3_service.py
#
# LOCAL DEV VERSION — saves uploaded files to disk instead of S3.
# Same function signature as the original S3 version: upload_file(file_name, file_bytes).
#
# Files are saved under /app/uploads inside the container,
# which is exposed at http://localhost:8000/uploads/<path>
#
# When ready for production, swap this file back to the original S3 version
# (or use an env var STORAGE_BACKEND=s3|local to toggle).

import os
from pathlib import Path

# Base directory where files are written inside the container
UPLOAD_DIR = Path("/app/uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# Public base URL — backend serves /uploads/<key> as a static mount
# Use env var if set, otherwise fall back to localhost for dev
PUBLIC_BASE_URL = os.getenv("PUBLIC_API_URL", "http://localhost:8000")


def upload_file(file_name: str, file_bytes: bytes) -> str:
    """
    Save bytes to local disk under UPLOAD_DIR and return a public URL.

    file_name can contain forward slashes for nested folders
    (e.g. "tenant-documents/<id>/<uuid>-photo.jpg").
    """
    # Build full local path
    full_path = UPLOAD_DIR / file_name

    # Make sure parent directories exist
    full_path.parent.mkdir(parents=True, exist_ok=True)

    # Write the file
    with open(full_path, "wb") as f:
        f.write(file_bytes)

    # Return the public URL that the frontend can use to fetch it
    return f"{PUBLIC_BASE_URL}/uploads/{file_name}"