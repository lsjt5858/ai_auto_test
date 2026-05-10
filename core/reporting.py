from __future__ import annotations

import json
from dataclasses import asdict, is_dataclass
from pathlib import Path
from typing import Any

from config.settings import ROOT_DIR, settings


SENSITIVE_PATTERNS = (
    "PASSWORD",
    "TOKEN",
    "SECRET",
    "API_KEY",
    "ACCESS_KEY",
    "PRIVATE_KEY",
    "PASSPHRASE",
    "SECRET_KEY",
    "AUTHORIZATION",
)


def report_path() -> Path:
    path = Path(settings.case_results_file)
    if not path.is_absolute():
        path = ROOT_DIR / path
    return path


def reset_report_file() -> None:
    path = report_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("", encoding="utf-8")


def record_case_result(case: Any, skill: Any, context: dict[str, Any], response: Any, evaluation: Any) -> None:
    path = report_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    record = {
        "case_id": getattr(case, "case_id", ""),
        "skill_name": getattr(case, "skill_name", ""),
        "skill_type": getattr(skill, "skill_type", ""),
        "execute_mode": getattr(skill, "execute_mode", ""),
        "question": getattr(case, "question", ""),
        "expected_answer": getattr(case, "expected_answer", ""),
        "assert_type": getattr(case, "assert_type", "") or getattr(skill, "assert_type", ""),
        "score_threshold": getattr(case, "score_threshold", None) or getattr(skill, "score_threshold", None),
        "context": mask_sensitive(context),
        "response": mask_sensitive(_to_plain(response)),
        "evaluation": mask_sensitive(_to_plain(evaluation)),
        "raw_case": mask_sensitive(getattr(case, "raw", {})),
    }
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False, default=str) + "\n")


def mask_sensitive(value: Any) -> Any:
    if isinstance(value, dict):
        masked = {}
        for key, item in value.items():
            key_text = str(key).upper()
            if any(pattern in key_text for pattern in SENSITIVE_PATTERNS):
                masked[key] = "***MASKED***" if item not in (None, "") else item
            else:
                masked[key] = mask_sensitive(item)
        return masked
    if isinstance(value, list):
        return [mask_sensitive(item) for item in value]
    return value


def _to_plain(value: Any) -> Any:
    if is_dataclass(value):
        return asdict(value)
    if isinstance(value, dict):
        return {key: _to_plain(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_to_plain(item) for item in value]
    return value
