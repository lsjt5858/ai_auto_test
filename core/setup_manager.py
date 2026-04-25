from __future__ import annotations

from typing import Any
from uuid import uuid4

from core.models import SkillConfig


class SetupManager:
    def run(self, skill: SkillConfig, params: dict[str, Any]) -> dict[str, Any]:
        context = dict(params)
        if not skill.init_required:
            return context

        for step in skill.setup_steps:
            handler = getattr(self, f"_step_{step}", None)
            if handler is None:
                raise ValueError(f"Unsupported setup step '{step}' for skill '{skill.skill_name}'")
            context = handler(skill, context)
        return context

    def _step_create_session(self, skill: SkillConfig, context: dict[str, Any]) -> dict[str, Any]:
        context = dict(context)
        context.setdefault("session_id", f"{skill.skill_name}-{uuid4().hex[:12]}")
        return context

    def _step_bind_kb(self, skill: SkillConfig, context: dict[str, Any]) -> dict[str, Any]:
        context = dict(context)
        if context.get("knowledge_base_id"):
            context["kb_bound"] = True
        return context

