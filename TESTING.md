# Testing

Install `.[dev]`, then run `ruff format --check .`, `ruff check .`, `mypy src tests`, `pytest`, and `python -m build`. Retain the existing coverage gate.

Test zero through ninety-nine against Arabic equivalents, explicit duration cues, names/idioms, unsupported phrases, offsets, subject filters and all four read-only formats.

Install the built wheel into an isolated environment and exercise the documented CLI before release. Protected cross-platform CI and CodeQL remain required.
