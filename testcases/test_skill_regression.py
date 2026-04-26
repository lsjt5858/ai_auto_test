from __future__ import annotations

import pytest

from core.assertion import assert_evaluation_passed
from core.reporting import record_case_result


@pytest.mark.regression
def test_skill_regression(case, skill_manager, setup_manager, skill_client, evaluator, runtime_params) -> None:
    skill = skill_manager.get(case.skill_name)
    merged_params = runtime_params.merge(case.skill_name, case.input_params)
    skill_manager.validate_required_params(skill, merged_params)
    context = setup_manager.run(skill, merged_params)
    response = skill_client.execute(skill, case, context)
    result = evaluator.evaluate(skill, case, response)
    record_case_result(case, skill, context, response, result)
    assert_evaluation_passed(result)
