from __future__ import annotations

import json
import sqlite3
import urllib.parse
import urllib.request
from contextlib import contextmanager
from typing import Any, Iterator

from app.config import get_settings

settings = get_settings()


def _dict_factory(cursor, row) -> dict[str, Any]:
    columns = [col[0] for col in cursor.description]
    return {columns[idx]: row[idx] for idx in range(len(columns))}


def _rest_mode() -> bool:
    return bool(settings.supabase_url and settings.supabase_service_role_key and settings.app_base_url.startswith("https://"))


def _db_kind() -> str:
    if _rest_mode():
        return "supabase_rest"
    return "postgres" if settings.database_url else "sqlite"


def _rest_headers(prefer: str | None = None) -> dict[str, str]:
    headers = {
        "apikey": settings.supabase_service_role_key,
        "Authorization": f"Bearer {settings.supabase_service_role_key}",
        "Content-Type": "application/json",
    }
    if prefer:
        headers["Prefer"] = prefer
    return headers


def _rest_request(
    method: str,
    table: str,
    *,
    query: dict[str, str] | None = None,
    payload: dict[str, Any] | list[dict[str, Any]] | None = None,
    prefer: str | None = None,
) -> Any:
    query_string = f"?{urllib.parse.urlencode(query)}" if query else ""
    url = f"{settings.supabase_url}/rest/v1/{table}{query_string}"
    data = None if payload is None else json.dumps(payload, ensure_ascii=False).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=data,
        method=method,
        headers=_rest_headers(prefer),
    )
    with urllib.request.urlopen(request, timeout=20) as response:
        body = response.read()
        if not body:
            return None
        return json.loads(body.decode("utf-8"))


@contextmanager
def connect() -> Iterator[Any]:
    if _db_kind() == "postgres":
        import psycopg
        from psycopg.rows import dict_row

        conn = psycopg.connect(settings.database_url, row_factory=dict_row)
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()
        return

    if _db_kind() == "supabase_rest":
        yield None
        return

    settings.database_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(settings.database_path)
    conn.row_factory = _dict_factory
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def _execute(conn: Any, sql: str, params: tuple[Any, ...] = ()) -> Any:
    if _db_kind() == "postgres":
        sql = sql.replace("?", "%s")
    return conn.execute(sql, params)


def _fetchall(cursor: Any) -> list[dict[str, Any]]:
    return list(cursor.fetchall())


def _fetchone(cursor: Any) -> dict[str, Any] | None:
    return cursor.fetchone()


def init_db() -> None:
    if _db_kind() == "supabase_rest":
        return

    with connect() as conn:
        if _db_kind() == "postgres":
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS articles (
                    id BIGSERIAL PRIMARY KEY,
                    slug TEXT NOT NULL UNIQUE,
                    title TEXT NOT NULL,
                    deck TEXT NOT NULL,
                    generated_at TEXT NOT NULL,
                    generated_date TEXT NOT NULL,
                    status TEXT NOT NULL,
                    article_path TEXT NOT NULL,
                    article_url TEXT,
                    article_html TEXT NOT NULL,
                    audio_path TEXT,
                    audio_url TEXT,
                    payload_json JSONB NOT NULL,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                );
                """
            )
            conn.execute("ALTER TABLE articles ADD COLUMN IF NOT EXISTS article_url TEXT;")
            conn.execute("ALTER TABLE articles ADD COLUMN IF NOT EXISTS article_html TEXT;")
            conn.execute("ALTER TABLE articles ADD COLUMN IF NOT EXISTS audio_url TEXT;")
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS subscriptions (
                    id BIGSERIAL PRIMARY KEY,
                    email TEXT NOT NULL UNIQUE,
                    active INTEGER NOT NULL DEFAULT 1,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                );
                """
            )
            return

        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS articles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                slug TEXT NOT NULL UNIQUE,
                title TEXT NOT NULL,
                deck TEXT NOT NULL,
                generated_at TEXT NOT NULL,
                generated_date TEXT NOT NULL,
                status TEXT NOT NULL,
                article_path TEXT NOT NULL,
                article_url TEXT,
                article_html TEXT NOT NULL,
                audio_path TEXT,
                audio_url TEXT,
                payload_json TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS subscriptions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT NOT NULL UNIQUE,
                active INTEGER NOT NULL DEFAULT 1,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
            """
        )
        existing_columns = {
            row["name"]
            for row in conn.execute("PRAGMA table_info(articles)").fetchall()
        }
        if "article_url" not in existing_columns:
            conn.execute("ALTER TABLE articles ADD COLUMN article_url TEXT")
        if "article_html" not in existing_columns:
            conn.execute("ALTER TABLE articles ADD COLUMN article_html TEXT NOT NULL DEFAULT ''")
        if "audio_url" not in existing_columns:
            conn.execute("ALTER TABLE articles ADD COLUMN audio_url TEXT")


def insert_article(
    *,
    slug: str,
    title: str,
    deck: str,
    generated_at: str,
    generated_date: str,
    status: str,
    article_path: str,
    article_url: str | None,
    article_html: str,
    audio_path: str | None,
    audio_url: str | None,
    payload: dict[str, Any],
) -> int:
    if _db_kind() == "supabase_rest":
        rows = _rest_request(
            "POST",
            "articles",
            payload={
                "slug": slug,
                "title": title,
                "deck": deck,
                "generated_at": generated_at,
                "generated_date": generated_date,
                "status": status,
                "article_path": article_path,
                "article_url": article_url,
                "article_html": article_html,
                "audio_path": audio_path,
                "audio_url": audio_url,
                "payload_json": payload,
            },
            prefer="return=representation",
        )
        return int(rows[0]["id"])

    payload_value = json.dumps(payload, ensure_ascii=False, indent=2) if _db_kind() == "sqlite" else json.dumps(payload, ensure_ascii=False)
    with connect() as conn:
        cursor = _execute(
            conn,
            """
            INSERT INTO articles (
                slug, title, deck, generated_at, generated_date, status,
                article_path, article_url, article_html, audio_path, audio_url, payload_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                slug,
                title,
                deck,
                generated_at,
                generated_date,
                status,
                article_path,
                article_url,
                article_html,
                audio_path,
                audio_url,
                payload_value,
            ),
        )
        if _db_kind() == "postgres":
            fetch = _execute(conn, "SELECT id FROM articles WHERE slug = ?", (slug,))
            row = _fetchone(fetch)
            return int(row["id"])
        return int(cursor.lastrowid)


def update_article_status(
    slug: str,
    status: str,
    audio_path: str | None = None,
    audio_url: str | None = None,
) -> None:
    if _db_kind() == "supabase_rest":
        _rest_request(
            "PATCH",
            "articles",
            query={"slug": f"eq.{slug}"},
            payload={
                "status": status,
                **({"audio_path": audio_path} if audio_path else {}),
                **({"audio_url": audio_url} if audio_url else {}),
            },
        )
        return

    with connect() as conn:
        _execute(
            conn,
            """
            UPDATE articles
            SET status = ?,
                audio_path = COALESCE(?, audio_path),
                audio_url = COALESCE(?, audio_url)
            WHERE slug = ?
            """,
            (status, audio_path, audio_url, slug),
        )


def list_articles(limit: int = 20) -> list[dict[str, Any]]:
    if _db_kind() == "supabase_rest":
        return _rest_request(
            "GET",
            "articles",
            query={
                "select": "id,slug,title,deck,generated_at,generated_date,article_path,article_url,audio_path,audio_url,status",
                "order": "generated_at.desc",
                "limit": str(limit),
            },
        )

    with connect() as conn:
        rows = _execute(
            conn,
            """
            SELECT id, slug, title, deck, generated_at, generated_date, article_path, article_url, audio_path, audio_url, status
            FROM articles
            ORDER BY generated_at DESC
            LIMIT ?
            """,
            (limit,),
        )
        return _fetchall(rows)


def get_article_by_slug(slug: str) -> dict[str, Any] | None:
    if _db_kind() == "supabase_rest":
        rows = _rest_request(
            "GET",
            "articles",
            query={"select": "*", "slug": f"eq.{slug}", "limit": "1"},
        )
        return rows[0] if rows else None

    with connect() as conn:
        row = _execute(conn, "SELECT * FROM articles WHERE slug = ?", (slug,))
        return _fetchone(row)


def get_latest_article() -> dict[str, Any] | None:
    if _db_kind() == "supabase_rest":
        rows = _rest_request(
            "GET",
            "articles",
            query={"select": "*", "order": "generated_at.desc", "limit": "1"},
        )
        return rows[0] if rows else None

    with connect() as conn:
        row = _execute(
            conn,
            """
            SELECT *
            FROM articles
            ORDER BY generated_at DESC
            LIMIT 1
            """,
        )
        return _fetchone(row)


def add_subscription(email: str) -> bool:
    if _db_kind() == "supabase_rest":
        existing = _rest_request(
            "GET",
            "subscriptions",
            query={"select": "id,active", "email": f"eq.{email}", "limit": "1"},
        )
        if existing:
            if int(existing[0]["active"]) == 1:
                return False
            _rest_request("PATCH", "subscriptions", query={"email": f"eq.{email}"}, payload={"active": 1})
            return True
        _rest_request("POST", "subscriptions", payload={"email": email, "active": 1}, prefer="return=representation")
        return True

    with connect() as conn:
        existing = _fetchone(_execute(conn, "SELECT id, active FROM subscriptions WHERE email = ?", (email,)))
        if existing:
            if int(existing["active"]) == 1:
                return False
            _execute(conn, "UPDATE subscriptions SET active = 1 WHERE email = ?", (email,))
            return True
        _execute(conn, "INSERT INTO subscriptions (email, active) VALUES (?, 1)", (email,))
        return True


def list_active_subscriptions() -> list[str]:
    if _db_kind() == "supabase_rest":
        rows = _rest_request(
            "GET",
            "subscriptions",
            query={"select": "email", "active": "eq.1", "order": "created_at.asc"},
        )
        return [row["email"] for row in rows]

    with connect() as conn:
        rows = _execute(conn, "SELECT email FROM subscriptions WHERE active = 1 ORDER BY created_at ASC")
        return [row["email"] for row in _fetchall(rows)]
