# Architecture

TarpScout has one directional flow. Raw JSON is validated once; all later
layers receive immutable typed values and trust those invariants.

```text
JSON file
   │
   ▼
models.py ── strict boundary validation ── Scenario dataclasses
   │
   ├──────────────► geometry.py ── containment/intersection primitives
   │
   ▼
pitches.py ── finite A-frame/lean-to enumeration
   │
   ├──────────────► cords.py ── exact whole-segment assignment
   ▼
solver.py ── hard constraints, rejection counts, deterministic ranking
   │
   ▼
render.py ── stable JSON/CSV/SVG/HTML
   │
   ▼
cli.py ── validate / solve / demo and exit-code policy
```

There is no database, service process, network client, plugin system, or runtime
dependency.

## State ownership

- The site JSON is the sole authority for user measurements and constraints.
- `Scenario` is the sole in-memory domain representation after validation.
- `PitchGeometry` owns generated physical coordinates; renderers do not
  recalculate pitch geometry.
- `SolveResult` owns status, rejection counts, hints, and ranked candidates.
- The JSON report is the machine-readable output authority. CSV, SVG, and HTML
  are views of the same result, not alternate solvers.

The `demo` command creates fresh documents from `demo_data.py`. Checked-in
example JSON files are compared against those documents in tests, making drift a
test failure rather than a second hidden truth.

## Finite search

For each unordered support pair, `pitches.py` lazily samples positions along the
span and attachment heights using `search_step`. It generates one A-frame
orientation and both lean-to orientations requested by the input, stopping at
the explicit `max_search_states` boundary without first materializing a large
grid.

Every geometry then passes, in order:

1. required-footprint coverage with inward margin;
2. all recommended stakes inside at least one stakeable polygon;
3. no tarp, stake, or guyline conflict with circular keep-outs;
4. an exact one-to-one cord assignment, when inventory is supplied.

Cord assignment uses an exact dynamic program over assigned-line subsets and
minimizes total unused length. A pitch requires only three lines for lean-to or
five for A-frame, so extra inventory grows work linearly rather than creating a
factorial permutation search.

## Deterministic ranking and artifacts

Candidates sort by:

1. wind-alignment penalty when `wind_from_deg` exists;
2. total unused assigned cord;
3. distance from preferred ridge height;
4. a stable collision-free geometry identifier containing the support IDs,
   pitch type, full grid coordinates, and orientation.

JSON keys are sorted, CSV uses explicit LF records, SVG coordinates use fixed
decimal formatting, HTML contains no scripts or timestamps, and the demo ZIP
uses sorted entries with a fixed archive timestamp. Output paths are never
embedded in artifacts. These rules are exercised by two independent demo runs
inside the release gate.

## Boundary and failure design

`models.py` rejects malformed external data with an exact field path. The CLI
catches only `InputError` and filesystem `OSError`, maps them to exit `2`, and
lets unexpected internal errors fail fast. Valid no-solution results are not
exceptions: they return exit `1` with counted reasons and a JSON report.

When the same scenario output directory is reused, a no-solution run removes
only the four exact solution-view filenames owned by that scenario. It preserves
the new report, input files, other scenario outputs, and unrelated user files.

## Deliberate limits

The model is a two-dimensional level plane with vertical point supports,
rectangular tarp projection, simple stake polygons, circular keep-outs, and
rectangular required footprints. No load, elasticity, sag, catenary, soil,
weather, GPS, or material-strength model exists. Adding one would change the
product's safety meaning and is outside v0.1.0.
