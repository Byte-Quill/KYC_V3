"""Thin Supabase Storage client via plain REST.

Uses the service-role key directly instead of the full `supabase` SDK
(which drags in pydantic/httpx/websockets) to keep the backend install
lightweight. All helpers degrade to no-ops when Supabase is unconfigured.
"""
import logging

import requests
from django.conf import settings

logger = logging.getLogger(__name__)


def is_configured() -> bool:
    """True when the minimum Supabase settings are present."""
    return bool(settings.SUPABASE_URL and settings.SUPABASE_SERVICE_ROLE_KEY)


def _headers() -> dict[str, str]:
    return {
        "Authorization": f"Bearer {settings.SUPABASE_SERVICE_ROLE_KEY}",
        "apikey": settings.SUPABASE_SERVICE_ROLE_KEY,
    }


# ---- Storage ----

def upload_document(path: str, data: bytes, content_type: str) -> str | None:
    """Upload bytes to the configured bucket. Returns the storage path or None."""
    if not is_configured():
        return None
    try:
        url = (
            f"{settings.SUPABASE_URL}/storage/v1/object/"
            f"{settings.SUPABASE_STORAGE_BUCKET}/{path}"
        )
        headers = _headers()
        headers["Content-Type"] = content_type
        headers["x-upsert"] = "true"
        res = requests.post(url, data=data, headers=headers, timeout=30)
        res.raise_for_status()
        return path
    except Exception as exc:  # noqa: BLE001
        logger.warning("Supabase storage upload failed: %s", exc)
        return None


def create_signed_url(path: str, expires_in: int = 3600) -> str | None:
    """Return a time-limited signed URL for a private object."""
    if not is_configured():
        return None
    try:
        url = (
            f"{settings.SUPABASE_URL}/storage/v1/object/sign/"
            f"{settings.SUPABASE_STORAGE_BUCKET}/{path}"
        )
        res = requests.post(
            url, json={"expiresIn": expires_in}, headers=_headers(), timeout=10
        )
        res.raise_for_status()
        signed = res.json().get("signedURL")
        return f"{settings.SUPABASE_URL}{signed}" if signed else None
    except Exception as exc:  # noqa: BLE001
        logger.warning("Supabase create_signed_url failed: %s", exc)
        return None


# ---- Embeddings ----

def trigger_embedding(application_id: str) -> bool:
    """Ask the Supabase Edge Function to (re)generate the application embedding.

    The Edge Function is authenticated with a shared secret so only our backend
    can invoke it. No-op when the secret is unset.
    """
    secret = getattr(settings, "SUPABASE_FUNCTION_SECRET", "")
    url = getattr(settings, "SUPABASE_FUNCTIONS_URL", "")
    if not secret or not url:
        return False
    try:
        res = requests.post(
            f"{url}/generate-embedding",
            json={"application_id": str(application_id)},
            headers={"Authorization": f"Bearer {secret}"},
            timeout=5,
        )
        return res.status_code == 200
    except Exception as exc:  # noqa: BLE001
        logger.warning("Embedding trigger failed: %s", exc)
        return False