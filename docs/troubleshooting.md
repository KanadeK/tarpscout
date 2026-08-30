# Troubleshooting and repair flow

Start with the command's exit code and the JSON report. Do not change several
constraints at once: repair the highest-count rejection, rerun, and inspect the
new evidence.

## Exit 2: input, CLI, or filesystem error

1. Run `tarpscout validate SITE.json`.
2. Read the exact field path on stderr, for example
   `tarp.width: expected positive number`.
3. Correct that measurement or field name; do not add unknown fields as notes.
4. Validate again before solving.

If validation succeeds but writing fails, choose a writable `--output`
directory. TarpScout reports the filesystem error and does not turn it into a
false no-solution result.

## Exit 1: valid survey, no sampled plan

The report's `result.rejections` counts why candidates were removed, while
`result.repair_hints` gives a concrete next change.

| Reason | What it means | Repair to test |
|---|---|---|
| `support_span_too_short` | Tarp length plus both end clearances exceeds the support span | Use farther supports, a shorter tarp, or smaller measured clearance |
| `ridge_height_unavailable` | Support attachment ranges do not overlap the requested ridge range | Change supports or correct the measured height ranges |
| `slope_out_of_range` | Ridge/edge height and tarp width cannot make an allowed roof angle | Adjust the declared heights or slope range |
| `footprint_not_covered` | At least one required rectangle corner misses coverage or margin | Move/reduce the footprint or use a larger tarp |
| `stake_outside_zone` | A recommended stake lands outside every polygon | Remeasure/expand the legal stake zone or change setback |
| `keepout_conflict` | Tarp, stake, or guyline intersects a forbidden circle | Move the protected object, footprint, or support choice |
| `cord_shortage` | No one-to-one assignment satisfies every line length | Add longer segments or reduce measured allowances/setback |
| `search_limit` | `max_search_states` stopped enumeration | Use a coarser `search_step` or raise the explicit state limit |

`no_solution` means no candidate in the declared model passed. It does not prove
that a different pitch style, an unmeasured anchor, or a position between grid
samples cannot work.

## Demo acceptance

```powershell
tarpscout demo demo-output
```

Expected stdout, in order:

```text
found: pine-gap
found: creek-lean-to
no_solution: fire-ring
no_solution: short-cords
```

Any different status is a regression or local modification; run the repository
gate before reporting an issue.

## Development gate failure

Run the exact failing command printed after `+` by `scripts/check.py`:

- formatting: `uv run ruff format src tests scripts`, then recheck;
- lint/type: fix the cited source, never disable the rule;
- test/coverage: run the cited test file, repair behavior or add a missing
  meaningful boundary test, then rerun the full gate;
- build/install: inspect the first build or console error; do not reuse an old
  file in `dist/` because the gate rebuilds that directory;
- byte stability: compare the two demo trees for timestamps, platform newlines,
  unordered iteration, or output-path leakage.

On Windows, an old pytest directory created by another account can cause
`WinError 5`. Use an explicit directory owned by the current account for a
focused run:

```powershell
uv run pytest -q --basetemp "$env:TEMP\tarpscout-pytest"
```

The release gate already uses a fresh project-specific temporary directory.
