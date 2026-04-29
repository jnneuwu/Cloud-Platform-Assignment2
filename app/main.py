"""FastAPI application entry point.

Follows the structure of the course PaaS-by-example.pdf: a single FastAPI
instance, static files mounted at ``/static``, Jinja2 templates under
``templates/``, and authentication carried in the ``token`` cookie set by
``static/firebase-login.js``. No SessionMiddleware is used.
"""
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from .config import settings
from .db import ensure_indexes
from .routes.web import router as web_router


app = FastAPI(title=settings.app_name)
app.mount("/static", StaticFiles(directory="static"), name="static")
app.include_router(web_router)


@app.on_event("startup")
def on_startup():
    """Create the unique MongoDB indexes our queries rely on."""
    ensure_indexes()


@app.get("/health")
def health():
    return {"status": "ok"}
