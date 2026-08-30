# Changelog

All notable user-visible changes are documented here.

## [0.1.0] - 2026-08-30

### Added

- Strict measured-site JSON model for tarps, supports, stake zones, circular
  keep-outs, covered footprints, reusable cords, and finite search settings.
- Deterministic A-frame and lean-to geometry search with exact whole-cord
  assignment, ranked candidates, counted rejection reasons, and repair hints.
- `validate`, `solve`, and four-scenario `demo` commands with documented exit
  codes `0`, `1`, and `2`.
- Stable JSON/CSV output, labelled plan/elevation SVGs, and self-contained
  script-free HTML reports.
- Feasible and blocking example surveys, English/Chinese documentation, and a
  one-command local release gate.
- Wheel, source archive, and deterministic demo-bundle release artifacts.
- Lazy bounded grid generation and exact subset-based cord assignment that
  remains practical with large cord inventories.

### Security

- Strict unknown-field rejection, finite-number/range checks, filename-safe
  scenario names, simple-polygon enforcement, escaped SVG/HTML text,
  spreadsheet-safe CSV text, and no runtime network or dependencies.
