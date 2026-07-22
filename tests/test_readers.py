import zipfile
from pathlib import Path

import pytest

from fiction_number_checker.readers import (
    TextExtractor,
    normalize_text,
    read_document,
)


def test_reads_markdown_and_normalizes_whitespace(tmp_path: Path) -> None:
    source = tmp_path / "story.md"
    source.write_text("Mara  had  3 keys.\r\n\r\nDorian had 4.", encoding="utf-8")
    assert read_document(source) == "Mara had 3 keys.\nDorian had 4."


def test_reads_minimal_docx(tmp_path: Path) -> None:
    source = tmp_path / "story.docx"
    xml = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
        "<w:body><w:p><w:r><w:t>Mara had 3 keys.</w:t></w:r></w:p></w:body></w:document>"
    )
    with zipfile.ZipFile(source, "w") as archive:
        archive.writestr("word/document.xml", xml)
    assert "Mara had 3 keys." in read_document(source)


def test_reads_epub_html_and_ignores_scripts(tmp_path: Path) -> None:
    source = tmp_path / "story.epub"
    with zipfile.ZipFile(source, "w") as archive:
        archive.writestr(
            "chapter.xhtml",
            "<html><body><p>Mara had 3 keys.</p><script>bad 99</script></body></html>",
        )
    text = read_document(source)
    assert "Mara had 3 keys." in text
    assert "99" not in text


def test_rejects_invalid_sources_and_archives(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="not found"):
        read_document(tmp_path / "missing.txt")
    bad = tmp_path / "story.pdf"
    bad.write_bytes(b"x")
    with pytest.raises(ValueError, match="supported"):
        read_document(bad)
    bad_docx = tmp_path / "bad.docx"
    bad_docx.write_bytes(b"not zip")
    with pytest.raises(ValueError, match="ZIP-based"):
        read_document(bad_docx)
    empty_epub = tmp_path / "empty.epub"
    with zipfile.ZipFile(empty_epub, "w"):
        pass
    with pytest.raises(ValueError, match="no HTML"):
        read_document(empty_epub)


def test_html_extractor_and_normalizer() -> None:
    extractor = TextExtractor()
    extractor.feed("<style>hidden</style><h1>Title</h1><p>Text</p>")
    assert "hidden" not in extractor.text()
    assert normalize_text(" a  b \r\n c ") == "a b\nc"
