from __future__ import annotations

from core.models import AssertionResult, SkillResponse, TestCase


def evaluate_tool_call_check(case: TestCase, response: SkillResponse) -> AssertionResult:
    expected_tool = case.raw.get("expected_tool")
    if not expected_tool:
        return AssertionResult(type="tool_call_check", passed=True, score=1.0, detail="no expected_tool configured")
    tools = [str(item.get("name") or item.get("tool_name")) for item in response.tool_calls]
    passed = expected_tool in tools
    return AssertionResult(
        type="tool_call_check",
        passed=passed,
        score=1.0 if passed else 0.0,
        detail="expected tool called" if passed else f"expected_tool={expected_tool}, actual_tools={tools}",
    )

