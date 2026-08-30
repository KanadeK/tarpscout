"""Command-line interface for validating and solving measured tarp sites."""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence
from pathlib import Path

from tarpscout import __version__
from tarpscout.models import InputError, load_scenario
from tarpscout.render import write_artifacts
from tarpscout.solver import solve


def _positive_integer(value: str) -> int:
    parsed = int(value)
    if parsed <= 0:
        raise argparse.ArgumentTypeError("expected a positive integer")
    return parsed


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="tarpscout",
        description="Find A-frame and lean-to tarp pitches from measured site constraints.",
    )
    parser.add_argument("--version", action="version", version=f"tarpscout {__version__}")
    commands = parser.add_subparsers(dest="command", required=True)
    validate = commands.add_parser("validate", help="validate a survey without solving it")
    validate.add_argument("survey", type=Path)
    solve_command = commands.add_parser("solve", help="solve a survey and write artifacts")
    solve_command.add_argument("survey", type=Path)
    solve_command.add_argument("--output", type=Path, default=Path("tarpscout-output"))
    solve_command.add_argument("--limit", type=_positive_integer, default=5)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        scenario = load_scenario(args.survey)
        if args.command == "validate":
            print(f"valid: {scenario.name}")
            return 0
        result = solve(scenario, limit=args.limit)
        paths = write_artifacts(args.output, scenario, result)
    except (InputError, OSError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 2
    for path in paths:
        print(path)
    return 0 if result.status == "found" else 1
