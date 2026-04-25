from __future__ import annotations

from core.models import EvaluationResult


def assert_evaluation_passed(result: EvaluationResult) -> None:
    assert result.passed, f"score={result.score:.2f}, reason={result.reason}"

