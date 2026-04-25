from __future__ import annotations

import math
import re
from collections import Counter

from core.models import AssertionResult, SkillResponse, TestCase


def evaluate_semantic_similarity(case: TestCase, response: SkillResponse) -> AssertionResult:
    if not case.expected_answer:
        return AssertionResult(type="semantic_similarity", passed=True, score=1.0, detail="no expected_answer configured")
    score = _cosine(_tokens(case.expected_answer), _tokens(response.answer))
    passed = score >= (case.score_threshold or 0.75)
    return AssertionResult(
        type="semantic_similarity",
        passed=passed,
        score=score,
        detail=f"token cosine similarity={score:.2f}",
    )


def _tokens(text: str) -> Counter[str]:
    tokens = re.findall(r"[\w\u4e00-\u9fff]+", text.lower())
    chars: list[str] = []
    for token in tokens:
        if re.fullmatch(r"[\u4e00-\u9fff]+", token):
            chars.extend(token)
        else:
            chars.append(token)
    return Counter(chars)


def _cosine(left: Counter[str], right: Counter[str]) -> float:
    if not left or not right:
        return 0.0
    keys = set(left) | set(right)
    dot = sum(left[key] * right[key] for key in keys)
    left_norm = math.sqrt(sum(value * value for value in left.values()))
    right_norm = math.sqrt(sum(value * value for value in right.values()))
    return dot / (left_norm * right_norm) if left_norm and right_norm else 0.0

