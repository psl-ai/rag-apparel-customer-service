from __future__ import annotations

from dataclasses import dataclass
from typing import Callable


@dataclass(frozen=True)
class EvaluationCase:
    name: str
    check: Callable[[], bool]


def run_evaluation(cases: list[EvaluationCase]) -> dict[str, object]:
    results = [{"name": case.name, "passed": bool(case.check())} for case in cases]
    passed = sum(1 for item in results if item["passed"])
    total = len(results)
    return {"passed": passed, "total": total, "pass_rate": (passed / total if total else 0.0), "cases": results}
