
import json
import os
import argparse
from pathlib import Path

import requests
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
DATASET_PATH = ROOT / "inputs" / "dataset.json"
MAPPING_PATH = ROOT / "reports" / "issue_mapping.json"

load_dotenv(ROOT / ".env")

BASE_URL = os.getenv("JIRA_BASE_URL", "").rstrip("/")
EMAIL = os.getenv("JIRA_EMAIL")
API_TOKEN = os.getenv("JIRA_API_TOKEN")
PROJECT_KEY = os.getenv("JIRA_PROJECT_KEY", "TYN")
DATASET_LABEL = "tyn-release-assessment-v2"

session = requests.Session()
session.auth = (EMAIL, API_TOKEN)
session.headers.update({
    "Accept": "application/json",
    "Content-Type": "application/json"
})


def to_adf(text):
    return {
        "type": "doc",
        "version": 1,
        "content": [{
            "type": "paragraph",
            "content": [{"type": "text", "text": text}]
        }]
    }


def api(method, path, **kwargs):
    response = session.request(
        method,
        f"{BASE_URL}{path}",
        timeout=30,
        **kwargs
    )
    if not response.ok:
        raise RuntimeError(
            f"Jira API error {response.status_code}: "
            f"{response.text[:1000]}"
        )
    return response


def load_json(path, default):
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return default


def save_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(data, indent=2),
        encoding="utf-8"
    )


def load_mapping():
    return load_json(MAPPING_PATH, {})


def create_issue(record):
    source_id = record["source_id"]

    description = (
        f"Source ID: {source_id}\n"
        f"Record kind: {record['kind']}\n"
        f"Release: {record.get('release', 'N/A')}\n"
        f"Recorded status: {record.get('recorded_status', 'N/A')}\n"
        f"Dataset label: {DATASET_LABEL}\n\n"
        f"Original description:\n{record.get('description', '')}"
    )

    payload = {
        "fields": {
            "project": {"key": PROJECT_KEY},
            "summary": f"[{source_id}] {record['summary']}",
            "issuetype": {"name": "Task"},
            "description": to_adf(description),
            "labels": [DATASET_LABEL]
        }
    }

    result = api("POST", "/rest/api/3/issue", json=payload).json()
    return result["key"]


def get_all_comments(issue_key):
    comments = []
    start_at = 0

    while True:
        data = api(
            "GET",
            f"/rest/api/3/issue/{issue_key}/comment",
            params={"startAt": start_at, "maxResults": 100}
        ).json()

        batch = data.get("comments", [])
        comments.extend(batch)

        if start_at + len(batch) >= data.get("total", 0):
            break
        if not batch:
            break

        start_at += len(batch)

    return comments


def adf_text(node):
    """Extract text recursively from Jira Atlassian Document Format."""
    if isinstance(node, dict):
        result = node.get("text", "")
        for child in node.get("content", []):
            result += adf_text(child)
        return result

    if isinstance(node, list):
        return "".join(adf_text(item) for item in node)

    return ""


def import_comments(record, issue_key):
    source_id = record["source_id"]
    existing = get_all_comments(issue_key)

    existing_text = {
        adf_text(comment.get("body", {}))
        for comment in existing
    }

    added = 0

    for index, original_comment in enumerate(
        record.get("comments", []), start=1
    ):
        marker = f"[SOURCE_COMMENT:{source_id}:{index}]"

        if any(marker in text for text in existing_text):
            continue

        body = f"{original_comment}\n\n{marker}"

        api(
            "POST",
            f"/rest/api/3/issue/{issue_key}/comment",
            json={"body": to_adf(body)}
        )

        existing_text.add(body)
        added += 1

    return added


def get_issue_links(issue_key, cache):
    if issue_key not in cache:
        data = api(
            "GET",
            f"/rest/api/3/issue/{issue_key}",
            params={"fields": "issuelinks"}
        ).json()

        linked = set()

        for link in data["fields"].get("issuelinks", []):
            if "inwardIssue" in link:
                linked.add(link["inwardIssue"]["key"])
            if "outwardIssue" in link:
                linked.add(link["outwardIssue"]["key"])

        cache[issue_key] = linked

    return cache[issue_key]


def import_links(records, mapping):
    cache = {}
    created = 0
    skipped = 0
    seen_pairs = set()

    for record in records:
        source_id = record["source_id"]

        if source_id not in mapping:
            continue

        for target_id in record.get("links", []):
            if target_id not in mapping:
                raise RuntimeError(
                    f"Missing Jira mapping for linked record {target_id}"
                )

            pair = tuple(sorted((source_id, target_id)))
            if pair in seen_pairs:
                continue
            seen_pairs.add(pair)

            source_key = mapping[source_id]
            target_key = mapping[target_id]

            existing = get_issue_links(source_key, cache)

            if target_key in existing:
                skipped += 1
                continue

            api(
                "POST",
                "/rest/api/3/issueLink",
                json={
                    "type": {"name": "Relates"},
                    "inwardIssue": {"key": source_key},
                    "outwardIssue": {"key": target_key}
                }
            )

            cache.setdefault(source_key, set()).add(target_key)
            cache.setdefault(target_key, set()).add(source_key)
            created += 1

    print(f"Links created: {created}")
    print(f"Existing links skipped: {skipped}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--limit",
        type=int,
        default=1,
        help="Number of dataset records to process"
    )
    parser.add_argument(
        "--links",
        action="store_true",
        help="Import relationships after issues and comments"
    )
    args = parser.parse_args()

    if not BASE_URL or not EMAIL or not API_TOKEN:
        raise SystemExit("Missing Jira credentials. Check .env.")

    data = load_json(DATASET_PATH, None)
    if data is None:
        raise SystemExit(f"Dataset not found: {DATASET_PATH}")

    records = data["records"][:args.limit]
    mapping = load_mapping()

    print(f"Records selected: {len(records)}")
    print(f"Existing mappings: {len(mapping)}")

    # Phase 1: create missing issues
    for record in records:
        source_id = record["source_id"]

        if source_id in mapping:
            continue

        print(f"Creating {source_id}...")
        mapping[source_id] = create_issue(record)
        save_json(MAPPING_PATH, mapping)
        print(f"  Created {mapping[source_id]}")

    # Phase 2: import comments
    total_comments = 0

    for record in records:
        issue_key = mapping[record["source_id"]]
        count = import_comments(record, issue_key)
        total_comments += count

        if count:
            print(
                f"{record['source_id']} ({issue_key}): "
                f"{count} comments imported"
            )

    print(f"\nComments imported in this run: {total_comments}")

    # Phase 3: import links only when requested
    if args.links:
        if len(mapping) < len(data["records"]):
            raise RuntimeError(
                "Not all records have Jira mappings. "
                "Run the full issue import first."
            )
        import_links(data["records"], mapping)

    print("\nImport run completed.")
    print(f"Mapping: {MAPPING_PATH}")


if __name__ == "__main__":
    main()
