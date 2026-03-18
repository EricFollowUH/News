from __future__ import annotations

import json
import re
import wave
from pathlib import Path

from google.genai import Client, types

from app.config import get_settings
from app.schemas import GeneratedArticle

settings = get_settings()


class GeminiService:
    def __init__(self) -> None:
        self._client = Client(api_key=settings.gemini_api_key) if settings.gemini_api_key else None

    @property
    def enabled(self) -> bool:
        return self._client is not None

    def generate_article(self) -> GeneratedArticle:
        if not self.enabled:
            if settings.allow_demo_fallback:
                return self._load_demo_article()
            raise RuntimeError("GEMINI_API_KEY is not configured.")

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

请仅返回单个 JSON 对象，不要包含解释文字、代码块或额外前后缀。
""".strip()

        response = self._client.models.generate_content(
            model=settings.gemini_news_model,
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.4,
                tools=[types.Tool(google_search=types.GoogleSearch())],
                response_mime_type="application/json",
            ),
        )

        payload = self._normalize_payload(self._parse_json_payload(response.text or ""))
        return GeneratedArticle.model_validate(payload)

    def synthesize_podcast(self, script: str, target_path: Path) -> Path | None:
        if not self.enabled:
            return None

        try:
            response = self._client.models.generate_content(
                model=settings.gemini_tts_model,
                contents=script,
                config=types.GenerateContentConfig(
                    response_modalities=["AUDIO"],
                    speech_config=types.SpeechConfig(
                        voice_config=types.VoiceConfig(
                            prebuilt_voice_config=types.PrebuiltVoiceConfig(
                                voice_name=settings.gemini_tts_voice
                            )
                        )
                    ),
                ),
            )

            audio_bytes = None
            mime_type = None
            for candidate in response.candidates or []:
                parts = candidate.content.parts if candidate.content else []
                for part in parts:
                    inline_data = getattr(part, "inline_data", None)
                    if inline_data and inline_data.data:
                        audio_bytes = inline_data.data
                        mime_type = inline_data.mime_type
                        break
                if audio_bytes:
                    break

            if not audio_bytes:
                return None

            self._write_audio_file(target_path, audio_bytes, mime_type)
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

    def _parse_json_payload(self, content: str) -> dict:
        text = content.strip()
        if text.startswith("```"):
            text = re.sub(r"^```(?:json)?\s*", "", text)
            text = re.sub(r"\s*```$", "", text)
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            match = re.search(r"\{.*\}", text, flags=re.DOTALL)
            if not match:
                raise
            return json.loads(match.group(0))

    def _normalize_payload(self, payload: dict) -> dict:
        if "morning_report" in payload and isinstance(payload["morning_report"], dict):
            payload = payload["morning_report"]
        elif len(payload) == 1:
            only_value = next(iter(payload.values()))
            if isinstance(only_value, dict):
                payload = only_value

        market_snapshot = payload.get("market_snapshot")
        if isinstance(market_snapshot, dict):
            normalized_market_snapshot = []
            for key, item in market_snapshot.items():
                if isinstance(item, dict):
                    normalized_market_snapshot.append({"key": key, **item})
            payload["market_snapshot"] = normalized_market_snapshot

        news_items = payload.get("news_items")
        if isinstance(news_items, dict):
            payload["news_items"] = list(news_items.values())

        return payload

    def _write_audio_file(self, target_path: Path, audio_bytes: bytes, mime_type: str | None) -> None:
        if mime_type and mime_type.startswith("audio/L16"):
            sample_rate = 24000
            match = re.search(r"rate=(\d+)", mime_type)
            if match:
                sample_rate = int(match.group(1))
            target_path.parent.mkdir(parents=True, exist_ok=True)
            with wave.open(str(target_path), "wb") as wav_file:
                wav_file.setnchannels(1)
                wav_file.setsampwidth(2)
                wav_file.setframerate(sample_rate)
                wav_file.writeframes(audio_bytes)
            return

        target_path.parent.mkdir(parents=True, exist_ok=True)
        target_path.write_bytes(audio_bytes)
