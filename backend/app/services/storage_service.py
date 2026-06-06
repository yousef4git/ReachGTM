# TODO: Epic 3 PR #22 — S3 document storage
async def upload_to_s3(content: bytes, key: str, bucket: str) -> str:
    """Returns the S3 URL of the uploaded object."""
    raise NotImplementedError("S3 storage implemented in Epic 3 PR #22")

async def download_from_s3(key: str, bucket: str) -> bytes:
    raise NotImplementedError("S3 storage implemented in Epic 3 PR #22")
