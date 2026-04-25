from __future__ import annotations

from core.models import AssertionResult, SkillResponse, TestCase


def evaluate_keyword_match(case: TestCase, response: SkillResponse) -> AssertionResult:
    answer = response.answer
    missing = [word for word in case.keywords if word not in answer]
    forbidden_hits = [word for word in case.forbidden_words if word and word in answer]
    total = max(len(case.keywords) + len(case.forbidden_words), 1)
    score = (total - len(missing) - len(forbidden_hits)) / total
    passed = not missing and not forbidden_hits
    detail = "keyword assertions passed" if passed else f"missing={missing}, forbidden_hits={forbidden_hits}"
    return AssertionResult(type="keyword", passed=passed, score=max(score, 0.0), detail=detail)

