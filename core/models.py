from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class SkillConfig:
    skill_name: str
    skill_type: str
    base_url: str
    auth_type: str = "none"
    init_required: bool = False
    required_params: list[str] = field(default_factory=list)
    default_headers: dict[str, str] = field(default_factory=dict)
    setup_steps: list[str] = field(default_factory=list)
    execute_mode: str = "chat"
    assert_type: str = "keyword"
    score_threshold: float = 0.8
    enabled: bool = True
    raw: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class TestCase:
    case_id: str
    skill_name: str
    question: str
    expected_answer: str = ""
    input_params: dict[str, Any] = field(default_factory=dict)
    keywords: list[str] = field(default_factory=list)
    regex_patterns: list[str] = field(default_factory=list)
    forbidden_words: list[str] = field(default_factory=list)
    assert_type: str = ""
    score_threshold: float | None = None
    enabled: bool = True
    priority: str = "P1"
    raw: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class SkillResponse:
    success: bool
    answer: str
    status_code: int = 200
    request_id: str = ""
    latency_ms: float = 0
    raw: dict[str, Any] = field(default_factory=dict)
    retrievals: list[dict[str, Any]] = field(default_factory=list)
    tool_calls: list[dict[str, Any]] = field(default_factory=list)


@dataclass(frozen=True)
class AssertionResult:
    type: str
    passed: bool
    score: float
    detail: str


@dataclass(frozen=True)
class EvaluationResult:
    passed: bool
    score: float
    assertions: list[AssertionResult]
    reason: str

