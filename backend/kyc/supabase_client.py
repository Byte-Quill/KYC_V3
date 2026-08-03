"""Thin wrapper around the Supabase Python client.

Provides lazy-initialised clients for:
  - Postgres (via the service role, bypassing RLS for trusted server code)
  - Storage (document uploads)
  - Realtime (broadcasting status-change events)

All helpers degrade gracefully to no-ops when Supabase is not configured, so
local development against SQLite keeps working without any Supabase project.
"""
from __future__ import annotations

import logging
from functools import lru_cache
from typing import Any, Optional

from django.conf import settings

logger = logging.getLogger(__name__)

try:
    from supabase import Client, create_client
except ImportError:  # pragma: no cover - supabase is an optional runtime dep
    Client = None  # type: ignore
    create_client = None  # type: ignore


def is_configured() -> bool:
    """True when the minimum Supabase settings are present."""
    return bool(settings.SUPABASE_URL and settings.SUPABASE_SERVICE_ROLE_KEY)


@lru_cache(maxsize=1)
def get_client() -> Optional["Client"]:
    """Return a cached service-role Supabase client, or None if unconfigured."""
    if not is_configured() or create_client is None:
        return None
    return create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_ROLE_KEY)


# ---- Storage ----

def upload_document(path: str, data: bytes, content_type: str) -> Optional[str]:
    """Upload bytes to the configured bucket. Returns the storage path or None."""
    client = get_client()
    if client is None:
        return None
    try:
        client.storage.from_(settings.SUPABASE_STORAGE_BUCKET).upload(
            path=path,
            file=data,
            file_options={"content-type": content_type, "upsert": "true"},
        )
        return path
    except Exception as exc:  # noqa: BLE001
        logger.warning("Supabase storage upload failed: %s", exc)
        return None


def get_public_url(path: str) -> Optional[str]:
    """Return the public URL for a stored object, or None if unconfigured."""
    client = get_client()
    if client is None:
        return None
    try:
        return client.storage.from_(settings.SUPABASE_STORAGE_BUCKET).get_public_url(path)
    except Exception as exc:  # noqa: BLE001
        logger.warning("Supabase get_public_url failed: %s", exc)
        return None


def create_signed_url(path: str, expires_in: int = 3600) -> Optional[str]:
    """Return a time-limited signed URL for a private object."""
    client = get_client()
    if client is None:
        return None
    try:
        res = client.storage.from_(settings.SUPABASE_STORAGE_BUCKET).create_signed_url(
            path, expires_in
        )
        return res.get("signedURL") or res.get("signedUrl")
    except Exception as exc:  # noqa: BLE001
        logger.warning("Supabase create_signed_url failed: %s", exc)
        return None


# ---- Realtime ----

def broadcast_status_change(application_id: str, status: str, detail: str = "") -> bool:
    """Broadcast an application status change to a Realtime channel.

    The frontend can subscribe to the `kyc-status` channel to receive live
    updates without polling. Returns True when the event was sent.
    """
    client = get_client()
    if client is None:
        return False
    try:
        channel = client.channel("kyc-status")
        channel.send_broadcast(
            "status_changed",
            {"application_id": application_id, "status": status, "detail": detail},
        )
        return True
    except Exception as exc:  # noqa: BLE001
        logger.warning("Supabase realtime broadcast failed: %s", exc)
        return False


# ---- Generic helpers ----

def insert(table: str, row: dict[str, Any]) -> Optional[dict[str, Any]]:
    """Insert a row into a Supabase table (service role). Returns the row."""
    client = get_client()
    if client is None:
        return None
    try:
        res = client.table(table).insert(row).execute()
        return res.data[0] if res.data else None
    except Exception as exc:  # noqa: BLE001
        logger.warning("Supabase insert into %s failed: %s", table, exc)
        return None
