"""
Supabase Storage upload module voor ProfielScore.
Upload rapport HTML, mockup PNG, en banner PNG naar persistent storage.
"""

import os
from datetime import datetime
from typing import Optional


def _get_storage_client():
    """Maak Supabase storage client met service_role key."""
    from supabase import create_client
    url = os.environ.get("SUPABASE_URL", "")
    key = os.environ.get("SUPABASE_SERVICE_KEY", "")
    if not url or not key:
        raise ValueError("SUPABASE_URL of SUPABASE_SERVICE_KEY ontbreekt")
    return create_client(url, key)


def _ensure_bucket(client, bucket: str = "profielscore-assets"):
    """Maak bucket aan als die niet bestaat (idempotent)."""
    try:
        client.storage.create_bucket(bucket, options={"public": True})
    except Exception:
        pass


def _safe_name(name: str) -> str:
    """Maak naam URL-safe."""
    return "".join(c if c.isalnum() or c in "-_" else "_" for c in name).strip("_")[:50]


def upload_bytes(
    data: bytes,
    filename: str,
    content_type: str,
    lead_name: str,
    bucket: str = "profielscore-assets",
) -> str:
    """Upload bytes naar Supabase Storage, return public URL."""
    try:
        client = _get_storage_client()
        _ensure_bucket(client, bucket)

        date_prefix = datetime.now().strftime("%Y%m%d")
        safe = _safe_name(lead_name)
        storage_path = f"{date_prefix}/{safe}/{filename}"

        client.storage.from_(bucket).upload(
            storage_path, data, {"content-type": content_type, "upsert": "true"}
        )

        public_url = client.storage.from_(bucket).get_public_url(storage_path)
        print(f"   ✅ Storage upload: {storage_path}")
        return public_url

    except Exception as e:
        print(f"   ⚠️ Storage upload fout ({filename}): {e}")
        return ""


def upload_rapport(html_content: str, lead_name: str) -> str:
    """Upload hosted rapport HTML, return public URL."""
    return upload_bytes(
        data=html_content.encode("utf-8"),
        filename="rapport.html",
        content_type="text/html; charset=utf-8",
        lead_name=lead_name,
    )


def upload_image(image_bytes: bytes, lead_name: str, filename: str = "mockup.png") -> str:
    """Upload PNG image, return public URL."""
    return upload_bytes(
        data=image_bytes,
        filename=filename,
        content_type="image/png",
        lead_name=lead_name,
    )


def upload_file(file_path: str, lead_name: str) -> str:
    """Upload bestand van disk, return public URL."""
    if not file_path or not os.path.exists(file_path):
        return ""

    filename = os.path.basename(file_path)
    content_type = "image/png" if filename.endswith(".png") else "text/html"

    with open(file_path, "rb") as f:
        data = f.read()

    return upload_bytes(data, filename, content_type, lead_name)
