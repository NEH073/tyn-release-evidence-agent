
import json

import pytest
import requests

import jira_tools


@pytest.fixture(autouse=True)
def configure_test_jira(monkeypatch):
    """Provide isolated Jira configuration for every test."""

    monkeypatch.setattr(
        jira_tools,
        "JIRA_BASE_URL",
        "https://example.atlassian.net",
    )
    monkeypatch.setattr(
        jira_tools,
        "JIRA_PROJECT_KEY",
        "TYN",
    )
    monkeypatch.setattr(
        jira_tools,
        "DATASET_LABEL",
        "tyn-release-assessment-v2",
    )
    monkeypatch.setattr(
        jira_tools,
        "JIRA_AUTH",
        ("test@example.com", "test-token"),
    )


def test_configure_jira_scope():
    jira_tools.configure_jira_scope(
        "abc",
        "test-dataset",
    )

    assert jira_tools.JIRA_PROJECT_KEY == "ABC"
    assert jira_tools.DATASET_LABEL == "test-dataset"


def test_configure_jira_scope_rejects_empty_values():
    with pytest.raises(ValueError):
        jira_tools.configure_jira_scope(
            "",
            "test-dataset",
        )


def test_adf_to_text():
    document = {
        "type": "doc",
        "content": [
            {
                "type": "paragraph",
                "content": [
                    {
                        "type": "text",
                        "text": "Release evidence",
                    }
                ],
            },
            {
                "type": "paragraph",
                "content": [
                    {
                        "type": "text",
                        "text": "Production approved",
                    }
                ],
            },
        ],
    }

    result = jira_tools.adf_to_text(document)

    assert result == "Release evidence\nProduction approved\n"


def test_get_jira_issue_returns_issue_and_comments(monkeypatch):

    def fake_jira_get(path, params=None):

        if path == "/rest/api/3/issue/TYN-186":
            return {
                "fields": {
                    "summary": "Production verification",
                    "description": {
                        "type": "doc",
                        "content": [
                            {
                                "type": "paragraph",
                                "content": [
                                    {
                                        "type": "text",
                                        "text": "Verification completed",
                                    }
                                ],
                            }
                        ],
                    },
                    "status": {
                        "name": "Done",
                    },
                    "issuetype": {
                        "name": "Task",
                    },
                    "labels": [
                        "tyn-release-assessment-v2",
                    ],
                    "issuelinks": [
                        {
                            "type": {
                                "name": "Relates",
                            },
                            "outwardIssue": {
                                "key": "TYN-187",
                            },
                        }
                    ],
                }
            }

        if path == "/rest/api/3/issue/TYN-186/comment":
            return {
                "total": 1,
                "comments": [
                    {
                        "body": {
                            "type": "doc",
                            "content": [
                                {
                                    "type": "paragraph",
                                    "content": [
                                        {
                                            "type": "text",
                                            "text": "Production test passed",
                                        }
                                    ],
                                }
                            ],
                        },
                        "author": {
                            "displayName": "Test Engineer",
                        },
                        "created": "2026-11-01T10:00:00.000+0000",
                    }
                ],
            }

        raise AssertionError(f"Unexpected Jira API path: {path}")

    monkeypatch.setattr(
        jira_tools,
        "jira_get",
        fake_jira_get,
    )

    raw = jira_tools.get_jira_issue.invoke(
        {"issue_key": "TYN-186"}
    )

    result = json.loads(raw)

    assert result["issue_key"] == "TYN-186"
    assert result["summary"] == "Production verification"
    assert result["status"] == "Done"
    assert result["description"] == "Verification completed"
    assert len(result["comments"]) == 1
    assert result["comments"][0]["body"] == "Production test passed"
    assert "jira_author" not in result["comments"][0]
    assert result["linked_issues"][0]["issue_key"] == "TYN-187"


def test_get_jira_issue_rejects_other_project(monkeypatch):

    def unexpected_call(*args, **kwargs):
        raise AssertionError("Jira API must not be called")

    monkeypatch.setattr(
        jira_tools,
        "jira_get",
        unexpected_call,
    )

    result = jira_tools.get_jira_issue.invoke(
        {"issue_key": "OTHER-123"}
    )

    assert result.startswith("Rejected:")
    assert "TYN" in result


def test_get_jira_issue_rejects_wrong_dataset_label(monkeypatch):

    def fake_jira_get(path, params=None):
        return {
            "fields": {
                "labels": ["another-dataset"],
            }
        }

    monkeypatch.setattr(
        jira_tools,
        "jira_get",
        fake_jira_get,
    )

    result = jira_tools.get_jira_issue.invoke(
        {"issue_key": "TYN-186"}
    )

    assert result.startswith("Rejected:")
    assert "required dataset label" in result


def test_search_jira_issues_enforces_project_and_dataset_scope(
    monkeypatch,
):

    captured = {}

    def fake_jira_get(path, params=None):
        captured["path"] = path
        captured["params"] = params

        return {
            "issues": [
                {
                    "key": "TYN-186",
                    "fields": {
                        "summary": "Valid issue",
                        "status": {
                            "name": "Done",
                        },
                        "labels": [
                            "tyn-release-assessment-v2",
                        ],
                    },
                },
                {
                    "key": "OTHER-123",
                    "fields": {
                        "summary": "Wrong project",
                        "status": {
                            "name": "Done",
                        },
                        "labels": [
                            "tyn-release-assessment-v2",
                        ],
                    },
                },
                {
                    "key": "TYN-999",
                    "fields": {
                        "summary": "Wrong dataset",
                        "status": {
                            "name": "Done",
                        },
                        "labels": [
                            "another-dataset",
                        ],
                    },
                },
            ]
        }

    monkeypatch.setattr(
        jira_tools,
        "jira_get",
        fake_jira_get,
    )

    raw = jira_tools.search_jira_issues.invoke(
        {
            "jql": "key = TYN-186 OR project = OTHER"
        }
    )

    results = json.loads(raw)

    assert captured["path"] == "/rest/api/3/search/jql"

    scoped_jql = captured["params"]["jql"]

    assert 'project = "TYN"' in scoped_jql
    assert 'labels = "tyn-release-assessment-v2"' in scoped_jql
    assert "(key = TYN-186 OR project = OTHER)" in scoped_jql

    assert len(results) == 1
    assert results[0]["issue_key"] == "TYN-186"


def test_search_jira_issues_preserves_order_by(monkeypatch):

    captured = {}

    def fake_jira_get(path, params=None):
        captured["jql"] = params["jql"]
        return {"issues": []}

    monkeypatch.setattr(
        jira_tools,
        "jira_get",
        fake_jira_get,
    )

    jira_tools.search_jira_issues.invoke(
        {
            "jql": "status = Done ORDER BY created DESC"
        }
    )

    assert 'project = "TYN"' in captured["jql"]
    assert 'labels = "tyn-release-assessment-v2"' in captured["jql"]
    assert "ORDER BY created DESC" in captured["jql"]


def test_search_jira_issues_rejects_empty_jql():

    result = jira_tools.search_jira_issues.invoke(
        {"jql": ""}
    )

    assert result.startswith("Rejected:")


# --------------------------------------------------
# Jira search pagination tests
# --------------------------------------------------

def test_search_jira_issues_retrieves_multiple_pages(
    monkeypatch,
):
    calls = []

    def make_issue(key, summary, labels=None):
        return {
            "key": key,
            "fields": {
                "summary": summary,
                "status": {
                    "name": "Done",
                },
                "labels": labels or [
                    "tyn-release-assessment-v2",
                ],
            },
        }

    def fake_jira_get(path, params=None):
        calls.append({
            "path": path,
            "params": params.copy(),
        })

        if len(calls) == 1:
            return {
                "issues": [
                    make_issue("TYN-100", "First page issue"),
                    make_issue("TYN-101", "Another first page issue"),
                    make_issue(
                        "OTHER-200",
                        "Wrong project",
                    ),
                    make_issue(
                        "TYN-102",
                        "Wrong dataset",
                        ["another-dataset"],
                    ),
                ],
                "nextPageToken": "cursor-page-2",
            }

        if len(calls) == 2:
            return {
                "issues": [
                    make_issue("TYN-103", "Second page issue"),
                ],
            }

        raise AssertionError("Unexpected extra Jira search request")

    monkeypatch.setattr(
        jira_tools,
        "jira_get",
        fake_jira_get,
    )

    raw = jira_tools.search_jira_issues.invoke(
        {"jql": "status = Done"}
    )

    results = json.loads(raw)

    # Two pages must have been retrieved.
    assert len(calls) == 2

    # Both requests must use the Jira search endpoint.
    assert all(
        call["path"] == "/rest/api/3/search/jql"
        for call in calls
    )

    # The second request must use the first page's cursor.
    assert (
        calls[1]["params"]["nextPageToken"]
        == "cursor-page-2"
    )

    # Every page must retain the same scoped JQL.
    assert (
        calls[0]["params"]["jql"]
        == calls[1]["params"]["jql"]
    )

    assert 'project = "TYN"' in calls[0]["params"]["jql"]
    assert (
        'labels = "tyn-release-assessment-v2"'
        in calls[0]["params"]["jql"]
    )

    # Every page must use the configured page size.
    assert calls[0]["params"]["maxResults"] == 100
    assert calls[1]["params"]["maxResults"] == 100

    # Wrong-project and wrong-dataset records must be filtered.
    assert [issue["issue_key"] for issue in results] == [
        "TYN-100",
        "TYN-101",
        "TYN-103",
    ]


def test_search_jira_issues_rejects_repeated_pagination_token(
    monkeypatch,
):
    call_count = 0

    def fake_jira_get(path, params=None):
        nonlocal call_count
        call_count += 1

        if call_count == 1:
            return {
                "issues": [],
                "nextPageToken": "cursor-page-2",
            }

        if call_count == 2:
            return {
                "issues": [],
                "nextPageToken": "cursor-page-2",
            }

        raise AssertionError("Unexpected extra Jira search request")

    monkeypatch.setattr(
        jira_tools,
        "jira_get",
        fake_jira_get,
    )

    raw = jira_tools.search_jira_issues.invoke(
        {"jql": "status = Done"}
    )

    assert raw.startswith("Jira search API error:")
    assert "repeated pagination token" in raw
    assert call_count == 2


def test_search_jira_issues_fails_when_page_limit_is_exceeded(
    monkeypatch,
):
    monkeypatch.setattr(
        jira_tools,
        "MAX_SEARCH_PAGES",
        2,
    )

    call_count = 0

    def fake_jira_get(path, params=None):
        nonlocal call_count
        call_count += 1

        return {
            "issues": [],
            "nextPageToken": f"cursor-{call_count + 1}",
        }

    monkeypatch.setattr(
        jira_tools,
        "jira_get",
        fake_jira_get,
    )

    raw = jira_tools.search_jira_issues.invoke(
        {"jql": "status = Done"}
    )

    assert raw.startswith("Jira search API error:")
    assert "maximum of 2 pages" in raw
    assert call_count == 2

def test_get_jira_issue_retrieves_comments_from_multiple_pages(
    monkeypatch,
):
    comment_calls = []

    def make_comment(text):
        return {
            "body": {
                "type": "doc",
                "content": [
                    {
                        "type": "paragraph",
                        "content": [
                            {
                                "type": "text",
                                "text": text,
                            }
                        ],
                    }
                ],
            },
            "author": {
                "displayName": "Test Engineer",
            },
            "created": "2026-11-01T10:00:00.000+0000",
        }

    def fake_jira_get(path, params=None):

        if path == "/rest/api/3/issue/TYN-186":
            return {
                "fields": {
                    "summary": "Comment pagination test",
                    "description": None,
                    "status": {"name": "Done"},
                    "issuetype": {"name": "Task"},
                    "labels": ["tyn-release-assessment-v2"],
                    "issuelinks": [],
                }
            }

        if path == "/rest/api/3/issue/TYN-186/comment":
            comment_calls.append(params.copy())

            if params["startAt"] == 0:
                return {
                    "total": 3,
                    "comments": [
                        make_comment("First comment"),
                        make_comment("Second comment"),
                    ],
                }

            if params["startAt"] == 2:
                return {
                    "total": 3,
                    "comments": [
                        make_comment("Third comment"),
                    ],
                }

        raise AssertionError(f"Unexpected Jira API path: {path}")

    monkeypatch.setattr(
        jira_tools,
        "jira_get",
        fake_jira_get,
    )

    raw = jira_tools.get_jira_issue.invoke(
        {"issue_key": "TYN-186"}
    )

    result = json.loads(raw)

    assert len(comment_calls) == 2
    assert comment_calls[0]["startAt"] == 0
    assert comment_calls[1]["startAt"] == 2

    assert len(result["comments"]) == 3
    assert [
        comment["body"]
        for comment in result["comments"]
    ] == [
        "First comment",
        "Second comment",
        "Third comment",
    ]


def test_get_jira_issue_rejects_incomplete_comment_pagination(
    monkeypatch,
):
    def fake_jira_get(path, params=None):

        if path == "/rest/api/3/issue/TYN-186":
            return {
                "fields": {
                    "summary": "Incomplete comment test",
                    "description": None,
                    "status": {"name": "Done"},
                    "issuetype": {"name": "Task"},
                    "labels": ["tyn-release-assessment-v2"],
                    "issuelinks": [],
                }
            }

        if path == "/rest/api/3/issue/TYN-186/comment":
            return {
                "total": 3,
                "comments": [],
            }

        raise AssertionError(f"Unexpected Jira API path: {path}")

    monkeypatch.setattr(
        jira_tools,
        "jira_get",
        fake_jira_get,
    )

    raw = jira_tools.get_jira_issue.invoke(
        {"issue_key": "TYN-186"}
    )

    assert raw.startswith("Jira API error for TYN-186:")
    assert "empty comment page" in raw
    assert "Retrieved 0 of 3" in raw
