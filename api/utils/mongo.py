from django.conf import settings
from pymongo import MongoClient
from urllib.parse import urlparse
import threading
import logging

logger = logging.getLogger(__name__)

# Thread-safe lazy singleton for MongoDB DB instance
_client_lock = threading.Lock()
_db_instance = None


def _choose_db_name_from_settings(parsed_uri_path: str | None) -> str:
    """
    Resolve DB name using (in order):
     - DB name from the URI path (if present)
     - settings.MONGODB dict 'DB_NAME' (if available)
     - settings.MONGODB_DB_NAME (legacy single-var)
     - fallback 'provision_mongo'
    """
    if parsed_uri_path:
        name = parsed_uri_path.strip("/")
        if name:
            return name

    # settings.MONGODB may be dict (as used in settings.py)
    try:
        m = getattr(settings, "MONGODB", None)
        if isinstance(m, dict):
            dbn = m.get("DB_NAME")
            if dbn:
                return dbn
    except Exception:
        pass

    # legacy single ENV var
    dbn = getattr(settings, "MONGODB_DB_NAME", None)
    if dbn:
        return dbn

    return "provision_mongo"


def get_mongo_client():
    """
    Return a cached/persistent pymongo database handle.

    Behavior:
    - First preference: use settings.MONGODB_URL (per your request).
    - Backward compatibility: if MONGODB_URL not set, attempt settings.MONGODB_URI.
    - If a full URI is provided it is passed directly to MongoClient and the DB name is picked
      from the URI path (or from settings.MONGODB / settings.MONGODB_DB_NAME).
    - Otherwise fall back to host/port/user/password keys on settings.MONGODB (or individual
      settings like MONGODB_HOST) to construct a connection.

    Returns the DB object (client[db_name]) and caches it in module global `_db_instance`.
    """
    global _db_instance
    if _db_instance is not None:
        return _db_instance

    # Try to obtain a connection URI from settings (MONGODB_URL requested)
    mongo_uri = getattr(settings, "MONGODB_URL", None) or getattr(settings, "MONGODB_URI", None)
    print(mongo_uri)

    # Also tolerate settings.MONGODB dict that may include 'URI'
    if not mongo_uri:
        try:
            m = getattr(settings, "MONGODB", None)
            if isinstance(m, dict):
                mongo_uri = m.get("URI") or m.get("URL")  # be flexible
        except Exception:
            mongo_uri = None

    try:
        with _client_lock:
            if _db_instance is not None:
                return _db_instance

            if mongo_uri:
                # Use the full URI. Determine DB name from the path portion if present.
                parsed = urlparse(mongo_uri)
                db_name = _choose_db_name_from_settings(parsed.path)
                client = MongoClient(mongo_uri)
                _db_instance = client[db_name]
                logger.info("Connected to MongoDB (URI) database '%s'", db_name)
                return _db_instance

            # No URI: fallback to host/port/user/password style config
            # Prefer settings.MONGODB dict, else individual settings
            m = getattr(settings, "MONGODB", None) or {}
            host = m.get("HOST") or getattr(settings, "MONGODB_HOST", "localhost")
            port = int(m.get("PORT") or getattr(settings, "MONGODB_PORT", 27017) or 27017)
            db_name = m.get("DB_NAME") or getattr(settings, "MONGODB_DB_NAME", "provision_mongo")
            user = m.get("USER") or getattr(settings, "MONGODB_USER", None)
            password = m.get("PASSWORD") or getattr(settings, "MONGODB_PASSWORD", None)

            if user and password:
                # Build a safe mongodb URI for auth
                uri = f"mongodb://{user}:{password}@{host}:{port}/{db_name}"
                client = MongoClient(uri)
                _db_instance = client[db_name]
                logger.info("Connected to MongoDB database '%s' at %s:%s using user auth", db_name, host, port)
                return _db_instance
            else:
                client = MongoClient(host, port)
                _db_instance = client[db_name]
                logger.info("Connected to MongoDB database '%s' at %s:%s", db_name, host, port)
                return _db_instance
    except Exception as exc:
        logger.exception("Failed to create MongoDB client: %s", exc)
        raise