from __future__ import annotations

import re
from collections import defaultdict
from pathlib import Path

from .models import Mention, Report, ReviewGroup
from .readers import read_document

NUMBER = r"(?:\d{1,3}(?:,\d{3})*|\d+)(?:\.\d+)?"
FACT_PATTERN = re.compile(
    rf"""(?ix)
    (?P<money>\$\s*{NUMBER})
    |
    (?P<measure>{NUMBER}\s*(?:years?\s+old|years?|months?|weeks?|days?|hours?|minutes?|seconds?|miles?|kilometers?|kilometres?|km|meters?|metres?|feet|foot|inches?|percent|%))
    |
    (?P<count>{NUMBER})
    """
)
SENTENCE_BOUNDARY = re.compile(r"(?<=[.!?])\s+|\n+")
SUBJECT = re.compile(r"\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\b")
SUBJECT_STOP = {
    "A",
    "An",
    "At",
    "By",
    "For",
    "He",
    "Her",
    "His",
    "I",
    "In",
    "It",
    "Later",
    "On",
    "She",
    "The",
    "They",
    "We",
}

UNIT_MAP = {
    "year": ("duration", "days", 365.25),
    "month": ("duration", "days", 30.4375),
    "week": ("duration", "days", 7),
    "day": ("duration", "days", 1),
    "hour": ("duration", "seconds", 3600),
    "minute": ("duration", "seconds", 60),
    "second": ("duration", "seconds", 1),
    "mile": ("distance", "meters", 1609.344),
    "kilometer": ("distance", "meters", 1000),
    "kilometre": ("distance", "meters", 1000),
    "km": ("distance", "meters", 1000),
    "meter": ("distance", "meters", 1),
    "metre": ("distance", "meters", 1),
    "foot": ("distance", "meters", 0.3048),
    "feet": ("distance", "meters", 0.3048),
    "inch": ("distance", "meters", 0.0254),
    "percent": ("percentage", "percent", 1),
    "%": ("percentage", "percent", 1),
}


def analyze(path: Path, *, subjects: list[str] | None = None) -> Report:
    source = path.expanduser().resolve()
    text = read_document(source)
    mentions = extract_mentions(text, subjects=subjects)
    groups = build_review_groups(mentions)
    return Report(source, tuple(mentions), tuple(groups))


def extract_mentions(text: str, *, subjects: list[str] | None = None) -> list[Mention]:
    requested = [subject.strip() for subject in subjects or [] if subject.strip()]
    mentions: list[Mention] = []
    cursor = 0
    for sentence in SENTENCE_BOUNDARY.split(text):
        sentence_start = text.find(sentence, cursor)
        cursor = sentence_start + len(sentence)
        if not sentence.strip():
            continue
        sentence_subjects = find_subjects(sentence, requested)
        if requested and not sentence_subjects:
            continue
        subject = ", ".join(sentence_subjects) if sentence_subjects else "Unassigned"
        for match in FACT_PATTERN.finditer(sentence):
            raw = match.group(0)
            kind, value, unit = normalize_fact(raw)
            mentions.append(
                Mention(
                    value=raw,
                    kind=kind,
                    normalized_value=value,
                    normalized_unit=unit,
                    subject=subject,
                    context=sentence.strip(),
                    offset=sentence_start + match.start(),
                )
            )
    return mentions


def find_subjects(sentence: str, requested: list[str]) -> list[str]:
    if requested:
        return [
            subject
            for subject in requested
            if re.search(r"\b" + re.escape(subject) + r"\b", sentence, flags=re.IGNORECASE)
        ]
    found = []
    for match in SUBJECT.finditer(sentence):
        candidate = match.group(1)
        if candidate.split()[0] not in SUBJECT_STOP and candidate not in found:
            found.append(candidate)
    return found[:3]


def normalize_fact(raw: str) -> tuple[str, float, str]:
    number_match = re.search(r"\d[\d,]*(?:\.\d+)?", raw)
    if not number_match:
        raise ValueError(f"number could not be normalized: {raw}")
    number = float(number_match.group(0).replace(",", ""))
    lowered = raw.casefold().strip()
    if "$" in raw:
        return "money", round(number, 2), "currency units"
    if re.search(r"years?\s+old", lowered):
        return "age", number, "years"
    unit_text = lowered[number_match.end() :].strip()
    unit_text = re.sub(r"s$", "", unit_text)
    mapped = UNIT_MAP.get(unit_text)
    if mapped:
        kind, unit, factor = mapped
        return kind, round(number * factor, 6), unit
    return "count", number, "count"


def build_review_groups(mentions: list[Mention]) -> list[ReviewGroup]:
    grouped: dict[tuple[str, str, str], list[Mention]] = defaultdict(list)
    for mention in mentions:
        grouped[(mention.subject.casefold(), mention.kind, mention.normalized_unit)].append(mention)
    results = []
    for (_, kind, _), matches in sorted(grouped.items()):
        values = sorted({mention.normalized_value for mention in matches})
        if len(values) < 2:
            continue
        results.append(
            ReviewGroup(
                subject=matches[0].subject,
                kind=kind,
                values=tuple(mention.value for mention in matches),
                mentions=tuple(matches),
            )
        )
    return results
