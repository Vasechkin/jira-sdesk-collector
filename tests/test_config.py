from __future__ import annotations

from pathlib import Path

import pytest

from jira_sdesk_collector.config import ConfigError, load_config


def test_load_config_expands_period_and_reads_token(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    config = tmp_path / "config.toml"
    config.write_text(
        """
[jira]
base_url = "https://jira.example.invalid"
token_env = "COLLECTOR_TEST_TOKEN"
period_days = 7
jql = "updated >= -{period_days}d OR statusCategory != Done"
fields = ["summary"]
[output]
directory = "result"
""",
        encoding="utf-8",
    )
    monkeypatch.setenv("COLLECTOR_TEST_TOKEN", "secret")

    loaded = load_config(config)

    assert loaded.jira.jql == "updated >= -7d OR statusCategory != Done"
    assert loaded.jira.token == "secret"
    assert loaded.output.directory == (tmp_path / "result").resolve()


def test_missing_token_is_rejected(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    config = tmp_path / "config.toml"
    config.write_text(
        """
[jira]
base_url = "https://jira.example.invalid"
token_env = "MISSING_COLLECTOR_TEST_TOKEN"
period_days = 1
jql = "updated >= -{period_days}d"
fields = ["summary"]
""",
        encoding="utf-8",
    )
    monkeypatch.delenv("MISSING_COLLECTOR_TEST_TOKEN", raising=False)

    with pytest.raises(ConfigError, match="не задана"):
        load_config(config)
