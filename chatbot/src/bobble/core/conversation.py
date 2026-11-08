
from datetime import datetime, timezone


class Conversation:
    """
    Stores and manages one Bobble conversation.
    """

    def __init__(self):
        self.messages = []
        self.created_at = datetime.now(timezone.utc)

    def add_message(self, role: str, content: str):
        """Add a user or assistant message to the conversation."""

        if role not in {"user", "assistant"}:
            raise ValueError(f"Unsupported role: {role}")

        if not content or not content.strip():
            raise ValueError("Message content cannot be empty.")

        self.messages.append({
            "role": role,
            "content": content.strip()
        })

    def get_history(self) -> list[dict[str, str]]:
        """Return a copy of the conversation history."""

        return self.messages.copy()

    def clear(self):
        """Clear the conversation history."""

        self.messages.clear()

    def message_count(self) -> int:
        """Return the number of messages."""

        return len(self.messages)
