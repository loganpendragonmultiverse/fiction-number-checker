from pathlib import Path

from fiction_number_checker.cli import main
from fiction_number_checker.core import analyze
from fiction_number_checker.render import render_json, render_markdown


def test_renderers_and_cli(tmp_path: Path) -> None:
    source = tmp_path / "story.txt"
    source.write_text("Mara was 18 years old. Mara was 19 years old.", encoding="utf-8")
    report = analyze(source)
    assert '"reviewGroups"' in render_json(report)
    assert "Possible consistency" in render_markdown(report)
    json_path = tmp_path / "out" / "report.json"
    markdown_path = tmp_path / "out" / "report.md"
    assert main([str(source), "--json", str(json_path), "--markdown", str(markdown_path)]) == 0
    assert main([str(source), "--fail-on-review"]) == 1
    assert main([str(source), "--json", str(json_path)]) == 2


def test_cli_missing_source(tmp_path: Path) -> None:
    assert main([str(tmp_path / "missing.txt")]) == 2
