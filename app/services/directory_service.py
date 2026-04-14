from datetime import datetime, timezone

from bson import ObjectId

from ..db import get_db


def _utcnow():
    return datetime.now(timezone.utc)


def _normalise_name(name: str) -> str:
    cleaned = name.strip()
    if not cleaned:
        raise ValueError("Directory name cannot be empty.")
    if "/" in cleaned or "\\" in cleaned:
        raise ValueError("Directory name cannot contain slashes.")
    if cleaned in {".", ".."}:
        raise ValueError("Directory name cannot be . or ..")
    return cleaned


def _child_path(parent_path: str, name: str) -> str:
    if parent_path == "/":
        return f"/{name}"
    return f"{parent_path}/{name}"


def get_root_directory(owner_uid: str):
    directory = get_db().directories.find_one({"owner_uid": owner_uid, "path": "/"})
    if directory is None:
        raise ValueError("Root directory was not found for this user.")
    return directory


def get_directory_by_id(owner_uid: str, directory_id: str):
    try:
        object_id = ObjectId(directory_id)
    except Exception:
        return None
    return get_db().directories.find_one({"_id": object_id, "owner_uid": owner_uid})


def list_child_directories(owner_uid: str, parent_id):
    return list(
        get_db().directories.find(
            {"owner_uid": owner_uid, "parent_id": parent_id}
        ).sort("name", 1)
    )


def create_directory(owner_uid: str, parent_id, name: str):
    name = _normalise_name(name)
    db = get_db()
    parent = db.directories.find_one({"_id": parent_id, "owner_uid": owner_uid})

    if parent is None:
        raise ValueError("Parent directory not found.")

    path = _child_path(parent["path"], name)
    existing = db.directories.find_one({"owner_uid": owner_uid, "path": path})
    if existing is not None:
        raise ValueError("A directory with that name already exists here.")

    db.directories.insert_one(
        {
            "owner_uid": owner_uid,
            "name": name,
            "parent_id": parent_id,
            "path": path,
            "created_at": _utcnow(),
            "updated_at": _utcnow(),
        }
    )


def delete_directory(owner_uid: str, directory_id: str):
    directory = get_directory_by_id(owner_uid, directory_id)
    if directory is None:
        raise ValueError("Directory not found.")
    if directory["path"] == "/":
        raise ValueError("The root directory cannot be deleted.")

    db = get_db()
    has_children = db.directories.count_documents({"owner_uid": owner_uid, "parent_id": directory["_id"]}) > 0
    has_files = db.files.count_documents({"owner_uid": owner_uid, "directory_id": directory["_id"]}) > 0

    if has_children or has_files:
        raise ValueError("Directory is not empty.")

    db.directories.delete_one({"_id": directory["_id"]})
