# Contributing

Thanks for helping TarpScout stay small, inspectable, and trustworthy.

## Set up

```powershell
git clone https://github.com/KanadeK/tarpscout.git
cd tarpscout
uv sync --locked
uv run python scripts/check.py
```

Python 3.11 through 3.14 is supported. There are no runtime dependencies.

## Change discipline

- Open an issue before adding pitch types, changing public JSON fields, or
  introducing a dependency.
- Keep each change focused; do not mix a behavior change with unrelated cleanup.
- For behavior, add a test that fails first, implement the minimum fix, then run
  the focused test and full gate.
- Validate only external boundaries. Internal invariant violations should fail
  fast rather than silently default or fall back.
- Never weaken an assertion, coverage threshold, or diagnostic to make CI green.
- Do not add structural/weather/safety claims without a real validated physical
  model; that is outside the current project contract.

## Style and verification

Ruff formatting/lint and strict mypy are authoritative. The complete check is:

```powershell
uv run python scripts/check.py
```

It must finish with `TarpScout release gate passed.` Pull requests should state
the user-visible outcome, tests added, and exact verification command/result.

## Commit messages

Use focused conventional messages such as:

```text
feat: add a measured-site constraint
fix: preserve no-solution report integrity
docs: explain cord assignment inputs
chore: update the release gate
```
