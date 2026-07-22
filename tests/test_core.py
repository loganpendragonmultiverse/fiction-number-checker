from pathlib import Path

from fiction_number_checker.core import (
    analyze,
    build_review_groups,
    extract_mentions,
    find_subjects,
    normalize_fact,
)


def test_extracts_and_normalizes_supported_facts() -> None:
    text = (
        "Mara was 18 years old and carried $12.50. "
        "Mara walked 2 miles in 30 minutes. "
        "Later, Mara said she was 19 years old."
    )
    mentions = extract_mentions(text)
    assert {mention.kind for mention in mentions} >= {"age", "money", "distance", "duration"}
    assert (
        next(mention for mention in mentions if mention.kind == "distance").normalized_value
        == 3218.688
    )
    groups = build_review_groups(mentions)
    assert any(group.subject == "Mara" and group.kind == "age" for group in groups)


def test_subject_filter_limits_review_scope() -> None:
    mentions = extract_mentions(
        "Mara carried 3 keys. Dorian carried 8 keys.",
        subjects=["Mara"],
    )
    assert len(mentions) == 1
    assert mentions[0].subject == "Mara"


def test_normalizes_units_and_counts() -> None:
    assert normalize_fact("$1,200.50") == ("money", 1200.5, "currency units")
    assert normalize_fact("5 feet") == ("distance", 1.524, "meters")
    assert normalize_fact("25%") == ("percentage", 25, "percent")
    assert normalize_fact("7") == ("count", 7, "count")
    assert find_subjects("The door had 2 locks.", []) == []


def test_analyze_plain_text_creates_review_groups(tmp_path: Path) -> None:
    source = tmp_path / "story.txt"
    source.write_text("Mara was 18 years old. Mara was 19 years old.", encoding="utf-8")
    report = analyze(source)
    assert len(report.mentions) == 2
    assert len(report.review_groups) == 1
