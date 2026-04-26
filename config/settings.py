from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]


def _load_dotenv() -> None:
    env_path = ROOT_DIR / ".env"
    if not env_path.exists():
        return
    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


_load_dotenv()


@dataclass(frozen=True)
class Settings:
    env: str = os.getenv("AI_TEST_ENV", "local")
    timeout_seconds: float = float(os.getenv("AI_TEST_TIMEOUT_SECONDS", "30"))
    default_score_threshold: float = float(os.getenv("AI_TEST_DEFAULT_SCORE_THRESHOLD", "0.8"))
    case_file: str = os.getenv("AI_TEST_CASE_FILE", "")
    case_dir: str = os.getenv("AI_TEST_CASE_DIR", "")
    case_results_file: str = os.getenv("AI_TEST_CASE_RESULTS_FILE", "reports/current/case_results.jsonl")
    runtime_params_file: str = os.getenv("AI_TEST_RUNTIME_PARAMS_FILE", "")
    api_token: str = os.getenv("AI_TEST_API_TOKEN", "")
    judge_api_key: str = os.getenv("AI_TEST_JUDGE_API_KEY", "")


settings = Settings()
