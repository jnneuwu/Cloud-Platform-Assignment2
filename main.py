"""Mini Dropbox - one-file FastAPI server.

Follows PaaS-by-example.pdf style: single main.py, cookie-based Firebase auth,
MongoDB for metadata, Azurite (Azure Blob Storage emulator) for file blobs.

Implements every assignment task in Groups 1-4.
"""

import hashlib
import os
import uuid
from datetime import datetime, timezone

import google.oauth2.id_token
from azure.storage.blob import BlobServiceClient
from bson import ObjectId
from fastapi import FastAPI, File, Form, Request, UploadFile
from fastapi.responses import HTMLResponse, RedirectResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from google.auth.transport import requests as google_requests
from pymongo import ASCENDING, MongoClient

# --- Configuration (read once from environment) ---
MONGODB_URI = os.getenv("MONGODB_URI", "")
DB_NAME = os.getenv("MONGODB_DB_NAME", "cloud_platform_assignment")
CONTAINER = os.getenv("AZURE_CONTAINER_NAME", "dropbox-files")

# Full Azurite dev connection string. The newer azure-storage-blob versions
# do not accept the "UseDevelopmentStorage=true" shortcut anymore, so we keep
# the expanded form here. The account key below is the public one shipped
# with Azurite, not a secret.
AZURITE_DEV = (
    "DefaultEndpointsProtocol=http;"
    "AccountName=devstoreaccount1;"
    "AccountKey=Eby8vdM02xNOcqFlqUwJPLlmEtlCDXJ1OUzFT50uSRZ6"
    "IFsuFq2UVErCz4I6tq/K1SZFPTOtr/KBHBeksoGMGw==;"
    "BlobEndpoint=http://127.0.0.1:10000/devstoreaccount1;"
)
AZURE_CONN = os.getenv("AZURE_STORAGE_CONNECTION_STRING") or AZURITE_DEV
if AZURE_CONN.strip().lower() == "usedevelopmentstorage=true":
    AZURE_CONN = AZURITE_DEV

# --- Cloud clients (created once at import time) ---
app = FastAPI(title="Mini Dropbox")
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

firebase_request_adapter = google_requests.Request()
mongo = MongoClient(MONGODB_URI) if MONGODB_URI else None
db = mongo[DB_NAME] if mongo is not None else None
blob_service = BlobServiceClient.from_connection_string(AZURE_CONN)


@app.on_event("startup")
def on_startup():
    """Create the blob container and the unique indexes we rely on."""
    # Make sure the Azurite/Azure container exists.
    try:
        blob_service.create_container(CONTAINER)
    except Exception:
        pass  # Already exists - safe to ignore.

    if db is None:
        return

    # One user document per Firebase uid.
    db.users.create_index([("uid", ASCENDING)], unique=True)
    # Two directories with the same path under the same user is a major bug -
    # this unique index makes it impossible at the database level.
    db.directories.create_index([("uid", ASCENDING), ("path", ASCENDING)], unique=True)
    # Same idea for files: same name twice in the same directory is forbidden.
    db.files.create_index(
        [("uid", ASCENDING), ("dir_id", ASCENDING), ("name", ASCENDING)], unique=True
    )


# --- Helpers ----------------------------------------------------------------

def get_user(request: Request):
    """Return the decoded Firebase token from the cookie, or None if invalid.

    Matches PaaS-by-example.pdf Example 03: token cookie -> verify_firebase_token.
    """
    token = request.cookies.get("token")
    if not token:
        return None
    try:
        return google.oauth2.id_token.verify_firebase_token(
            token, firebase_request_adapter
        )
    except ValueError as err:
        print(f"Token verification failed: {err}")
        return None


def bootstrap(uid: str, email: str | None):
    """First-login setup: create the User document and the root '/' directory."""
    if db.users.find_one({"uid": uid}) is None:
        db.users.insert_one(
            {"uid": uid, "email": email or "", "created": datetime.now(timezone.utc)}
        )
    if db.directories.find_one({"uid": uid, "path": "/"}) is None:
        db.directories.insert_one(
            {
                "uid": uid,
                "name": "/",
                "parent": None,
                "path": "/",
                "created": datetime.now(timezone.utc),
            }
        )


def current_dir(request: Request, uid: str):
    """Return the directory the user is currently inside.

    Tracked in the 'cur' cookie (set by /open-dir and /up-dir). Falls back to
    the user's root directory.
    """
    cur_id = request.cookies.get("cur")
    if cur_id:
        try:
            d = db.directories.find_one({"_id": ObjectId(cur_id), "uid": uid})
            if d:
                return d
        except Exception:
            pass
    return db.directories.find_one({"uid": uid, "path": "/"})


def child_path(parent_path: str, name: str) -> str:
    """Build a path string for a child directory."""
    return f"/{name}" if parent_path == "/" else f"{parent_path}/{name}"


def full_file_path(uid: str, file_doc: dict) -> str:
    """Build the visible path of a file, e.g. /docs/notes.txt."""
    parent = db.directories.find_one({"_id": file_doc["dir_id"]})
    base = parent["path"] if parent else "/"
    return f"{base}/{file_doc['name']}".replace("//", "/")


# --- Routes -----------------------------------------------------------------

@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    """Main page. Shows login box when logged out, drive view when logged in."""
    user = get_user(request)
    if user is None:
        # Not logged in - just render the login box (firebase-login.js handles it).
        return templates.TemplateResponse(
            "main.html", {"request": request, "user_token": None}
        )

    bootstrap(user["user_id"], user.get("email"))
    cur = current_dir(request, user["user_id"])

    children = list(
        db.directories.find({"uid": user["user_id"], "parent": cur["_id"]}).sort(
            "name", ASCENDING
        )
    )
    files = list(
        db.files.find({"uid": user["user_id"], "dir_id": cur["_id"]}).sort(
            "name", ASCENDING
        )
    )

    # Group 3.12: highlight files that share a SHA-256 inside this directory.
    counts: dict[str, int] = {}
    for f in files:
        counts[f["sha256"]] = counts.get(f["sha256"], 0) + 1
    for f in files:
        f["is_dup"] = counts[f["sha256"]] > 1

    # Group 4.14: files other people have shared with me (read-only).
    shared = list(
        db.files.find({"shared_with": user.get("email", "").lower()}).sort(
            "name", ASCENDING
        )
    )
    for f in shared:
        f["path"] = full_file_path(user["user_id"], f)

    return templates.TemplateResponse(
        "main.html",
        {
            "request": request,
            "user_token": user,
            "current": cur,
            "children": children,
            "files": files,
            "shared": shared,
            # Group 2.7: hide ../ when sitting at root.
            "show_up": cur["path"] != "/",
            "msg": request.query_params.get("msg", ""),
            # Group 2.8: signal the template to ask before overwriting.
            "confirm_overwrite": request.query_params.get("confirm") == "overwrite",
            "pending_filename": request.query_params.get("file", ""),
        },
    )


# Group 1.3: create directory.
@app.post("/create-dir")
async def create_dir(request: Request, name: str = Form(...)):
    user = get_user(request)
    if user is None:
        return RedirectResponse("/", 303)

    name = name.strip()
    if not name or "/" in name or "\\" in name or name in (".", ".."):
        return RedirectResponse("/?msg=Invalid+name", 303)

    cur = current_dir(request, user["user_id"])
    new_path = child_path(cur["path"], name)
    # Major-bug guard: never allow two directories with the same path.
    if db.directories.find_one({"uid": user["user_id"], "path": new_path}):
        return RedirectResponse("/?msg=Directory+already+exists", 303)

    db.directories.insert_one(
        {
            "uid": user["user_id"],
            "name": name,
            "parent": cur["_id"],
            "path": new_path,
            "created": datetime.now(timezone.utc),
        }
    )
    return RedirectResponse("/", 303)


# Group 1.4 + Group 3.11: delete directory, refusing if not empty.
@app.post("/delete-dir")
async def delete_dir(request: Request, dir_id: str = Form(...)):
    user = get_user(request)
    if user is None:
        return RedirectResponse("/", 303)

    try:
        oid = ObjectId(dir_id)
    except Exception:
        return RedirectResponse("/?msg=Invalid+id", 303)

    # Look up by id AND uid - never trust the id alone (avoids deleting wrong dir).
    d = db.directories.find_one({"_id": oid, "uid": user["user_id"]})
    if d is None:
        return RedirectResponse("/?msg=Directory+not+found", 303)
    if d["path"] == "/":
        return RedirectResponse("/?msg=Cannot+delete+root", 303)

    if db.directories.count_documents({"uid": user["user_id"], "parent": oid}) > 0:
        return RedirectResponse("/?msg=Directory+has+sub-directories", 303)
    if db.files.count_documents({"uid": user["user_id"], "dir_id": oid}) > 0:
        return RedirectResponse("/?msg=Directory+has+files", 303)

    db.directories.delete_one({"_id": oid})
    response = RedirectResponse("/", 303)
    # If the user was inside the directory we just deleted, reset to root.
    if request.cookies.get("cur") == dir_id:
        response.delete_cookie("cur", path="/")
    return response


# Group 2.5: change into a directory.
@app.get("/open-dir/{dir_id}")
async def open_dir(dir_id: str, request: Request):
    user = get_user(request)
    if user is None:
        return RedirectResponse("/", 303)

    try:
        oid = ObjectId(dir_id)
    except Exception:
        return RedirectResponse("/?msg=Invalid+id", 303)

    d = db.directories.find_one({"_id": oid, "uid": user["user_id"]})
    if d is None:
        return RedirectResponse("/?msg=Directory+not+found", 303)

    response = RedirectResponse("/", 303)
    response.set_cookie("cur", dir_id, path="/", samesite="lax")
    return response


# Group 2.6: go up one level (the ../ entry).
@app.get("/up-dir")
async def up_dir(request: Request):
    user = get_user(request)
    if user is None:
        return RedirectResponse("/", 303)

    cur = current_dir(request, user["user_id"])
    response = RedirectResponse("/", 303)
    if cur.get("parent") is not None:
        response.set_cookie("cur", str(cur["parent"]), path="/", samesite="lax")
    else:
        response.delete_cookie("cur", path="/")
    return response


# Group 2.8: upload a file to Azurite. Asks before overwriting.
@app.post("/upload")
async def upload(
    request: Request,
    file: UploadFile = File(...),
    overwrite: str = Form(""),
):
    user = get_user(request)
    if user is None:
        return RedirectResponse("/", 303)

    # Strip any path components from the uploaded filename.
    name = os.path.basename(file.filename or "").strip()
    if not name:
        return RedirectResponse("/?msg=Empty+filename", 303)

    cur = current_dir(request, user["user_id"])
    existing = db.files.find_one(
        {"uid": user["user_id"], "dir_id": cur["_id"], "name": name}
    )
    # Major-bug guard: never overwrite without an explicit second confirmation.
    if existing is not None and overwrite != "yes":
        return RedirectResponse(f"/?confirm=overwrite&file={name}", 303)

    content = await file.read()
    sha = hashlib.sha256(content).hexdigest()
    container = blob_service.get_container_client(CONTAINER)

    if existing is not None:
        # Overwrite the existing blob, keep the same metadata id.
        container.upload_blob(existing["blob_name"], content, overwrite=True)
        db.files.update_one(
            {"_id": existing["_id"]},
            {
                "$set": {
                    "sha256": sha,
                    "size": len(content),
                    "uploaded": datetime.now(timezone.utc),
                }
            },
        )
    else:
        # Blob name is namespaced by uid + uuid so we never collide between users.
        blob_name = f"{user['user_id']}/{uuid.uuid4().hex}_{name}"
        container.upload_blob(blob_name, content)
        db.files.insert_one(
            {
                "uid": user["user_id"],
                "dir_id": cur["_id"],
                "name": name,
                "blob_name": blob_name,
                "sha256": sha,
                "size": len(content),
                "shared_with": [],
                "uploaded": datetime.now(timezone.utc),
            }
        )

    return RedirectResponse("/", 303)


# Group 3.9: delete a file.
@app.post("/delete-file")
async def delete_file(request: Request, file_id: str = Form(...)):
    user = get_user(request)
    if user is None:
        return RedirectResponse("/", 303)

    try:
        oid = ObjectId(file_id)
    except Exception:
        return RedirectResponse("/?msg=Invalid+id", 303)

    # Look up by id AND uid (avoids deleting someone else's file).
    f = db.files.find_one({"_id": oid, "uid": user["user_id"]})
    if f is None:
        return RedirectResponse("/?msg=File+not+found", 303)

    try:
        blob_service.get_container_client(CONTAINER).delete_blob(f["blob_name"])
    except Exception as err:
        print(f"Blob delete failed (continuing): {err}")
    db.files.delete_one({"_id": oid})
    return RedirectResponse("/", 303)


# Group 3.10 + Group 4.14: download a file (owner OR shared user).
@app.get("/download/{file_id}")
async def download(file_id: str, request: Request):
    user = get_user(request)
    if user is None:
        return RedirectResponse("/", 303)

    try:
        oid = ObjectId(file_id)
    except Exception:
        return RedirectResponse("/?msg=Invalid+id", 303)

    email = (user.get("email") or "").lower()
    f = db.files.find_one(
        {
            "_id": oid,
            "$or": [{"uid": user["user_id"]}, {"shared_with": email}],
        }
    )
    if f is None:
        return RedirectResponse("/?msg=File+not+found", 303)

    data = (
        blob_service.get_container_client(CONTAINER)
        .download_blob(f["blob_name"])
        .readall()
    )
    return Response(
        content=data,
        media_type="application/octet-stream",
        headers={"Content-Disposition": f'attachment; filename="{f["name"]}"'},
    )


# Group 4.13: detect duplicates across the entire user's drive.
@app.get("/duplicates", response_class=HTMLResponse)
async def duplicates(request: Request):
    user = get_user(request)
    if user is None:
        return RedirectResponse("/", 303)

    # Group files by SHA-256, only keep groups with more than one file.
    pipeline = [
        {"$match": {"uid": user["user_id"]}},
        {
            "$group": {
                "_id": "$sha256",
                "files": {
                    "$push": {
                        "_id": "$_id",
                        "name": "$name",
                        "dir_id": "$dir_id",
                        "size": "$size",
                    }
                },
                "count": {"$sum": 1},
            }
        },
        {"$match": {"count": {"$gt": 1}}},
    ]
    groups = list(db.files.aggregate(pipeline))
    # Annotate each file with its full path (e.g. /docs/notes.txt).
    for g in groups:
        for f in g["files"]:
            d = db.directories.find_one({"_id": f["dir_id"]})
            base = d["path"] if d else "/"
            f["path"] = f"{base}/{f['name']}".replace("//", "/")

    return templates.TemplateResponse(
        "duplicates.html",
        {"request": request, "user_token": user, "groups": groups},
    )


# Group 4.14: share a file read-only with another user (by email).
@app.post("/share")
async def share(
    request: Request,
    file_id: str = Form(...),
    email: str = Form(...),
):
    user = get_user(request)
    if user is None:
        return RedirectResponse("/", 303)

    try:
        oid = ObjectId(file_id)
    except Exception:
        return RedirectResponse("/?msg=Invalid+id", 303)

    f = db.files.find_one({"_id": oid, "uid": user["user_id"]})
    if f is None:
        return RedirectResponse("/?msg=File+not+found", 303)

    target = email.strip().lower()
    if not target:
        return RedirectResponse("/?msg=Email+required", 303)

    # $addToSet keeps the list unique - sharing twice is a no-op.
    db.files.update_one({"_id": oid}, {"$addToSet": {"shared_with": target}})
    return RedirectResponse(f"/?msg=Shared+with+{target}", 303)


@app.post("/unshare")
async def unshare(
    request: Request,
    file_id: str = Form(...),
    email: str = Form(...),
):
    user = get_user(request)
    if user is None:
        return RedirectResponse("/", 303)

    try:
        oid = ObjectId(file_id)
    except Exception:
        return RedirectResponse("/?msg=Invalid+id", 303)

    db.files.update_one(
        {"_id": oid, "uid": user["user_id"]},
        {"$pull": {"shared_with": email.strip().lower()}},
    )
    return RedirectResponse("/?msg=Removed+share", 303)


@app.get("/health")
def health():
    return {"status": "ok"}
