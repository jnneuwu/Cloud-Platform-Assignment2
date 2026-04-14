from datetime import datetime, timezone

from ..db import get_db


def _utcnow():
    return datetime.now(timezone.utc)


def ensure_user_with_root_directory(firebase_uid: str, email: str | None, display_name: str | None):
    db = get_db()
    users = db.users
    directories = db.directories

    user = users.find_one({"firebase_uid": firebase_uid})
    root_directory = directories.find_one({"owner_uid": firebase_uid, "path": "/"})

    if root_directory is None:
        root_directory_id = directories.insert_one(
            {
                "owner_uid": firebase_uid,
                "name": "/",
                "parent_id": None,
                "path": "/",
                "created_at": _utcnow(),
                "updated_at": _utcnow(),
            }
        ).inserted_id
        root_directory = directories.find_one({"_id": root_directory_id})

    if user is None:
        user_id = users.insert_one(
            {
                "firebase_uid": firebase_uid,
                "email": email or "",
                "display_name": display_name or "",
                "root_directory_id": root_directory["_id"],
                "created_at": _utcnow(),
                "updated_at": _utcnow(),
            }
        ).inserted_id
        user = users.find_one({"_id": user_id})
        return user, root_directory

    users.update_one(
        {"_id": user["_id"]},
        {
            "$set": {
                "email": email or user.get("email", ""),
                "display_name": display_name or user.get("display_name", ""),
                "root_directory_id": root_directory["_id"],
                "updated_at": _utcnow(),
            }
        },
    )
    user = users.find_one({"_id": user["_id"]})
    return user, root_directory
