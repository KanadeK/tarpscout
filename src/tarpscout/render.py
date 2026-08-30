"""Deterministic report artifacts for solved sites."""

from __future__ import annotations

import csv
import html
import io
import json
from dataclasses import asdict
from pathlib import Path
from typing import Any

from tarpscout.geometry import rotated_rectangle
from tarpscout.models import Point, Scenario
from tarpscout.solver import CandidateSolution, SolveResult

LIMITATIONS = [
    "This output is planning evidence, not a structural, weather, soil, knot, or safety guarantee.",
    (
        "Coordinates and lengths are metres in a local level XY plane; "
        "field measurements remain authoritative."
    ),
]


def _candidate_dict(candidate: CandidateSolution) -> dict[str, Any]:
    raw = asdict(candidate)
    geometry = raw.pop("geometry")
    return {**geometry, **raw}


def report_dict(scenario: Scenario, result: SolveResult) -> dict[str, object]:
    """Build the stable public JSON report."""
    return {
        "schema_version": 1,
        "scenario": {
            "name": scenario.name,
            "tarp": asdict(scenario.tarp),
            "support_count": len(scenario.supports),
            "footprint_count": len(scenario.footprints),
            "keepout_count": len(scenario.keepouts),
            "cord_count": len(scenario.cords),
        },
        "result": {
            "status": result.status,
            "considered": result.considered,
            "search_states": result.search_states,
            "search_limited": result.search_limited,
            "rejections": result.rejections,
            "repair_hints": result.repair_hints,
            "candidates": [_candidate_dict(candidate) for candidate in result.candidates],
        },
        "limitations": LIMITATIONS,
    }


def _csv_text(result: SolveResult) -> str:
    stream = io.StringIO(newline="")
    writer = csv.writer(stream, lineterminator="\n")
    writer.writerow(
        [
            "candidate",
            "line",
            "start_x",
            "start_y",
            "start_height",
            "end_x",
            "end_y",
            "end_height",
            "required_length",
            "cord",
            "cord_length",
            "spare_length",
        ]
    )
    for candidate in result.candidates:
        uses = {use.need_id: use for use in candidate.cord_uses}
        for line in candidate.geometry.lines:
            use = uses.get(line.id)
            writer.writerow(
                [
                    candidate.geometry.id,
                    line.id,
                    line.start.x,
                    line.start.y,
                    line.start_height,
                    line.end.x,
                    line.end.y,
                    line.end_height,
                    line.required_length,
                    use.cord_id if use else "",
                    use.cord_length if use else "",
                    use.spare_length if use else "",
                ]
            )
    return stream.getvalue()


def _plan_svg(scenario: Scenario, candidate: CandidateSolution) -> str:
    geometry = candidate.geometry
    points = [support.point for support in scenario.supports]
    points.extend(point for zone in scenario.stake_zones for point in zone.polygon)
    points.extend(point for item in scenario.footprints for point in rotated_rectangle(item))
    points.extend(geometry.coverage)
    points.extend(stake.point for stake in geometry.stakes)
    for keepout in scenario.keepouts:
        points.extend(
            [
                Point(keepout.center.x - keepout.radius, keepout.center.y - keepout.radius),
                Point(keepout.center.x + keepout.radius, keepout.center.y + keepout.radius),
            ]
        )
    min_x = min(point.x for point in points)
    max_x = max(point.x for point in points)
    min_y = min(point.y for point in points)
    max_y = max(point.y for point in points)
    scale = min(720 / max(max_x - min_x, 1), 500 / max(max_y - min_y, 1))

    def xy(point: Point) -> tuple[float, float]:
        return 40 + (point.x - min_x) * scale, 560 - (point.y - min_y) * scale

    def polygon(points: tuple[Point, ...]) -> str:
        return " ".join(f"{x:.2f},{y:.2f}" for x, y in map(xy, points))

    shapes = [
        '<rect width="800" height="600" fill="#f7f3e8"/>',
        (
            f'<text x="40" y="28" font-family="sans-serif" font-size="18">'
            f"{html.escape(scenario.name)} — plan</text>"
        ),
    ]
    for zone in scenario.stake_zones:
        shapes.append(
            f'<polygon points="{polygon(zone.polygon)}" fill="#dce9cc" '
            'stroke="#668542" stroke-width="2"/>'
        )
    for keepout in scenario.keepouts:
        x, y = xy(keepout.center)
        shapes.append(
            f'<circle cx="{x:.2f}" cy="{y:.2f}" r="{keepout.radius * scale:.2f}" '
            'fill="#f2b6a0" stroke="#a64228" stroke-width="2"/>'
        )
    for footprint in scenario.footprints:
        shapes.append(
            f'<polygon points="{polygon(rotated_rectangle(footprint))}" fill="#9fc8de" '
            'stroke="#28627f" stroke-width="2"/>'
        )
    shapes.append(
        f'<polygon points="{polygon(geometry.coverage)}" fill="#e7c55c" '
        'fill-opacity=".55" stroke="#8a6710" stroke-width="3"/>'
    )
    for line in geometry.lines:
        start_x, start_y = xy(line.start)
        end_x, end_y = xy(line.end)
        shapes.append(
            f'<line x1="{start_x:.2f}" y1="{start_y:.2f}" x2="{end_x:.2f}" '
            f'y2="{end_y:.2f}" stroke="#5b4636" stroke-width="2"/>'
        )
    for support in scenario.supports:
        x, y = xy(support.point)
        shapes.append(f'<circle cx="{x:.2f}" cy="{y:.2f}" r="6" fill="#315c3b"/>')
    for stake in geometry.stakes:
        x, y = xy(stake.point)
        shapes.append(
            f'<rect x="{x - 4:.2f}" y="{y - 4:.2f}" width="8" height="8" fill="#9a2f1f"/>'
        )
    shapes.append(
        '<text x="40" y="585" font-family="sans-serif" font-size="12">'
        "green=stake zone · red=keep-out · blue=footprint · gold=tarp</text>"
    )
    return (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 600">\n'
        + "\n".join(shapes)
        + "\n</svg>\n"
    )


def _elevation_svg(scenario: Scenario, candidate: CandidateSolution) -> str:
    geometry = candidate.geometry
    floor = 500.0
    ridge = floor - geometry.ridge_height * 220
    edge = floor - geometry.edge_height * 220
    if geometry.pitch_type == "a_frame":
        roof = (
            f'<polyline points="120,{edge:.2f} 400,{ridge:.2f} 680,{edge:.2f}" '
            'fill="none" stroke="#8a6710" stroke-width="6"/>'
        )
    else:
        roof = (
            f'<line x1="150" y1="{ridge:.2f}" x2="650" y2="{edge:.2f}" '
            'stroke="#8a6710" stroke-width="6"/>'
        )
    return (
        "\n".join(
            [
                '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 600">',
                '<rect width="800" height="600" fill="#f7f3e8"/>',
                (
                    '<text x="40" y="35" font-family="sans-serif" font-size="18">'
                    f"{html.escape(scenario.name)} — elevation</text>"
                ),
                (
                    f'<line x1="60" y1="{floor}" x2="740" y2="{floor}" '
                    'stroke="#6d7452" stroke-width="3"/>'
                ),
                roof,
                (
                    '<text x="40" y="555" font-family="sans-serif" font-size="14">'
                    f"ridge {geometry.ridge_height:.2f} m · "
                    f"edge {geometry.edge_height:.2f} m · "
                    f"slope {geometry.slope_angle_deg:.1f}°</text>"
                ),
                "</svg>",
            ]
        )
        + "\n"
    )


def _html_text(report: dict[str, object], name: str, plan_svg: str, elevation_svg: str) -> str:
    payload = html.escape(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    safe_name = html.escape(name)
    return (
        "\n".join(
            [
                "<!doctype html>",
                '<html lang="en"><head><meta charset="utf-8">',
                '<meta name="viewport" content="width=device-width,initial-scale=1">',
                f"<title>{safe_name} · TarpScout</title><style>",
                "body{font:16px/1.5 system-ui;max-width:960px;margin:2rem auto;padding:0 1rem}",
                "img{max-width:100%;border:1px solid #ccc}",
                "pre{overflow:auto;background:#f5f2e9;padding:1rem}",
                "</style></head>",
                f'<body><h1>{safe_name}</h1><p><a href="{safe_name}.lines.csv">Line CSV</a></p>',
                "<h2>Plan</h2>",
                plan_svg.rstrip(),
                "<h2>Elevation</h2>",
                elevation_svg.rstrip(),
                f"<h2>Report</h2><pre>{payload}</pre></body></html>",
            ]
        )
        + "\n"
    )


def write_artifacts(output: Path, scenario: Scenario, result: SolveResult) -> tuple[Path, ...]:
    """Write diagnostics and, when solved, practical construction artifacts."""
    output.mkdir(parents=True, exist_ok=True)
    report = report_dict(scenario, result)
    report_path = output / f"{scenario.name}.report.json"
    report_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    written = [report_path]
    if result.status == "no_solution":
        for suffix in ("lines.csv", "plan.svg", "elevation.svg", "report.html"):
            stale_path = output / f"{scenario.name}.{suffix}"
            if stale_path.exists():
                stale_path.unlink()
        return tuple(written)
    candidate = result.candidates[0]
    plan_svg = _plan_svg(scenario, candidate)
    elevation_svg = _elevation_svg(scenario, candidate)
    contents = {
        f"{scenario.name}.lines.csv": _csv_text(result),
        f"{scenario.name}.plan.svg": plan_svg,
        f"{scenario.name}.elevation.svg": elevation_svg,
        f"{scenario.name}.report.html": _html_text(report, scenario.name, plan_svg, elevation_svg),
    }
    for filename, content in contents.items():
        path = output / filename
        path.write_text(content, encoding="utf-8", newline="\n")
        written.append(path)
    return tuple(written)
