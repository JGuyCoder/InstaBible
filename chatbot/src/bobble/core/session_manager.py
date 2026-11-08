
from uuid import uuid4

from bobble.core.chat_service import ChatService
from bobble.providers.base import BaseProvider
from bobble.providers.gemini import GeminiProvider


class SessionManager:
    """
    Creates and manages independent Bobble conversations.
    """

    def __init__(self, provider: BaseProvider | None = None):
        # One shared provider connection for all sessions.
        self.provider = provider if provider is not None else GeminiProvider()

        # Maps session IDs to individual ChatService instances.
        self.sessions: dict[str, ChatService] = {}

    def create_session(self) -> str:
        """Create a new conversation and return its unique ID."""

        session_id = str(uuid4())

        self.sessions[session_id] = ChatService(
            provider=self.provider
        )

        return session_id

    def get_session(self, session_id: str) -> ChatService:
        """Retrieve a conversation using its session ID."""

        if session_id not in self.sessions:
            raise KeyError(f"Session not found: {session_id}")

        return self.sessions[session_id]

    async def send_message(self, session_id: str, message: str) -> str:
        """Send a message to the specified conversation."""

        conversation = self.get_session(session_id)

        return await conversation.send_message(message)

    def reset_session(self, session_id: str):
        """Clear the history of one conversation."""

        conversation = self.get_session(session_id)
        conversation.reset_conversation()

    def delete_session(self, session_id: str):
        """Remove one conversation from memory."""

        if session_id not in self.sessions:
            raise KeyError(f"Session not found: {session_id}")

        del self.sessions[session_id]

    def session_count(self) -> int:
        """Return the number of active sessions."""

        return len(self.sessions)

    async def close(self):
        """Close the shared provider connection."""

        await self.provider.close()
        self.sessions.clear()
