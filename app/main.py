from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

from .config import settings
from .db import ensure_indexes
from .routes.web import router as web_router


app = FastAPI(title=settings.app_name)
app.add_middleware(SessionMiddleware, secret_key=settings.session_secret)
app.mount("/static", StaticFiles(directory="static"), name="static")
app.include_router(web_router)


@app.on_event("startup")
def on_startup():
    ensure_indexes()


@app.get("/health")
def health():
    return {"status": "ok"}
