"""Typed input model and strict JSON-boundary validation."""

from __future__ import annotations

import json
import math
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, cast


class InputError(ValueError):
    """A scenario failed validation at the external input boundary."""


@dataclass(frozen=True, slots=True)
class Point:
    x: float
    y: float

    def distance_to(self, other: Point) -> float:
        return math.hypot(other.x - self.x, other.y - self.y)


@dataclass(frozen=True, slots=True)
class Tarp:
    length: float
    width: float


@dataclass(frozen=True, slots=True)
class Support:
    id: str
    point: Point
    min_height: float
    max_height: float
    wrap_allowance: float


@dataclass(frozen=True, slots=True)
class StakeZone:
    id: str
    polygon: tuple[Point, ...]


@dataclass(frozen=True, slots=True)
class CircleKeepout:
    id: str
    center: Point
    radius: float


@dataclass(frozen=True, slots=True)
class Footprint:
    id: str
    center: Point
    length: float
    width: float
    angle_deg: float


@dataclass(frozen=True, slots=True)
class Cord:
    id: str
    length: float


@dataclass(frozen=True, slots=True)
class NumberRange:
    minimum: float
    maximum: float


@dataclass(frozen=True, slots=True)
class Requirements:
    pitch_types: tuple[str, ...]
    ridge_height: NumberRange
    preferred_ridge_height: float
    edge_height: float
    slope_angle: NumberRange
    stake_setback: float
    knot_allowance: float
    coverage_margin: float
    search_step: float
    end_clearance: float
    max_search_states: int
    wind_from_deg: float | None


@dataclass(frozen=True, slots=True)
class Scenario:
    name: str
    tarp: Tarp
    supports: tuple[Support, ...]
    stake_zones: tuple[StakeZone, ...]
    keepouts: tuple[CircleKeepout, ...]
    footprints: tuple[Footprint, ...]
    cords: tuple[Cord, ...]
    requirements: Requirements


def load_scenario(path: Path) -> Scenario:
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise InputError(f"{path}: {error}") from error
    return parse_scenario(raw)


def _object(value: object, path: str) -> dict[str, object]:
    if not isinstance(value, dict) or not all(isinstance(key, str) for key in value):
        raise InputError(f"{path}: expected object")
    return cast(dict[str, object], value)


def _array(value: object, path: str) -> list[object]:
    if not isinstance(value, list):
        raise InputError(f"{path}: expected array")
    return cast(list[object], value)


def _fields(
    value: object,
    path: str,
    *,
    required: set[str],
    optional: set[str] | None = None,
) -> dict[str, object]:
    result = _object(value, path)
    unknown = sorted(set(result) - required - (optional or set()))
    if unknown:
        field = unknown[0]
        raise InputError(f"{path}.{field}: unknown field")
    missing = sorted(required - set(result))
    if missing:
        raise InputError(f"{path}.{missing[0]}: required field")
    return result


def _text(value: object, path: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise InputError(f"{path}: expected non-empty string")
    if not value.isprintable():
        raise InputError(f"{path}: expected printable text")
    return value


def _number(value: object, path: str) -> float:
    if isinstance(value, bool) or not isinstance(value, int | float):
        raise InputError(f"{path}: expected number")
    result = float(value)
    if not math.isfinite(result):
        raise InputError(f"{path}: expected finite number")
    return result


def _positive(value: object, path: str, *, allow_zero: bool = False) -> float:
    result = _number(value, path)
    if result < 0 if allow_zero else result <= 0:
        comparator = "non-negative" if allow_zero else "positive"
        raise InputError(f"{path}: expected {comparator} number")
    return result


def _integer(value: object, path: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise InputError(f"{path}: expected integer")
    return value


def _point(value: object, path: str) -> Point:
    values = _array(value, path)
    if len(values) != 2:
        raise InputError(f"{path}: expected [x, y]")
    return Point(_number(values[0], f"{path}[0]"), _number(values[1], f"{path}[1]"))


def _polygon_area(points: tuple[Point, ...]) -> float:
    return abs(
        sum(
            point.x * points[(index + 1) % len(points)].y
            - points[(index + 1) % len(points)].x * point.y
            for index, point in enumerate(points)
        )
        / 2
    )


def _cross(first: Point, second: Point, third: Point) -> float:
    return (second.x - first.x) * (third.y - first.y) - (second.y - first.y) * (third.x - first.x)


def _on_segment(point: Point, start: Point, end: Point) -> bool:
    return (
        abs(_cross(start, end, point)) <= 1e-9
        and min(start.x, end.x) - 1e-9 <= point.x <= max(start.x, end.x) + 1e-9
        and min(start.y, end.y) - 1e-9 <= point.y <= max(start.y, end.y) + 1e-9
    )


def _segments_intersect(first: Point, second: Point, third: Point, fourth: Point) -> bool:
    first_side = _cross(first, second, third)
    second_side = _cross(first, second, fourth)
    third_side = _cross(third, fourth, first)
    fourth_side = _cross(third, fourth, second)
    if (
        (first_side > 1e-9 and second_side < -1e-9) or (first_side < -1e-9 and second_side > 1e-9)
    ) and (
        (third_side > 1e-9 and fourth_side < -1e-9) or (third_side < -1e-9 and fourth_side > 1e-9)
    ):
        return True
    return (
        _on_segment(third, first, second)
        or _on_segment(fourth, first, second)
        or _on_segment(first, third, fourth)
        or _on_segment(second, third, fourth)
    )


def _polygon_is_simple(points: tuple[Point, ...]) -> bool:
    edge_count = len(points)
    for first_index, first in enumerate(points):
        second = points[(first_index + 1) % edge_count]
        for third_index in range(first_index + 1, edge_count):
            third = points[third_index]
            fourth = points[(third_index + 1) % edge_count]
            adjacent = third_index == first_index + 1 or (
                first_index == 0 and third_index == edge_count - 1
            )
            if not adjacent:
                if _segments_intersect(first, second, third, fourth):
                    return False
                continue
            shared = second if second in (third, fourth) else first
            first_other = first if first != shared else second
            second_other = third if third != shared else fourth
            if _on_segment(first_other, shared, second_other) or _on_segment(
                second_other, shared, first_other
            ):
                return False
    return True


def _unique(items: list[tuple[str, str]]) -> None:
    seen: set[str] = set()
    for identifier, path in items:
        if identifier in seen:
            raise InputError(f"{path}: duplicate '{identifier}'")
        seen.add(identifier)


def _parse_range(value: object, path: str, *, preferred: bool) -> tuple[NumberRange, float | None]:
    required = {"min", "max", "preferred"} if preferred else {"min", "max"}
    raw = _fields(value, path, required=required)
    minimum = _number(raw["min"], f"{path}.min")
    maximum = _number(raw["max"], f"{path}.max")
    if minimum > maximum:
        raise InputError(f"{path}: min must be <= max")
    preferred_value = _number(raw["preferred"], f"{path}.preferred") if preferred else None
    if preferred_value is not None and not minimum <= preferred_value <= maximum:
        raise InputError(f"{path}.preferred: must be inside min/max")
    return NumberRange(minimum, maximum), preferred_value


def parse_scenario(value: Any) -> Scenario:
    root = _fields(
        value,
        "scenario",
        required={"name", "tarp", "supports", "stake_zones", "footprints", "requirements"},
        optional={"keepouts", "cords"},
    )
    name = _text(root["name"], "name")
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{0,63}", name):
        raise InputError("name: use 1-64 ASCII letters, digits, underscore, or hyphen")

    tarp_raw = _fields(root["tarp"], "tarp", required={"length", "width"})
    tarp = Tarp(
        _positive(tarp_raw["length"], "tarp.length"), _positive(tarp_raw["width"], "tarp.width")
    )

    supports: list[Support] = []
    for index, item in enumerate(_array(root["supports"], "supports")):
        path = f"supports[{index}]"
        raw = _fields(
            item,
            path,
            required={"id", "x", "y", "min_height", "max_height"},
            optional={"wrap_allowance"},
        )
        minimum = _positive(raw["min_height"], f"{path}.min_height", allow_zero=True)
        maximum = _positive(raw["max_height"], f"{path}.max_height")
        if minimum > maximum:
            raise InputError(f"{path}: min_height must be <= max_height")
        supports.append(
            Support(
                _text(raw["id"], f"{path}.id"),
                Point(_number(raw["x"], f"{path}.x"), _number(raw["y"], f"{path}.y")),
                minimum,
                maximum,
                _positive(
                    raw.get("wrap_allowance", 0.0), f"{path}.wrap_allowance", allow_zero=True
                ),
            )
        )
    if len(supports) < 2:
        raise InputError("supports: expected at least two supports")
    _unique([(item.id, f"supports[{index}].id") for index, item in enumerate(supports)])
    if len({(item.point.x, item.point.y) for item in supports}) != len(supports):
        raise InputError("supports: coordinates must be unique")

    stake_zones: list[StakeZone] = []
    for index, item in enumerate(_array(root["stake_zones"], "stake_zones")):
        path = f"stake_zones[{index}]"
        raw = _fields(item, path, required={"id", "polygon"})
        points = tuple(
            _point(point, f"{path}.polygon[{point_index}]")
            for point_index, point in enumerate(_array(raw["polygon"], f"{path}.polygon"))
        )
        if len(points) < 3:
            raise InputError(f"{path}.polygon: expected at least three points")
        if len(set(points)) != len(points):
            raise InputError(f"{path}.polygon: points must be unique")
        if _polygon_area(points) <= 1e-9:
            raise InputError(f"{path}.polygon: area must be non-zero")
        if not _polygon_is_simple(points):
            raise InputError(f"{path}.polygon: must be simple")
        stake_zones.append(StakeZone(_text(raw["id"], f"{path}.id"), points))
    if not stake_zones:
        raise InputError("stake_zones: expected at least one polygon")
    _unique([(item.id, f"stake_zones[{index}].id") for index, item in enumerate(stake_zones)])

    keepouts: list[CircleKeepout] = []
    for index, item in enumerate(_array(root.get("keepouts", []), "keepouts")):
        path = f"keepouts[{index}]"
        raw = _fields(item, path, required={"id", "center", "radius"})
        keepouts.append(
            CircleKeepout(
                _text(raw["id"], f"{path}.id"),
                _point(raw["center"], f"{path}.center"),
                _positive(raw["radius"], f"{path}.radius"),
            )
        )
    _unique([(item.id, f"keepouts[{index}].id") for index, item in enumerate(keepouts)])

    footprints: list[Footprint] = []
    for index, item in enumerate(_array(root["footprints"], "footprints")):
        path = f"footprints[{index}]"
        raw = _fields(item, path, required={"id", "center", "length", "width", "angle_deg"})
        footprints.append(
            Footprint(
                _text(raw["id"], f"{path}.id"),
                _point(raw["center"], f"{path}.center"),
                _positive(raw["length"], f"{path}.length"),
                _positive(raw["width"], f"{path}.width"),
                _number(raw["angle_deg"], f"{path}.angle_deg"),
            )
        )
    if not footprints:
        raise InputError("footprints: expected at least one rectangle")
    _unique([(item.id, f"footprints[{index}].id") for index, item in enumerate(footprints)])

    cords: list[Cord] = []
    for index, item in enumerate(_array(root.get("cords", []), "cords")):
        path = f"cords[{index}]"
        raw = _fields(item, path, required={"id", "length"})
        cords.append(
            Cord(_text(raw["id"], f"{path}.id"), _positive(raw["length"], f"{path}.length"))
        )
    _unique([(item.id, f"cords[{index}].id") for index, item in enumerate(cords)])

    raw = _fields(
        root["requirements"],
        "requirements",
        required={
            "pitch_types",
            "ridge_height",
            "edge_height",
            "slope_angle",
            "stake_setback",
            "knot_allowance",
            "coverage_margin",
            "search_step",
            "end_clearance",
            "max_search_states",
        },
        optional={"wind_from_deg"},
    )
    pitch_types = tuple(
        _text(item, f"requirements.pitch_types[{index}]")
        for index, item in enumerate(_array(raw["pitch_types"], "requirements.pitch_types"))
    )
    if not pitch_types or len(set(pitch_types)) != len(pitch_types):
        raise InputError("requirements.pitch_types: expected unique values")
    unsupported = sorted(set(pitch_types) - {"a_frame", "lean_to"})
    if unsupported:
        raise InputError(f"requirements.pitch_types: unsupported '{unsupported[0]}'")
    ridge_height, preferred = _parse_range(
        raw["ridge_height"], "requirements.ridge_height", preferred=True
    )
    slope_angle, _ = _parse_range(raw["slope_angle"], "requirements.slope_angle", preferred=False)
    if not (0 < slope_angle.minimum <= slope_angle.maximum < 90):
        raise InputError("requirements.slope_angle: expected 0 < min <= max < 90")
    edge_height = _positive(raw["edge_height"], "requirements.edge_height", allow_zero=True)
    if edge_height >= ridge_height.minimum:
        raise InputError("requirements.edge_height: must be below minimum ridge height")
    search_step = _positive(raw["search_step"], "requirements.search_step")
    if search_step < 1e-9:
        raise InputError("requirements.search_step: expected >= 0.000000001")
    max_search_states = _integer(raw["max_search_states"], "requirements.max_search_states")
    if not 1 <= max_search_states <= 1_000_000:
        raise InputError("requirements.max_search_states: expected 1..1000000")
    wind = None
    if "wind_from_deg" in raw:
        wind = _number(raw["wind_from_deg"], "requirements.wind_from_deg")
        if not 0 <= wind < 360:
            raise InputError("requirements.wind_from_deg: expected 0 <= value < 360")

    requirements = Requirements(
        pitch_types,
        ridge_height,
        cast(float, preferred),
        edge_height,
        slope_angle,
        _positive(raw["stake_setback"], "requirements.stake_setback"),
        _positive(raw["knot_allowance"], "requirements.knot_allowance", allow_zero=True),
        _positive(raw["coverage_margin"], "requirements.coverage_margin", allow_zero=True),
        search_step,
        _positive(raw["end_clearance"], "requirements.end_clearance", allow_zero=True),
        max_search_states,
        wind,
    )
    return Scenario(
        name,
        tarp,
        tuple(supports),
        tuple(stake_zones),
        tuple(keepouts),
        tuple(footprints),
        tuple(cords),
        requirements,
    )
