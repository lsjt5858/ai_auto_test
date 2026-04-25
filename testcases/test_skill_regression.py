from __future__ import annotations

import pytest

from core.assertion import assert_evaluation_passed


@pytest.mark.regression
def test_skill_regression(case, skill_manager, setup_manager, skill_client, evaluator) -> None:
    skill = skill_manager.get(case.skill_name)
    context = setup_manager.run(skill, case.input_params)
    response = skill_client.execute(skill, case, context)
    result = evaluator.evaluate(skill, case, response)
    assert_evaluation_passed(result)

