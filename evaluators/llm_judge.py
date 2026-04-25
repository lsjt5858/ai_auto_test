from __future__ import annotations

from core.models import AssertionResult, SkillResponse, TestCase
from evaluators.keyword_match import evaluate_keyword_match
from evaluators.semantic_similarity import evaluate_semantic_similarity


def evaluate_llm_judge(case: TestCase, response: SkillResponse) -> AssertionResult:
    # Placeholder judge: deterministic local scoring for MVP. Replace with model call later.
    keyword = evaluate_keyword_match(case, response)
    semantic = evaluate_semantic_similarity(case, response)
    score = (keyword.score + semantic.score) / 2
    passed = score >= (case.score_threshold or 0.8)
    return AssertionResult(
        type="llm_judge",
        passed=passed,
        score=score,
        detail=f"local judge placeholder score={score:.2f}",
    )

