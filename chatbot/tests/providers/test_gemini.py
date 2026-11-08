
from types import SimpleNamespace

import pytest

from bobble.config import Config
from bobble.providers import gemini


class FakeModels:
    """Simulates Gemini's asynchronous API."""

    def __init__(self):
        self.last_request = None

    async def generate_content(self, **kwargs):
        self.last_request = kwargs
        return SimpleNamespace(text="Hello from simulated Gemini!")


class FakeAsyncClient:
    def __init__(self):
        self.models = FakeModels()
        self.closed = False

    async def aclose(self):
        self.closed = True


class FakeClient:
    """Replaces the real Gemini client during testing."""

    def __init__(self, api_key):
        self.api_key = api_key
        self.aio = FakeAsyncClient()


@pytest.mark.asyncio
async def test_gemini_generation(monkeypatch):
    monkeypatch.setattr(Config, "GEMINI_API_KEY", "fake-api-key")
    monkeypatch.setattr(Config, "GEMINI_MODEL", "test-model")
    monkeypatch.setattr(gemini.genai, "Client", FakeClient)

    provider = gemini.GeminiProvider()

    messages = [
        {"role": "user", "content": "Hello!"},
        {"role": "assistant", "content": "Hi there!"},
        {"role": "user", "content": "How are you?"}
    ]

    response = await provider.generate(
        messages=messages,
        instructions="You are Bobble."
    )

    request = provider.async_client.models.last_request

    assert response == "Hello from simulated Gemini!"
    assert request["model"] == "test-model"
    assert request["contents"][0]["role"] == "user"
    assert request["contents"][1]["role"] == "model"
    assert request["contents"][2]["role"] == "user"
    assert request["config"].system_instruction == "You are Bobble."

    await provider.close()


@pytest.mark.asyncio
async def test_gemini_rejects_unsupported_roles(monkeypatch):
    monkeypatch.setattr(Config, "GEMINI_API_KEY", "fake-api-key")
    monkeypatch.setattr(gemini.genai, "Client", FakeClient)

    provider = gemini.GeminiProvider()

    messages = [
        {"role": "system", "content": "Invalid message"}
    ]

    with pytest.raises(ValueError):
        await provider.generate(messages)

    await provider.close()
