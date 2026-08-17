from __future__ import annotations

import csv
import json
from pathlib import Path

from jira_sdesk_collector.exporters import export_csv, export_json


def test_export_json_and_csv(tmp_path: Path) -> None:
    issues = [
        {
            "key": "EX-1",
            "fields": {
                "summary": "Service unavailable",
                "status": {"name": "Open"},
                "assignee": {"displayName": "Example User"},
                "labels": ["incident", "critical"],
                "components": [{"name": "API"}],
                "issuelinks": [{"outwardIssue": {"key": "EX-2"}}],
            },
        }
    ]
    json_path = tmp_path / "issues.json"
    csv_path = tmp_path / "issues.csv"

    export_json(issues, json_path)
    export_csv(issues, csv_path)

    assert json.loads(json_path.read_text(encoding="utf-8"))[0]["key"] == "EX-1"
    with csv_path.open(encoding="utf-8-sig", newline="") as file:
        row = next(csv.DictReader(file))
    assert row["key"] == "EX-1"
    assert row["status"] == "Open"
    assert row["labels"] == "incident; critical"
    assert row["issue_links"] == "EX-2"
