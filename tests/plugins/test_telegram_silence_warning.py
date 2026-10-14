"""Silence warnings from peer bots must not remove a human's reply obligation."""

from types import SimpleNamespace

import pytest
from telegram import Update

from gateway.config import PlatformConfig
from gateway.platforms.base import MessageType
from plugins.platforms.telegram.adapter import TelegramAdapter


def _event(text, *, is_bot, caption=False):
    adapter = TelegramAdapter(
        PlatformConfig(
            enabled=True,
            token="999:offline-fixture",
            extra={"free_response_chats": ["-10042"], "allowed_topics": [], "mention_patterns": ["wake"]},
        )
    )
    adapter._bot = SimpleNamespace(id=999, username="fixturebot")
    message = {
        "message_id": 1,
        "date": 1791955140,
        "chat": {"id": -10042, "type": "supergroup", "title": "Fixture"},
        "from": {"id": 123, "is_bot": is_bot, "first_name": "Fixture"},
        "caption" if caption else "text": text,
        "caption_entities" if caption else "entities": [
            {"type": "mention", "offset": 0, "length": 11}
        ],
    }
    update = Update.de_json({"update_id": 1, "message": message}, None)
    return adapter._build_message_event(update.message, MessageType.TEXT, 1)


@pytest.mark.parametrize(
    "text",
    [
        "@fixturebot returned only a silence marker",
        "@fixturebot 只返回了静默标记",
    ],
)
def test_peer_bot_warning_does_not_restart_a_required_reply_loop(text):
    assert _event(text, is_bot=True).reply_expected is False


@pytest.mark.parametrize("caption", [False, True])
@pytest.mark.parametrize(
    "text",
    [
        "@fixturebot please explain",
        "@fixturebot why does it say returned only a silence marker?",
        "@fixturebot explain 只返回了静默标记",
    ],
)
def test_explicit_human_question_requires_a_reply_even_when_quoting_warning(text, caption):
    assert _event(text, is_bot=False, caption=caption).reply_expected is True


@pytest.mark.parametrize(
    "text,is_bot,expected",
    [("wake explain", False, True), ("wake peer chatter", True, False),
     ("@fixturebot explain", True, True)],
)
def test_keyword_wakeups_are_human_scoped_but_direct_peer_mentions_still_work(text, is_bot, expected):
    assert _event(text, is_bot=is_bot).reply_expected is expected
