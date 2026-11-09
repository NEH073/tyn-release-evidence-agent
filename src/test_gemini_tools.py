
import sys
from pathlib import Path
from types import SimpleNamespace

# Make the nested application source importable.
sys.path.insert(
    0,
    str(Path(__file__).resolve().parent / "src"),
)

from agent import (
    content_to_text,
    get_final_answer,
    get_decision,
    serialize_messages,
    aggregate_token_usage,
    validate_assessment,
)


def test_content_to_text_with_string():
    assert content_to_text("Hello") == "Hello"


def test_content_to_text_with_text_blocks():
    content = [
        {"type": "text", "text": "First"},
        {"type": "text", "text": "Second"},
    ]

    assert content_to_text(content) == "First\nSecond"


def test_content_to_text_ignores_non_text_dictionary_blocks():
    content = [
        {"type": "text", "text": "Hello"},
        {"type": "image", "data": "ignored"},
    ]

    assert content_to_text(content) == "Hello"


def test_content_to_text_handles_mixed_blocks():
    content = [
        {"type": "text", "text": "Hello"},
        "World",
    ]

    assert content_to_text(content) == "Hello\nWorld"


def test_content_to_text_handles_none():
    assert content_to_text(None) == "None"


def test_get_final_answer_skips_tool_calls():
    messages = [
        SimpleNamespace(
            type="ai",
            tool_calls=[{"name": "search_jira_issues"}],
            content="Searching Jira",
        ),
        SimpleNamespace(
            type="tool",
            tool_calls=[],
            content="Jira result",
        ),
        SimpleNamespace(
            type="ai",
            tool_calls=[],
            content="Decision: PASS",
        ),
    ]

    assert get_final_answer(messages) == "Decision: PASS"


def test_get_final_answer_skips_empty_ai_responses():
    messages = [
        SimpleNamespace(
            type="ai",
            tool_calls=[],
            content="   ",
        ),
    ]

    assert (
        get_final_answer(messages)
        == "No final assessment was returned by the model."
    )


def test_get_decision_extracts_pass():
    assert get_decision("Decision: PASS") == "PASS"


def test_get_decision_extracts_fail_case_insensitively():
    assert get_decision("decision: fail") == "FAIL"


def test_get_decision_extracts_insufficient_evidence():
    assert (
        get_decision("Decision: INSUFFICIENT_EVIDENCE")
        == "INSUFFICIENT_EVIDENCE"
    )


def test_get_decision_defaults_to_insufficient():
    assert (
        get_decision("The evidence is unclear.")
        == "INSUFFICIENT_EVIDENCE"
    )


def test_serialize_messages_uses_model_dump():
    class MockMessage:
        def model_dump(self):
            return {
                "type": "ai",
                "content": "Decision: PASS",
            }

    result = serialize_messages([MockMessage()])

    assert result == [
        {
            "type": "ai",
            "content": "Decision: PASS",
        }
    ]


def test_serialize_messages_falls_back_to_string():
    result = serialize_messages(["plain message"])

    assert result == ["plain message"]


def test_aggregate_token_usage():
    results = [
        {
            "token_usage": [
                {
                    "input_tokens": 100,
                    "output_tokens": 20,
                    "total_tokens": 120,
                },
                {
                    "prompt_tokens": 50,
                    "completion_tokens": 10,
                    "total_tokens": 60,
                },
            ]
        },
        {
            "token_usage": [
                {
                    "input_tokens": 30,
                    "output_tokens": 5,
                    "total_tokens": 35,
                }
            ]
        },
    ]

    assert aggregate_token_usage(results) == {
        "input_tokens": 180,
        "output_tokens": 35,
        "total_tokens": 215,
        "usage_records": 3,
    }


def test_aggregate_token_usage_ignores_invalid_records():
    results = [
        {
            "token_usage": [
                None,
                "invalid",
                {
                    "input_tokens": 10,
                    "output_tokens": 2,
                    "total_tokens": 12,
                },
            ]
        }
    ]

    assert aggregate_token_usage(results) == {
        "input_tokens": 10,
        "output_tokens": 2,
        "total_tokens": 12,
        "usage_records": 1,
    }


def test_aggregate_token_usage_handles_empty_results():
    assert aggregate_token_usage([]) == {
        "input_tokens": 0,
        "output_tokens": 0,
        "total_tokens": 0,
        "usage_records": 0,
    }


# --------------------------------------------------
# Assessment validation tests
# --------------------------------------------------

VALID_MULTILINE_ASSESSMENT = """
Requirement ID: REQ-01

Requirement: Automated regression tests

Decision: PASS

Explanation:
The required regression tests completed successfully.
The recorded results meet the release criteria.

Evidence:
TYN-100 confirms the regression test execution.
TYN-101 contains the corresponding test results.

Outstanding verification:
No additional verification is outstanding.
"""


def test_validate_assessment_accepts_multiline_sections():
    result = validate_assessment(
        VALID_MULTILINE_ASSESSMENT,
        [],
    )

    assert result["valid"] is True
    assert result["decision"] == "PASS"
    assert result["problems"] == []
    assert result["tool_errors"] == []


def test_validate_assessment_rejects_missing_section():
    answer = """
Requirement ID: REQ-01
Requirement: Automated regression tests
Decision: PASS
Explanation:
Tests completed successfully.
Evidence:
TYN-100 contains the results.
"""

    result = validate_assessment(answer, [])

    assert result["valid"] is False
    assert any(
        "Missing section: Outstanding verification" in problem
        for problem in result["problems"]
    )


def test_validate_assessment_rejects_empty_section():
    answer = """
Requirement ID: REQ-01
Requirement: Automated regression tests
Decision: PASS
Explanation:
Tests completed successfully.
Evidence:
Outstanding verification:
No additional verification is outstanding.
"""

    result = validate_assessment(answer, [])

    assert result["valid"] is False
    assert any(
        "Empty section: Evidence" in problem
        for problem in result["problems"]
    )


def test_validate_assessment_rejects_invalid_decision():
    answer = """
Requirement ID: REQ-01
Requirement: Automated regression tests
Decision: MAYBE
Explanation:
The result is unclear.
Evidence:
TYN-100 contains the test results.
Outstanding verification:
Further investigation is required.
"""

    result = validate_assessment(answer, [])

    assert result["valid"] is False
    assert result["decision"] == "INSUFFICIENT_EVIDENCE"
    assert any(
        "Missing or invalid structured decision" in problem
        for problem in result["problems"]
    )


def test_validate_assessment_rejects_jira_tool_error():
    messages = [
        SimpleNamespace(
            type="tool",
            name="get_jira_issue",
            content="Jira API error for TYN-100: Request timed out",
        )
    ]

    result = validate_assessment(
        VALID_MULTILINE_ASSESSMENT,
        messages,
    )

    assert result["valid"] is False
    assert len(result["tool_errors"]) == 1
    assert any(
        "Jira tool error" in problem
        for problem in result["problems"]
    )


def test_validate_assessment_accepts_insufficient_evidence():
    answer = """
Requirement ID: REQ-03
Requirement: Answer quality

Decision: INSUFFICIENT_EVIDENCE

Explanation:
The available evidence does not establish the required prompt version.

Evidence:
TYN-225 records a test using prompt version p6.

Outstanding verification:
A test using prompt version p7 is required.
"""

    result = validate_assessment(answer, [])

    assert result["valid"] is True
    assert result["decision"] == "INSUFFICIENT_EVIDENCE"
    assert result["problems"] == []
