from __future__ import annotations

import json
from pathlib import Path

import pytest

from tarpscout.demo_data import demo_documents
from tarpscout.models import parse_scenario
from tarpscout.solver import solve

EXAMPLES = Path(__file__).parents[1] / "examples"


@pytest.mark.parametrize(
    ("name", "expected_status"),
    [
        ("pine-gap", "found"),
        ("creek-lean-to", "found"),
        ("fire-ring", "no_solution"),
        ("short-cords", "no_solution"),
    ],
)
def test_checked_in_examples_match_demo_and_solve(name: str, expected_status: str) -> None:
    raw = json.loads((EXAMPLES / f"{name}.site.json").read_text(encoding="utf-8"))
    built_in = {document["name"]: document for document in demo_documents()}

    assert raw == built_in[name]
    result = solve(parse_scenario(raw))
    assert result.status == expected_status
    if name == "creek-lean-to":
        assert result.candidates[0].geometry.pitch_type == "lean_to"
    if name == "fire-ring":
        assert result.rejections["keepout_conflict"] > 0
    if name == "short-cords":
        assert result.rejections["cord_shortage"] > 0
