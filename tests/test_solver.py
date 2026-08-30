from __future__ import annotations

from conftest import survey_dict

from tarpscout.cords import CordNeed, assign_cords
from tarpscout.models import Cord, parse_scenario
from tarpscout.solver import solve


def test_cord_assignment_minimizes_unused_length() -> None:
    needs = (CordNeed("ridge", 5.8), CordNeed("guy", 1.0))
    cords = (Cord("long", 7.0), Cord("ridge-fit", 6.0), Cord("guy-fit", 1.2))

    assignment = assign_cords(needs, cords)

    assert assignment is not None
    assert [(use.need_id, use.cord_id) for use in assignment] == [
        ("ridge", "ridge-fit"),
        ("guy", "guy-fit"),
    ]
    assert round(sum(use.spare_length for use in assignment), 6) == 0.4


def test_cord_assignment_reports_shortage_and_stable_ties() -> None:
    needs = (CordNeed("guy", 1.0),)

    assert assign_cords(needs, (Cord("short", 0.9),)) is None
    tied = assign_cords(needs, (Cord("z-cord", 1.2), Cord("a-cord", 1.2)))
    assert tied is not None
    assert tied[0].cord_id == "a-cord"


def test_cord_assignment_handles_large_inventory_exactly() -> None:
    needs = tuple(CordNeed(f"line-{length}", float(length)) for length in range(10, 5, -1))
    cords = tuple(Cord(f"cord-{length:03d}", float(length)) for length in range(1, 81))

    assignment = assign_cords(needs, cords)

    assert assignment is not None
    assert [use.cord_id for use in assignment] == [
        "cord-010",
        "cord-009",
        "cord-008",
        "cord-007",
        "cord-006",
    ]
    assert sum(use.spare_length for use in assignment) == 0


def test_feasible_site_returns_ranked_a_frame_with_cords() -> None:
    result = solve(parse_scenario(survey_dict()), limit=3)

    assert result.status == "found"
    chosen = result.candidates[0]
    assert chosen.geometry.pitch_type == "a_frame"
    assert {use.need_id for use in chosen.cord_uses} == {
        "ridge",
        "guy-left-start",
        "guy-left-end",
        "guy-right-start",
        "guy-right-end",
    }


def test_keepout_reports_the_blocking_constraint() -> None:
    raw = survey_dict()
    raw["keepouts"] = [{"id": "fire-ring", "center": [2.5, 0.0], "radius": 0.3}]

    result = solve(parse_scenario(raw))

    assert result.status == "no_solution"
    assert result.rejections["keepout_conflict"] > 0
    assert "move the tarp footprint" in result.repair_hints["keepout_conflict"].lower()


def test_short_cords_report_shortage_instead_of_geometry_failure() -> None:
    raw = survey_dict()
    raw["cords"] = [{"id": f"short-{index}", "length": 0.5} for index in range(5)]

    result = solve(parse_scenario(raw))

    assert result.status == "no_solution"
    assert result.rejections["cord_shortage"] > 0


def test_solver_is_deterministic() -> None:
    scenario = parse_scenario(survey_dict())

    assert solve(scenario, limit=5) == solve(scenario, limit=5)
