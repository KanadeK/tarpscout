"""Finite generation of A-frame and lean-to tarp geometry."""

from __future__ import annotations

import math
from collections import Counter
from dataclasses import dataclass
from itertools import combinations

from tarpscout.models import Point, Scenario, Support


@dataclass(frozen=True, slots=True)
class LineGeometry:
    id: str
    start: Point
    start_height: float
    end: Point
    end_height: float
    required_length: float


@dataclass(frozen=True, slots=True)
class StakeGeometry:
    id: str
    point: Point


@dataclass(frozen=True, slots=True)
class PitchGeometry:
    id: str
    pitch_type: str
    support_ids: tuple[str, str]
    center: Point
    axis: Point
    low_side: Point | None
    center_offset: float
    ridge_height: float
    edge_height: float
    slope_angle_deg: float
    coverage: tuple[Point, ...]
    stakes: tuple[StakeGeometry, ...]
    lines: tuple[LineGeometry, ...]


@dataclass(frozen=True, slots=True)
class GenerationResult:
    geometries: tuple[PitchGeometry, ...]
    rejections: dict[str, int]
    search_states: int
    search_limited: bool


def _point(origin: Point, axis: Point, distance: float) -> Point:
    return Point(origin.x + axis.x * distance, origin.y + axis.y * distance)


def _grid(start: float, stop: float, step: float) -> tuple[float, ...]:
    if start > stop + 1e-9:
        return ()
    count = math.floor((stop - start) / step + 1e-9)
    values = [round(start + index * step, 9) for index in range(count + 1)]
    if stop - values[-1] > 1e-9:
        values.append(round(stop, 9))
    return tuple(values)


def _ridge_line(first: Support, second: Support, height: float, scenario: Scenario) -> LineGeometry:
    length = (
        first.point.distance_to(second.point)
        + first.wrap_allowance
        + second.wrap_allowance
        + scenario.requirements.knot_allowance
    )
    return LineGeometry("ridge", first.point, height, second.point, height, round(length, 9))


def _guy_line(identifier: str, corner: Point, stake: Point, scenario: Scenario) -> LineGeometry:
    length = math.hypot(scenario.requirements.stake_setback, scenario.requirements.edge_height)
    length += scenario.requirements.knot_allowance
    return LineGeometry(
        identifier, corner, scenario.requirements.edge_height, stake, 0.0, round(length, 9)
    )


def enumerate_geometries(scenario: Scenario) -> GenerationResult:
    geometries: list[PitchGeometry] = []
    rejections: Counter[str] = Counter()
    states = 0
    limit = scenario.requirements.max_search_states

    for first, second in combinations(scenario.supports, 2):
        span = first.point.distance_to(second.point)
        required_span = scenario.tarp.length + 2 * scenario.requirements.end_clearance
        if span + 1e-9 < required_span:
            rejections["support_span_too_short"] += len(scenario.requirements.pitch_types)
            continue
        axis = Point(
            (second.point.x - first.point.x) / span, (second.point.y - first.point.y) / span
        )
        normal = Point(-axis.y, axis.x)
        offset_start = scenario.tarp.length / 2 + scenario.requirements.end_clearance
        offset_stop = span - scenario.tarp.length / 2 - scenario.requirements.end_clearance
        low_height = max(
            first.min_height, second.min_height, scenario.requirements.ridge_height.minimum
        )
        high_height = min(
            first.max_height, second.max_height, scenario.requirements.ridge_height.maximum
        )
        heights = _grid(low_height, high_height, scenario.requirements.search_step)
        if not heights:
            rejections["ridge_height_unavailable"] += len(scenario.requirements.pitch_types)
            continue

        for offset in _grid(offset_start, offset_stop, scenario.requirements.search_step):
            center = _point(first.point, axis, offset)
            ridge_start = _point(center, axis, -scenario.tarp.length / 2)
            ridge_end = _point(center, axis, scenario.tarp.length / 2)
            for height in heights:
                for pitch_type in scenario.requirements.pitch_types:
                    orientations = (0,) if pitch_type == "a_frame" else (-1, 1)
                    for orientation in orientations:
                        if states >= limit:
                            rejections["search_limit"] += 1
                            return GenerationResult(
                                tuple(geometries), dict(rejections), states, True
                            )
                        states += 1
                        rise = height - scenario.requirements.edge_height
                        slope_length = (
                            scenario.tarp.width / 2
                            if pitch_type == "a_frame"
                            else scenario.tarp.width
                        )
                        if rise >= slope_length:
                            rejections["slope_out_of_range"] += 1
                            continue
                        slope = math.degrees(math.asin(rise / slope_length))
                        if not (
                            scenario.requirements.slope_angle.minimum - 1e-9
                            <= slope
                            <= scenario.requirements.slope_angle.maximum + 1e-9
                        ):
                            rejections["slope_out_of_range"] += 1
                            continue
                        run = math.sqrt(slope_length * slope_length - rise * rise)
                        ridge = _ridge_line(first, second, height, scenario)
                        stakes: tuple[StakeGeometry, ...]
                        lines: tuple[LineGeometry, ...]
                        if pitch_type == "a_frame":
                            left_start = _point(ridge_start, normal, run)
                            left_end = _point(ridge_end, normal, run)
                            right_start = _point(ridge_start, normal, -run)
                            right_end = _point(ridge_end, normal, -run)
                            stake_left_start = _point(
                                left_start, normal, scenario.requirements.stake_setback
                            )
                            stake_left_end = _point(
                                left_end, normal, scenario.requirements.stake_setback
                            )
                            stake_right_start = _point(
                                right_start, normal, -scenario.requirements.stake_setback
                            )
                            stake_right_end = _point(
                                right_end, normal, -scenario.requirements.stake_setback
                            )
                            coverage = (right_start, right_end, left_end, left_start)
                            stakes = (
                                StakeGeometry("left-start", stake_left_start),
                                StakeGeometry("left-end", stake_left_end),
                                StakeGeometry("right-start", stake_right_start),
                                StakeGeometry("right-end", stake_right_end),
                            )
                            lines = (
                                ridge,
                                _guy_line("guy-left-start", left_start, stake_left_start, scenario),
                                _guy_line("guy-left-end", left_end, stake_left_end, scenario),
                                _guy_line(
                                    "guy-right-start", right_start, stake_right_start, scenario
                                ),
                                _guy_line("guy-right-end", right_end, stake_right_end, scenario),
                            )
                            low_side = None
                        else:
                            low_side = Point(normal.x * orientation, normal.y * orientation)
                            low_start = _point(ridge_start, low_side, run)
                            low_end = _point(ridge_end, low_side, run)
                            stake_start = _point(
                                low_start, low_side, scenario.requirements.stake_setback
                            )
                            stake_end = _point(
                                low_end, low_side, scenario.requirements.stake_setback
                            )
                            coverage = (ridge_start, ridge_end, low_end, low_start)
                            stakes = (
                                StakeGeometry("low-start", stake_start),
                                StakeGeometry("low-end", stake_end),
                            )
                            lines = (
                                ridge,
                                _guy_line("guy-low-start", low_start, stake_start, scenario),
                                _guy_line("guy-low-end", low_end, stake_end, scenario),
                            )
                        identifier = (
                            f"{first.id}--{second.id}--{pitch_type}--"
                            f"o{offset:.3f}--h{height:.3f}--s{orientation:+d}"
                        )
                        geometries.append(
                            PitchGeometry(
                                identifier,
                                pitch_type,
                                (first.id, second.id),
                                center,
                                axis,
                                low_side,
                                offset,
                                height,
                                scenario.requirements.edge_height,
                                slope,
                                coverage,
                                stakes,
                                lines,
                            )
                        )
    return GenerationResult(tuple(geometries), dict(rejections), states, False)
