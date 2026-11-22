from __future__ import annotations

from pathlib import Path

from ..core.config import UPLOAD_DIR


class LocalStorage:
    def put(self, key: str, data: bytes, content_type: str | None = None) -> str:
        filename = Path(key).name
        path = UPLOAD_DIR / filename
        path.write_bytes(data)
        return f"local/{filename}"

    def local_path(self, key: str) -> Path:
        return UPLOAD_DIR / Path(key).name


def get_storage() -> LocalStorage:
    return LocalStorage()
