import json
from pathlib import Path

import pytest

from apps.services.advisories import evaluate

CASES = json.loads((Path(__file__).parent / "fixtures/s08/advisory-source-cases.json").read_text())


@pytest.mark.parametrize("case", CASES, ids=lambda c: c["id"])
def test_reference_advisory_case(case):
    actual = evaluate(case["config"], case["answers"], case["funding"])
    assert actual["effective_answers"] == case["effective_answers"]
    assert [q["id"] for q in actual["questions"]] == case["active_question_ids"]
    assert actual["missing"] == case["missing"]
    assert actual["blocked_question_ids"] == case["blocked_question_ids"]
    assert actual["guidance"] == case["expected"]
