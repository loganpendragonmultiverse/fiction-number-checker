from __future__ import annotations

import json

from .models import Report


def render_json(report: Report) -> str:
    return json.dumps(report.to_dict(), indent=2, ensure_ascii=False) + "\n"


def render_markdown(report: Report) -> str:
    lines = [
        "# Fiction number review",
        "",
        f"Source: {report.source}",
        "",
        f"Extracted {len(report.mentions)} numerical mentions and created {len(report.review_groups)} review groups.",
        "",
        "| Subject | Type | Value | Normalized | Context |",
        "| --- | --- | --- | --- | --- |",
    ]
    for mention in report.mentions:
        context = mention.context.replace("|", "\\|")
        lines.append(
            f"| {mention.subject} | {mention.kind} | {mention.value} | "
            f"{mention.normalized_value:g} {mention.normalized_unit} | {context} |"
        )
    lines.extend(["", "## Possible consistency review groups", ""])
    if not report.review_groups:
        lines.append("None.")
    for group in report.review_groups:
        lines.append(f"- **{group.subject} / {group.kind}:** " + "; ".join(group.values))
    lines.extend(
        [
            "",
            "## Important limitation",
            "",
            "Different numbers are not automatically contradictory. Time, estimates, unit conversions, viewpoint, and narrative change all require human interpretation.",
            "",
        ]
    )
    return "\n".join(lines)
