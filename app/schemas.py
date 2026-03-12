from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, EmailStr, Field, HttpUrl


class SourceLink(BaseModel):
    title: str
    publisher: str
    url: HttpUrl


class MarketQuote(BaseModel):
    key: Literal["gold", "oil", "sp500", "shanghai"]
    name: str
    close: str
    change: str
    as_of: str
    source_name: str
    source_url: HttpUrl


class NewsItem(BaseModel):
    rank: int = Field(ge=1, le=30)
    region: Literal["美国", "中国", "国际"]
    category: Literal["热点", "财经", "科技"]
    headline: str
    summary_cn: str
    impact_cn: str
    published_at: str
    source_links: list[SourceLink]


class GeneratedArticle(BaseModel):
    title: str
    deck: str
    generated_at_et: str
    window_start_et: str
    window_end_et: str
    market_snapshot: list[MarketQuote]
    news_items: list[NewsItem] = Field(min_length=30, max_length=30)
    podcast_script_cn: str


class ArticleRecord(BaseModel):
    id: int
    slug: str
    title: str
    deck: str
    generated_at: str
    generated_date: str
    article_path: str
    audio_path: str | None = None
    status: str


class SubscribeRequest(BaseModel):
    email: EmailStr


class GenerateResponse(BaseModel):
    ok: bool
    article_url: str
    slug: str
    generated_at: datetime
