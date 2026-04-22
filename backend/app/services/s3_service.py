# backend/app/services/s3_service.py
import boto3
import os

s3 = boto3.client(
    "s3",
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
    region_name=os.getenv("AWS_REGION")
)

def upload_file(file_name, file_bytes):
    bucket = os.getenv("AWS_BUCKET_NAME")
    s3.put_object(
        Bucket=bucket,
        Key=file_name,
        Body=file_bytes
    )
    return f"https://{bucket}.s3.amazonaws.com/{file_name}"