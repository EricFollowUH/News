from __future__ import annotations

import smtplib
from email.message import EmailMessage

from app.config import get_settings

settings = get_settings()


class EmailService:
    @property
    def enabled(self) -> bool:
        return bool(settings.smtp_host and settings.smtp_from_email)

    def send_article(self, recipients: list[str], article_title: str, article_url: str, deck: str) -> int:
        if not recipients or not self.enabled:
            return 0

        message = EmailMessage()
        message["Subject"] = f"每日新闻摘要 | {article_title}"
        message["From"] = f"{settings.smtp_from_name} <{settings.smtp_from_email}>"
        message["To"] = ", ".join(recipients)
        message.set_content(f"{article_title}\n\n{deck}\n\n阅读全文：{article_url}")
        message.add_alternative(
            f"""
            <html>
              <body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; color: #172033;">
                <h1 style="font-size: 24px;">{article_title}</h1>
                <p style="font-size: 15px; line-height: 1.8;">{deck}</p>
                <p><a href="{article_url}">点击阅读完整日报</a></p>
              </body>
            </html>
            """,
            subtype="html",
        )

        with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=30) as server:
            if settings.smtp_use_tls:
                server.starttls()
            if settings.smtp_username:
                server.login(settings.smtp_username, settings.smtp_password)
            server.send_message(message)
        return len(recipients)
