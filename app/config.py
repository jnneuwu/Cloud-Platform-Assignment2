"""Application configuration pulled from environment variables.

Kept intentionally small. ``firebase_credentials_path`` is no longer required
because token verification is done with ``google.oauth2.id_token`` (see
``app/auth.py``) which only needs the public Firebase certificates fetched at
runtime. ``session_secret`` is gone because we use the Firebase cookie pattern
from the example, not server-side sessions.
"""
from dataclasses import dataclass
import os


@dataclass(frozen=True)
class Settings:
    app_name: str = "Mini Dropbox"
    mongodb_uri: str = os.getenv("MONGODB_URI", "")
    mongodb_db_name: str = os.getenv("MONGODB_DB_NAME", "cloud_platform_assignment")
    azure_storage_connection_string: str = os.getenv(
        "AZURE_STORAGE_CONNECTION_STRING", "UseDevelopmentStorage=true"
    )
    azure_container_name: str = os.getenv("AZURE_CONTAINER_NAME", "dropbox-files")


settings = Settings()
