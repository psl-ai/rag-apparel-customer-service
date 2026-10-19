from dataclasses import dataclass

import pytest


@dataclass
class FakeAdapter:
    calls: int = 0

    def complete(self, messages, tools):
        from app.agents.model_adapter import ModelToolCall, ModelTurn
        self.calls += 1
        if self.calls == 1:
            return ModelTurn(tool_calls=[ModelToolCall("call-1", "echo", {"value": "ok"})])
        return ModelTurn(content=messages[-1]["content"])

    def compose(self, question, evidence):
        return question


def test_agent_runner_executes_structured_tool_then_returns_answer():
    from app.agents.runner import AgentRunner
    from sqlalchemy import create_engine
    from sqlalchemy.orm import Session

    adapter = FakeAdapter()
    runner = AgentRunner(adapter, {"echo": lambda _session, args: {"echo": args["value"]}})
    engine = create_engine("sqlite+pysqlite:///:memory:")
    with Session(engine) as session:
        result = runner.run(session, [{"role": "user", "content": "hi"}], [])

    assert adapter.calls == 2
    assert result.content == '{"echo": "ok"}'


def test_agent_runner_rejects_unknown_tool():
    from app.agents.runner import AgentRunner
    from sqlalchemy import create_engine
    from sqlalchemy.orm import Session

    adapter = FakeAdapter()
    runner = AgentRunner(adapter, {})
    with Session(create_engine("sqlite+pysqlite:///:memory:")) as session:
        with pytest.raises(Exception, match="未知工具"):
            runner.run(session, [{"role": "user", "content": "hi"}], [])
