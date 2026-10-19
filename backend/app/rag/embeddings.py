from __future__ import annotations

import hashlib
import math


def embed_text(text: str, dimensions: int = 32) -> list[float]:
    """Return a deterministic hash embedding for offline development/tests."""
    digest = hashlib.sha256(text.encode("utf-8")).digest()
    values = []
    for index in range(dimensions):
        byte = digest[index % len(digest)]
        values.append((byte / 127.5) - 1.0)
    norm = math.sqrt(sum(value * value for value in values)) or 1.0
    return [round(value / norm, 8) for value in values]
