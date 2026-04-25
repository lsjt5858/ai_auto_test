from __future__ import annotations

import csv
import hashlib
import json
import re
from pathlib import Path
from typing import Any

from config.settings import ROOT_DIR
from config.settings import settings
from core.models import TestCase


def load_cases(path: str | Path | None = None) -> list[TestCase]:
    selected_path = path or settings.case_file or ROOT_DIR / "data" / "skill_cases.json"
    case_path = Path(selected_path)
    if not case_path.is_absolute():
        case_path = ROOT_DIR / case_path

    suffix = case_path.suffix.lower()
    if suffix == ".json":
        records = json.loads(case_path.read_text(encoding="utf-8"))
    elif suffix == ".csv":
        with case_path.open(newline="", encoding="utf-8-sig") as f:
            records = list(csv.DictReader(f))
    else:
        raise ValueError(f"Unsupported case file type: {case_path}")

    return [_to_case(record) for record in records if _is_valid_record(record) and _as_bool(record.get("enabled", True))]


def _to_case(record: dict[str, Any]) -> TestCase:
    normalized = _normalize_record(record)
    return TestCase(
        case_id=str(normalized["case_id"]),
        skill_name=str(normalized["skill_name"]),
        question=str(normalized["question"]),
        expected_answer=str(normalized.get("expected_answer", "")),
        input_params=_as_dict(normalized.get("input_params", {})),
        keywords=_as_list(normalized.get("keywords", [])),
        regex_patterns=_as_list(normalized.get("regex_patterns", [])),
        forbidden_words=_as_list(normalized.get("forbidden_words", [])),
        assert_type=str(normalized.get("assert_type", "")),
        score_threshold=float(normalized["score_threshold"]) if normalized.get("score_threshold") not in (None, "") else None,
        enabled=_as_bool(normalized.get("enabled", True)),
        priority=str(normalized.get("priority", "P1")),
        raw=normalized,
    )


def _normalize_record(record: dict[str, Any]) -> dict[str, Any]:
    normalized = dict(record)
    normalized["skill_name"] = _clean_text(
        normalized.get("skill_name")
        or normalized.get("skill")
        or normalized.get("技能")
        or "unknown_skill"
    )
    normalized["question"] = _clean_text(
        normalized.get("question")
        or normalized.get("input")
        or normalized.get("输入")
        or normalized.get("问题")
        or ""
    )
    normalized["expected_answer"] = _clean_text(
        normalized.get("expected_answer")
        or normalized.get("预期的返回（部分关键信息）")
        or normalized.get("预期返回")
        or ""
    )
    normalized["actual_response"] = _clean_text(
        normalized.get("actual_response")
        or normalized.get("真实返回举例（ArkClaw）")
        or normalized.get("真实返回")
        or ""
    )
    normalized["rule"] = _clean_text(normalized.get("rule") or normalized.get("规则") or "")
    normalized["case_id"] = _clean_text(normalized.get("case_id") or normalized.get("用例ID") or "") or _build_case_id(normalized)
    normalized["assert_type"] = _clean_text(normalized.get("assert_type") or normalized.get("断言方式") or "rubric")
    normalized["score_threshold"] = normalized.get("score_threshold") or normalized.get("通过阈值") or 0.8
    normalized["enabled"] = normalized.get("enabled", normalized.get("是否启用", True))
    normalized["keywords"] = normalized.get("keywords") or normalized.get("关键词") or _extract_keywords(normalized["expected_answer"])
    normalized["forbidden_words"] = normalized.get("forbidden_words") or normalized.get("禁用词") or _extract_forbidden_words(normalized["rule"])
    normalized["regex_patterns"] = normalized.get("regex_patterns") or normalized.get("正则") or []
    normalized["input_params"] = normalized.get("input_params") or normalized.get("输入参数") or {}
    return normalized


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


def _is_valid_record(record: dict[str, Any]) -> bool:
    values = [_clean_text(value) for value in record.values()]
    if not any(values):
        return False
    normalized = _normalize_record(record)
    return bool(normalized.get("skill_name") != "unknown_skill" and normalized.get("question"))


def _clean_text(value: Any) -> str:
    return str(value or "").replace("\ufeff", "").replace("\u200e", "").strip()


def _build_case_id(record: dict[str, Any]) -> str:
    skill_name = re.sub(r"\W+", "_", record.get("skill_name", "skill")).strip("_").upper()
    question = record.get("question", "")
    digest = hashlib.md5(question.encode("utf-8")).hexdigest()[:8].upper()
    return f"{skill_name}_{digest}"


def _extract_keywords(expected_answer: str) -> list[str]:
    candidates = re.findall(r"[A-Za-z_][A-Za-z0-9_]*|[\u4e00-\u9fff]{2,}", expected_answer)
    ignored = {"成功", "完成", "返回", "查询结果", "包含"}
    return [item for item in candidates[:8] if item not in ignored]


def _extract_forbidden_words(rule: str) -> list[str]:
    words: list[str] = []
    patterns = [
        r"不允许出现([^，。\n]+)",
        r"不应该出现([^，。\n]+)",
        r"不允许显示([^，。\n]+)",
    ]
    for pattern in patterns:
        words.extend(match.strip(" ：:「」任意字段信息") for match in re.findall(pattern, rule))
    return [word for word in words if word]
