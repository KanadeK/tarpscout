"""Small deterministic 2D geometry primitives."""

from __future__ import annotations

import math

from tarpscout.models import CircleKeepout, Footprint, Point


def rotated_rectangle(footprint: Footprint) -> tuple[Point, ...]:
    angle = math.radians(footprint.angle_deg)
    axis = Point(math.cos(angle), math.sin(angle))
    normal = Point(-axis.y, axis.x)
    half_length = footprint.length / 2
    half_width = footprint.width / 2
    return tuple(
        Point(
            footprint.center.x + axis.x * along + normal.x * across,
            footprint.center.y + axis.y * along + normal.y * across,
        )
        for along, across in (
            (-half_length, -half_width),
            (half_length, -half_width),
            (half_length, half_width),
            (-half_length, half_width),
        )
    )


def _point_segment_distance(point: Point, start: Point, end: Point) -> float:
    dx = end.x - start.x
    dy = end.y - start.y
    length_squared = dx * dx + dy * dy
    if length_squared == 0:
        return point.distance_to(start)
    fraction = ((point.x - start.x) * dx + (point.y - start.y) * dy) / length_squared
    fraction = min(1.0, max(0.0, fraction))
    projection = Point(start.x + fraction * dx, start.y + fraction * dy)
    return point.distance_to(projection)


def point_in_polygon(point: Point, polygon: tuple[Point, ...], margin: float = 0.0) -> bool:
    on_boundary = any(
        _point_segment_distance(point, start, polygon[(index + 1) % len(polygon)]) <= 1e-9
        for index, start in enumerate(polygon)
    )
    inside = on_boundary
    if not on_boundary:
        inside = False
        previous = polygon[-1]
        for current in polygon:
            crosses = (current.y > point.y) != (previous.y > point.y)
            if crosses:
                x_crossing = (previous.x - current.x) * (point.y - current.y) / (
                    previous.y - current.y
                ) + current.x
                if point.x < x_crossing:
                    inside = not inside
            previous = current
    if not inside:
        return False
    if margin == 0:
        return True
    return all(
        _point_segment_distance(point, start, polygon[(index + 1) % len(polygon)]) + 1e-9 >= margin
        for index, start in enumerate(polygon)
    )


def circle_intersects_polygon(circle: CircleKeepout, polygon: tuple[Point, ...]) -> bool:
    if point_in_polygon(circle.center, polygon):
        return True
    return any(
        _point_segment_distance(circle.center, start, polygon[(index + 1) % len(polygon)])
        <= circle.radius + 1e-9
        for index, start in enumerate(polygon)
    )


def segment_intersects_circle(start: Point, end: Point, circle: CircleKeepout) -> bool:
    return _point_segment_distance(circle.center, start, end) <= circle.radius + 1e-9
