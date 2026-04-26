from __future__ import annotations

import json

import pytest

try:
    import allure
except ModuleNotFoundError:  # pragma: no cover
    allure = None

from core.client import SkillClient
from core.evaluator import Evaluator
from core.loader import load_cases
from core.reporting import mask_sensitive, reset_report_file
from core.runtime_params import RuntimeParams
from core.setup_manager import SetupManager
from core.skill_manager import SkillManager


def pytest_sessionstart(session: pytest.Session) -> None:
    reset_report_file()


@pytest.fixture(scope="session")
def skill_manager() -> SkillManager:
    return SkillManager()


@pytest.fixture(scope="session")
def setup_manager() -> SetupManager:
    return SetupManager()


@pytest.fixture(scope="session")
def skill_client() -> SkillClient:
    return SkillClient()


@pytest.fixture(scope="session")
def evaluator() -> Evaluator:
    return Evaluator()


@pytest.fixture(scope="session")
def runtime_params() -> RuntimeParams:
    return RuntimeParams()


def pytest_generate_tests(metafunc: pytest.Metafunc) -> None:
    if "case" in metafunc.fixturenames:
        cases = load_cases()
        metafunc.parametrize("case", cases, ids=[case.case_id for case in cases])


def attach_json(name: str, value: object) -> None:
    text = json.dumps(mask_sensitive(value), ensure_ascii=False, indent=2, default=str)
    if allure:
        allure.attach(text, name=name, attachment_type=allure.attachment_type.JSON)
