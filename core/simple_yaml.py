from __future__ import annotations

from pathlib import Path
from typing import Any


def load_yaml(path: Path) -> dict[str, Any]:
    try:
        import yaml  # type: ignore

        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        return data or {}
    except ModuleNotFoundError:
        return _load_simple_yaml(path)


def _load_simple_yaml(path: Path) -> dict[str, Any]:
    data: dict[str, Any] = {}
    current_key: str | None = None
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        if not raw_line.strip() or raw_line.lstrip().startswith("#"):
            continue
        if raw_line.startswith("  - ") and current_key:
            data.setdefault(current_key, []).append(_parse_scalar(raw_line[4:].strip()))
            continue
        if raw_line.startswith("  ") and current_key:
            key, value = raw_line.strip().split(":", 1)
            data.setdefault(current_key, {})[key.strip().strip('"')] = _parse_scalar(value.strip())
            continue
        key, _, value = raw_line.partition(":")
        current_key = key.strip()
        data[current_key] = [] if not value.strip() else _parse_scalar(value.strip())
    return data


def _parse_scalar(value: str) -> Any:
    value = value.strip().strip('"').strip("'")
    if value.lower() == "true":
        return True
    if value.lower() == "false":
        return False
    try:
        return int(value)
    except ValueError:
        pass
    try:
        return float(value)
    except ValueError:
        return value

