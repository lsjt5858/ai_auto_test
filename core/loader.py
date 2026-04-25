from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

from config.settings import ROOT_DIR
from core.models import TestCase


def load_cases(path: str | Path = ROOT_DIR / "data" / "skill_cases.json") -> list[TestCase]:
    case_path = Path(path)
    if not case_path.is_absolute():
        case_path = ROOT_DIR / case_path

    suffix = case_path.suffix.lower()
    if suffix == ".json":
        records = json.loads(case_path.read_text(encoding="utf-8"))
    elif suffix == ".csv":
        with case_path.open(newline="", encoding="utf-8") as f:
            records = list(csv.DictReader(f))
    else:
        raise ValueError(f"Unsupported case file type: {case_path}")

    return [_to_case(record) for record in records if _as_bool(record.get("enabled", True))]


def _to_case(record: dict[str, Any]) -> TestCase:
    return TestCase(
        case_id=str(record["case_id"]),
        skill_name=str(record["skill_name"]),
        question=str(record["question"]),
        expected_answer=str(record.get("expected_answer", "")),
        input_params=_as_dict(record.get("input_params", {})),
        keywords=_as_list(record.get("keywords", [])),
        regex_patterns=_as_list(record.get("regex_patterns", [])),
        forbidden_words=_as_list(record.get("forbidden_words", [])),
        assert_type=str(record.get("assert_type", "")),
        score_threshold=float(record["score_threshold"]) if record.get("score_threshold") not in (None, "") else None,
        enabled=_as_bool(record.get("enabled", True)),
        priority=str(record.get("priority", "P1")),
        raw=record,
    )


def _as_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item) for item in value if str(item)]
    return [item.strip() for item in str(value).split(",") if item.strip()]


def _as_dict(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return value
    if not value:
        return {}
    return json.loads(str(value))


def _as_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() not in {"0", "false", "no", "n"}

