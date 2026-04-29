"""Web routes for the Mini Dropbox UI.

Authentication follows PaaS-by-example.pdf Example 03: ``static/firebase-login.js``
signs the user in with Firebase, stores the resulting ID token in a cookie
called ``token``, then ``verify_firebase_id_token`` validates that cookie on
every request. There is no server-side session — current-directory tracking is
also held in a small ``current_dir`` cookie.
"""
from fastapi import APIRouter, Form, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
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


CURRENT_DIR_COOKIE = "current_dir"
FLASH_COOKIE = "flash"


def _redirect(location: str, *, clear_current_dir: bool = False) -> RedirectResponse:
    """Redirect helper. ``clear_current_dir`` is used after deleting the active
    directory so the next render falls back to root."""
    response = RedirectResponse(url=location, status_code=status.HTTP_303_SEE_OTHER)
    if clear_current_dir:
        response.delete_cookie(CURRENT_DIR_COOKIE)
    return response


def _set_flash(response: RedirectResponse, level: str, text: str) -> None:
    """Stash a one-shot toast message in a cookie that the next render clears."""
    response.set_cookie(
        FLASH_COOKIE,
        f"{level}|{text}",
        max_age=10,
        path="/",
        samesite="lax",
    )


def _current_user(request: Request):
    """Verify the Firebase token cookie and return the decoded claims (or None)."""
    return verify_firebase_id_token(request.cookies.get("token"))


def _resolve_current_directory(request: Request, owner_uid: str):
    """Resolve which directory the user is currently viewing.

    Order of precedence: ``directory_id`` query parameter, then the
    ``current_dir`` cookie, then the user's root directory.
    """
    selected_id = request.query_params.get("directory_id") or request.cookies.get(
        CURRENT_DIR_COOKIE
    )
    if selected_id:
        directory = get_directory_by_id(owner_uid, selected_id)
        if directory:
            return directory
    return get_root_directory(owner_uid)


@router.get("/", response_class=HTMLResponse)
def home(request: Request):
    """Landing page. Shows the Firebase login box from the example, or the
    drive view once the cookie token validates."""
    user_token = _current_user(request)

    # First-login bootstrap: ensure the User document and root directory exist.
    error_message = "No error here"
    if user_token:
        try:
            ensure_user_with_root_directory(
                firebase_uid=user_token["user_id"],
                email=user_token.get("email"),
                display_name=user_token.get("name"),
            )
        except Exception as exc:  # surface bootstrap failures to the UI
            print(f"Bootstrap failed: {exc}")
            error_message = "Could not initialise your account."

    # Read (and queue clearing of) the one-shot flash cookie.
    raw_flash = request.cookies.get(FLASH_COOKIE)
    flash = None
    if raw_flash and "|" in raw_flash:
        level, _, text = raw_flash.partition("|")
        flash = {"level": level, "text": text}

    directory = None
    children = []
    show_parent_link = False

    if user_token:
        directory = _resolve_current_directory(request, user_token["user_id"])
        children = list_child_directories(user_token["user_id"], directory["_id"])
        show_parent_link = directory["path"] != "/"

    rendered = templates.TemplateResponse(
        "main.html",
        {
            "request": request,
            "user_token": user_token,
            "error_message": error_message,
            "flash": flash,
            "directory": directory,
            "children": children,
            "show_parent_link": show_parent_link,
        },
    )
    if flash is not None:
        rendered.delete_cookie(FLASH_COOKIE, path="/")
    return rendered


@router.get("/directories/up")
def go_up(request: Request):
    """Navigate to the parent of the active directory (Group 2 task 6)."""
    user_token = _current_user(request)
    if not user_token:
        return _redirect("/")

    directory = _resolve_current_directory(request, user_token["user_id"])
    parent_id = directory.get("parent_id")
    response = _redirect("/")
    if parent_id is not None:
        response.set_cookie(CURRENT_DIR_COOKIE, str(parent_id), path="/", samesite="lax")
    else:
        response.delete_cookie(CURRENT_DIR_COOKIE, path="/")
    return response


@router.get("/directories/{directory_id}/open")
def open_directory(directory_id: str, request: Request):
    """Change into a sub-directory (Group 2 task 5)."""
    user_token = _current_user(request)
    if not user_token:
        return _redirect("/")

    directory = get_directory_by_id(user_token["user_id"], directory_id)
    response = _redirect("/")
    if directory is None:
        _set_flash(response, "error", "Directory not found.")
    else:
        response.set_cookie(
            CURRENT_DIR_COOKIE, str(directory["_id"]), path="/", samesite="lax"
        )
    return response


@router.post("/directories")
async def add_directory(request: Request, name: str = Form(...)):
    """Create a sub-directory under the active directory (Group 1 task 3)."""
    user_token = _current_user(request)
    if not user_token:
        return _redirect("/")

    current_directory = _resolve_current_directory(request, user_token["user_id"])
    response = _redirect("/")
    try:
        create_directory(user_token["user_id"], current_directory["_id"], name.strip())
        _set_flash(response, "success", f'Directory "{name.strip()}" created.')
    except ValueError as exc:
        _set_flash(response, "error", str(exc))
    return response


@router.post("/directories/{directory_id}/delete")
def remove_directory(directory_id: str, request: Request):
    """Delete a sub-directory (Group 1 task 4)."""
    user_token = _current_user(request)
    if not user_token:
        return _redirect("/")

    clear_active = request.cookies.get(CURRENT_DIR_COOKIE) == directory_id
    response = _redirect("/", clear_current_dir=clear_active)
    try:
        delete_directory(user_token["user_id"], directory_id)
        _set_flash(response, "success", "Directory deleted.")
    except ValueError as exc:
        _set_flash(response, "error", str(exc))
    return response
