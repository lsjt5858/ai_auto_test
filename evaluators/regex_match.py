from __future__ import annotations

import re

from core.models import AssertionResult, SkillResponse, TestCase


def evaluate_regex_match(case: TestCase, response: SkillResponse) -> AssertionResult:
    if not case.regex_patterns:
        return AssertionResult(type="regex", passed=True, score=1.0, detail="no regex patterns configured")
    missing = [pattern for pattern in case.regex_patterns if not re.search(pattern, response.answer)]
    passed = not missing
    score = (len(case.regex_patterns) - len(missing)) / len(case.regex_patterns)
    detail = "regex assertions passed" if passed else f"unmatched_patterns={missing}"
    return AssertionResult(type="regex", passed=passed, score=score, detail=detail)

