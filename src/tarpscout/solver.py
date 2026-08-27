"""Constraint checks, deterministic ranking, and explainable rejection counts."""

from __future__ import annotations

import math
from collections import Counter
from dataclasses import dataclass

from tarpscout.cords import CordNeed, CordUse, assign_cords
from tarpscout.geometry import (
    circle_intersects_polygon,
    point_in_polygon,
    rotated_rectangle,
    segment_intersects_circle,
)
from tarpscout.models import Point, Scenario
from tarpscout.pitches import PitchGeometry, enumerate_geometries

REPAIR_HINTS = {
    "support_span_too_short": (
        "Choose supports farther apart, reduce end clearance, or use a shorter tarp."
    ),
    "ridge_height_unavailable": (
        "Use supports whose attachment ranges overlap the requested ridge height."
    ),
    "slope_out_of_range": (
        "Adjust ridge/edge height or allow a roof slope compatible with the tarp width."
    ),
    "footprint_not_covered": "Move or reduce the required footprint, or use a larger tarp.",
    "stake_outside_zone": "Expand the measured stakeable area or change the stake setback.",
    "keepout_conflict": (
        "Move the tarp footprint, guylines, or circular keep-out before solving again."
    ),
    "cord_shortage": "Add a longer reusable cord segment or reduce declared allowances/setback.",
    "search_limit": "Increase max_search_states or use a coarser search_step.",
}


@dataclass(frozen=True, slots=True)
class CandidateSolution:
    geometry: PitchGeometry
    cord_uses: tuple[CordUse, ...]
    score: tuple[float, float, float, str]


@dataclass(frozen=True, slots=True)
class SolveResult:
    status: str
    considered: int
    search_states: int
    search_limited: bool
    rejections: dict[str, int]
    repair_hints: dict[str, str]
    candidates: tuple[CandidateSolution, ...]


def _footprints_fit(scenario: Scenario, geometry: PitchGeometry) -> bool:
    return all(
        point_in_polygon(point, geometry.coverage, scenario.requirements.coverage_margin)
        for footprint in scenario.footprints
        for point in rotated_rectangle(footprint)
    )


def _stakes_fit(scenario: Scenario, geometry: PitchGeometry) -> bool:
    return all(
        any(point_in_polygon(stake.point, zone.polygon) for zone in scenario.stake_zones)
        for stake in geometry.stakes
    )


def _keepouts_clear(scenario: Scenario, geometry: PitchGeometry) -> bool:
    for keepout in scenario.keepouts:
        if circle_intersects_polygon(keepout, geometry.coverage):
            return False
        if any(
            stake.point.distance_to(keepout.center) <= keepout.radius + 1e-9
            for stake in geometry.stakes
        ):
            return False
        if any(
            line.id.startswith("guy-") and segment_intersects_circle(line.start, line.end, keepout)
            for line in geometry.lines
        ):
            return False
    return True


def _wind_penalty(scenario: Scenario, geometry: PitchGeometry) -> float:
    wind = scenario.requirements.wind_from_deg
    if wind is None:
        return 0.0
    radians = math.radians(wind)
    source_direction = Point(math.sin(radians), math.cos(radians))
    if geometry.pitch_type == "a_frame":
        return round(
            abs(geometry.axis.x * source_direction.y - geometry.axis.y * source_direction.x), 9
        )
    low_side = geometry.low_side
    assert low_side is not None
    alignment = low_side.x * source_direction.x + low_side.y * source_direction.y
    return round(1 - alignment, 9)


def solve(scenario: Scenario, *, limit: int = 5) -> SolveResult:
    generated = enumerate_geometries(scenario)
    rejections: Counter[str] = Counter(generated.rejections)
    candidates: list[CandidateSolution] = []
    for geometry in generated.geometries:
        if not _footprints_fit(scenario, geometry):
            rejections["footprint_not_covered"] += 1
            continue
        if not _stakes_fit(scenario, geometry):
            rejections["stake_outside_zone"] += 1
            continue
        if not _keepouts_clear(scenario, geometry):
            rejections["keepout_conflict"] += 1
            continue
        needs = tuple(CordNeed(line.id, line.required_length) for line in geometry.lines)
        cord_uses: tuple[CordUse, ...] = ()
        if scenario.cords:
            assignment = assign_cords(needs, scenario.cords)
            if assignment is None:
                rejections["cord_shortage"] += 1
                continue
            cord_uses = assignment
        slack = round(sum(use.spare_length for use in cord_uses), 9)
        score = (
            _wind_penalty(scenario, geometry),
            slack,
            round(abs(geometry.ridge_height - scenario.requirements.preferred_ridge_height), 9),
            geometry.id,
        )
        candidates.append(CandidateSolution(geometry, cord_uses, score))
    candidates.sort(key=lambda candidate: candidate.score)
    visible = tuple(candidates[:limit])
    relevant_hints = {
        reason: REPAIR_HINTS[reason] for reason in sorted(rejections) if reason in REPAIR_HINTS
    }
    return SolveResult(
        "found" if visible else "no_solution",
        len(generated.geometries),
        generated.search_states,
        generated.search_limited,
        dict(sorted(rejections.items())),
        relevant_hints,
        visible,
    )
