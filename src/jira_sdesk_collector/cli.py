"""Точка входа командной строки."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import requests

from .client import JiraClient
from .config import ConfigError, load_config
from .exporters import export_csv, export_json


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="jira-sdesk-collector",
        description="Получение заявок Jira с выгрузкой в JSON и CSV.",
    )
    parser.add_argument(
        "--config",
        default="config.toml",
        help="путь к локальной конфигурации TOML (по умолчанию: config.toml)",
    )
    return parser


def run(config_path: str | Path) -> tuple[Path, Path, int]:
    config = load_config(config_path)
    issues = list(JiraClient(config.jira).iter_issues())
    json_path = config.output.directory / config.output.json_filename
    csv_path = config.output.directory / config.output.csv_filename
    export_json(issues, json_path)
    export_csv(issues, csv_path)
    return json_path, csv_path, len(issues)


def main() -> int:
    args = build_parser().parse_args()
    try:
        json_path, csv_path, count = run(args.config)
    except (ConfigError, requests.RequestException, ValueError, OSError) as error:
        print(f"Ошибка: {error}", file=sys.stderr)
        return 1
    print(f"Получено заявок: {count}")
    print(f"JSON: {json_path}")
    print(f"CSV:  {csv_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
