from __future__ import annotations

from core.models import AssertionResult, SkillResponse, TestCase


def evaluate_exact_match(case: TestCase, response: SkillResponse) -> AssertionResult:
    passed = response.answer.strip() == case.expected_answer.strip()
    return AssertionResult(
        type="exact_match",
        passed=passed,
        score=1.0 if passed else 0.0,
        detail="answer exactly matches expected_answer" if passed else "answer does not exactly match expected_answer",
    )

