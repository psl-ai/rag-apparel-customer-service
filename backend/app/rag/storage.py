from __future__ import annotations

from pathlib import Path
from typing import Protocol

from app.core.config import get_settings


class ObjectStorage(Protocol):
    def put(self, key: str, content: bytes, content_type: str) -> None: ...

    def get(self, key: str) -> bytes | None: ...

    def delete(self, key: str) -> None: ...


class InMemoryObjectStorage:
    def __init__(self) -> None:
        self._items: dict[str, bytes] = {}

    def put(self, key: str, content: bytes, content_type: str) -> None:
        del content_type
        self._items[key] = content

    def get(self, key: str) -> bytes | None:
        return self._items.get(key)

    def delete(self, key: str) -> None:
        self._items.pop(key, None)


class LocalObjectStorage:
    def __init__(self, root: str | Path = ".fashionrag-objects") -> None:
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)

    def _path(self, key: str) -> Path:
        path = (self.root / key).resolve()
        if self.root.resolve() not in path.parents:
            raise ValueError("invalid object key")
        return path

    def put(self, key: str, content: bytes, content_type: str) -> None:
        del content_type
        path = self._path(key)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)

    def get(self, key: str) -> bytes | None:
        path = self._path(key)
        return path.read_bytes() if path.exists() else None

    def delete(self, key: str) -> None:
        path = self._path(key)
        if path.exists():
            path.unlink()


def get_object_storage() -> ObjectStorage:
    settings = get_settings()
    if settings.object_storage_backend == "memory":
        return _memory_storage
    return LocalObjectStorage(settings.object_storage_path)


_memory_storage = InMemoryObjectStorage()
