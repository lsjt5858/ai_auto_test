from __future__ import annotations

import time
from typing import Any
from uuid import uuid4

import requests
from tenacity import retry, stop_after_attempt, wait_fixed

from config.settings import settings
from core.models import SkillConfig, SkillResponse, TestCase


class SkillClient:
    def __init__(self, timeout_seconds: float | None = None) -> None:
        self.timeout_seconds = timeout_seconds or settings.timeout_seconds

    def execute(self, skill: SkillConfig, case: TestCase, context: dict[str, Any]) -> SkillResponse:
        started = time.perf_counter()
        if skill.base_url.startswith("sample://"):
            response = self._execute_sample(case, context)
        elif skill.base_url.startswith("mock://"):
            response = self._execute_mock(skill, case, context)
        else:
            response = self._execute_http(skill, case, context)
        latency_ms = (time.perf_counter() - started) * 1000
        return SkillResponse(
            success=response.success,
            answer=response.answer,
            status_code=response.status_code,
            request_id=response.request_id,
            latency_ms=latency_ms,
            raw=response.raw,
            retrievals=response.retrievals,
            tool_calls=response.tool_calls,
        )

    def _execute_mock(self, skill: SkillConfig, case: TestCase, context: dict[str, Any]) -> SkillResponse:
        answers = dict(skill.raw.get("mock_answers", {}))
        answer = answers.get(case.question, f"Mock answer for {case.question}")
        return SkillResponse(
            success=True,
            answer=answer,
            request_id=uuid4().hex,
            raw={"context": context, "skill": skill.skill_name, "question": case.question},
        )

    def _execute_sample(self, case: TestCase, context: dict[str, Any]) -> SkillResponse:
        answer = str(
            case.raw.get("actual_response")
            or case.raw.get("真实返回举例（ArkClaw）")
            or case.raw.get("真实返回")
            or ""
        )
        return SkillResponse(
            success=bool(answer),
            answer=answer,
            request_id=uuid4().hex,
            raw={"context": context, "question": case.question, "source": "sample_response"},
        )

    @retry(stop=stop_after_attempt(2), wait=wait_fixed(1))
    def _execute_http(self, skill: SkillConfig, case: TestCase, context: dict[str, Any]) -> SkillResponse:
        headers = dict(skill.default_headers)
        if skill.auth_type == "bearer" and context.get("token"):
            headers["Authorization"] = f"Bearer {context['token']}"

        payload = {
            "skill_name": skill.skill_name,
            "question": case.question,
            "params": context,
        }
        resp = requests.post(skill.base_url, json=payload, headers=headers, timeout=self.timeout_seconds)
        resp.raise_for_status()
        data = resp.json()

        return SkillResponse(
            success=bool(data.get("success", True)),
            answer=str(data.get("answer", data.get("content", ""))),
            status_code=resp.status_code,
            request_id=str(data.get("request_id", "")),
            raw=data,
            retrievals=list(data.get("retrievals", [])),
            tool_calls=list(data.get("tool_calls", [])),
        )
