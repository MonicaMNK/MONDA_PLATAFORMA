from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path

from ..core.config import DATA_DIR, UPLOAD_DIR, settings


class Storage(ABC):
    @abstractmethod
    def put(self, key: str, data: bytes, content_type: str | None = None) -> str: ...
    @abstractmethod
    def local_path(self, key: str) -> Path: ...


class LocalStorage(Storage):
    def put(self, key: str, data: bytes, content_type: str | None = None) -> str:
        filename = Path(key).name
        path = UPLOAD_DIR / filename
        path.write_bytes(data)
        return f"local/{filename}"

    def local_path(self, key: str) -> Path:
        return UPLOAD_DIR / Path(key).name


class S3Storage(Storage):
    def __init__(self):
        try:
            import boto3  # type: ignore
        except Exception as exc:
            raise RuntimeError("STORAGE_MODE=s3 requiere boto3") from exc
        if not settings.s3_bucket:
            raise RuntimeError("S3_BUCKET no configurado")
        self.client = boto3.client("s3", region_name=settings.aws_region)

    def put(self, key: str, data: bytes, content_type: str | None = None) -> str:
        kwargs = {"Bucket": settings.s3_bucket, "Key": key, "Body": data, "ServerSideEncryption": "AES256"}
        if content_type:
            kwargs["ContentType"] = content_type
        self.client.put_object(**kwargs)
        return f"s3://{settings.s3_bucket}/{key}"

    def local_path(self, key: str) -> Path:
        prefix = f"s3://{settings.s3_bucket}/"
        object_key = key[len(prefix):] if key.startswith(prefix) else key
        cache = DATA_DIR / "s3_cache" / Path(object_key).name
        cache.parent.mkdir(parents=True, exist_ok=True)
        self.client.download_file(settings.s3_bucket, object_key, str(cache))
        return cache


def get_storage() -> Storage:
    return S3Storage() if settings.storage_mode == "s3" else LocalStorage()
