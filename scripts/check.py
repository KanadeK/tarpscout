"""Run the complete local TarpScout release gate."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VERSION = "0.1.0"


def _run(arguments: list[str]) -> subprocess.CompletedProcess[str]:
    print(f"+ {subprocess.list2cmdline(arguments)}", flush=True)
    completed = subprocess.run(
        arguments,
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    if completed.stdout:
        print(completed.stdout, end="")
    if completed.stderr:
        print(completed.stderr, end="", file=sys.stderr)
    completed.check_returncode()
    return completed


def _snapshot(directory: Path) -> dict[str, bytes]:
    return {
        path.relative_to(directory).as_posix(): path.read_bytes()
        for path in sorted(directory.rglob("*"))
        if path.is_file()
    }


def _write_demo_bundle(source: Path, target: Path) -> None:
    with zipfile.ZipFile(target, "w") as archive:
        for path in sorted(source.rglob("*")):
            if not path.is_file():
                continue
            info = zipfile.ZipInfo(path.relative_to(source).as_posix())
            info.date_time = (1980, 1, 1, 0, 0, 0)
            info.external_attr = 0o644 << 16
            archive.writestr(info, path.read_bytes())


def main() -> None:
    with tempfile.TemporaryDirectory(prefix="tarpscout-check-") as temporary:
        temp = Path(temporary)
        _run(["uv", "lock", "--check"])
        _run(["uv", "run", "ruff", "format", "--check", "src", "tests", "scripts"])
        _run(["uv", "run", "ruff", "check", "src", "tests", "scripts"])
        _run(["uv", "run", "mypy", "src", "tests", "scripts"])
        _run(
            [
                "uv",
                "run",
                "pytest",
                "--cov=tarpscout",
                "--cov-branch",
                "--cov-fail-under=90",
                "--cov-report=term-missing",
                "--basetemp",
                str(temp / "pytest"),
            ]
        )

        first_demo = temp / "demo-first"
        second_demo = temp / "demo-second"
        _run([sys.executable, "-m", "tarpscout", "demo", str(first_demo)])
        _run([sys.executable, "-m", "tarpscout", "demo", str(second_demo)])
        if _snapshot(first_demo) != _snapshot(second_demo):
            raise RuntimeError("demo output is not byte-stable")

        dist = ROOT / "dist"
        if dist.exists():
            shutil.rmtree(dist)
        _run(["uv", "build"])
        wheels = sorted(dist.glob(f"tarpscout-{VERSION}-*.whl"))
        source_archives = sorted(dist.glob(f"tarpscout-{VERSION}.tar.gz"))
        if len(wheels) != 1 or len(source_archives) != 1:
            raise RuntimeError("build did not produce exactly one wheel and one source archive")
        _write_demo_bundle(first_demo, dist / f"tarpscout-{VERSION}-demo.zip")

        installed = temp / "installed"
        _run(["uv", "venv", "--python", sys.executable, str(installed)])
        installed_python = installed / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
        console = installed / ("Scripts/tarpscout.exe" if os.name == "nt" else "bin/tarpscout")
        _run(["uv", "pip", "install", "--python", str(installed_python), str(wheels[0])])
        version = _run([str(console), "--version"])
        if version.stdout.strip() != f"tarpscout {VERSION}":
            raise RuntimeError("installed console reported the wrong version")
        installed_output = temp / "installed-solve"
        _run(
            [
                str(console),
                "solve",
                str(ROOT / "examples/pine-gap.site.json"),
                "--output",
                str(installed_output),
            ]
        )
        expected = {
            "pine-gap.report.json",
            "pine-gap.lines.csv",
            "pine-gap.plan.svg",
            "pine-gap.elevation.svg",
            "pine-gap.report.html",
        }
        if {path.name for path in installed_output.iterdir()} != expected:
            raise RuntimeError("installed console did not produce the expected artifact set")
        _run([str(console), "demo", str(temp / "installed-demo")])

    print("TarpScout release gate passed.")


if __name__ == "__main__":
    main()
