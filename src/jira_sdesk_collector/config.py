"""Configuration loading and validation."""

from __future__ import annotations

import os
import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from dotenv import load_dotenv


class ConfigError(ValueError):
    """Raised when local collector configuration is invalid."""


@dataclass(frozen=True)
class JiraConfig:
    base_url: str
    api_path: str
    token: str
    proxy: str | None
    verify: bool | str
    timeout_seconds: float
    page_size: int
    jql: str
    fields: tuple[str, ...]


@dataclass(frozen=True)
class OutputConfig:
    directory: Path
    json_filename: str
    csv_filename: str


@dataclass(frozen=True)
class Config:
    jira: JiraConfig
    output: OutputConfig


def _required(section: dict[str, Any], key: str) -> Any:
    value = section.get(key)
    if value is None or value == "":
        raise ConfigError(f"Missing required configuration value: {key}")
    return value


def _validate_url(value: str, label: str) -> str:
    parsed = urlparse(value)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ConfigError(f"{label} must be an absolute HTTP(S) URL")
    return value.rstrip("/")


def load_config(path: str | Path) -> Config:
    config_path = Path(path).expanduser().resolve()
    if not config_path.is_file():
        raise ConfigError(f"Configuration file not found: {config_path}")

    load_dotenv(config_path.parent / ".env", override=False)
    with config_path.open("rb") as file:
        raw = tomllib.load(file)

    jira = raw.get("jira", {})
    output = raw.get("output", {})
    if not isinstance(jira, dict) or not isinstance(output, dict):
        raise ConfigError("[jira] and [output] must be TOML tables")

    token_env = str(_required(jira, "token_env"))
    token = os.getenv(token_env)
    if not token:
        raise ConfigError(f"Environment variable {token_env!r} is not set")

    period_days = int(_required(jira, "period_days"))
    if period_days < 1:
        raise ConfigError("period_days must be at least 1")
    jql_template = str(_required(jira, "jql"))
    try:
        jql = jql_template.format(period_days=period_days)
    except (KeyError, ValueError) as error:
        raise ConfigError(f"Invalid jql template: {error}") from error

    proxy_value = str(jira.get("proxy", "")).strip() or None
    proxy = _validate_url(proxy_value, "proxy") if proxy_value else None
    verify_tls = jira.get("verify_tls", True)
    if not isinstance(verify_tls, bool):
        raise ConfigError("verify_tls must be true or false")
    ca_bundle = str(jira.get("ca_bundle", "")).strip()
    if ca_bundle:
        ca_path = Path(ca_bundle).expanduser()
        if not ca_path.is_absolute():
            ca_path = config_path.parent / ca_path
        if not ca_path.is_file():
            raise ConfigError(f"TLS CA bundle not found: {ca_path}")
        verify: bool | str = str(ca_path.resolve())
    else:
        verify = verify_tls

    fields = jira.get("fields", [])
    if not isinstance(fields, list) or not fields or not all(isinstance(item, str) for item in fields):
        raise ConfigError("fields must be a non-empty list of strings")

    page_size = int(jira.get("page_size", 100))
    if not 1 <= page_size <= 1000:
        raise ConfigError("page_size must be between 1 and 1000")
    timeout_seconds = float(jira.get("timeout_seconds", 30))
    if timeout_seconds <= 0:
        raise ConfigError("timeout_seconds must be greater than 0")

    output_dir = Path(str(output.get("directory", "output"))).expanduser()
    if not output_dir.is_absolute():
        output_dir = config_path.parent / output_dir

    return Config(
        jira=JiraConfig(
            base_url=_validate_url(str(_required(jira, "base_url")), "base_url"),
            api_path="/" + str(jira.get("api_path", "/rest/api/2")).strip("/"),
            token=token,
            proxy=proxy,
            verify=verify,
            timeout_seconds=timeout_seconds,
            page_size=page_size,
            jql=jql,
            fields=tuple(fields),
        ),
        output=OutputConfig(
            directory=output_dir.resolve(),
            json_filename=Path(str(output.get("json_filename", "jira_tickets.json"))).name,
            csv_filename=Path(str(output.get("csv_filename", "jira_tickets.csv"))).name,
        ),
    )
