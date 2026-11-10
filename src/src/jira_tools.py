
import os
import re
import json
import time
import requests

from dotenv import load_dotenv
from langchain_core.tools import tool

load_dotenv(".env")

JIRA_BASE_URL = os.getenv("JIRA_BASE_URL", "").rstrip("/")
JIRA_PROJECT_KEY = os.getenv("JIRA_PROJECT_KEY", "TYN")
DATASET_LABEL = os.getenv(
    "DATASET_LABEL",
    "tyn-release-assessment-v2",
)

JIRA_AUTH = (
    os.getenv("JIRA_EMAIL"),
    os.getenv("JIRA_API_TOKEN"),
)

SESSION = requests.Session()
SESSION.auth = JIRA_AUTH
SESSION.headers.update({"Accept": "application/json"})

SEARCH_PAGE_SIZE = 100
MAX_SEARCH_PAGES = 20


def configure_jira_scope(project_key: str, dataset_label: str):
    """Configure the Jira project and dataset boundary for this run."""
    global JIRA_PROJECT_KEY, DATASET_LABEL

    project_key = project_key.strip().upper()
    dataset_label = dataset_label.strip()

    if not project_key or not dataset_label:
        raise ValueError("Project key and dataset label are required.")

    JIRA_PROJECT_KEY = project_key
    DATASET_LABEL = dataset_label


def adf_to_text(node):
    """Convert Jira's Atlassian Document Format into readable text."""
    if isinstance(node, str):
        return node

    if isinstance(node, list):
        return "".join(adf_to_text(item) for item in node)

    if not isinstance(node, dict):
        return ""

    text = node.get("text", "")
    children = adf_to_text(node.get("content", []))

    if node.get("type") in ("paragraph", "heading"):
        return text + children + "\n"

    if node.get("type") == "hardBreak":
        return "\n"

    return text + children


def jira_get(path, params=None):
    """GET Jira data with bounded retries for transient failures."""
    max_attempts = 4

    for attempt in range(max_attempts):
        try:
            response = SESSION.get(
                f"{JIRA_BASE_URL}{path}",
                params=params,
                timeout=30,
            )

            if response.status_code == 429 or response.status_code >= 500:
                if attempt == max_attempts - 1:
                    response.raise_for_status()

                retry_after = response.headers.get("Retry-After")

                try:
                    delay = (
                        float(retry_after)
                        if retry_after
                        else 2 ** attempt
                    )
                except (ValueError, TypeError):
                    delay = 2 ** attempt

                time.sleep(min(delay, 30))
                continue

            response.raise_for_status()
            return response.json()

        except (requests.Timeout, requests.ConnectionError):
            if attempt == max_attempts - 1:
                raise

            time.sleep(min(2 ** attempt, 30))

    raise requests.RequestException(
        f"Jira request failed after {max_attempts} attempts."
    )


@tool
def get_jira_issue(issue_key: str) -> str:
    """
    Retrieve a dataset issue from the configured Jira project,
    including its description, status, labels, all comments
    and linked issue references.
    """
    if not JIRA_BASE_URL or not all(JIRA_AUTH):
        return "Error: Jira credentials or JIRA_BASE_URL are missing."

    issue_key = issue_key.strip().upper()

    if not issue_key.startswith(f"{JIRA_PROJECT_KEY}-"):
        return (
            f"Rejected: issue must belong to project "
            f"{JIRA_PROJECT_KEY}."
        )

    try:
        issue = jira_get(
            f"/rest/api/3/issue/{issue_key}",
            params={
                "fields": (
                    "summary,description,status,labels,"
                    "issuetype,issuelinks"
                ),
            },
        )

        fields = issue.get("fields", {})
        labels = fields.get("labels", [])

        if DATASET_LABEL not in labels:
            return (
                f"Rejected: {issue_key} does not have the required "
                f"dataset label {DATASET_LABEL}."
            )

        # Retrieve every comment page.
        comments = []
        start_at = 0
        page_size = 100

        while True:
            page = jira_get(
                f"/rest/api/3/issue/{issue_key}/comment",
                params={
                    "startAt": start_at,
                    "maxResults": page_size,
                    "orderBy": "created",
                },
            )

            page_comments = page.get("comments", [])

            for comment in page_comments:
                comments.append({
                    "body": adf_to_text(
                        comment.get("body", {})
                    ).strip(),
                })

            total_comments = page.get("total")

            if not page_comments:
                if (
                    total_comments is not None
                    and start_at < total_comments
                ):
                    raise requests.RequestException(
                        f"Jira returned an empty comment page for "
                        f"{issue_key} before all comments were retrieved. "
                        f"Retrieved {start_at} of {total_comments}."
                    )

                break

            start_at += len(page_comments)

            if (
                total_comments is not None
                and start_at >= total_comments
            ):
                break

        # Extract linked issues.
        links = []

        for link in fields.get("issuelinks", []):
            linked_issue = (
                link.get("outwardIssue")
                or link.get("inwardIssue")
                or {}
            )

            links.append({
                "issue_key": linked_issue.get("key"),
                "relationship": link.get("type", {}).get("name"),
            })

        result = {
            "issue_key": issue_key,
            "summary": fields.get("summary"),
            "description": adf_to_text(
                fields.get("description", {})
            ).strip(),
            "status": fields.get("status", {}).get("name"),
            "issue_type": fields.get("issuetype", {}).get("name"),
            "labels": labels,
            "comments": comments,
            "linked_issues": links,
        }

        return json.dumps(
            result,
            indent=2,
            ensure_ascii=False,
        )

    except requests.RequestException as exc:
        return f"Jira API error for {issue_key}: {exc}"

    except (KeyError, TypeError, ValueError) as exc:
        return f"Error processing Jira issue {issue_key}: {exc}"


@tool
def search_jira_issues(jql: str) -> str:
    """
    Search Jira issues within the configured project and dataset only.

    The supplied JQL is treated as an additional filter.
    Project and dataset restrictions are always enforced.
    All result pages are retrieved using Jira's nextPageToken.
    """
    if not JIRA_BASE_URL or not all(JIRA_AUTH):
        return "Error: Jira credentials or JIRA_BASE_URL are missing."

    try:
        user_jql = jql.strip()

        if not user_jql:
            return "Rejected: an additional JQL filter is required."

        # Preserve an optional ORDER BY clause.
        order_match = re.search(
            r"\bORDER\s+BY\b",
            user_jql,
            flags=re.IGNORECASE,
        )

        order_clause = ""

        if order_match:
            order_clause = user_jql[order_match.start():].strip()
            user_jql = user_jql[:order_match.start()].strip()

        # Enforce project and dataset restrictions.
        scoped_jql = (
            f'project = "{JIRA_PROJECT_KEY}" '
            f'AND labels = "{DATASET_LABEL}" '
            f'AND ({user_jql})'
        )

        if order_clause:
            scoped_jql += f" {order_clause}"

        issues = []
        next_page_token = None
        seen_tokens = set()

        # Retrieve all pages, subject to a bounded page limit.
        for page_number in range(MAX_SEARCH_PAGES):

            params = {
                "jql": scoped_jql,
                "fields": (
                    "summary,description,status,labels,issuelinks"
                ),
                "maxResults": SEARCH_PAGE_SIZE,
            }

            if next_page_token:
                params["nextPageToken"] = next_page_token

            result = jira_get(
                "/rest/api/3/search/jql",
                params=params,
            )

            for issue in result.get("issues", []):
                fields = issue.get("fields", {})
                labels = fields.get("labels", [])

                # Defence in depth: verify every returned issue.
                if (
                    not issue.get("key", "").startswith(
                        f"{JIRA_PROJECT_KEY}-"
                    )
                    or DATASET_LABEL not in labels
                ):
                    continue

                issues.append({
                    "issue_key": issue.get("key"),
                    "summary": fields.get("summary"),
                    "status": fields.get("status", {}).get("name"),
                    "labels": labels,
                })

            next_page_token = result.get("nextPageToken")

            if not next_page_token:
                break

            if next_page_token in seen_tokens:
                raise requests.RequestException(
                    "Jira returned a repeated pagination token."
                )

            seen_tokens.add(next_page_token)

        else:
            # Never silently report an incomplete search.
            if next_page_token:
                raise requests.RequestException(
                    f"Jira search exceeded the maximum of "
                    f"{MAX_SEARCH_PAGES} pages. Results may be incomplete."
                )

        return json.dumps(
            issues,
            indent=2,
            ensure_ascii=False,
        )

    except requests.RequestException as exc:
        return f"Jira search API error: {exc}"
