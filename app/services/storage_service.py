from __future__ import annotations

import mimetypes
from pathlib import Path

from app.config import get_settings

settings = get_settings()


class StorageService:
    def __init__(self) -> None:
        self._client = None
        if settings.supabase_url and settings.supabase_service_role_key:
            from supabase import create_client

            self._client = create_client(settings.supabase_url, settings.supabase_service_role_key)

    @property
    def uses_supabase(self) -> bool:
        return self._client is not None

    def save_bytes(self, *, relative_path: str, content: bytes, content_type: str | None = None) -> tuple[str, str | None]:
        if self.uses_supabase:
            bucket = self._client.storage.from_(settings.supabase_storage_bucket)
            bucket.upload(
                path=relative_path,
                file=content,
                file_options={
                    "content-type": content_type or "application/octet-stream",
                    "upsert": "true",
                },
            )
            return relative_path, self._public_url(relative_path)

        target_path = settings.data_dir / relative_path
        target_path.parent.mkdir(parents=True, exist_ok=True)
        target_path.write_bytes(content)
        return str(target_path), f"/data/{relative_path}"

    def save_text(self, *, relative_path: str, content: str, content_type: str = "text/plain; charset=utf-8") -> tuple[str, str | None]:
        return self.save_bytes(relative_path=relative_path, content=content.encode("utf-8"), content_type=content_type)

    def _public_url(self, relative_path: str) -> str | None:
        if settings.supabase_storage_public_base_url:
            return f"{settings.supabase_storage_public_base_url}/{relative_path}"
        if not self._client:
            return None
        return self._client.storage.from_(settings.supabase_storage_bucket).get_public_url(relative_path)


def guess_content_type(path: str) -> str:
    guessed, _ = mimetypes.guess_type(path)
    return guessed or "application/octet-stream"
