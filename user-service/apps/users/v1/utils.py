"""
Higher-level storage utilities used by views and services.

These functions own the business logic around file naming and path conventions.
The raw GCS operations (upload, delete, sign) live in apps.core.storage.
"""

import uuid as _uuid

from apps.core.storage import delete_blob, generate_signed_url, upload_blob

# Path template for user photos inside the bucket
_PHOTO_PATH_TEMPLATE = "users/{user_id}/{filename}"


def _build_blob_name(user_id: str, content_type: str) -> str:
    """
    Build a unique blob path for a user photo.

    Format: users/<user_id>/<uuid>.<ext>

    Parameters
    ----------
    user_id      : UUID string of the user
    content_type : MIME type (e.g. "image/jpeg" → ext "jpeg")
    """
    ext = content_type.split("/")[-1].lower()
    # Normalise common aliases
    if ext == "jpg":
        ext = "jpeg"
    filename = f"{_uuid.uuid4()}.{ext}"
    return _PHOTO_PATH_TEMPLATE.format(user_id=user_id, filename=filename)


def upload_photo(file_obj, user_id: str, content_type: str = "image/jpeg") -> str:
    """
    Upload a user photo to GCS and return its blob path.

    Parameters
    ----------
    file_obj     : file-like object (e.g. request.FILES['photo'])
    user_id      : UUID string of the owning user
    content_type : MIME type of the image

    Returns
    -------
    str — blob path (e.g. "users/abc123/def456.jpeg")
          Store this in UserPhoto.image_url (it's a path, not a URL).
    """
    blob_name = _build_blob_name(user_id, content_type)
    return upload_blob(blob_name, file_obj, content_type)


def get_photo_url(blob_name: str) -> str:
    """
    Return a V4 signed URL for a photo blob, valid for 1 hour.

    Parameters
    ----------
    blob_name : blob path stored in UserPhoto.image_url

    Returns
    -------
    str — time-limited HTTPS URL for the client to fetch the image
    """
    return generate_signed_url(blob_name)


def remove_photo(blob_name: str) -> None:
    """
    Delete a photo blob from GCS.

    Parameters
    ----------
    blob_name : blob path stored in UserPhoto.image_url
    """
    delete_blob(blob_name)
