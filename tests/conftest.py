"""Shared fixtures. `case(...)` records Test ID / Scenario / Input / Expected / Actual so
tests/generate_test_report.py can build docs/TEST_RESULTS.md from the real run."""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.app import create_app  # noqa: E402
from backend.questionnaire import safest_answers, worst_answers  # noqa: E402


@pytest.fixture()
def app(tmp_path):
    return create_app({"DATABASE_PATH": str(tmp_path / "test.db"), "TESTING": True,
                       "RATE_LIMIT_PER_MINUTE": 1000, "RATE_LIMIT_POST_PER_MINUTE": 1000})


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture()
def safe():
    return safest_answers()


@pytest.fixture()
def worst():
    return worst_answers()


@pytest.fixture()
def case(record_property):
    def _case(test_id, scenario, input_, expected, actual):
        record_property("test_id", test_id)
        record_property("scenario", scenario)
        record_property("input", str(input_))
        record_property("expected", str(expected))
        record_property("actual", str(actual))
    return _case
