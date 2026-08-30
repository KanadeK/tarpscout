from __future__ import annotations

import math
from pathlib import Path

import pytest
from conftest import survey_dict

from tarpscout.models import InputError, load_scenario, parse_scenario


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


def test_invalid_json_reports_the_input_path(tmp_path: Path) -> None:
    path = tmp_path / "broken.site.json"
    path.write_text("{", encoding="utf-8")

    with pytest.raises(InputError, match=r"broken\.site\.json"):
        load_scenario(path)


def test_top_level_value_must_be_an_object() -> None:
    with pytest.raises(InputError, match=r"scenario: expected object"):
        parse_scenario([])


def test_missing_required_field_reports_exact_path() -> None:
    raw = survey_dict()
    del raw["tarp"]

    with pytest.raises(InputError, match=r"scenario\.tarp: required field"):
        parse_scenario(raw)


def test_name_must_be_non_empty_and_filename_safe() -> None:
    empty = survey_dict()
    empty["name"] = ""
    unsafe = survey_dict()
    unsafe["name"] = "pine gap"

    with pytest.raises(InputError, match=r"name: expected non-empty string"):
        parse_scenario(empty)
    with pytest.raises(InputError, match=r"name: use 1-64 ASCII"):
        parse_scenario(unsafe)


def test_numbers_must_be_finite() -> None:
    raw = survey_dict()
    raw["tarp"]["width"] = math.inf

    with pytest.raises(InputError, match=r"tarp\.width: expected finite number"):
        parse_scenario(raw)


def test_points_must_have_two_coordinates() -> None:
    raw = survey_dict()
    raw["footprints"][0]["center"] = [2.5]

    with pytest.raises(InputError, match=r"footprints\[0\]\.center: expected \[x, y\]"):
        parse_scenario(raw)


def test_ranges_require_ordered_bounds_and_an_internal_preference() -> None:
    reversed_range = survey_dict()
    reversed_range["requirements"]["ridge_height"] = {
        "min": 1.6,
        "max": 1.4,
        "preferred": 1.5,
    }
    outside_preference = survey_dict()
    outside_preference["requirements"]["ridge_height"]["preferred"] = 2.0

    with pytest.raises(InputError, match=r"requirements\.ridge_height: min must be <= max"):
        parse_scenario(reversed_range)
    with pytest.raises(InputError, match=r"ridge_height\.preferred: must be inside min/max"):
        parse_scenario(outside_preference)


def test_supports_require_two_unique_coordinates() -> None:
    too_few = survey_dict()
    too_few["supports"] = too_few["supports"][:1]
    duplicate_point = survey_dict()
    duplicate_point["supports"][1]["x"] = 0.0

    with pytest.raises(InputError, match=r"supports: expected at least two supports"):
        parse_scenario(too_few)
    with pytest.raises(InputError, match=r"supports: coordinates must be unique"):
        parse_scenario(duplicate_point)


def test_required_collections_cannot_be_empty() -> None:
    no_stake_zone = survey_dict()
    no_stake_zone["stake_zones"] = []
    no_footprint = survey_dict()
    no_footprint["footprints"] = []

    with pytest.raises(InputError, match=r"stake_zones: expected at least one polygon"):
        parse_scenario(no_stake_zone)
    with pytest.raises(InputError, match=r"footprints: expected at least one rectangle"):
        parse_scenario(no_footprint)


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("pitch_types", ["a_frame", "a_frame"], "expected unique values"),
        ("pitch_types", ["diamond"], "unsupported 'diamond'"),
        ("slope_angle", {"min": 0.0, "max": 70.0}, "expected 0 < min <= max < 90"),
        ("edge_height", 1.4, "must be below minimum ridge height"),
        ("max_search_states", 0, "expected 1..1000000"),
        ("wind_from_deg", 360.0, "expected 0 <= value < 360"),
    ],
)
def test_requirement_boundaries_are_rejected(field: str, value: object, message: str) -> None:
    raw = survey_dict()
    raw["requirements"][field] = value

    with pytest.raises(InputError, match=message):
        parse_scenario(raw)
