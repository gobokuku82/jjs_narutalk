import os
import boto3
from fastapi import UploadFile

MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "http://localhost:9000")
MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY", "minioadmin")
MINIO_BUCKET = os.getenv("MINIO_BUCKET", "documents")

s3_client = boto3.client(
    "s3",
    endpoint_url=MINIO_ENDPOINT,
    aws_access_key_id=MINIO_ACCESS_KEY,
    aws_secret_access_key=MINIO_SECRET_KEY,
    region_name="us-east-1",
)

def upload_file(file: UploadFile):
    # 버킷이 없으면 생성
    try:
        s3_client.head_bucket(Bucket=MINIO_BUCKET)
    except Exception:
        s3_client.create_bucket(Bucket=MINIO_BUCKET)
    # 파일 업로드
    s3_client.upload_fileobj(file.file, MINIO_BUCKET, file.filename)
    url = f"{MINIO_ENDPOINT}/{MINIO_BUCKET}/{file.filename}"
    return url 