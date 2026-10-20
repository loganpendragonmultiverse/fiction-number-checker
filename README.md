# Fiction Number Checker

Fiction Number Checker extracts numerical facts from TXT, Markdown, DOCX, and EPUB manuscripts into a reviewable inventory. It normalizes common ages, money, distances, durations, percentages, and counts, then groups differing values attached to the same inferred or explicitly requested subject.

The result is a consistency checklist, not an automated verdict.

## Three-minute use

Python 3.10 or newer is required.

    python -m pip install "fiction-number-checker @ https://github.com/loganpendragonmultiverse/fiction-number-checker/releases/download/v1.1.1/fiction_number_checker-1.1.1-py3-none-any.whl"
    fiction-number-checker manuscript.docx --subject Mara --subject Dorian --markdown number-review.md --json number-review.json
    fiction-number-checker manuscript.epub --fail-on-review

Supplying subjects is the most precise workflow. Without them, the tool conservatively uses nearby capitalized names and labels unmatched facts “Unassigned.”

## Interpretation and privacy

Different values are not automatically inconsistent. Characters age, money is spent, distances are estimated, time passes, measurements are rounded, and multiple facts can legitimately occur in one scene. Every review group requires manuscript context.

Files are processed locally and read-only. No manuscript text is uploaded or sent to an API. Reports contain excerpts and should be treated as manuscript material.

Arabic numerals retain their existing detection. Version 1.1 also recognizes English
number words zero through ninety-nine, including space or hyphen compounds, in
`years old` ages, explicit duration contexts and a focused count vocabulary.
It does not resolve dates, currencies without a dollar sign, chronology, pronouns,
or narrative truth.

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

## Number-word boundaries

Examples: `Mara is twenty-one years old`, `Mara waited for two hours`,
`Two years passed`, and `Mara carried ninety-nine coins`. Durations require a
preceding cue (`for`, `after`, `before`, `within`, `in`, `lasted`, `waited`, `spent`,
`took`, `takes`, `over`) or following `passed`/`elapsed`; an isolated `one day` or
`one second` does not create a fact. Count nouns are people/persons, guards,
soldiers, coins, ships, books, doors, rooms, horses, children and items, with singular
forms where applicable. Unsupported larger, signed, decimal or `and` phrases are
not partially converted. Number-word distance, money and percentage phrases are
outside this bounded feature. Original text, offsets, excerpts and subject filters
are preserved. These syntactic rules cannot disambiguate every idiom or a name that
looks exactly like a supported quantity; review the excerpt.

Automatic subject guesses exclude standalone number-word tokens. Explicit `--subject` filters still support characters named Seven or similar ambiguous names.

Duration cues match whole words: suffixes such as `in` in `cousin` or `again` do not count. Signed number-word phrases include `+twenty` and `plus twenty` and are excluded.

## Numeric and export boundaries

Arabic numbers retain full ungrouped or comma-grouped values and decimal fractions. Numeric identifiers, malformed comma/decimal fragments, and Arabic quantities with explicit plus/minus signs or plus/minus/negative prefixes are excluded rather than reported as positive values. All durations are reported in seconds; a day is 86,400 seconds, a week seven days, and year/month estimates use 365.25/30.4375 days. These are comparison conventions, not inferred chronology. Non-finite quantities produce an error rather than invalid JSON. DOCX text runs and EPUB inline markup preserve adjacent text; EPUB HTML members are inspected in filename order, without claiming reading-order chronology.

Reports require distinct new files. Existing files and leaf symbolic links are rejected before writing either requested report. A runtime I/O error can still leave an earlier new report written; this is not a multi-file transaction or a defense against hostile leaf or parent-directory replacement.

Installed distributions include the four project guides under `share/fiction-number-checker` and a synthetic example in its `examples` subfolder.
