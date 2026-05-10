from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any

from config.settings import ROOT_DIR, settings


class RuntimeParams:
    def __init__(self, path: str | Path | None = None) -> None:
        self.path = Path(path or settings.runtime_params_file) if path or settings.runtime_params_file else None
        self.data = self._load_file(self.path)

    def for_skill(self, skill_name: str) -> dict[str, Any]:
        params: dict[str, Any] = {}
        params.update(self.data.get("global", {}))
        params.update(self.data.get("skills", {}).get(skill_name, {}))
        params.update(self.data.get(skill_name, {}))
        params.update(_env_runtime_params())
        return {key: value for key, value in params.items() if value not in (None, "")}

    def merge(self, skill_name: str, case_params: dict[str, Any]) -> dict[str, Any]:
        params = self.for_skill(skill_name)
        params.update(case_params)
        return params

    def _load_file(self, path: Path | None) -> dict[str, Any]:
        if path is None:
            return {}
        if not path.is_absolute():
            path = ROOT_DIR / path
        if not path.exists():
            raise FileNotFoundError(f"Runtime params file not found: {path}")
        if path.suffix.lower() == ".json":
            return json.loads(path.read_text(encoding="utf-8"))
        if path.suffix.lower() in {".md", ".env", ".sh", ".txt"}:
            return {"global": _parse_export_file(path)}
        raise ValueError(f"Runtime params supports JSON or export-style files only: {path}")


def _parse_export_file(path: Path) -> dict[str, str]:
    params: dict[str, str] = {}
    pattern = re.compile(r"^(?:export\s+)?([A-Za-z_][A-Za-z0-9_]*)=(.*)$")
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        match = pattern.match(line)
        if not match:
            continue
        key, value = match.groups()
        params[key] = value.strip().strip('"').strip("'")
    return params


def _env_runtime_params() -> dict[str, Any]:
    keys = [
        "BYTEHOUSE_HOST",
        "BYTEHOUSE_PORT",
        "BYTEHOUSE_USER",
        "BYTEHOUSE_PASSWORD",
        "BYTEHOUSE_DATABASE",
        "BYTEHOUSE_SECURE",
        "BYTEHOUSE_VERIFY",
        "KB_ID",
        "BH_ARK_API_KEY",
        "BH_ARK_BASE_URL",
        "BH_EMBEDDING_MODEL",
        "OPENCLAW_HOST",
        "OPENCLAW_PORT",
        "OPENCLAW_USERNAME",
        "OPENCLAW_PASSWORD",
        "OPENCLAW_PRIVATE_KEY",
        "OPENCLAW_PRIVATE_KEY_FILE",
        "OPENCLAW_PASSPHRASE",
        "OPENCLAW_KNOWN_HOSTS",
        "OPENCLAW_STRICT_HOST_KEY",
        "OPENCLAW_CONNECT_TIMEOUT",
        "OPENCLAW_COMMAND_TIMEOUT",
        "OPENCLAW_MODE",
        "OPENCLAW_AGENT_NAME",
        "OPENCLAW_AGENT_TIMEOUT",
    ]
    return {key: os.getenv(key) for key in keys if os.getenv(key)}
