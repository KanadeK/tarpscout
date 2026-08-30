"""Canonical built-in surveys used by the installed demo command."""

from __future__ import annotations

from typing import Any


def _base_document(
    name: str, pitch_types: list[str], footprint_center: list[float]
) -> dict[str, Any]:
    return {
        "name": name,
        "tarp": {"length": 3.0, "width": 3.0},
        "supports": [
            {
                "id": "west-pine",
                "x": 0.0,
                "y": 0.0,
                "min_height": 1.2,
                "max_height": 2.0,
                "wrap_allowance": 0.4,
            },
            {
                "id": "east-pine",
                "x": 5.0,
                "y": 0.0,
                "min_height": 1.2,
                "max_height": 2.0,
                "wrap_allowance": 0.4,
            },
        ],
        "stake_zones": [
            {
                "id": "soft-ground",
                "polygon": [[-1.0, -4.0], [6.0, -4.0], [6.0, 4.0], [-1.0, 4.0]],
            }
        ],
        "keepouts": [],
        "footprints": [
            {
                "id": "sleeping-pad",
                "center": footprint_center,
                "length": 2.0,
                "width": 1.0,
                "angle_deg": 0.0,
            }
        ],
        "cords": [
            {"id": "ridge-6.2", "length": 6.2},
            {"id": "guy-nw", "length": 1.5},
            {"id": "guy-ne", "length": 1.5},
            {"id": "guy-sw", "length": 1.5},
            {"id": "guy-se", "length": 1.5},
        ],
        "requirements": {
            "pitch_types": pitch_types,
            "ridge_height": {"min": 1.4, "max": 1.6, "preferred": 1.5},
            "edge_height": 0.2,
            "slope_angle": {"min": 20.0, "max": 70.0},
            "stake_setback": 0.8,
            "knot_allowance": 0.2,
            "coverage_margin": 0.05,
            "search_step": 0.5,
            "end_clearance": 0.2,
            "max_search_states": 1000,
            "wind_from_deg": 270.0,
        },
    }


def demo_documents() -> tuple[dict[str, Any], ...]:
    """Return fresh feasible and blocking surveys in display order."""
    pine_gap = _base_document("pine-gap", ["a_frame", "lean_to"], [2.5, 0.0])
    creek_lean_to = _base_document("creek-lean-to", ["lean_to"], [2.5, 1.0])
    fire_ring = _base_document("fire-ring", ["a_frame", "lean_to"], [2.5, 0.0])
    fire_ring["keepouts"] = [{"id": "fire", "center": [2.5, 0.0], "radius": 0.6}]
    short_cords = _base_document("short-cords", ["a_frame", "lean_to"], [2.5, 0.0])
    short_cords["cords"] = [{"id": f"short-{index}", "length": 0.5} for index in range(5)]
    return pine_gap, creek_lean_to, fire_ring, short_cords
