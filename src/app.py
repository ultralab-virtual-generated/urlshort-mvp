import logging
import os
import random
import string
from datetime import datetime, timezone
from typing import Optional

import segno
from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.responses import RedirectResponse

from . import db
from .logging_setup import setup_logging
from .schemas import ShortenRequest, ShortenResponse, StatsResponse

setup_logging()
logger = logging.getLogger(__name__)

app = FastAPI(title="URL Shortener MVP")

def base_url(request: Request) -> str:
    host = request.headers.get("x-forwarded-host") or request.headers.get("host")
    proto = request.headers.get("x-forwarded-proto") or request.url.scheme
    return f"{proto}://{host}" if host else str(request.base_url).rstrip("/")


def generate_code(length: int = 6) -> str:
    alphabet = string.ascii_letters + string.digits
    return "".join(random.choice(alphabet) for _ in range(length))


@app.on_event("startup")
async def on_startup():
    db.create_tables()
    logger.info("Tables ensured; service starting up")


@app.get("/healthz")
async def healthz():
    return {"ok": True}


@app.post("/api/shorten", response_model=ShortenResponse)
async def shorten(req: ShortenRequest, request: Request):
    code = req.custom_code.strip() if req.custom_code else None
    if code:
        if not code.replace("-", "").isalnum():
            raise HTTPException(status_code=400, detail="custom_code must be alphanumeric or hyphen")
        if db.code_exists(code):
            raise HTTPException(status_code=409, detail="custom_code already exists")
    else:
        # generate unique code
        for _ in range(10):
            candidate = generate_code()
            if not db.code_exists(candidate):
                code = candidate
                break
        if not code:
            raise HTTPException(status_code=500, detail="Failed to generate unique code")

    now = datetime.now(timezone.utc).isoformat()
    db.insert_url(code, str(req.url), now)

    short = f"{base_url(request)}/{code}"
    logger.info("Created short URL", extra={"code": code, "long_url": str(req.url)})
    return ShortenResponse(code=code, short_url=short, long_url=str(req.url))


@app.get("/{code}")
async def redirect(code: str, request: Request):
    row = db.get_url(code)
    if not row:
        raise HTTPException(status_code=404, detail="Not found")

    ua = request.headers.get("user-agent")
    # Prefer X-Forwarded-For if behind proxy
    ip_header = request.headers.get("x-forwarded-for") or request.client.host if request.client else None
    ip = ip_header.split(",")[0].strip() if ip_header else None
    city: Optional[str] = None  # Not available offline
    now = datetime.now(timezone.utc).isoformat()
    db.insert_visit(code=code, ts=now, user_agent=ua, ip=ip, city=city)
    logger.info("Visit recorded", extra={"code": code, "ip": ip})

    return RedirectResponse(url=row["long_url"], status_code=307)


@app.get("/api/{code}/stats", response_model=StatsResponse)
async def stats(code: str):
    row = db.get_url(code)
    if not row:
        raise HTTPException(status_code=404, detail="Not found")
    s = db.visit_stats(code)
    return StatsResponse(
        code=code,
        long_url=row["long_url"],
        total_clicks=s["total"],
        last_access=s.get("last_access"),
        recent=s["recent"],
    )


@app.get("/api/{code}/qr")
async def qr(code: str, request: Request):
    row = db.get_url(code)
    if not row:
        raise HTTPException(status_code=404, detail="Not found")
    short = f"{base_url(request)}/{code}"
    qr = segno.make(short)
    # Return bytes directly as PNG
    import io
    buf = io.BytesIO()
    qr.save(buf, kind="png", scale=5)
    data = buf.getvalue()
    return Response(content=data, media_type="image/png")
