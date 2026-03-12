from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path


def _load_dotenv(dotenv_path: Path) -> None:
    if not dotenv_path.exists():
        return
    for raw_line in dotenv_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip())


@dataclass(frozen=True)
class Settings:
    app_name: str
    app_base_url: str
    app_timezone: str
    app_locale: str
    secret_key: str
    openai_api_key: str
    openai_news_model: str
    openai_tts_model: str
    openai_tts_voice: str
    allow_demo_fallback: bool
    smtp_host: str
    smtp_port: int
    smtp_username: str
    smtp_password: str
    smtp_from_email: str
    smtp_from_name: str
    smtp_use_tls: bool
    database_url: str
    supabase_url: str
    supabase_service_role_key: str
    supabase_storage_bucket: str
    supabase_storage_public_base_url: str
    data_dir: Path
    database_path: Path
    project_root: Path
    templates_dir: Path
    static_dir: Path
    article_dir: Path
    audio_dir: Path


def _as_bool(value: str | None, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    project_root = Path(__file__).resolve().parent.parent
    _load_dotenv(project_root / ".env")

    data_dir = project_root / os.getenv("DATA_DIR", "data")
    database_path = project_root / os.getenv("DATABASE_PATH", "data/app.db")

    article_dir = data_dir / "articles"
    audio_dir = data_dir / "audio"
    for path in (data_dir, article_dir, audio_dir):
        path.mkdir(parents=True, exist_ok=True)

    return Settings(
        app_name=os.getenv("APP_NAME", "Daily News Briefing"),
        app_base_url=os.getenv("APP_BASE_URL", "http://127.0.0.1:8000").rstrip("/"),
        app_timezone=os.getenv("APP_TIMEZONE", "America/New_York"),
        app_locale=os.getenv("APP_LOCALE", "zh_CN"),
        secret_key=os.getenv("SECRET_KEY", "change-me"),
        openai_api_key=os.getenv("OPENAI_API_KEY", ""),
        openai_news_model=os.getenv("OPENAI_NEWS_MODEL", "gpt-4.1"),
        openai_tts_model=os.getenv("OPENAI_TTS_MODEL", "gpt-4o-mini-tts"),
        openai_tts_voice=os.getenv("OPENAI_TTS_VOICE", "alloy"),
        allow_demo_fallback=_as_bool(os.getenv("ALLOW_DEMO_FALLBACK"), True),
        smtp_host=os.getenv("SMTP_HOST", ""),
        smtp_port=int(os.getenv("SMTP_PORT", "587")),
        smtp_username=os.getenv("SMTP_USERNAME", ""),
        smtp_password=os.getenv("SMTP_PASSWORD", ""),
        smtp_from_email=os.getenv("SMTP_FROM_EMAIL", ""),
        smtp_from_name=os.getenv("SMTP_FROM_NAME", "Daily News Briefing"),
        smtp_use_tls=_as_bool(os.getenv("SMTP_USE_TLS"), True),
        database_url=os.getenv("DATABASE_URL", ""),
        supabase_url=os.getenv("SUPABASE_URL", ""),
        supabase_service_role_key=os.getenv("SUPABASE_SERVICE_ROLE_KEY", ""),
        supabase_storage_bucket=os.getenv("SUPABASE_STORAGE_BUCKET", "daily-news-assets"),
        supabase_storage_public_base_url=os.getenv("SUPABASE_STORAGE_PUBLIC_BASE_URL", "").rstrip("/"),
        data_dir=data_dir,
        database_path=database_path,
        project_root=project_root,
        templates_dir=project_root / "app" / "templates",
        static_dir=project_root / "app" / "static",
        article_dir=article_dir,
        audio_dir=audio_dir,
    )
