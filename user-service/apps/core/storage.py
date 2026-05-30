"""
Low-level GCP Cloud Storage client.

Authentication
--------------
Uses Application Default Credentials (ADC) — no JSON key file needed at runtime.

Local dev  : set GOOGLE_APPLICATION_CREDENTIALS=/path/to/key.json in .env
Production : attach a service account to the VM/Cloud Run instance

Bucket
------
Private bucket — no public access, no ACLs.
Signed URLs (V4) are used to grant time-limited read access.
"""

import datetime
from google.cloud import storage

_BUCKET_NAME = "elara_photos"
_SIGNED_URL_TTL = datetime.timedelta(hours=1)

# Lazy singletons — initialised on first use, reused across requests
_client: storage.Client | None = None
_bucket: storage.Bucket | None = None


def get_bucket() -> storage.Bucket:
    """Return the shared GCS bucket instance (lazy init)."""
    global _client, _bucket
    if _bucket is None:
        # ADC: picks up GOOGLE_APPLICATION_CREDENTIALS locally,
        # or the attached service account in production.
        _client = storage.Client()
        _bucket = _client.bucket(_BUCKET_NAME)
    return _bucket


def upload_blob(blob_name: str, file_obj, content_type: str) -> str:
    """
    Upload a file-like object to GCS.

    Parameters
    ----------
    blob_name    : destination path inside the bucket (e.g. users/123/abc.jpg)
    file_obj     : file-like object opened in binary mode
    content_type : MIME type (e.g. "image/jpeg")

    Returns
    -------
    str — the blob name (path inside the bucket), NOT a public URL
    """
    bucket = get_bucket()
    blob = bucket.blob(blob_name)
    blob.upload_from_file(file_obj, content_type=content_type)
    return blob_name


def delete_blob(blob_name: str) -> None:
    """
    Delete a blob from GCS by its path.
    Silently ignores missing blobs.

    Parameters
    ----------
    blob_name : path inside the bucket (e.g. users/123/abc.jpg)
    """
    bucket = get_bucket()
    blob = bucket.blob(blob_name)
    try:
        blob.delete()
    except Exception:
        pass  # blob already gone — not an error


def generate_signed_url(blob_name: str) -> str:
    """
    Generate a V4 signed URL for a private blob, valid for 1 hour.

    Parameters
    ----------
    blob_name : path inside the bucket (e.g. users/123/abc.jpg)

    Returns
    -------
    str — HTTPS signed URL granting temporary read access
    """
    bucket = get_bucket()
    blob = bucket.blob(blob_name)
    return blob.generate_signed_url(
        version="v4",
        expiration=_SIGNED_URL_TTL,
        method="GET",
    )
