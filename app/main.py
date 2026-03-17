from __future__ import annotations

import json
import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Form, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.config import get_settings
from app.db import add_subscription, get_article_by_slug, get_latest_article, init_db, list_articles
from app.schemas import SubscribeRequest
from app.services.article_service import ArticleOrchestrator
from app.services.scheduler import SchedulerService

settings = get_settings()
templates = Jinja2Templates(directory=str(settings.templates_dir))
orchestrator = ArticleOrchestrator()
scheduler_service = None if os.getenv("VERCEL") else SchedulerService(orchestrator=orchestrator)


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    if scheduler_service is not None:
        scheduler_service.start()
    yield
    if scheduler_service is not None:
        scheduler_service.stop()


app = FastAPI(title=settings.app_name, lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=list(settings.cors_allowed_origins) or ["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.mount("/static", StaticFiles(directory=str(settings.static_dir)), name="static")
app.mount("/data", StaticFiles(directory=str(settings.data_dir)), name="data")


def _article_payload(article: dict | None) -> dict | None:
    if not article:
        return None
    raw_payload = article["payload_json"]
    payload = raw_payload if isinstance(raw_payload, dict) else json.loads(raw_payload)
    payload["slug"] = article["slug"]
    payload["audio_path"] = article["audio_path"]
    payload["article_path"] = article["article_path"]
    payload["article_url"] = article.get("article_url")
    payload["status"] = article["status"]
    if article.get("audio_url"):
        payload["audio_url"] = article["audio_url"]
    elif article["audio_path"]:
        audio_path = Path(article["audio_path"])
        payload["audio_url"] = f"/data/{audio_path.relative_to(settings.data_dir).as_posix()}"
    else:
        payload["audio_url"] = None
    return payload


@app.get("/", response_class=HTMLResponse)
async def index(request: Request) -> HTMLResponse:
    latest = _article_payload(get_latest_article())
    articles = list_articles(limit=30)
    generate_endpoint = (
        f"{settings.generator_api_base_url}/api/generate-now"
        if settings.generator_api_base_url
        else "/api/generate-now"
    )
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "settings": settings,
            "latest": latest,
            "articles": articles,
            "generate_endpoint": generate_endpoint,
        },
    )


@app.get("/articles/{slug}", response_class=HTMLResponse)
async def article_detail(request: Request, slug: str) -> HTMLResponse:
    article = get_article_by_slug(slug)
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    payload = _article_payload(article)
    html = article.get("article_html", "")
    return templates.TemplateResponse(
        "article_detail.html",
        {
            "request": request,
            "settings": settings,
            "article": payload,
            "article_html": html,
        },
    )


@app.post("/api/generate-now", response_class=JSONResponse)
async def generate_now() -> JSONResponse:
    try:
        article = orchestrator.generate_and_archive()
    except Exception as exc:
        message = str(exc).strip() or "生成失败，请稍后再试。"
        return JSONResponse({"ok": False, "message": message}, status_code=500)
    return JSONResponse(
        {
            "ok": True,
            "slug": article["slug"],
            "article_url": f"/articles/{article['slug']}",
            "generated_at": article["generated_at"],
        }
    )


@app.post("/api/subscribe", response_class=JSONResponse)
async def subscribe(email: str = Form(...)) -> JSONResponse:
    payload = SubscribeRequest(email=email)
    created = add_subscription(payload.email)
    return JSONResponse(
        {
            "ok": True,
            "created": created,
            "message": "订阅成功，日报会在美东时间每天早上 8:00 发送到你的邮箱。"
            if created
            else "这个邮箱已经订阅，无需重复提交。",
        }
    )


@app.get("/healthz", response_class=JSONResponse)
async def healthz() -> JSONResponse:
    return JSONResponse({"ok": True})
