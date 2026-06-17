"""Tests for the S3/R2-compatible storage service (PR #22).

boto3 is mocked — no network, no real bucket. Deterministic.
"""
import io
import uuid

import pytest

import backend.app.services.storage_service as storage
from backend.app.config import settings
from backend.app.services.knowledge_service import _storage_key


class _FakeS3:
    def __init__(self):
        self.objects: dict[tuple[str, str], bytes] = {}
        self.puts: list[tuple] = []

    def put_object(self, Bucket, Key, Body):
        self.puts.append((Bucket, Key, Body))
        self.objects[(Bucket, Key)] = Body

    def get_object(self, Bucket, Key):
        return {"Body": io.BytesIO(self.objects[(Bucket, Key)])}


@pytest.fixture
def fake_s3(monkeypatch):
    client = _FakeS3()
    monkeypatch.setattr(storage, "_client", lambda: client)
    monkeypatch.setattr(settings, "s3_bucket_name", "test-bucket")
    monkeypatch.setattr(settings, "s3_endpoint_url", "")
    monkeypatch.setattr(settings, "aws_region", "us-east-1")
    return client


# ── upload / download ────────────────────────────────────────────────────────

class TestUploadDownload:
    @pytest.mark.asyncio
    async def test_upload_puts_object_and_returns_url(self, fake_s3):
        url = await storage.upload_object(b"hello", "acme/doc.pdf")
        assert fake_s3.puts == [("test-bucket", "acme/doc.pdf", b"hello")]
        assert url == "https://test-bucket.s3.us-east-1.amazonaws.com/acme/doc.pdf"

    @pytest.mark.asyncio
    async def test_round_trip(self, fake_s3):
        await storage.upload_object(b"payload-bytes", "k/file.docx")
        out = await storage.download_object("k/file.docx")
        assert out == b"payload-bytes"

    @pytest.mark.asyncio
    async def test_explicit_bucket_overrides_default(self, fake_s3):
        await storage.upload_object(b"x", "k", bucket="other")
        assert fake_s3.puts[0][0] == "other"


# ── bucket resolution & URL shape ────────────────────────────────────────────

class TestBucketAndUrl:
    def test_missing_bucket_raises(self, monkeypatch):
        monkeypatch.setattr(settings, "s3_bucket_name", "")
        with pytest.raises(ValueError, match="No object-storage bucket"):
            storage._resolve_bucket(None)

    def test_r2_endpoint_url_shape(self, monkeypatch):
        monkeypatch.setattr(settings, "s3_bucket_name", "bkt")
        monkeypatch.setattr(settings, "s3_endpoint_url", "https://acc.r2.cloudflarestorage.com")
        assert storage.object_url("a/b.pdf") == "https://acc.r2.cloudflarestorage.com/bkt/a/b.pdf"

    def test_s3_url_shape(self, monkeypatch):
        monkeypatch.setattr(settings, "s3_bucket_name", "bkt")
        monkeypatch.setattr(settings, "s3_endpoint_url", "")
        monkeypatch.setattr(settings, "aws_region", "eu-west-1")
        assert storage.object_url("a/b.pdf") == "https://bkt.s3.eu-west-1.amazonaws.com/a/b.pdf"


# ── key helper used by ingest ────────────────────────────────────────────────

def test_storage_key_is_tenant_scoped():
    doc_id = uuid.UUID("00000000-0000-0000-0000-000000000001")
    key = _storage_key("company-123", doc_id, "report.pdf")
    assert key == "company-123/00000000-0000-0000-0000-000000000001/report.pdf"
