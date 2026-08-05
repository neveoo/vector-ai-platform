"""
Thin wrapper around S3-compatible object storage (AWS S3, or Backblaze
B2 / DigitalOcean Spaces if you want a cheaper option for a demo
deployment). Keeping this behind a small function interface means
swapping providers later is a one-file change.
"""
import uuid
from uuid import UUID

import boto3

from app.core.config import get_settings

settings = get_settings()

_s3_client = boto3.client(
    "s3",
    endpoint_url=settings.s3_endpoint_url,  # None => real AWS; set for B2/Spaces/minio
    aws_access_key_id=settings.aws_access_key_id,
    aws_secret_access_key=settings.aws_secret_access_key,
    region_name=settings.aws_region,
)


def upload_file_to_storage(*, tenant_id: UUID, filename: str, contents: bytes) -> str:
    """
    Stores the raw file under a tenant-prefixed key so that even at the
    storage layer, one tenant's files live in a distinct namespace from
    another's -- defense in depth alongside the RLS-protected metadata.
    """
    key = f"{tenant_id}/{uuid.uuid4()}-{filename}"
    _s3_client.put_object(Bucket=settings.s3_bucket, Key=key, Body=contents)
    return key


def download_file_from_storage(storage_key: str) -> bytes:
    response = _s3_client.get_object(Bucket=settings.s3_bucket, Key=storage_key)
    return response["Body"].read()
