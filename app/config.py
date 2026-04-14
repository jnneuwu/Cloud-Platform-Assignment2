from dataclasses import dataclass
import os


@dataclass(frozen=True)
class Settings:
    app_name: str = "Mini Dropbox"
    mongodb_uri: str = os.getenv("MONGODB_URI", "")
    mongodb_db_name: str = os.getenv("MONGODB_DB_NAME", "cloud_platform_assignment")
    session_secret: str = os.getenv("SESSION_SECRET", "change-this-before-submitting")
    firebase_project_id: str = os.getenv("FIREBASE_PROJECT_ID", "")
    firebase_credentials_path: str = os.getenv("FIREBASE_CREDENTIALS_PATH", "")
    azure_storage_connection_string: str = os.getenv("AZURE_STORAGE_CONNECTION_STRING", "")
    azure_container_name: str = os.getenv("AZURE_CONTAINER_NAME", "dropbox-files")


settings = Settings()
