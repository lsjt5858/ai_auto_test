from __future__ import annotations

from statistics import mean

from config.settings import settings
from core.models import EvaluationResult, SkillConfig, SkillResponse, TestCase
from evaluators.exact_match import evaluate_exact_match
from evaluators.keyword_match import evaluate_keyword_match
from evaluators.llm_judge import evaluate_llm_judge
from evaluators.regex_match import evaluate_regex_match
from evaluators.retrieval_check import evaluate_retrieval_check
from evaluators.semantic_similarity import evaluate_semantic_similarity
from evaluators.tool_call_check import evaluate_tool_call_check


class Evaluator:
    def evaluate(self, skill: SkillConfig, case: TestCase, response: SkillResponse) -> EvaluationResult:
        strategies = _parse_strategies(case.assert_type or skill.assert_type)
        assertions = []
        for strategy in strategies:
            if strategy == "exact_match":
                assertions.append(evaluate_exact_match(case, response))
            elif strategy == "keyword":
                assertions.append(evaluate_keyword_match(case, response))
            elif strategy == "regex":
                assertions.append(evaluate_regex_match(case, response))
            elif strategy == "semantic_similarity":
                assertions.append(evaluate_semantic_similarity(case, response))
            elif strategy == "llm_judge":
                assertions.append(evaluate_llm_judge(case, response))
            elif strategy == "tool_call_check":
                assertions.append(evaluate_tool_call_check(case, response))
            elif strategy == "retrieval_check":
                assertions.append(evaluate_retrieval_check(case, response))
            else:
                raise ValueError(f"Unsupported assert strategy: {strategy}")

        score = mean([item.score for item in assertions]) if assertions else 0.0
        threshold = case.score_threshold or skill.score_threshold or settings.default_score_threshold
        passed = bool(assertions) and all(item.passed for item in assertions) and score >= threshold
        failed_details = [item.detail for item in assertions if not item.passed]
        reason = "passed" if passed else "; ".join(failed_details) or f"score {score:.2f} below threshold {threshold:.2f}"
        return EvaluationResult(passed=passed, score=score, assertions=assertions, reason=reason)


def _parse_strategies(assert_type: str) -> list[str]:
    return [item.strip() for item in assert_type.replace(",", "+").split("+") if item.strip()]

