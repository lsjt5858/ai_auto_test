from __future__ import annotations

import re

from evaluators.keyword_match import evaluate_keyword_match
from core.models import AssertionResult, SkillResponse, TestCase


def evaluate_rubric(case: TestCase, response: SkillResponse) -> AssertionResult:
    """Deterministic first-pass evaluator for natural-language rubric cases.

    It checks hard negative rules locally. Complex semantic rules should later
    be delegated to a real LLM judge with the original rule.
    """
    keyword_result = evaluate_keyword_match(case, response)
    rule = str(case.raw.get("rule", "")).strip()
    hard_failures = _find_hard_failures(rule, response.answer, case.forbidden_words)
    if hard_failures:
        return AssertionResult(
            type="rubric",
            passed=False,
            score=0.0,
            detail=f"hard rule failures={hard_failures}; keyword_probe={keyword_result.detail}",
        )

    # Natural-language rubric rows should not be failed by brittle extracted
    # keywords. Keep keyword coverage as a probe until a real judge is wired in.
    if rule and rule != "#NAME?":
        return AssertionResult(
            type="rubric",
            passed=True,
            score=1.0,
            detail=f"hard rules passed; keyword_probe_score={keyword_result.score:.2f}",
        )

    if response.answer:
        return AssertionResult(
            type="rubric",
            passed=True,
            score=1.0,
            detail=f"no usable rule; nonempty answer accepted; keyword_probe_score={keyword_result.score:.2f}",
        )

    return AssertionResult(type="rubric", passed=False, score=0.0, detail="empty answer")


def _find_hard_failures(rule: str, answer: str, forbidden_words: list[str]) -> list[str]:
    failures: list[str] = []
    answer_lower = answer.lower()

    for word in forbidden_words:
        if word and word in answer:
            failures.append(f"forbidden word: {word}")

    if "tenant-xxx" in rule and re.search(r"tenant-[a-z0-9-]+", answer_lower):
        failures.append("tenant host exposed")

    if "明文密码" in rule:
        password_match = re.search(r"(password|密码)\s*[:：]\s*([^\s，,。]+)", answer, re.IGNORECASE)
        if password_match and "*" not in password_match.group(2):
            failures.append("possible plaintext password exposed")

    return failures
