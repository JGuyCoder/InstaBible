
import pytest

from bobble.core.session_manager import SessionManager


class FakeProvider:
    """Simulates one shared AI provider."""

    def __init__(self):
        self.requests = []
        self.closed = False

    async def generate(self, messages, instructions=None):
        self.requests.append({
            "messages": messages,
            "instructions": instructions
        })

        return f"Reply {len(self.requests)}"

    async def close(self):
        self.closed = True


def test_create_unique_sessions():
    provider = FakeProvider()
    manager = SessionManager(provider=provider)

    session_a = manager.create_session()
    session_b = manager.create_session()

    assert session_a != session_b
    assert manager.session_count() == 2


def test_retrieve_session():
    manager = SessionManager(provider=FakeProvider())

    session_id = manager.create_session()

    assert manager.get_session(session_id) is not None


def test_unknown_session_is_rejected():
    manager = SessionManager(provider=FakeProvider())

    with pytest.raises(KeyError):
        manager.get_session("invalid-session-id")


@pytest.mark.asyncio
async def test_message_routing():
    provider = FakeProvider()
    manager = SessionManager(provider=provider)

    session_id = manager.create_session()

    response = await manager.send_message(
        session_id,
        "Hello Bobble!"
    )

    assert response == "Reply 1"
    assert len(provider.requests) == 1
    assert provider.requests[0]["messages"][0]["content"] == "Hello Bobble!"


@pytest.mark.asyncio
async def test_sessions_are_isolated():
    provider = FakeProvider()
    manager = SessionManager(provider=provider)

    session_a = manager.create_session()
    session_b = manager.create_session()

    await manager.send_message(session_a, "Message from A")
    await manager.send_message(session_b, "Message from B")
    await manager.send_message(session_a, "Another message from A")

    history_a = manager.get_session(session_a).get_history()
    history_b = manager.get_session(session_b).get_history()

    assert len(history_a) == 4
    assert len(history_b) == 2

    assert history_a[0]["content"] == "Message from A"
    assert history_b[0]["content"] == "Message from B"

    # Both sessions use the same provider instance.
    assert manager.get_session(session_a).provider is provider
    assert manager.get_session(session_b).provider is provider


def test_reset_session():
    manager = SessionManager(provider=FakeProvider())

    session_id = manager.create_session()
    manager.reset_session(session_id)

    assert manager.get_session(session_id).get_history() == []


def test_delete_session():
    manager = SessionManager(provider=FakeProvider())

    session_id = manager.create_session()
    manager.delete_session(session_id)

    assert manager.session_count() == 0

    with pytest.raises(KeyError):
        manager.get_session(session_id)


@pytest.mark.asyncio
async def test_close_manager():
    provider = FakeProvider()
    manager = SessionManager(provider=provider)

    manager.create_session()
    manager.create_session()

    await manager.close()

    assert provider.closed is True
    assert manager.session_count() == 0
