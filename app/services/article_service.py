from __future__ import annotations

import html
import json
import re
from datetime import datetime
from zoneinfo import ZoneInfo

from app.config import get_settings
from app.db import insert_article, list_active_subscriptions, update_article_status
from app.schemas import GeneratedArticle
from app.services.email_service import EmailService
from app.services.gemini_service import GeminiService
from app.services.storage_service import StorageService, guess_content_type

settings = get_settings()


def _slugify(text: str) -> str:
    ascii_text = text.encode("ascii", "ignore").decode("ascii")
    cleaned = re.sub(r"[^A-Za-z0-9\s-]", "", ascii_text).strip().lower()
    slug = re.sub(r"[-\s]+", "-", cleaned)
    if not slug:
        slug = datetime.now().strftime("%Y%m%d-%H%M%S")
    return slug[:80]


class ArticleOrchestrator:
    def __init__(self) -> None:
        self.gemini = GeminiService()
        self.email = EmailService()
        self.storage = StorageService()

    def generate_and_archive(self) -> dict[str, str]:
        print("[generate] starting pipeline", flush=True)
        now_et = datetime.now(ZoneInfo(settings.app_timezone))
        print("[generate] requesting Gemini article", flush=True)
        article = self.gemini.generate_article()
        print("[generate] article ready", flush=True)
        slug = f"{now_et.strftime('%Y%m%d-%H%M')}-{_slugify(article.title)}"

        article_html = self._render_article_html(article, slug)
        date_prefix = now_et.strftime("%Y-%m-%d")
        article_relative_path = f"articles/{date_prefix}/{slug}.html"
        payload_relative_path = f"articles/{date_prefix}/{slug}.json"
        script_relative_path = f"articles/{date_prefix}/{slug}-podcast.txt"
        audio_relative_path = f"audio/{date_prefix}/{slug}.wav"

        print("[generate] saving article html", flush=True)
        article_path, article_url = self.storage.save_text(
            relative_path=article_relative_path,
            content=article_html,
            content_type="text/html; charset=utf-8",
        )
        print("[generate] saving article payload", flush=True)
        self.storage.save_text(
            relative_path=payload_relative_path,
            content=article.model_dump_json(indent=2),
            content_type="application/json; charset=utf-8",
        )
        print("[generate] saving podcast script", flush=True)
        self.storage.save_text(
            relative_path=script_relative_path,
            content=article.podcast_script_cn,
            content_type="text/plain; charset=utf-8",
        )

        print("[generate] inserting article record", flush=True)
        insert_article(
            slug=slug,
            title=article.title,
            deck=article.deck,
            generated_at=now_et.isoformat(),
            generated_date=now_et.strftime("%Y-%m-%d"),
            status="generated",
            article_path=article_path,
            article_url=article_url,
            article_html=article_html,
            audio_path=None,
            audio_url=None,
            payload=article.model_dump(mode="json"),
        )

        local_audio_path = settings.audio_dir / date_prefix / f"{slug}.wav"
        local_audio_path.parent.mkdir(parents=True, exist_ok=True)
        print("[generate] synthesizing podcast audio", flush=True)
        rendered_audio = self.gemini.synthesize_podcast(article.podcast_script_cn, local_audio_path)
        if rendered_audio:
            print("[generate] uploading podcast audio", flush=True)
            audio_path, audio_url = self.storage.save_bytes(
                relative_path=audio_relative_path,
                content=rendered_audio.read_bytes(),
                content_type=guess_content_type(audio_relative_path),
            )
            update_article_status(slug, "published", audio_path, audio_url)
        else:
            print("[generate] audio skipped", flush=True)
            update_article_status(slug, "published")

        print("[generate] loading subscriptions", flush=True)
        recipients = list_active_subscriptions()
        article_url = f"{settings.app_base_url}/articles/{slug}"
        print(f"[generate] sending email to {len(recipients)} recipients", flush=True)
        try:
            self.email.send_article(recipients, article.title, article_url, article.deck)
        except Exception as exc:
            print(f"[generate] email delivery skipped: {exc}", flush=True)
        print("[generate] pipeline complete", flush=True)

        return {
            "slug": slug,
            "generated_at": now_et.isoformat(),
        }

    def _render_article_html(self, article: GeneratedArticle, slug: str) -> str:
        market_cards = "\n".join(
            f"""
            <article class="market-card">
              <div class="market-card__top">
                <span>{html.escape(item.name)}</span>
                <a href="{item.source_url}" target="_blank" rel="noreferrer">来源</a>
              </div>
              <strong>{html.escape(item.close)}</strong>
              <p>{html.escape(item.change)} · {html.escape(item.as_of)}</p>
            </article>
            """.strip()
            for item in article.market_snapshot
        )

        sections = []
        for item in article.news_items:
            links = " ".join(
                f'<a href="{source.url}" target="_blank" rel="noreferrer">{html.escape(source.publisher)}</a>'
                for source in item.source_links
            )
            sections.append(
                f"""
                <section class="article-item" id="news-{item.rank}">
                  <div class="article-item__meta">
                    <span>#{item.rank}</span>
                    <span>{html.escape(item.region)}</span>
                    <span>{html.escape(item.category)}</span>
                    <span>{html.escape(item.published_at)}</span>
                  </div>
                  <h3>{html.escape(item.headline)}</h3>
                  <p>{html.escape(item.summary_cn)}</p>
                  <p class="impact"><strong>影响：</strong>{html.escape(item.impact_cn)}</p>
                  <p class="sources">{links}</p>
                </section>
                """.strip()
            )

        return f"""
        <div class="article-shell">
          <header class="article-header">
            <p class="eyebrow">Daily Briefing · {html.escape(article.generated_at_et)}</p>
            <h1>{html.escape(article.title)}</h1>
            <p class="deck">{html.escape(article.deck)}</p>
            <div class="window">
              统计窗口：{html.escape(article.window_start_et)} - {html.escape(article.window_end_et)}
            </div>
          </header>

          <section class="article-market">
            <h2>主要经济指标</h2>
            <div class="market-grid">{market_cards}</div>
          </section>

          <section class="article-podcast">
            <div>
              <h2>播客导读</h2>
              <p>{html.escape(article.podcast_script_cn)}</p>
            </div>
          </section>

          <section class="article-list">
            <h2>30条重点新闻</h2>
            {"".join(sections)}
          </section>

          <footer class="article-footer">
            <p>归档编号：{html.escape(slug)}</p>
          </footer>
        </div>
        """.strip()
