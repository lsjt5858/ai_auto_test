from __future__ import annotations

import pytest


@pytest.mark.routing
def test_case_skill_config_exists(case, skill_manager) -> None:
    skill = skill_manager.get(case.skill_name)
    assert skill.enabled
    assert skill.skill_name == case.skill_name

