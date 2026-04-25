from __future__ import annotations

from pathlib import Path
from typing import Any

from config.settings import ROOT_DIR
from core.models import SkillConfig
from core.simple_yaml import load_yaml


class SkillManager:
    def __init__(self, config_dir: str | Path = ROOT_DIR / "config" / "skills") -> None:
        self.config_dir = Path(config_dir)
        self._skills = self._load_skills()

    def get(self, skill_name: str) -> SkillConfig:
        try:
            return self._skills[skill_name]
        except KeyError as exc:
            available = ", ".join(sorted(self._skills))
            raise KeyError(f"Unknown skill '{skill_name}'. Available skills: {available}") from exc

    def enabled_skills(self) -> list[SkillConfig]:
        return [skill for skill in self._skills.values() if skill.enabled]

    def validate_required_params(self, skill: SkillConfig, params: dict[str, Any]) -> None:
        missing = [name for name in skill.required_params if params.get(name) in (None, "")]
        if missing:
            raise ValueError(f"{skill.skill_name} missing required params: {', '.join(missing)}")

    def _load_skills(self) -> dict[str, SkillConfig]:
        skills: dict[str, SkillConfig] = {}
        for path in sorted(self.config_dir.glob("*.yaml")):
            raw = load_yaml(path)
            skill = SkillConfig(
                skill_name=str(raw["skill_name"]),
                skill_type=str(raw.get("skill_type", "qa")),
                base_url=str(raw["base_url"]),
                auth_type=str(raw.get("auth_type", "none")),
                init_required=bool(raw.get("init_required", False)),
                required_params=list(raw.get("required_params", [])),
                default_headers=dict(raw.get("default_headers", {})),
                setup_steps=list(raw.get("setup_steps", [])),
                execute_mode=str(raw.get("execute_mode", "chat")),
                assert_type=str(raw.get("assert_type", "keyword")),
                score_threshold=float(raw.get("score_threshold", 0.8)),
                enabled=bool(raw.get("enabled", True)),
                raw=raw,
            )
            skills[skill.skill_name] = skill
        return skills

