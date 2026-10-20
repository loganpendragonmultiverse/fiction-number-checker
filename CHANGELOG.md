# Changelog

## 1.1.1 - 2026-10-20

- Package the four handoff guides and a synthetic example with both distributions.

- Preserve full Arabic numbers, grouped decimals, plural inches and inline DOCX/EPUB text instead of splitting them into misleading facts.
- Normalize all durations to seconds so equivalent day/hour and week/day quantities compare equally; month/year estimates remain approximate.
- Exclude signed Arabic phrases rather than silently reporting their magnitude as positive.
- Report unreadable or corrupt DOCX/EPUB members as controlled CLI errors.
- Refuse non-finite quantities and no-clobber report conflicts, including symbolic-link outputs.

## 1.1.0 - 2026-10-15

- Require whole-word duration cues and exclude positive-signed number-word phrases.

- Recognize English number words zero through ninety-nine in focused age, count and explicit duration contexts.
- Normalize simple, spaced and hyphenated forms while retaining original excerpts and offsets.
- Skip unsupported larger/signed/decimal phrases and isolated duration idioms; retain read-only format handling.

## 1.0.0 - 2026-07-22

- Extract numerical facts from TXT, Markdown, DOCX, and EPUB manuscripts.
- Normalize focused ages, money, distances, durations, percentages, and counts.
- Export human-review groups through terminal, Markdown, and JSON reports.
