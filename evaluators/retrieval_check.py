from __future__ import annotations

from core.models import AssertionResult, SkillResponse, TestCase


def evaluate_retrieval_check(case: TestCase, response: SkillResponse) -> AssertionResult:
    expected_doc_id = case.raw.get("expected_doc_id")
    if not expected_doc_id:
        return AssertionResult(type="retrieval_check", passed=True, score=1.0, detail="no expected_doc_id configured")
    doc_ids = [str(item.get("doc_id")) for item in response.retrievals]
    passed = expected_doc_id in doc_ids
    return AssertionResult(
        type="retrieval_check",
        passed=passed,
        score=1.0 if passed else 0.0,
        detail="expected document retrieved" if passed else f"expected_doc_id={expected_doc_id}, actual_doc_ids={doc_ids}",
    )

