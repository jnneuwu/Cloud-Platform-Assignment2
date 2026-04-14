from pymongo import ASCENDING, MongoClient

from .config import settings


_client = MongoClient(settings.mongodb_uri) if settings.mongodb_uri else None


def get_db():
    if _client is None:
        raise RuntimeError("MONGODB_URI is not configured.")
    return _client[settings.mongodb_db_name]


def ensure_indexes():
    db = get_db()

    db.users.create_index([("firebase_uid", ASCENDING)], unique=True)
    db.directories.create_index([("owner_uid", ASCENDING), ("path", ASCENDING)], unique=True)
    db.directories.create_index(
        [("owner_uid", ASCENDING), ("parent_id", ASCENDING), ("name", ASCENDING)],
        unique=True,
        partialFilterExpression={"parent_id": {"$exists": True, "$ne": None}},
    )
    db.files.create_index([("owner_uid", ASCENDING), ("directory_id", ASCENDING), ("name", ASCENDING)], unique=True)
