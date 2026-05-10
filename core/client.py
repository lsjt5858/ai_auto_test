from __future__ import annotations

import os
import shlex
import subprocess
import sys
import time
from pathlib import Path
from typing import Any
from uuid import uuid4

import requests
from tenacity import retry, stop_after_attempt, wait_fixed

from config.settings import ROOT_DIR
from config.settings import settings
from core.models import SkillConfig, SkillResponse, TestCase
from integrations.openclaw import OpenClawExecutor


class SkillClient:
    def __init__(self, timeout_seconds: float | None = None) -> None:
        self.timeout_seconds = timeout_seconds or settings.timeout_seconds
        self.openclaw_executor = OpenClawExecutor()

    def execute(self, skill: SkillConfig, case: TestCase, context: dict[str, Any]) -> SkillResponse:
        started = time.perf_counter()
        if skill.base_url.startswith("script://"):
            response = self._execute_script(skill, case, context)
        elif skill.base_url.startswith("sample://"):
            response = self._execute_sample(case, context)
        elif skill.base_url.startswith("mock://"):
            response = self._execute_mock(skill, case, context)
        elif skill.base_url.startswith("openclaw://"):
            response = self._execute_openclaw(skill, case, context)
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

    def _execute_script(self, skill: SkillConfig, case: TestCase, context: dict[str, Any]) -> SkillResponse:
        script_ref = skill.base_url.removeprefix("script://")
        format_values = dict(case.raw)
        format_values.update(context)
        format_values["question"] = case.question
        script_ref = script_ref.format(**format_values)
        script_path = Path(script_ref)
        if not script_path.is_absolute():
            script_path = ROOT_DIR / script_path

        command = list(skill.raw.get("command", [sys.executable, str(script_path)]))
        command = [part.format(**format_values) for part in command]
        if not skill.raw.get("command"):
            command = [sys.executable, str(script_path)]
        script_args = []
        script_args.extend(_as_args(skill.raw.get("script_args", [])))
        script_args.extend(_as_args(case.raw.get("script_args", [])))
        command.extend(str(arg).format(**format_values) for arg in script_args)

        env = os.environ.copy()
        env.update({key: str(value) for key, value in context.items() if value not in (None, "")})
        env.update(
            {
                "AI_TEST_CASE_ID": case.case_id,
                "AI_TEST_SKILL_NAME": case.skill_name,
                "AI_TEST_QUESTION": case.question,
                "AI_TEST_EXPECTED_ANSWER": case.expected_answer,
            }
        )
        completed = subprocess.run(
            command,
            cwd=str(script_path.parent),
            capture_output=True,
            text=True,
            timeout=self.timeout_seconds,
            env=env,
        )
        answer = completed.stdout.strip() or completed.stderr.strip()
        if completed.returncode == 0 and not answer:
            answer = "script completed successfully"
        return SkillResponse(
            success=completed.returncode == 0,
            answer=answer,
            status_code=completed.returncode,
            request_id=uuid4().hex,
            raw={
                "command": command,
                "stdout": completed.stdout,
                "stderr": completed.stderr,
                "returncode": completed.returncode,
            },
        )

    def _execute_openclaw(self, skill: SkillConfig, case: TestCase, context: dict[str, Any]) -> SkillResponse:
        result = self.openclaw_executor.execute(skill, case, context)
        return SkillResponse(
            success=result.success,
            answer=result.answer,
            status_code=result.status_code,
            request_id=result.request_id,
            raw=result.raw,
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


def _as_args(value: Any) -> list[str]:
    if value in (None, ""):
        return []
    if isinstance(value, list):
        return [str(item) for item in value if str(item)]
    return shlex.split(str(value))
