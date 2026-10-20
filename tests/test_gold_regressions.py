import json
import sys
import zipfile
from pathlib import Path
from typing import IO, Any

import pytest

from fiction_number_checker.cli import main
from fiction_number_checker.core import build_review_groups, extract_mentions, normalize_fact
from fiction_number_checker.readers import read_document


@pytest.mark.parametrize(
    "quantity,value", [("1234", 1234), ("1234567", 1234567), ("1,234.50", 1234.5), ("12.75", 12.75)]
)
def test_complete_arabic_numbers(quantity: str, value: float) -> None:
    text = f"Mara carried {quantity} coins."
    mentions = extract_mentions(text)
    assert len(mentions) == 1
    assert mentions[0].normalized_value == value
    assert mentions[0].value == quantity
    assert text[mentions[0].offset :].startswith(quantity)


@pytest.mark.parametrize(
    "text", ["Mara has ID1234.", "Mara has 12,34 coins.", "Mara has 1.2.3 coins."]
)
def test_no_partial_numbers_or_identifiers(text: str) -> None:
    assert extract_mentions(text) == []


def test_units_compare_consistently() -> None:
    assert normalize_fact("12 inches") == normalize_fact("1 foot")
    assert normalize_fact("1 day") == normalize_fact("24 hours")
    assert normalize_fact("1 week") == normalize_fact("7 days")
    assert not build_review_groups(extract_mentions("Mara waited 1 day. Mara waited 24 hours."))
    assert build_review_groups(extract_mentions("Mara waited 1 day. Mara waited 25 hours."))


@pytest.mark.parametrize("number", ["9" * 400, "9" * 306 + " years"])
def test_extreme_values_have_controlled_diagnostic(
    number: str, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    source = tmp_path / "story.txt"
    source.write_text("Mara carried " + number + ".", encoding="utf-8")
    assert main([str(source)]) == 2
    assert "too large" in capsys.readouterr().err


def test_inline_runs_and_paragraphs_preserve_words(tmp_path: Path) -> None:
    docx = tmp_path / "story.docx"
    with zipfile.ZipFile(docx, "w") as archive:
        archive.writestr(
            "word/document.xml",
            '<w:document xmlns:w="urn:word"><w:p><w:r><w:t>Mara carried 12</w:t></w:r><w:r><w:t>34 coins.</w:t></w:r></w:p><w:p><w:r><w:t>Mara waited</w:t><w:tab/><w:t>two</w:t><w:br/><w:t>hours.</w:t></w:r></w:p></w:document>',
        )
    assert read_document(docx) == "Mara carried 1234 coins.\nMara waited two\nhours."
    epub = tmp_path / "story.epub"
    with zipfile.ZipFile(epub, "w") as archive:
        archive.writestr("a.xhtml", "<p>Mara carried <b>12</b>34 coins.</p>")
        archive.writestr("b.xhtml", "<p>Mara carried 3 coins.</p>")
    assert read_document(epub) == "Mara carried 1234 coins.\nMara carried 3 coins."


def test_output_preflight_preserves_both_reports_and_source(tmp_path: Path) -> None:
    source = tmp_path / "story.txt"
    source.write_text("Mara carried 1234 coins.", encoding="utf-8")
    output = tmp_path / "report.json"
    existing = tmp_path / "report.md"
    existing.write_text("keep", encoding="utf-8")
    assert main([str(source), "--json", str(output), "--markdown", str(existing)]) == 2
    assert not output.exists() and existing.read_text() == "keep"
    assert main([str(source), "--json", str(output), "--markdown", str(output)]) == 2
    assert not output.exists()
    assert main([str(source), "--json", str(source)]) == 2
    assert source.read_text() == "Mara carried 1234 coins."
    assert main([str(source), "--json", str(output)]) == 0
    assert json.loads(output.read_text())["mentions"][0]["normalized_value"] == 1234


def test_dangling_output_symlink_is_not_followed(tmp_path: Path) -> None:
    source = tmp_path / "story.txt"
    source.write_text("Mara carried 3 coins.", encoding="utf-8")
    target = tmp_path / "absent.json"
    link = tmp_path / "report.json"
    try:
        link.symlink_to(target)
    except OSError as exc:
        if sys.platform == "win32" and getattr(exc, "winerror", None) == 1314:
            pytest.skip("Windows account lacks symbolic-link privilege (1314)")
        raise
    assert main([str(source), "--json", str(link)]) == 2
    assert link.is_symlink() and not target.exists()


@pytest.mark.parametrize(
    "text",
    [
        "Mara moved -5 miles.",
        "Mara moved +5 miles.",
        "Mara carried - 5 coins.",
        "Mara carried plus 5 coins.",
        "Mara paid -$12.50.",
        "Mara paid minus $12.50.",
    ],
)
def test_signed_arabic_phrases_are_not_reported_as_positive(text: str) -> None:
    assert extract_mentions(text) == []


def test_singular_inch_is_distance() -> None:
    mentions = extract_mentions("Mara moved 1 inch.")
    assert len(mentions) == 1
    assert mentions[0].kind == "distance"
    assert mentions[0].normalized_value == 0.0254


def test_exclusive_creation_rejects_a_file_arriving_before_write(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from fiction_number_checker.cli import write_new

    output = tmp_path / "report.json"
    original_open = Path.open

    def arriving_file(path: Path, mode: str = "r", *args: Any, **kwargs: Any) -> IO[Any]:
        if path == output and mode == "x":
            with original_open(path, "w", encoding="utf-8") as stream:
                stream.write("keep")
        return original_open(path, mode, *args, **kwargs)

    monkeypatch.setattr(Path, "open", arriving_file)
    with pytest.raises(FileExistsError):
        write_new(output, "replace")
    assert output.read_text() == "keep"


@pytest.mark.parametrize(
    "suffix,member,content",
    [
        (
            ".docx",
            "word/document.xml",
            '<w:document xmlns:w="urn:word"><w:p><w:t>Mara is 21 years old.</w:t></w:p></w:document>',
        ),
        (".epub", "chapter.xhtml", "<p>Mara is 21 years old.</p>"),
    ],
)
def test_corrupted_archive_member_is_controlled_cli_error(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], suffix: str, member: str, content: str
) -> None:
    source = tmp_path / ("story" + suffix)
    with zipfile.ZipFile(source, "w") as archive:
        archive.writestr(member, content)
    corrupted = bytearray(source.read_bytes())
    offset = corrupted.index(b"PK\x01\x02")
    corrupted[offset + 16] ^= 1
    source.write_bytes(corrupted)
    original = source.read_bytes()
    output = tmp_path / "report.json"
    assert main([str(source), "--json", str(output)]) == 2
    assert "archive contents" in capsys.readouterr().err
    assert source.read_bytes() == original and not output.exists()
