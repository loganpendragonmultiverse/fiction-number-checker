# Fiction Number Checker

Fiction Number Checker extracts numerical facts from TXT, Markdown, DOCX, and EPUB manuscripts into a reviewable inventory. It normalizes common ages, money, distances, durations, percentages, and counts, then groups differing values attached to the same inferred or explicitly requested subject.

The result is a consistency checklist, not an automated verdict.

## Three-minute use

Python 3.10 or newer is required.

    python -m pip install "fiction-number-checker @ https://github.com/loganpendragonmultiverse/fiction-number-checker/releases/download/v1.0.0/fiction_number_checker-1.0.0-py3-none-any.whl"
    fiction-number-checker manuscript.docx --subject Mara --subject Dorian --markdown number-review.md --json number-review.json
    fiction-number-checker manuscript.epub --fail-on-review

Supplying subjects is the most precise workflow. Without them, the tool conservatively uses nearby capitalized names and labels unmatched facts “Unassigned.”

## Interpretation and privacy

Different values are not automatically inconsistent. Characters age, money is spent, distances are estimated, time passes, measurements are rounded, and multiple facts can legitimately occur in one scene. Every review group requires manuscript context.

Files are processed locally and read-only. No manuscript text is uploaded or sent to an API. Reports contain excerpts and should be treated as manuscript material.

Version 1 recognizes Arabic numerals and a focused set of English units. It does not resolve number words, dates, currencies without a dollar sign, chronology, pronouns, or narrative truth.

## Development

    python -m pip install -e ".[dev]"
    ruff format --check .
    ruff check .
    mypy src tests
    pytest
    python -m build

Contributions follow [CONTRIBUTING.md](CONTRIBUTING.md), security reports follow [SECURITY.md](SECURITY.md), and the project uses the [MIT License](LICENSE).

## More open-source projects

This project is part of the [Logan Pendragon Forge open-source collection](https://www.loganpendragonforge.com/open-source/). Browse the catalog for other released tools, source repositories, live demos, and downloads.
