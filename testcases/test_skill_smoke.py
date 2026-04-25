from __future__ import annotations

import pytest

from core.assertion import assert_evaluation_passed
from testcases.conftest import attach_json


@pytest.mark.smoke
def test_skill_smoke(case, skill_manager, setup_manager, skill_client, evaluator) -> None:
    skill = skill_manager.get(case.skill_name)
    skill_manager.validate_required_params(skill, case.input_params)
    context = setup_manager.run(skill, case.input_params)

    response = skill_client.execute(skill, case, context)
    result = evaluator.evaluate(skill, case, response)

    attach_json("skill_config", skill.raw)
    attach_json("input_params", context)
    attach_json("actual_response", response)
    attach_json("evaluation", result)

    assert response.success
    assert response.answer
    assert_evaluation_passed(result)

