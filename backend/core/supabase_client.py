from supabase import create_client
from backend.core.config import SUPABASE_URL, SUPABASE_SERVICE_KEY
import logging

logger = logging.getLogger("gridlock")

_client = None

def get_supabase_client():
    """
    Returns a singleton Supabase client.
    Raises RuntimeError if configuration is missing.
    """
    global _client
    if _client is not None:
        return _client
    
    if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
        raise RuntimeError(
            "SUPABASE_URL and SUPABASE_SERVICE_KEY must be set to initialize the Supabase client."
        )
    
    try:
        _client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
        return _client
    except Exception as e:
        logger.exception("Failed to initialize Supabase client")
        raise RuntimeError(f"Could not connect to Supabase: {e}")
