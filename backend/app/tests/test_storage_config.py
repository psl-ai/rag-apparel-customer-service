def test_default_object_storage_is_shared_local_backend(monkeypatch, tmp_path):
    from app.core.config import get_settings
    from app.rag.storage import LocalObjectStorage, get_object_storage

    monkeypatch.setenv("OBJECT_STORAGE_BACKEND", "local")
    monkeypatch.setenv("OBJECT_STORAGE_PATH", str(tmp_path))
    get_settings.cache_clear()
    storage = get_object_storage()
    assert isinstance(storage, LocalObjectStorage)
    storage.put("shared.txt", b"worker-visible", "text/plain")
    assert LocalObjectStorage(tmp_path).get("shared.txt") == b"worker-visible"
