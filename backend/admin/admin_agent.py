"""
Admin agent — protected endpoints for knowledge base ingestion and reindexing.
Requires ADMIN_SECRET for authentication.
"""
from config import ADMIN_SECRET


def verify_admin_token(token: str) -> bool:
    """
    Verify admin secret token for protected operations.
    Returns False if token is missing or invalid.
    """
    try:
        if not ADMIN_SECRET or not token:
            return False
        return token == ADMIN_SECRET
    except Exception:
        return False


def trigger_reindex() -> dict:
    """
    Trigger full knowledge base re-ingestion and vector reindex.
    Returns status dict with success flag and message.
    """
    try:
        # Phase 1: ingest.py integration will be wired here
        return {"success": True, "message": "Reindex queued"}
    except Exception as e:
        return {"success": False, "message": str(e)}
