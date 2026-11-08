
import pytest

from bobble.core.conversation import Conversation


def test_add_messages():
    conversation = Conversation()

    conversation.add_message("user", "Hello Bobble!")
    conversation.add_message("assistant", "Hello!")

    history = conversation.get_history()

    assert len(history) == 2
    assert history[0] == {
        "role": "user",
        "content": "Hello Bobble!"
    }
    assert history[1]["role"] == "assistant"


def test_reject_invalid_role():
    conversation = Conversation()

    with pytest.raises(ValueError):
        conversation.add_message("system", "Invalid role")


def test_reject_empty_message():
    conversation = Conversation()

    with pytest.raises(ValueError):
        conversation.add_message("user", "   ")


def test_clear_conversation():
    conversation = Conversation()
    conversation.add_message("user", "Hello!")

    conversation.clear()

    assert conversation.message_count() == 0
    assert conversation.get_history() == []


def test_history_is_a_copy():
    conversation = Conversation()
    conversation.add_message("user", "Hello!")

    history = conversation.get_history()
    history.clear()

    assert conversation.message_count() == 1
