import zipfile
from pathlib import Path

import pytest

from fiction_number_checker.core import analyze, extract_mentions


@pytest.mark.parametrize(
    "words,value",
    [
        ("zero", 0),
        ("nine", 9),
        ("thirteen", 13),
        ("twenty", 20),
        ("twenty-one", 21),
        ("ninety nine", 99),
    ],
)
def test_number_words_match_arabic_in_supported_contexts(words: str, value: int) -> None:
    for template in [
        "Mara is {} years old.",
        "Mara waited for {} hours.",
        "Mara carried {} coins.",
    ]:
        text = template.format(words)
        mentions = extract_mentions(text, subjects=["Mara"])
        equivalent = extract_mentions(template.format(value), subjects=["Mara"])
        assert len(mentions) == 1
        assert (mentions[0].kind, mentions[0].normalized_value, mentions[0].normalized_unit) == (
            equivalent[0].kind,
            equivalent[0].normalized_value,
            equivalent[0].normalized_unit,
        )
        assert mentions[0].value in text
        assert text[mentions[0].offset :].startswith(mentions[0].value)
        assert mentions[0].context == text


@pytest.mark.parametrize(
    "text",
    [
        "Seven met Nine.",
        "One day Mara would return.",
        "Mara said one second.",
        "Mara had one hundred coins.",
        "Mara waited for one hundred twenty-one hours.",
        "Mara is a hundred and twenty years old.",
        "Mara is minus twenty years old.",
        "Mara waited for two point five hours.",
        "Mara carried twenty-one-thirty coins.",
        "Mara paid twenty dollars.",
        "Mara traveled twenty miles.",
        "Mara carried one and two coins.",
    ],
)
def test_names_idioms_and_unsupported_phrases(text: str) -> None:
    assert extract_mentions(text, subjects=["Mara"]) == []


def test_attribution_case_and_mixed_numeric() -> None:
    text = "Mara waited two hours. Two hours passed. Dorian carried Twenty-One coins. Mara has 3 coins."
    mentions = extract_mentions(text, subjects=["Dorian"])
    assert len(mentions) == 1 and mentions[0].normalized_value == 21
    assert mentions[0].subject == "Dorian"
    all_mentions = extract_mentions(text)
    assert [m.normalized_value for m in all_mentions] == [7200, 7200, 21, 3]


@pytest.mark.parametrize("suffix", [".txt", ".md", ".docx", ".epub"])
def test_read_only_formats_with_words(tmp_path: Path, suffix: str) -> None:
    path = tmp_path / ("draft" + suffix)
    text = "Mara is twenty-one years old. Mara is 22 years old."
    if suffix in {".txt", ".md"}:
        path.write_text(text, encoding="utf-8")
    else:
        with zipfile.ZipFile(path, "w") as archive:
            if suffix == ".docx":
                archive.writestr(
                    "word/document.xml",
                    '<w:document xmlns:w="urn:word"><w:p><w:t>'
                    + text
                    + "</w:t></w:p></w:document>",
                )
            else:
                archive.writestr("chapter.xhtml", "<p>" + text + "</p>")
    original = path.read_bytes()
    report = analyze(path, subjects=["Mara"])
    assert [m.normalized_value for m in report.mentions] == [21, 22]
    assert len(report.review_groups) == 1
    assert path.read_bytes() == original
