from __future__ import annotations

import re
import zipfile
import zlib
from html.parser import HTMLParser
from io import BytesIO
from pathlib import Path
from xml.etree import ElementTree

MAX_SOURCE_BYTES = 20_000_000
MAX_ARCHIVE_BYTES = 100_000_000
MAX_ARCHIVE_FILES = 10_000
SUPPORTED = {".txt", ".md", ".docx", ".epub"}


class TextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.parts: list[str] = []
        self.hidden = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in {"script", "style", "svg"}:
            self.hidden += 1
        elif tag in {"p", "br", "div", "li", "h1", "h2", "h3", "h4", "h5", "h6"}:
            self.parts.append("\n")

    def handle_endtag(self, tag: str) -> None:
        if tag in {"script", "style", "svg"} and self.hidden:
            self.hidden -= 1
        elif tag in {"p", "div", "li"}:
            self.parts.append("\n")

    def handle_data(self, data: str) -> None:
        if not self.hidden:
            self.parts.append(data)

    def text(self) -> str:
        return normalize_text("".join(self.parts))


def read_document(path: Path) -> str:
    source = path.expanduser().resolve()
    if not source.is_file():
        raise ValueError(f"source file not found: {source}")
    if source.suffix.casefold() not in SUPPORTED:
        raise ValueError("supported formats are TXT, Markdown, DOCX, and EPUB")
    if source.stat().st_size > MAX_SOURCE_BYTES:
        raise ValueError("source exceeds the 20 MB safety limit")
    if source.suffix.casefold() in {".txt", ".md"}:
        try:
            return normalize_text(source.read_text(encoding="utf-8"))
        except UnicodeError as exc:
            raise ValueError("text source must be UTF-8") from exc
    try:
        if source.suffix.casefold() == ".docx":
            return read_docx(source)
        return read_epub(source)
    except (zipfile.BadZipFile, RuntimeError, NotImplementedError, EOFError, zlib.error) as exc:
        raise ValueError("document archive contents could not be read") from exc


def safe_archive(path: Path) -> zipfile.ZipFile:
    try:
        archive = zipfile.ZipFile(path)
    except (OSError, zipfile.BadZipFile) as exc:
        raise ValueError("source is not a readable ZIP-based document") from exc
    infos = archive.infolist()
    if len(infos) > MAX_ARCHIVE_FILES:
        archive.close()
        raise ValueError("document contains too many archive entries")
    if sum(info.file_size for info in infos) > MAX_ARCHIVE_BYTES:
        archive.close()
        raise ValueError("document exceeds the uncompressed-size safety limit")
    if any(
        name.startswith(("/", "\\")) or ".." in Path(name.replace("\\", "/")).parts
        for name in (info.filename for info in infos)
    ):
        archive.close()
        raise ValueError("document contains an unsafe archive path")
    return archive


def read_docx(path: Path) -> str:
    with safe_archive(path) as archive:
        try:
            content = archive.read("word/document.xml")
        except KeyError as exc:
            raise ValueError("DOCX is missing word/document.xml") from exc
    parts: list[str] = []
    try:
        for _, element in ElementTree.iterparse(BytesIO(content), events=("end",)):
            if element.tag.endswith("}t") and element.text:
                parts.append(element.text)
            elif element.tag.endswith(("}br", "}cr", "}p")):
                parts.append("\n")
            elif element.tag.endswith("}tab"):
                parts.append("\t")
    except ElementTree.ParseError as exc:
        raise ValueError("DOCX document XML is invalid") from exc
    return normalize_text("".join(parts))


def read_epub(path: Path) -> str:
    with safe_archive(path) as archive:
        names = sorted(
            info.filename
            for info in archive.infolist()
            if Path(info.filename).suffix.casefold() in {".xhtml", ".html", ".htm"}
        )
        if not names:
            raise ValueError("EPUB contains no HTML reading content")
        chapters = []
        for name in names:
            extractor = TextExtractor()
            try:
                extractor.feed(archive.read(name).decode("utf-8"))
            except UnicodeError as exc:
                raise ValueError(f"EPUB content is not UTF-8: {name}") from exc
            chapters.append(extractor.text())
    return "\n".join(chapters)


def normalize_text(value: str) -> str:
    value = value.replace("\r\n", "\n").replace("\r", "\n")
    value = re.sub(r"[ \t]+", " ", value)
    value = re.sub(r" *\n+ *", "\n", value)
    return value.strip()
