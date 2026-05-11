from __future__ import annotations

from types import SimpleNamespace

from core.reporting import mask_sensitive
from integrations.openclaw import OpenClawExecutor


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
