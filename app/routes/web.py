from fastapi import APIRouter, HTTPException, Request, status
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from ..auth import verify_firebase_id_token
from ..services.bootstrap_service import ensure_user_with_root_directory
from ..services.directory_service import (
    create_directory,
    delete_directory,
    get_directory_by_id,
    get_root_directory,
    list_child_directories,
)


router = APIRouter()
templates = Jinja2Templates(directory="templates")


def _redirect(location: str) -> RedirectResponse:
    return RedirectResponse(url=location, status_code=status.HTTP_303_SEE_OTHER)


def _current_user(request: Request):
    return request.session.get("user")


def _set_message(request: Request, level: str, text: str):
    request.session["flash_message"] = {"level": level, "text": text}


def _pop_message(request: Request):
    return request.session.pop("flash_message", None)


def _resolve_current_directory(request: Request, owner_uid: str):
    selected_id = request.query_params.get("directory_id") or request.session.get("current_directory_id")

    if selected_id:
        directory = get_directory_by_id(owner_uid, selected_id)
        if directory:
            request.session["current_directory_id"] = str(directory["_id"])
            return directory

    root_directory = get_root_directory(owner_uid)
    request.session["current_directory_id"] = str(root_directory["_id"])
    return root_directory


@router.get("/", response_class=HTMLResponse)
def home(request: Request):
    if _current_user(request):
        return _redirect("/drive")

    return templates.TemplateResponse(
        "login.html",
        {
            "request": request,
            "message": _pop_message(request),
        },
    )


@router.post("/auth/login")
async def login(request: Request):
    payload = await request.json()
    id_token = payload.get("idToken") or payload.get("id_token")

    if not id_token:
        raise HTTPException(status_code=400, detail="Missing Firebase ID token.")

    try:
        decoded = verify_firebase_id_token(id_token)
        user, root_directory = ensure_user_with_root_directory(
            firebase_uid=decoded["uid"],
            email=decoded.get("email"),
            display_name=decoded.get("name"),
        )
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    request.session["user"] = {
        "uid": user["firebase_uid"],
        "email": user.get("email", ""),
        "display_name": user.get("display_name", ""),
    }
    request.session["current_directory_id"] = str(root_directory["_id"])
    return JSONResponse({"ok": True, "redirect_url": "/drive"})


@router.get("/logout")
def logout(request: Request):
    request.session.clear()
    return _redirect("/")


@router.get("/drive", response_class=HTMLResponse)
def drive(request: Request):
    user = _current_user(request)
    if not user:
        _set_message(request, "error", "Please log in first.")
        return _redirect("/")

    directory = _resolve_current_directory(request, user["uid"])
    children = list_child_directories(user["uid"], directory["_id"])
    parent_id = str(directory["parent_id"]) if directory.get("parent_id") else None

    return templates.TemplateResponse(
        "drive.html",
        {
            "request": request,
            "message": _pop_message(request),
            "user": user,
            "directory": directory,
            "children": children,
            "show_parent_link": directory["path"] != "/",
            "parent_id": parent_id,
        },
    )


@router.get("/directories/up")
def go_up(request: Request):
    user = _current_user(request)
    if not user:
        return _redirect("/")

    current_directory = _resolve_current_directory(request, user["uid"])
    parent_id = current_directory.get("parent_id")
    if parent_id:
        request.session["current_directory_id"] = str(parent_id)

    return _redirect("/drive")


@router.get("/directories/{directory_id}/open")
def open_directory(directory_id: str, request: Request):
    user = _current_user(request)
    if not user:
        return _redirect("/")

    directory = get_directory_by_id(user["uid"], directory_id)
    if directory is None:
        _set_message(request, "error", "Directory not found.")
        return _redirect("/drive")

    request.session["current_directory_id"] = str(directory["_id"])
    return _redirect("/drive")


@router.post("/directories")
async def add_directory(request: Request):
    user = _current_user(request)
    if not user:
        return _redirect("/")

    form = await request.form()
    name = str(form.get("name", "")).strip()
    current_directory = _resolve_current_directory(request, user["uid"])

    try:
        create_directory(user["uid"], current_directory["_id"], name)
        _set_message(request, "success", f'Directory "{name}" created.')
    except ValueError as exc:
        _set_message(request, "error", str(exc))

    return _redirect("/drive")


@router.post("/directories/{directory_id}/delete")
def remove_directory(directory_id: str, request: Request):
    user = _current_user(request)
    if not user:
        return _redirect("/")

    try:
        delete_directory(user["uid"], directory_id)
        _set_message(request, "success", "Directory deleted.")
    except ValueError as exc:
        _set_message(request, "error", str(exc))

    current_directory_id = request.session.get("current_directory_id")
    if current_directory_id == directory_id:
        root_directory = get_root_directory(user["uid"])
        request.session["current_directory_id"] = str(root_directory["_id"])

    return _redirect("/drive")
