# Input format

TarpScout accepts one strict UTF-8 JSON object. Unknown fields are rejected so a
misspelled measurement cannot be silently ignored. Coordinates and lengths are
metres in a local, level XY plane; angles are degrees.

Start from [pine-gap.site.json](../examples/pine-gap.site.json) rather than
typing the structure from scratch.

Every `id` is a non-empty printable Unicode string and must be unique within
its collection. Control characters are rejected because IDs are rendered into
CSV, SVG, and HTML. Formula-shaped text is preserved in JSON but prefixed with
an apostrophe in CSV cells so spreadsheet software treats it as text.

## Top-level fields

| Field | Required | Meaning |
|---|---:|---|
| `name` | yes | 1–64 ASCII letters, digits, `_`, or `-`; used in output filenames |
| `tarp` | yes | Positive rectangular `length` and `width` |
| `supports` | yes | At least two unique support points |
| `stake_zones` | yes | At least one simple polygon where recommended stakes may land |
| `keepouts` | no | Circular areas forbidden to tarp coverage, stakes, and guylines |
| `footprints` | yes | At least one rotated rectangle that every plan must cover |
| `cords` | no | Reusable whole cord segments; omitted/empty means no inventory constraint |
| `requirements` | yes | Pitch types, height/slope ranges, allowances, and finite search controls |

## Supports

Each support has:

- `id`: non-empty printable identifier;
- `x`, `y`: local coordinates;
- `min_height`, `max_height`: allowable attachment range, with
  `0 <= min_height <= max_height` and positive maximum;
- `wrap_allowance`: optional non-negative extra cord consumed around the
  support.

Support IDs and coordinates must both be unique. Every candidate uses an
unordered pair of supports.

## Stake zones and keep-outs

A stake zone is `{ "id": ..., "polygon": [[x, y], ...] }`. Supply at least
three points in boundary order. The polygon must be simple and have non-zero
area; do not repeat the first point at the end.

A keep-out is `{ "id": ..., "center": [x, y], "radius": positive }`.
TarpScout rejects a candidate when its projected tarp, a recommended stake, or
a guyline intersects a keep-out circle.

## Required footprints

Each footprint is a rotated rectangle:

```json
{
  "id": "sleeping-pad",
  "center": [2.5, 0.0],
  "length": 2.0,
  "width": 1.0,
  "angle_deg": 0.0
}
```

All four corners of every footprint must lie inside projected tarp coverage by
at least `coverage_margin`.

## Reusable cords

Each cord is `{ "id": ..., "length": positive }`. When the array is present
and non-empty, every ridge/guy requirement must receive one distinct whole
segment. TarpScout does not splice cords or split one segment between lines. It
chooses the feasible one-to-one assignment with the least total unused length,
then a stable ID tie-break.

An A-frame needs one ridge line and four guys; a lean-to needs one ridge and two
guys. Required lengths include the declared support-wrap, knot, and stake-setback
allowances.

## Requirements

| Field | Contract |
|---|---|
| `pitch_types` | Unique non-empty list containing `a_frame`, `lean_to`, or both |
| `ridge_height` | `{min, max, preferred}` with ordered bounds and preference inside them |
| `edge_height` | Non-negative and below minimum ridge height |
| `slope_angle` | `{min, max}` with `0 < min <= max < 90` |
| `stake_setback` | Positive horizontal distance beyond a tarp edge |
| `knot_allowance` | Non-negative extra length on every line |
| `coverage_margin` | Non-negative inward clearance for required footprints |
| `search_step` | Sampling step for position and attachment height, at least `0.000000001` m |
| `end_clearance` | Non-negative tarp-to-support clearance at both ridge ends |
| `max_search_states` | Integer from 1 through 1,000,000 |
| `wind_from_deg` | Optional direction wind comes from: 0 north, 90 east, 180 south, 270 west |

`--limit` is a CLI output limit, not an input field. It controls how many ranked
candidates appear in a successful report; it does not enlarge the search.

## Validation behavior

`tarpscout validate SITE.json` returns `0` and prints `valid: <name>` when the
document is accepted. Invalid JSON, unknown/missing fields, non-finite numbers,
bad ranges, duplicate IDs, repeated/self-intersecting polygon points, and
invalid collection cardinalities return `2` with the exact failing field path
on stderr.
