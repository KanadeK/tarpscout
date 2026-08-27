# Implementation Plan: TarpScout v0.1.0

## Architecture

Parse JSON once into immutable dataclasses. Geometry, pitch generation, exact
cord assignment, solver diagnostics, and renderers are separate one-way layers.
Candidate search is a deterministic finite grid so every rejection is auditable.
The project has no runtime dependency and makes no structural-safety claim.

```text
model -> geometry -> pitch candidates -> cord assignment
                         \                /
                          solver/diagnostics -> CLI/renderers
```

## Ordered tasks

1. Repository and locked toolchain
   - Acceptance: independent `main`, correct local author, spec committed, lock valid.
   - Verify: `git status --short`; `uv lock --check`.
2. Boundary model
   - Acceptance: valid survey parses; invalid paths, fields, IDs, and dimensions fail.
   - Verify: `uv run pytest tests/test_models.py -q`.
3. Geometry and pitch projections
   - Acceptance: containment, keep-outs, A-frame, and lean-to match hand math.
   - Verify: `uv run pytest tests/test_geometry.py tests/test_pitches.py -q`.
4. Exact cord assignment
   - Acceptance: minimum-slack one-to-one assignment and proven shortage.
   - Verify: `uv run pytest tests/test_cords.py -q`.
5. Solver and diagnostics
   - Acceptance: deterministic ranked solutions and counted rejection reasons.
   - Verify: `uv run pytest tests/test_solver.py -q`.
6. CLI and artifacts
   - Acceptance: documented exit codes; JSON/CSV/SVG/HTML; no partial invalid output.
   - Verify: `uv run pytest tests/test_cli.py -q`.
7. Examples and documentation
   - Acceptance: feasible and blocking surveys plus English/Chinese usage and repair docs.
   - Verify: run every README acceptance command.
8. CI, package, and release gate
   - Acceptance: lock, format, lint, strict types, >=90% branch coverage, demos,
     deterministic output, build, clean wheel install, installed CLI.
   - Verify: `uv run python scripts/check.py`.
9. Five-axis review and public release
   - Acceptance: clean history and contributors; passing remote CI; annotated
     `v0.1.0`; non-draft Release with wheel, source archive, and demo bundle.
10. Gmail notification
   - Acceptance: self-email only after remote repository, CI, tag, assets, and
     contributor checks pass.

## Checkpoints

- After tasks 1-3: model/geometry tests, lint, and typing pass.
- After tasks 4-6: both feasible fixtures solve and both blocking fixtures explain why.
- After task 8: full local gate passes once on the final candidate commit.
- After task 9: exact remote state is verified before email.

## Risks

| Risk | Mitigation |
|---|---|
| Result mistaken for safety approval | Repeat the no-load-model limitation in every report |
| Unbounded user search | Validate a declared finite grid and maximum state count |
| Greedy cord mismatch | Use exact assignment with stable minimum-slack ranking |
| Stale GitHub login | Use official `gh auth login`; never extract credentials |

## Open questions

None for v0.1.0; the owner delegated product and release choices.
