from __future__ import annotations

import argparse
import sys
from pathlib import Path

from . import __version__
from .core import analyze
from .render import render_json, render_markdown


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(
        prog="fiction-number-checker",
        description="Extract numerical facts from fiction for human consistency review.",
    )
    result.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    result.add_argument("source", type=Path)
    result.add_argument("--subject", action="append", default=[])
    result.add_argument("--json", dest="json_path", type=Path)
    result.add_argument("--markdown", type=Path)
    result.add_argument("--fail-on-review", action="store_true")
    return result


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    try:
        outputs = [path for path in [args.json_path, args.markdown] if path is not None]
        targets = [output_target(path) for path in outputs]
        if len(targets) != len(set(targets)):
            raise ValueError("JSON and Markdown outputs must be different files")
        report = analyze(args.source, subjects=args.subject)
        markdown = render_markdown(report)
        if args.json_path:
            write_new(args.json_path, render_json(report))
        if args.markdown:
            write_new(args.markdown, markdown)
        if not args.json_path and not args.markdown:
            print(markdown)
        return 1 if args.fail_on_review and report.review_groups else 0
    except (OSError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


def output_target(path: Path) -> Path:
    expanded = path.expanduser()
    if expanded.is_symlink():
        raise ValueError(f"output is a symbolic link: {expanded}")
    target = expanded.absolute().parent.resolve() / expanded.name
    if target.exists():
        raise ValueError(f"output already exists: {target}")
    return target


def write_new(path: Path, content: str) -> None:
    target = output_target(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("x", encoding="utf-8", newline="\n") as stream:
        stream.write(content)
