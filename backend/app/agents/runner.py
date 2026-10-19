from __future__ import annotations

import json
from collections.abc import Callable
from typing import Any

from sqlalchemy.orm import Session

from app.agents.model_adapter import ChatModelAdapter, ModelTurn
from app.core.errors import AppError


Tool = Callable[[Session, dict[str, object]], object]


class AgentRunner:
    """Bounded structured tool-calling loop, independent from the HTTP layer."""

    def __init__(self, adapter: ChatModelAdapter, tools: dict[str, Tool], max_rounds: int = 4) -> None:
        self.adapter = adapter
        self.tools = tools
        self.max_rounds = max_rounds

    def run(self, session: Session, messages: list[dict[str, object]], tool_schemas: list[dict[str, object]]) -> ModelTurn:
        history = list(messages)
        for _ in range(self.max_rounds):
            turn = self.adapter.complete(history, tool_schemas)
            if not turn.tool_calls:
                return turn
            history.append({"role": "assistant", "tool_calls": [{"id": c.id, "type": "function", "function": {"name": c.name, "arguments": json.dumps(c.arguments, ensure_ascii=False)}} for c in turn.tool_calls]})
            for call in turn.tool_calls:
                function = self.tools.get(call.name)
                if function is None:
                    raise AppError("AGENT_UNKNOWN_TOOL", f"未知工具: {call.name}", 422)
                try:
                    result = function(session, call.arguments)
                except Exception as exc:
                    history.append({"role": "tool", "tool_call_id": call.id, "content": json.dumps({"error": str(exc)}, ensure_ascii=False)})
                else:
                    history.append({"role": "tool", "tool_call_id": call.id, "content": json.dumps(result, ensure_ascii=False, default=str)})
        raise AppError("AGENT_MAX_TOOL_ROUNDS", "智能客服工具调用次数达到上限", 422)
