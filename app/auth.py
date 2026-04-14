import firebase_admin
from firebase_admin import auth, credentials

from .config import settings


def _ensure_firebase_admin():
    if firebase_admin._apps:
        return

    if not settings.firebase_credentials_path:
        raise RuntimeError("FIREBASE_CREDENTIALS_PATH is not configured.")

    certificate = credentials.Certificate(settings.firebase_credentials_path)
    if settings.firebase_project_id:
        firebase_admin.initialize_app(certificate, {"projectId": settings.firebase_project_id})
    else:
        firebase_admin.initialize_app(certificate)


def verify_firebase_id_token(id_token: str) -> dict:
    if not id_token:
        raise ValueError("Missing Firebase ID token.")

    _ensure_firebase_admin()
    return auth.verify_id_token(id_token)
