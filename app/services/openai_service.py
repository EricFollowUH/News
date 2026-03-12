from __future__ import annotations

import json
from pathlib import Path

from app.config import get_settings
from app.schemas import GeneratedArticle

settings = get_settings()


class OpenAIService:
    def __init__(self) -> None:
        self._client = None
        if settings.openai_api_key:
            from openai import OpenAI

            self._client = OpenAI(api_key=settings.openai_api_key)

    @property
    def enabled(self) -> bool:
        return self._client is not None

    def generate_article(self) -> GeneratedArticle:
        if not self.enabled:
            if settings.allow_demo_fallback:
                return self._load_demo_article()
            raise RuntimeError("OPENAI_API_KEY is not configured.")

        prompt = """
你是一名顶级中文国际新闻总编。请搜索过去24小时的全球热点新闻，
生成一份适合专业读者的中文晨报，严格输出 JSON，不要输出 markdown。

要求：
1. 重点覆盖 美国、中国、国际 三个区域。
2. 聚焦 热点、财经、科技 三类内容。
3. 输出正好 30 条 news_items，按重要性排序。
4. 每条新闻必须包含：
   - rank: 1-30
   - region: 美国 / 中国 / 国际
   - category: 热点 / 财经 / 科技
   - headline: 中文标题
   - summary_cn: 2-3句中文总结，可组合多条相关新闻
   - impact_cn: 2句中文影响分析
   - published_at: 以原新闻主发布时间填写，标出时区
   - source_links: 1-3条来源，字段 title, publisher, url
5. 生成一段文章导语 deck，以及一段适合女生轻松播报口吻的中文 podcast_script_cn，长度约 700-1100 字。
6. 在 market_snapshot 中给出最近一次收盘的四项关键指标：
   - gold / 黄金
   - oil / 原油
   - sp500 / 标普500
   - shanghai / 沪指
   每项需包含 name, close, change, as_of, source_name, source_url。
7. 时间字段 generated_at_et、window_start_et、window_end_et 统一使用美东时间。
8. 文章标题要像专业媒体专题标题，不要平淡。
9. 所有 url 必须是可点击的原文或权威报道链接。
10. 必须基于真实过去24小时信息，不要编造。若同主题有多源，请优先 Reuters、Bloomberg、WSJ、CNBC、FT、AP、财新、财联社、新华社等权威来源。

JSON schema:
{
  "title": "string",
  "deck": "string",
  "generated_at_et": "YYYY-MM-DD HH:mm ET",
  "window_start_et": "YYYY-MM-DD HH:mm ET",
  "window_end_et": "YYYY-MM-DD HH:mm ET",
  "market_snapshot": [
    {
      "key": "gold|oil|sp500|shanghai",
      "name": "string",
      "close": "string",
      "change": "string",
      "as_of": "string",
      "source_name": "string",
      "source_url": "https://..."
    }
  ],
  "news_items": [
    {
      "rank": 1,
      "region": "美国|中国|国际",
      "category": "热点|财经|科技",
      "headline": "string",
      "summary_cn": "string",
      "impact_cn": "string",
      "published_at": "string",
      "source_links": [
        {
          "title": "string",
          "publisher": "string",
          "url": "https://..."
        }
      ]
    }
  ],
  "podcast_script_cn": "string"
}
""".strip()

        response = self._client.responses.create(
            model=settings.openai_news_model,
            input=prompt,
            tools=[{"type": "web_search"}],
            text={"format": {"type": "json_object"}},
        )
        payload = json.loads(response.output_text)
        return GeneratedArticle.model_validate(payload)

    def synthesize_podcast(self, script: str, target_path: Path) -> Path | None:
        if not self.enabled:
            return None

        try:
            speech = self._client.audio.speech.create(
                model=settings.openai_tts_model,
                voice=settings.openai_tts_voice,
                input=script,
                format="mp3",
            )
            target_path.write_bytes(speech.read())
            return target_path
        except Exception:
            return None

    def _load_demo_article(self) -> GeneratedArticle:
        fixture_path = settings.project_root / "app" / "fixtures" / "demo_article.json"
        payload = json.loads(fixture_path.read_text(encoding="utf-8"))
        news_items = payload["news_items"]
        while len(news_items) < 30:
            template = dict(news_items[len(news_items) % 10])
            rank = len(news_items) + 1
            template["rank"] = rank
            template["headline"] = f"{template['headline']}（延伸追踪 {rank}）"
            news_items.append(template)
        payload["news_items"] = news_items[:30]
        return GeneratedArticle.model_validate(payload)
