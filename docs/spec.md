# Spec: TarpScout v0.1.0

## Objective

TarpScout is an offline command-line solver for a measured campsite. It turns a
site survey—supports, stakeable ground, circular keep-outs, required covered
footprints, tarp dimensions, and reusable cords—into feasible A-frame or lean-to
pitch plans.

The target user is a tarp camper who wants to answer “does this tarp fit here,
with the anchors and cord I actually have?” before improvising in bad weather.
The tool produces planning evidence and measurements; it does not certify wind,
snow, fabric, knot, tree, pole, or anchor strength.

### Assumptions

1. Site coordinates are a local, level XY plane measured in metres.
2. Supports are vertical points with user-supplied attachment-height ranges.
3. Ground anchors are recommendations inside declared stakeable polygons, not
   proof that soil or stakes are strong enough.
4. Tarp fabric is represented as an inextensible rectangle. User-provided
   allowances account for knots and practical slack.
5. v0.1.0 is a deterministic planner for A-frame and lean-to pitches only.
6. The repository is public under MIT and released as `v0.1.0` under `KanadeK`.

## User-visible commands

```text
tarpscout validate SITE.json
tarpscout solve SITE.json --output build/plan --limit 5
tarpscout demo build/demo
tarpscout --version
```

Exit codes:

- `0`: valid input, or at least one feasible plan was produced.
- `1`: valid input but no feasible plan exists under the declared constraints.
- `2`: invalid JSON, invalid schema, I/O failure, or invalid CLI usage.

`solve` writes a stable JSON report for both feasible and infeasible scenarios.
It writes CSV, plan SVG, elevation SVG, and script-free HTML only when a feasible
plan exists. Invalid input must not create a partial output directory.

## Input contract

The top-level JSON object contains:

- `name`: scenario identifier.
- `tarp`: positive `length` and `width` in metres.
- `supports`: at least two unique support points with `id`, `x`, `y`,
  `min_height`, `max_height`, and optional `wrap_allowance`.
- `stake_zones`: one or more simple polygons where recommended stakes may land.
- `keepouts`: optional circular areas forbidden to tarp coverage, stakes, and
  guylines.
- `footprints`: one or more rotated rectangles that every feasible tarp plan
  must cover with the declared margin.
- `cords`: optional reusable cord segments with unique `id` and positive
  `length`. When present, every required line must receive one whole segment.
- `requirements`: requested pitch types, ridge-height range, edge height,
  allowed roof-slope range, stake setback, knot allowance, coverage margin,
  search step, result limit, and optional prevailing wind direction.

Unknown fields fail validation so misspelled constraints cannot be silently
ignored. Detailed field semantics and an annotated example live in
`docs/input-format.md`.

## Geometry and solver contract

For every unordered support pair, TarpScout samples only the declared search
grid:

1. valid tarp positions along the support span;
2. attachment heights in the intersection of both supports and the requested
   ridge range;
3. A-frame geometry and both lean-to orientations requested by the input.

Each candidate must pass all hard constraints:

- tarp length plus end clearance fits between supports;
- roof slope is inside the requested range;
- every required footprint corner lies inside the projected tarp coverage with
  the requested margin;
- every recommended stake lies inside a stakeable polygon;
- projected tarp coverage, stakes, and guylines avoid every circular keep-out;
- reusable cords, when supplied, admit a one-to-one assignment to the required
  ridge and guy lines.

Cord assignment is an exact finite search that minimizes total unused length.
Candidate ranking is deterministic: wind alignment (when supplied), cord slack,
distance from the preferred ridge height, then stable geometric identifiers.

When no plan is feasible, the report includes the number of candidates rejected
for each reason and concrete input changes that could make that reason pass. It
must not claim that no real-world pitch exists outside the sampled model.

## Output contract

For a feasible solve, the output directory contains:

- `<name>.report.json`: input summary, search statistics, ranked candidates,
  chosen geometry, cord assignment, assumptions, and limitations.
- `<name>.lines.csv`: each ridge/guy line, endpoints, required length, assigned
  cord, and spare length.
- `<name>.plan.svg`: true-coordinate top view with supports, zones, keep-outs,
  required footprints, tarp coverage, guylines, stakes, and labels.
- `<name>.elevation.svg`: cross-section with attachment heights, roof slope,
  edge height, and stake setback.
- `<name>.report.html`: self-contained, script-free report embedding both SVGs.

Outputs must be byte-stable for the same input and version.

## Tech stack

- Python `>=3.11,<3.15`
- Python standard library at runtime
- `argparse` CLI and `dataclasses` domain model
- `pytest`, `pytest-cov`, `ruff`, `mypy`, and `build` in the locked dev group
- uv build backend, wheel plus source archive
- GitHub Actions on Ubuntu/Python 3.11 and Windows/Python 3.14

## Commands

```powershell
# Environment
uv sync --locked

# Focused test during development
uv run pytest tests/test_solver.py -q

# Full local release gate
uv run python scripts/check.py

# Individual checks
uv run ruff format --check src tests scripts
uv run ruff check src tests scripts
uv run mypy src
uv run pytest --cov=tarpscout --cov-branch --cov-report=term-missing
uv build

# Runtime acceptance
uv run tarpscout demo build/demo
uv run tarpscout solve examples/pine-gap.site.json --output build/pine-gap
```

## Project structure

```text
src/tarpscout/       Runtime package
tests/               Unit, integration, and CLI tests
examples/            Feasible and blocking site surveys
docs/                Spec, input format, architecture, troubleshooting, releases
tasks/               Implementation plan and completion checklist
scripts/check.py      One-command release gate
.github/workflows/   CI and tag-driven GitHub Release
```

## Code style

Domain values are explicit immutable dataclasses; boundary parsing converts raw
JSON once and the core operates on typed values.

```python
@dataclass(frozen=True, slots=True)
class Point:
    x: float
    y: float

    def distance_to(self, other: "Point") -> float:
        return math.hypot(other.x - self.x, other.y - self.y)
```

- Functions and variables use `snake_case`; types use `PascalCase`.
- Public functions are typed. `mypy --strict` is the authority.
- Validation occurs at JSON/CLI boundaries. Internal invariants fail fast.
- No broad exception handlers, silent defaults, or speculative abstractions.

## Testing strategy

- Unit tests cover parsing, geometry predicates, pitch dimensions, and exact
  cord assignment.
- Integration tests cover ranked solves and aggregated no-solution diagnostics.
- CLI tests run real subprocesses against checked-in fixtures and verify exit
  codes plus artifacts.
- The release gate requires at least 90% branch coverage, clean formatting,
  lint, strict typing, deterministic demo output, package build, clean wheel
  installation, and installed-console execution.
- TDD is required for behavior: each slice starts with a test that fails for the
  missing behavior before the minimum implementation is added.

## Boundaries

### Always

- Preserve deterministic output and stable reason codes.
- Treat site JSON as untrusted input and report exact field paths.
- Run the focused tests for each slice and the full gate before release.
- State model assumptions in generated reports.

### Ask first

- Add runtime dependencies.
- Expand beyond A-frame and lean-to geometry.
- Publish to a package registry other than GitHub Releases.

### Never

- Claim structural, weather, soil, tree, pole, knot, or anchor safety.
- Fetch location or weather data, require an account, or upload site data.
- Infer dimensions from photos or silently repair invalid measurements.
- Commit credentials, generated build output, or local environment files.

## Success criteria

1. Feasible A-frame and lean-to fixtures produce complete deterministic artifact
   sets with geometry and cord assignments.
2. Keep-out and short-cord fixtures return exit `1`, write diagnostic JSON, and
   identify the actual blocking constraints.
3. Invalid input returns exit `2` and leaves no partial output directory.
4. Full local release gate passes with at least 90% branch coverage.
5. A clean environment installs the built wheel and runs the console command.
6. Public `KanadeK/tarpscout` contains a clean `main`, passing CI, annotated
   `v0.1.0`, non-draft GitHub Release, wheel, source archive, and demo bundle.
7. Remote repository, CI, tag, Release assets, and contributors are verified
   before a Gmail self-notification is sent.

## Non-goals for v0.1.0

- Dynamic fabric sag, catenary cuts, snow/wind load calculations, or soil tests.
- GPS/GIS terrain, elevation meshes, weather APIs, or live navigation.
- Free-form tarp meshes, hammocks, tents, tarptents, or more pitch templates.
- A hosted service, login, database, mobile app, or visual editor.

## Open questions

None. The owner delegated product and release decisions for this first version.
