"""Minimal Jira REST API client."""

from __future__ import annotations

from collections.abc import Iterator
from typing import Any

import requests

from .config import JiraConfig


class JiraClient:
    def __init__(self, config: JiraConfig, session: requests.Session | None = None) -> None:
        self.config = config
        self.session = session or requests.Session()
        # Runtime connectivity must come from the local collector config, not
        # from ambient proxy or authentication settings on the host.
        self.session.trust_env = False
        self.session.headers.update(
            {"Authorization": f"Bearer {config.token}", "Accept": "application/json"}
        )
        if config.proxy:
            self.session.proxies.update({"http": config.proxy, "https": config.proxy})

    def iter_issues(self) -> Iterator[dict[str, Any]]:
        start_at = 0
        endpoint = f"{self.config.base_url}{self.config.api_path}/search"
        while True:
            response = self.session.get(
                endpoint,
                params={
                    "jql": self.config.jql,
                    "startAt": start_at,
                    "maxResults": self.config.page_size,
                    "fields": ",".join(self.config.fields),
                },
                timeout=self.config.timeout_seconds,
                verify=self.config.verify,
            )
            response.raise_for_status()
            payload = response.json()
            issues = payload.get("issues")
            if not isinstance(issues, list):
                raise ValueError("Jira response does not contain an issues list")
            yield from issues

            start_at += len(issues)
            total = int(payload.get("total", start_at))
            if not issues or start_at >= total:
                break
