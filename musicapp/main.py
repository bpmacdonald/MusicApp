from pathlib import Path

from fastapi import Depends, FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy import select
from sqlalchemy.orm import Session

from musicapp import __version__
from musicapp.db import get_db
from musicapp.models import AlbumLog

APP_DIR = Path(__file__).resolve().parent

app = FastAPI(title="MusicApp", version=__version__)
app.mount("/static", StaticFiles(directory=APP_DIR / "static"), name="static")
templates = Jinja2Templates(directory=APP_DIR / "templates")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "version": __version__}


@app.get("/", response_class=HTMLResponse)
def home(request: Request, db: Session = Depends(get_db)) -> HTMLResponse:
    recent = db.scalars(
        select(AlbumLog).order_by(AlbumLog.created_at.desc()).limit(20)
    ).all()
    return templates.TemplateResponse(
        request,
        "index.html",
        {"recent_logs": recent},
    )
