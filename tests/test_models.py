from __future__ import annotations

import pytest
from conftest import survey_dict

from tarpscout.models import InputError, parse_scenario


def test_parse_scenario_builds_typed_boundary_model() -> None:
    scenario = parse_scenario(survey_dict())

    assert scenario.name == "pine-gap"
    assert scenario.tarp.length == 3.0
    assert scenario.supports[1].point.x == 5.0
    assert scenario.requirements.pitch_types == ("a_frame", "lean_to")
    assert scenario.requirements.wind_from_deg == 270.0


def test_unknown_field_fails_with_exact_path() -> None:
    raw = survey_dict()
    raw["requirements"]["serach_step"] = 0.1

    with pytest.raises(InputError, match=r"requirements\.serach_step: unknown field"):
        parse_scenario(raw)


def test_duplicate_support_id_is_rejected() -> None:
    raw = survey_dict()
    raw["supports"][1]["id"] = "west-pine"

    with pytest.raises(InputError, match=r"supports\[1\]\.id: duplicate 'west-pine'"):
        parse_scenario(raw)


def test_degenerate_stake_polygon_is_rejected() -> None:
    raw = survey_dict()
    raw["stake_zones"][0]["polygon"] = [[0, 0], [1, 1], [2, 2]]

    with pytest.raises(InputError, match=r"stake_zones\[0\]\.polygon: area must be non-zero"):
        parse_scenario(raw)


def test_boolean_is_not_accepted_as_a_number() -> None:
    raw = survey_dict()
    raw["tarp"]["length"] = True

    with pytest.raises(InputError, match=r"tarp\.length: expected number"):
        parse_scenario(raw)
