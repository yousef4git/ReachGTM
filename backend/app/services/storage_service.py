"""S3-compatible object storage for knowledge document uploads (PR #22).

Uses boto3, so it works with AWS S3 and any S3-compatible store. ReachGTM
deploys on Cloudflare R2 (S3-compatible): set S3_ENDPOINT_URL to the R2 endpoint,
AWS_REGION=auto, and the R2 token as AWS_ACCESS_KEY_ID / AWS_SECRET_ACCESS_KEY.
With S3_ENDPOINT_URL empty it talks to real AWS S3.

boto3 is synchronous, so each call runs in a worker thread to avoid blocking the
event loop.
"""
from __future__ import annotations

import asyncio
from functools import lru_cache
from typing import Optional

import boto3
from botocore.config import Config

from backend.app.config import settings


@lru_cache(maxsize=1)
def _client():
    """Build (once) an S3 client honouring the configured endpoint/credentials."""
    kwargs: dict = {"region_name": settings.aws_region or None}
    if settings.s3_endpoint_url:
        kwargs["endpoint_url"] = settings.s3_endpoint_url  # Cloudflare R2 / custom
    if settings.aws_access_key_id and settings.aws_secret_access_key:
        kwargs["aws_access_key_id"] = settings.aws_access_key_id
        kwargs["aws_secret_access_key"] = settings.aws_secret_access_key
    # else: boto3 falls back to the standard credential chain (env, etc.)
    return boto3.client("s3", config=Config(signature_version="s3v4"), **kwargs)


def _resolve_bucket(bucket: Optional[str]) -> str:
    resolved = bucket or settings.s3_bucket_name
    if not resolved:
        raise ValueError("No object-storage bucket configured (set S3_BUCKET_NAME)")
    return resolved


def object_url(key: str, bucket: Optional[str] = None) -> str:
    """Return a stable URL/reference for an object."""
    resolved = _resolve_bucket(bucket)
    if settings.s3_endpoint_url:
        return f"{settings.s3_endpoint_url.rstrip('/')}/{resolved}/{key}"
    return f"https://{resolved}.s3.{settings.aws_region}.amazonaws.com/{key}"


async def upload_object(content: bytes, key: str, bucket: Optional[str] = None) -> str:
    """Upload bytes under `key`; returns the object's URL. Defaults to S3_BUCKET_NAME."""
    resolved = _resolve_bucket(bucket)
    await asyncio.to_thread(_client().put_object, Bucket=resolved, Key=key, Body=content)
    return object_url(key, resolved)


async def download_object(key: str, bucket: Optional[str] = None) -> bytes:
    """Download and return the bytes stored under `key`."""
    resolved = _resolve_bucket(bucket)
    resp = await asyncio.to_thread(_client().get_object, Bucket=resolved, Key=key)
    return resp["Body"].read()
