import import_jira


def test_to_adf_wraps_text_in_paragraph():
    assert import_jira.to_adf("Release approved") == {
        "type": "doc",
        "version": 1,
        "content": [
            {
                "type": "paragraph",
                "content": [
                    {"type": "text", "text": "Release approved"}
                ],
            }
        ],
    }


def test_adf_text_extracts_nested_text():
    document = {
        "type": "doc",
        "content": [
            {
                "type": "paragraph",
                "content": [
                    {"type": "text", "text": "First "},
                    {
                        "type": "text",
                        "text": "line",
                    },
                ],
            },
            {
                "type": "paragraph",
                "content": [{"type": "text", "text": "Second"}],
            },
        ],
    }

    assert import_jira.adf_text(document) == "First lineSecond"


def test_create_issue_sends_dataset_label_and_source_id(monkeypatch):
    captured = {}

    class FakeResponse:
        def json(self):
            return {"key": "TYN-101"}

    def fake_api(method, path, **kwargs):
        captured.update(method=method, path=path, **kwargs)
        return FakeResponse()

    monkeypatch.setattr(import_jira, "api", fake_api)
    monkeypatch.setattr(import_jira, "PROJECT_KEY", "TYN")
    monkeypatch.setattr(import_jira, "DATASET_LABEL", "dataset-v2")

    key = import_jira.create_issue({
        "source_id": "SRC-1",
        "kind": "requirement",
        "release": "R2.4",
        "recorded_status": "Open",
        "summary": "Validate deployment",
        "description": "Deployment evidence",
    })

    assert key == "TYN-101"
    assert captured["method"] == "POST"
    assert captured["path"] == "/rest/api/3/issue"
    fields = captured["json"]["fields"]
    assert fields["project"] == {"key": "TYN"}
    assert fields["summary"] == "[SRC-1] Validate deployment"
    assert fields["labels"] == ["dataset-v2"]
    assert "Source ID: SRC-1" in fields["description"]["content"][0]["content"][0]["text"]


def test_get_all_comments_retrieves_multiple_pages(monkeypatch):
    calls = []

    def fake_api(method, path, **kwargs):
        calls.append(kwargs["params"]["startAt"])
        if len(calls) == 1:
            return FakeResponse({
                "total": 3,
                "comments": [{"id": "1"}, {"id": "2"}],
            })
        return FakeResponse({
            "total": 3,
            "comments": [{"id": "3"}],
        })

    class FakeResponse:
        def __init__(self, payload):
            self.payload = payload

        def json(self):
            return self.payload

    monkeypatch.setattr(import_jira, "api", fake_api)

    comments = import_jira.get_all_comments("TYN-101")

    assert [comment["id"] for comment in comments] == ["1", "2", "3"]
    assert calls == [0, 2]


def test_import_comments_adds_only_missing_source_markers(monkeypatch):
    posted = []

    def fake_api(method, path, **kwargs):
        if method == "GET":
            return FakeResponse({
                "total": 1,
                "comments": [
                    {"body": import_jira.to_adf("Existing comment\n\n[SOURCE_COMMENT:SRC-1:1]")}
                ],
            })
        posted.append(kwargs["json"]["body"])
        return FakeResponse({})

    class FakeResponse:
        def __init__(self, payload):
            self.payload = payload

        def json(self):
            return self.payload

    monkeypatch.setattr(import_jira, "api", fake_api)

    added = import_jira.import_comments(
        {
            "source_id": "SRC-1",
            "comments": ["Existing comment", "New comment"],
        },
        "TYN-101",
    )

    assert added == 1
    assert len(posted) == 1
    assert import_jira.adf_text(posted[0]) == (
        "New comment\n\n[SOURCE_COMMENT:SRC-1:2]"
    )


def test_import_links_deduplicates_reciprocal_source_pairs(monkeypatch):
    calls = []

    def fake_api(method, path, **kwargs):
        calls.append((method, path, kwargs))
        if method == "GET":
            return FakeResponse({"fields": {"issuelinks": []}})
        return FakeResponse({})

    class FakeResponse:
        def __init__(self, payload):
            self.payload = payload

        def json(self):
            return self.payload

    monkeypatch.setattr(import_jira, "api", fake_api)

    import_jira.import_links(
        [
            {"source_id": "SRC-1", "links": ["SRC-2"]},
            {"source_id": "SRC-2", "links": ["SRC-1"]},
        ],
        {"SRC-1": "TYN-101", "SRC-2": "TYN-102"},
    )

    creates = [call for call in calls if call[0] == "POST"]
    assert len(creates) == 1
    assert creates[0][1] == "/rest/api/3/issueLink"


def test_import_links_skips_existing_relationship(monkeypatch):
    calls = []

    def fake_api(method, path, **kwargs):
        calls.append((method, path))
        if method == "GET":
            return FakeResponse({
                "fields": {
                    "issuelinks": [
                        {"outwardIssue": {"key": "TYN-102"}}
                    ]
                }
            })
        return FakeResponse({})

    class FakeResponse:
        def __init__(self, payload):
            self.payload = payload

        def json(self):
            return self.payload

    monkeypatch.setattr(import_jira, "api", fake_api)

    import_jira.import_links(
        [{"source_id": "SRC-1", "links": ["SRC-2"]}],
        {"SRC-1": "TYN-101", "SRC-2": "TYN-102"},
    )

    assert calls == [("GET", "/rest/api/3/issue/TYN-101")]
