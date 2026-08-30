from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from conftest import survey_dict


def run_cli(*arguments: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "tarpscout", *arguments],
        check=False,
        capture_output=True,
        text=True,
    )


def write_survey(path: Path, raw: object) -> None:
    path.write_text(json.dumps(raw), encoding="utf-8")


def test_version_and_validate_commands(tmp_path: Path) -> None:
    survey = tmp_path / "site.json"
    write_survey(survey, survey_dict())

    version = run_cli("--version")
    validated = run_cli("validate", str(survey))

    assert version.returncode == 0
    assert version.stdout.strip() == "tarpscout 0.1.0"
    assert validated.returncode == 0
    assert validated.stdout.strip() == "valid: pine-gap"


def test_feasible_solve_writes_complete_artifact_set(tmp_path: Path) -> None:
    survey = tmp_path / "site.json"
    output = tmp_path / "plan"
    write_survey(survey, survey_dict())

    completed = run_cli("solve", str(survey), "--output", str(output), "--limit", "3")

    assert completed.returncode == 0, completed.stderr
    assert {path.name for path in output.iterdir()} == {
        "pine-gap.report.json",
        "pine-gap.lines.csv",
        "pine-gap.plan.svg",
        "pine-gap.elevation.svg",
        "pine-gap.report.html",
    }
    report = json.loads((output / "pine-gap.report.json").read_text(encoding="utf-8"))
    assert report["result"]["status"] == "found"
    assert report["result"]["candidates"][0]["pitch_type"] == "a_frame"
    assert "planning evidence" in report["limitations"][0]
    html = (output / "pine-gap.report.html").read_text(encoding="utf-8")
    assert html.count("<svg") == 2
    assert 'src="pine-gap.plan.svg"' not in html
    assert "<script" not in html
    plan = (output / "pine-gap.plan.svg").read_text(encoding="utf-8")
    assert "west-pine" in plan
    assert "left-start" in plan
    elevation = (output / "pine-gap.elevation.svg").read_text(encoding="utf-8")
    assert "stake setback 0.80 m" in elevation


def test_no_solution_writes_only_diagnostic_json_and_exits_one(tmp_path: Path) -> None:
    raw = survey_dict()
    raw["cords"] = [{"id": f"short-{index}", "length": 0.5} for index in range(5)]
    survey = tmp_path / "site.json"
    output = tmp_path / "blocked"
    write_survey(survey, raw)

    completed = run_cli("solve", str(survey), "--output", str(output))

    assert completed.returncode == 1
    assert [path.name for path in output.iterdir()] == ["pine-gap.report.json"]
    report = json.loads((output / "pine-gap.report.json").read_text(encoding="utf-8"))
    assert report["result"]["status"] == "no_solution"
    assert report["result"]["rejections"]["cord_shortage"] > 0


def test_invalid_input_exits_two_without_partial_output(tmp_path: Path) -> None:
    raw = survey_dict()
    raw["tarp"]["width"] = -1
    survey = tmp_path / "invalid.json"
    output = tmp_path / "must-not-exist"
    write_survey(survey, raw)

    completed = run_cli("solve", str(survey), "--output", str(output))

    assert completed.returncode == 2
    assert "tarp.width" in completed.stderr
    assert not output.exists()


def test_same_solve_is_byte_stable(tmp_path: Path) -> None:
    survey = tmp_path / "site.json"
    first = tmp_path / "first"
    second = tmp_path / "second"
    write_survey(survey, survey_dict())

    assert run_cli("solve", str(survey), "--output", str(first)).returncode == 0
    assert run_cli("solve", str(survey), "--output", str(second)).returncode == 0

    for first_path in sorted(first.iterdir()):
        assert first_path.read_bytes() == (second / first_path.name).read_bytes()


def test_no_solution_removes_stale_artifacts_for_same_scenario(tmp_path: Path) -> None:
    survey = tmp_path / "site.json"
    output = tmp_path / "reused"
    write_survey(survey, survey_dict())
    assert run_cli("solve", str(survey), "--output", str(output)).returncode == 0

    blocked = survey_dict()
    blocked["cords"] = [{"id": f"short-{index}", "length": 0.5} for index in range(5)]
    write_survey(survey, blocked)

    assert run_cli("solve", str(survey), "--output", str(output)).returncode == 1
    assert [path.name for path in output.iterdir()] == ["pine-gap.report.json"]


def test_demo_command_runs_feasible_and_blocking_scenarios(tmp_path: Path) -> None:
    output = tmp_path / "demo"

    completed = run_cli("demo", str(output))

    assert completed.returncode == 0, completed.stderr
    expected = {
        "pine-gap": "found",
        "creek-lean-to": "found",
        "fire-ring": "no_solution",
        "short-cords": "no_solution",
    }
    assert completed.stdout.splitlines() == [
        f"{status}: {name}" for name, status in expected.items()
    ]
    for name, status in expected.items():
        scenario_dir = output / name
        assert (scenario_dir / f"{name}.site.json").is_file()
        report = json.loads((scenario_dir / f"{name}.report.json").read_text(encoding="utf-8"))
        assert report["result"]["status"] == status
