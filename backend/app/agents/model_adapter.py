from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, field
import json
import httpx
from typing import Protocol
from app.core.config import get_settings


@dataclass(frozen=True)
class ModelToolCall:
    id: str
    name: str
    arguments: dict[str, object]


@dataclass(frozen=True)
class ModelTurn:
    content: str | None = None
    tool_calls: list[ModelToolCall] = field(default_factory=list)


class ChatModelAdapter(Protocol):
    def compose(self, question: str, evidence: Iterable[str]) -> str: ...

    def complete(self, messages: list[dict[str, object]], tools: list[dict[str, object]]) -> ModelTurn: ...


class MockChatModel:
    def compose(self, question: str, evidence: Iterable[str]) -> str:
        joined = "；".join(list(evidence)[:5])
        return joined or "抱歉，我目前无法确认这个问题。"

    def complete(self, messages: list[dict[str, object]], tools: list[dict[str, object]]) -> ModelTurn:
        return ModelTurn(content=self.compose(str(messages[-1].get("content", "")), []))


class OpenAICompatibleChatModel:
    """Minimal synchronous adapter for OpenAI-compatible /chat/completions APIs."""

    def __init__(self, *, timeout: float = 20.0) -> None:
        settings = get_settings()
        self.base_url = str(settings.openai_base_url).rstrip("/")
        self.api_key = settings.openai_api_key.get_secret_value()
        self.model = settings.chat_model
        self.timeout = timeout

    def compose(self, question: str, evidence: Iterable[str]) -> str:
        turn = self.complete([{"role": "user", "content": question + "\n证据：" + "；".join(evidence)}], [])
        return turn.content or "抱歉，我目前无法确认这个问题。"

    def complete(self, messages: list[dict[str, object]], tools: list[dict[str, object]]) -> ModelTurn:
        response = httpx.post(
            f"{self.base_url}/chat/completions",
            headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
            json={"model": self.model, "messages": messages, "tools": tools, "tool_choice": "auto" if tools else None},
            timeout=self.timeout,
        )
        response.raise_for_status()
        message = response.json()["choices"][0]["message"]
        calls = []
        for call in message.get("tool_calls", []):
            function = call.get("function", {})
            raw = function.get("arguments", "{}")
            calls.append(ModelToolCall(id=str(call.get("id", "")), name=str(function.get("name", "")), arguments=json.loads(raw) if isinstance(raw, str) else raw))
        return ModelTurn(content=message.get("content"), tool_calls=calls)


def get_chat_model() -> ChatModelAdapter:
    return MockChatModel() if get_settings().chat_model == "mock-chat" else OpenAICompatibleChatModel()
