# Jira SDESK Collector

Python CLI collector that reads Jira issues through the REST API using Bearer-token authentication and an optional HTTP proxy. It writes the complete Jira issue objects to JSON and a flattened, report-friendly CSV file.

The repository contains no working endpoint, proxy, token, JQL, CA certificate, or local configuration. Runtime values live only in ignored local files.

## Requirements

- Python 3.11 or newer
- Jira personal access token with permission to search the target project
- corporate CA certificate if the Jira TLS chain is not trusted by the operating system

## Installation

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e .
```

For development and tests:

```bash
python -m pip install -e '.[dev]'
pytest
```

## Local configuration

Create local copies of both examples:

```bash
cp config.example.toml config.toml
cp .env.example .env
```

Edit `config.toml` with the real Jira base URL, REST API path, complete JQL, reporting period, proxy, TLS settings, requested fields, and output names. Put only the token in `.env` under the environment-variable name selected by `token_env`.

The sample JQL demonstrates the intended selection rule: tickets created or updated during the configured period, plus older tickets whose status category is not done. Replace the placeholder project key and adjust the query to match the local Jira workflow.

TLS behavior is controlled locally:

- set `ca_bundle` to a PEM CA bundle path for a private corporate CA;
- leave `ca_bundle` empty to use the system trust store;
- set `verify_tls = false` only for a temporary diagnostic run.

The same optional proxy is used for HTTP and HTTPS Jira requests. Leave `proxy` empty for a direct connection.

## Run

```bash
jira-sdesk-collector --config config.toml
```

The command creates the configured output directory and atomically replaces the JSON and CSV outputs. CSV is encoded as UTF-8 with BOM for convenient opening in spreadsheet applications. The process exits with status 1 on invalid configuration, transport errors, Jira HTTP errors, or malformed responses.

## Security notes

- Never commit `.env`, `config.toml`, certificates, keys, or generated exports.
- Keep `verify_tls = true` and configure `ca_bundle` for routine use.
- Give the Jira token only the permissions required to read the selected tickets.
- Review staged changes before every commit. The included `.gitignore` blocks the common local secret and output files, but it is not a substitute for review.

## Export formats

- JSON preserves each issue object returned by the Jira search endpoint.
- CSV includes common report columns: key, summary, description, status, priority, timestamps, assignee, reporter, components, labels, issue links, and security level.

Custom Jira field IDs can be added to `fields` in the local configuration. They remain present in JSON; add an explicit mapping in `issue_to_row()` if a custom field should also become a dedicated CSV column.
