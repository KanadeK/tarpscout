from __future__ import annotations

import math

import pytest
from conftest import survey_dict

from tarpscout.geometry import (
    circle_intersects_polygon,
    point_in_polygon,
    rotated_rectangle,
    segment_intersects_circle,
)
from tarpscout.models import CircleKeepout, Footprint, Point, parse_scenario
from tarpscout.pitches import enumerate_geometries


def test_rotated_rectangle_uses_declared_center_and_angle() -> None:
    rectangle = rotated_rectangle(
        Footprint("pad", Point(1.0, 2.0), length=2.0, width=1.0, angle_deg=90.0)
    )

    assert {(round(p.x, 6), round(p.y, 6)) for p in rectangle} == {
        (0.5, 1.0),
        (1.5, 1.0),
        (1.5, 3.0),
        (0.5, 3.0),
    }


def test_polygon_margin_rejects_point_too_close_to_edge() -> None:
    polygon = (Point(0, 0), Point(4, 0), Point(4, 2), Point(0, 2))

    assert point_in_polygon(Point(0.2, 1.0), polygon)
    assert not point_in_polygon(Point(0.2, 1.0), polygon, margin=0.25)


@pytest.mark.parametrize(
    ("center", "radius", "expected"),
    [((2.0, 1.0), 0.1, True), ((4.2, 1.0), 0.25, True), ((4.3, 1.0), 0.2, False)],
)
def test_circle_polygon_intersection(
    center: tuple[float, float], radius: float, expected: bool
) -> None:
    polygon = (Point(0, 0), Point(4, 0), Point(4, 2), Point(0, 2))
    keepout = CircleKeepout("hazard", Point(*center), radius)

    assert circle_intersects_polygon(keepout, polygon) is expected


def test_segment_circle_intersection_includes_tangent() -> None:
    keepout = CircleKeepout("root", Point(1.0, 1.0), 1.0)

    assert segment_intersects_circle(Point(0, 0), Point(2, 0), keepout)
    assert not segment_intersects_circle(Point(0, -0.1), Point(2, -0.1), keepout)


def test_enumeration_builds_both_declared_pitch_types() -> None:
    generated = enumerate_geometries(parse_scenario(survey_dict()))

    assert {candidate.pitch_type for candidate in generated.geometries} == {
        "a_frame",
        "lean_to",
    }
    assert generated.search_limited is False


def test_a_frame_cross_section_matches_hand_calculation() -> None:
    raw = survey_dict()
    raw["requirements"]["pitch_types"] = ["a_frame"]
    raw["requirements"]["ridge_height"] = {"min": 1.5, "max": 1.5, "preferred": 1.5}
    scenario = parse_scenario(raw)

    candidate = enumerate_geometries(scenario).geometries[0]

    expected_run = math.sqrt((scenario.tarp.width / 2) ** 2 - (1.5 - 0.2) ** 2)
    assert candidate.slope_angle_deg == pytest.approx(math.degrees(math.asin(1.3 / 1.5)))
    assert max(point.y for point in candidate.coverage) == pytest.approx(expected_run)
    assert len(candidate.lines) == 5
