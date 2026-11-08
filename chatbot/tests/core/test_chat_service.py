
import pytest

from bobble.core.chat_service import ChatService


class FakeProvider:
    """Simulates an AI provider without making API calls."""

    def __init__(self):
        self.received_messages = None
        self.received_instructions = None
        self.closed = False
        self.should_fail = False

    async def generate(self, messages, instructions=None):
        self.received_messages = messages
        self.received_instructions = instructions

        if self.should_fail:
            raise RuntimeError("Simulated provider failure")

        return "Hello! I am Bobble."

    async def close(self):
        self.closed = True


@pytest.mark.asyncio
async def test_send_message():
    provider = FakeProvider()
    service = ChatService(provider=provider)

    response = await service.send_message("Hello Bobble!")

    assert response == "Hello! I am Bobble."

    history = service.get_history()

    assert len(history) == 2
    assert history[0]["role"] == "user"
    assert history[0]["content"] == "Hello Bobble!"
    assert history[1]["role"] == "assistant"

    assert provider.received_instructions is not None


@pytest.mark.asyncio
async def test_conversation_context_is_preserved():
    provider = FakeProvider()
    service = ChatService(provider=provider)

    await service.send_message("First message")
    await service.send_message("Second message")

    assert len(provider.received_messages) == 3
    assert provider.received_messages[0]["content"] == "First message"
    assert provider.received_messages[1]["content"] == "Hello! I am Bobble."
    assert provider.received_messages[2]["content"] == "Second message"


@pytest.mark.asyncio
async def test_empty_message_is_rejected():
    service = ChatService(provider=FakeProvider())

    with pytest.raises(ValueError):
        await service.send_message("   ")

    assert service.get_history() == []


@pytest.mark.asyncio
async def test_failed_generation_does_not_update_history():
    provider = FakeProvider()
    provider.should_fail = True

    service = ChatService(provider=provider)

    with pytest.raises(RuntimeError):
        await service.send_message("Hello!")

    assert service.get_history() == []


@pytest.mark.asyncio
async def test_reset_conversation():
    service = ChatService(provider=FakeProvider())

    await service.send_message("Hello!")
    service.reset_conversation()

    assert service.get_history() == []


@pytest.mark.asyncio
async def test_close_provider():
    provider = FakeProvider()
    service = ChatService(provider=provider)

    await service.close()

    assert provider.closed is True
