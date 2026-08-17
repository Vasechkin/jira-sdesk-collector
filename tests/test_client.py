from __future__ import annotations

import requests
import responses

from jira_sdesk_collector.client import JiraClient
from jira_sdesk_collector.config import JiraConfig


def make_config() -> JiraConfig:
    return JiraConfig(
        base_url="https://jira.example.invalid",
        api_path="/rest/api/2",
        token="test-token",
        proxy=None,
        verify=True,
        timeout_seconds=10,
        page_size=2,
        jql="project = EXAMPLE",
        fields=("summary",),
    )


@responses.activate
def test_iter_issues_paginates_and_uses_bearer_auth() -> None:
    endpoint = "https://jira.example.invalid/rest/api/2/search"
    responses.get(endpoint, json={"total": 3, "issues": [{"key": "EX-1"}, {"key": "EX-2"}]})
    responses.get(endpoint, json={"total": 3, "issues": [{"key": "EX-3"}]})

    issues = list(JiraClient(make_config(), requests.Session()).iter_issues())

    assert [issue["key"] for issue in issues] == ["EX-1", "EX-2", "EX-3"]
    assert responses.calls[0].request.headers["Authorization"] == "Bearer test-token"
    assert "startAt=2" in responses.calls[1].request.url


def test_configured_proxy_is_used_for_both_protocols() -> None:
    config = make_config()
    config = JiraConfig(**{**config.__dict__, "proxy": "http://proxy.example.invalid:3128"})

    client = JiraClient(config)

    assert client.session.trust_env is False
    assert client.session.proxies == {
        "http": "http://proxy.example.invalid:3128",
        "https": "http://proxy.example.invalid:3128",
    }
