"""Выгрузка в JSON и удобный для отчётов CSV."""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any


CSV_COLUMNS = (
    "key",
    "summary",
    "description",
    "status",
    "priority",
    "created",
    "updated",
    "resolutiondate",
    "assignee",
    "reporter",
    "components",
    "labels",
    "issue_links",
    "security",
)


def _name(value: Any) -> str:
    if not isinstance(value, dict):
        return ""
    return str(value.get("displayName") or value.get("name") or "")


def _description(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"))


def issue_to_row(issue: dict[str, Any]) -> dict[str, str]:
    fields = issue.get("fields") or {}
    links = []
    for link in fields.get("issuelinks") or []:
        target = link.get("outwardIssue") or link.get("inwardIssue") or {}
        if target.get("key"):
            links.append(str(target["key"]))
    return {
        "key": str(issue.get("key", "")),
        "summary": str(fields.get("summary") or ""),
        "description": _description(fields.get("description")),
        "status": _name(fields.get("status")),
        "priority": _name(fields.get("priority")),
        "created": str(fields.get("created") or ""),
        "updated": str(fields.get("updated") or ""),
        "resolutiondate": str(fields.get("resolutiondate") or ""),
        "assignee": _name(fields.get("assignee")),
        "reporter": _name(fields.get("reporter")),
        "components": "; ".join(_name(item) for item in fields.get("components") or []),
        "labels": "; ".join(str(item) for item in fields.get("labels") or []),
        "issue_links": "; ".join(links),
        "security": _name(fields.get("security")),
    }


def export_json(issues: list[dict[str, Any]], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(issues, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temporary.replace(path)


def export_csv(issues: list[dict[str, Any]], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=CSV_COLUMNS, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(issue_to_row(issue) for issue in issues)
    temporary.replace(path)
