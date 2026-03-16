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


def _is_vercel() -> bool:
    return os.getenv("VERCEL") == "1"


def _env(key: str, default: str = "") -> str:
    value = os.getenv(key)
    if value is None:
        return default
    normalized = value.replace("\\n", "\n")
    return normalized.strip()


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    project_root = Path(__file__).resolve().parent.parent
    _load_dotenv(project_root / ".env")

    default_data_dir = "/tmp/data" if _is_vercel() else "data"
    default_database_path = "/tmp/data/app.db" if _is_vercel() else "data/app.db"

    raw_data_dir = _env("DATA_DIR", default_data_dir)
    raw_database_path = _env("DATABASE_PATH", default_database_path)

    data_dir = Path(raw_data_dir) if Path(raw_data_dir).is_absolute() else project_root / raw_data_dir
    database_path = Path(raw_database_path) if Path(raw_database_path).is_absolute() else project_root / raw_database_path

    article_dir = data_dir / "articles"
    audio_dir = data_dir / "audio"
    for path in (data_dir, article_dir, audio_dir):
        path.mkdir(parents=True, exist_ok=True)

    return Settings(
        app_name=_env("APP_NAME", "Daily News Briefing"),
        app_base_url=_env("APP_BASE_URL", "http://127.0.0.1:8000").rstrip("/"),
        app_timezone=_env("APP_TIMEZONE", "America/New_York"),
        app_locale=_env("APP_LOCALE", "zh_CN"),
        secret_key=_env("SECRET_KEY", "change-me"),
        openai_api_key=_env("OPENAI_API_KEY", ""),
        openai_news_model=_env("OPENAI_NEWS_MODEL", "gpt-4.1"),
        openai_tts_model=_env("OPENAI_TTS_MODEL", "gpt-4o-mini-tts"),
        openai_tts_voice=_env("OPENAI_TTS_VOICE", "alloy"),
        allow_demo_fallback=_as_bool(os.getenv("ALLOW_DEMO_FALLBACK"), True),
        smtp_host=_env("SMTP_HOST", ""),
        smtp_port=int(_env("SMTP_PORT", "587")),
        smtp_username=_env("SMTP_USERNAME", ""),
        smtp_password=_env("SMTP_PASSWORD", ""),
        smtp_from_email=_env("SMTP_FROM_EMAIL", ""),
        smtp_from_name=_env("SMTP_FROM_NAME", "Daily News Briefing"),
        smtp_use_tls=_as_bool(os.getenv("SMTP_USE_TLS"), True),
        database_url=_env("DATABASE_URL", ""),
        supabase_url=_env("SUPABASE_URL", ""),
        supabase_service_role_key=_env("SUPABASE_SERVICE_ROLE_KEY", ""),
        supabase_storage_bucket=_env("SUPABASE_STORAGE_BUCKET", "daily-news-assets"),
        supabase_storage_public_base_url=_env("SUPABASE_STORAGE_PUBLIC_BASE_URL", "").rstrip("/"),
        data_dir=data_dir,
        database_path=database_path,
        project_root=project_root,
        templates_dir=project_root / "app" / "templates",
        static_dir=project_root / "app" / "static",
        article_dir=article_dir,
        audio_dir=audio_dir,
    )
