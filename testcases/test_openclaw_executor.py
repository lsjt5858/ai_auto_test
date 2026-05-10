from __future__ import annotations

from types import SimpleNamespace

from core.reporting import mask_sensitive
from integrations.openclaw import OpenClawExecutor, _extract_agent_answer, _parse_agent_json


def test_openclaw_command_prefers_case_input_params() -> None:
    executor = OpenClawExecutor()
    skill = SimpleNamespace(raw={"command_template": "echo {question}"})
    case = SimpleNamespace(
        input_params={"openclaw_command": "cd {project_dir} && {question}"},
        raw={},
        question="python -m pytest -q",
    )

    command = executor._build_command(skill, case, {"project_dir": "/srv/app"})

    assert command == "cd /srv/app && python -m pytest -q"


def test_openclaw_command_keeps_shell_braces() -> None:
    executor = OpenClawExecutor()
    skill = SimpleNamespace(raw={})
    case = SimpleNamespace(
        input_params={"openclaw_command": "cd {project_dir} && awk '{print $1}' result.txt"},
        raw={},
        question="fallback",
    )

    command = executor._build_command(skill, case, {"project_dir": "/srv/app"})

    assert command == "cd /srv/app && awk '{print $1}' result.txt"


def test_openclaw_agent_command_wraps_case_as_message() -> None:
    executor = OpenClawExecutor()
    skill = SimpleNamespace(raw={"openclaw_mode": "agent", "agent_name": "main"})
    case = SimpleNamespace(
        input_params={"openclaw_task": "执行接口测试：curl -sS -i {api_url}/health"},
        raw={},
        question="fallback",
    )

    command = executor._build_command(skill, case, {"api_url": "http://127.0.0.1:18789"})

    assert command.startswith("openclaw agent --agent main -m ")
    assert "curl -sS -i http://127.0.0.1:18789/health" in command
    assert command.endswith("--timeout 180 --json")


def test_openclaw_agent_json_parser_ignores_plugin_logs() -> None:
    stdout = """
[plugins] initialized
{
  "runId": "r1",
  "status": "ok",
  "result": {
    "payloads": [
      {"text": "HTTP/1.1 200 OK\\n{\\"ok\\":true}"}
    ]
  }
}
"""

    parsed = _parse_agent_json(stdout)

    assert parsed["status"] == "ok"
    assert _extract_agent_answer(parsed) == 'HTTP/1.1 200 OK\n{"ok":true}'


def test_openclaw_report_masks_private_key_and_passphrase() -> None:
    masked = mask_sensitive(
        {
            "OPENCLAW_PRIVATE_KEY": "secret-key",
            "OPENCLAW_PASSPHRASE": "secret-passphrase",
            "stdout": "ok",
        }
    )

    assert masked["OPENCLAW_PRIVATE_KEY"] == "***MASKED***"
    assert masked["OPENCLAW_PASSPHRASE"] == "***MASKED***"
    assert masked["stdout"] == "ok"
