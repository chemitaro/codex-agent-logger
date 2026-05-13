import json

from codex_logger.internal_turn_filter import should_skip_telegram


def test_title_generation_payload_is_skipped() -> None:
    payload = {
        "input-messages": [
            "Generate a concise UI title for this task. Fill the structured title field."
        ],
        "last-assistant-message": json.dumps({"title": "defaultサブエージェント確認"}),
    }

    decision = should_skip_telegram(payload)

    assert decision.skip is True
    assert decision.rule_name == "desktop-title-generation"


def test_commit_message_generation_payload_is_skipped() -> None:
    payload = {
        "input-messages": [
            "Using the current thread context, generate a single-line git commit message. "
            "Write the result into the structured response field message."
        ],
        "last-assistant-message": json.dumps({"message": "Fix notification config"}),
    }

    decision = should_skip_telegram(payload)

    assert decision.skip is True
    assert decision.rule_name == "commit-message-generation"


def test_suggestions_generation_payload_is_skipped() -> None:
    payload = {
        "input-messages": [
            "Generate 0 to 3 hyperpersonalized suggestions for what this user can "
            "do with Codex in this local project. Return 0 to 3 fresh suggestions."
        ],
        "last-assistant-message": json.dumps(
            {
                "suggestions": [
                    {
                        "title": "Prepare a pinned uvx release",
                        "description": "Make the local notify helper releasable.",
                        "prompt": "Prepare the release.",
                        "appId": "local-project",
                    }
                ]
            }
        ),
    }

    decision = should_skip_telegram(payload)

    assert decision.skip is True
    assert decision.rule_name == "suggestions-generation"


def test_suggestions_exclude_payload_is_skipped() -> None:
    payload = {
        "input-messages": [
            "Avoid repeating these previously dismissed suggestions. "
            "Return the exclude list for the suggestion generator."
        ],
        "last-assistant-message": json.dumps({"exclude": []}),
    }

    decision = should_skip_telegram(payload)

    assert decision.skip is True
    assert decision.rule_name == "suggestions-exclude-generation"


def test_normal_json_response_without_internal_marker_is_not_skipped() -> None:
    payload = {
        "input-messages": ["Return the response as JSON."],
        "last-assistant-message": json.dumps({"title": "User requested title"}),
    }

    assert should_skip_telegram(payload).skip is False


def test_normal_suggestions_json_without_internal_marker_is_not_skipped() -> None:
    payload = {
        "input-messages": ["Return the response as JSON."],
        "last-assistant-message": json.dumps({"suggestions": [{"title": "User requested"}]}),
    }

    assert should_skip_telegram(payload).skip is False


def test_normal_exclude_json_without_internal_marker_is_not_skipped() -> None:
    payload = {
        "input-messages": ["Return the response as JSON."],
        "last-assistant-message": json.dumps({"exclude": []}),
    }

    assert should_skip_telegram(payload).skip is False


def test_internal_marker_with_normal_assistant_message_is_not_skipped() -> None:
    payload = {
        "input-messages": ["Generate a concise UI title for this task."],
        "last-assistant-message": "The title is ready.",
    }

    assert should_skip_telegram(payload).skip is False


def test_malformed_assistant_json_is_not_skipped() -> None:
    payload = {
        "input-messages": ["Generate a concise UI title for this task."],
        "last-assistant-message": '{"title":',
    }

    assert should_skip_telegram(payload).skip is False
