
from bobble.core.conversation import Conversation
from bobble.core.prompt_manager import PromptManager
from bobble.providers.base import BaseProvider
from bobble.providers.gemini import GeminiProvider


class ChatService:
    """
    Coordinates Bobble's conversation, instructions, and AI provider.
    """

    def __init__(self, provider: BaseProvider | None = None):
        self.conversation = Conversation()
        self.provider = provider if provider is not None else GeminiProvider()

    async def send_message(self, user_message: str) -> str:
        """
        Send a user message and return Bobble's response.

        The conversation history is updated only after a successful
        response from the provider.
        """

        if not user_message or not user_message.strip():
            raise ValueError("Message cannot be empty.")

        user_message = user_message.strip()

        # Build the history that will be sent to Gemini.
        messages = self.conversation.get_history()
        messages.append({
            "role": "user",
            "content": user_message
        })

        # Generate Bobble's response.
        response = await self.provider.generate(
            messages=messages,
            instructions=PromptManager.get_instructions()
        )

        if not response or not response.strip():
            raise RuntimeError("The AI provider returned an empty response.")

        response = response.strip()

        # Save both messages after successful generation.
        self.conversation.add_message("user", user_message)
        self.conversation.add_message("assistant", response)

        return response

    def get_history(self) -> list[dict[str, str]]:
        """Return the current conversation history."""

        return self.conversation.get_history()

    def reset_conversation(self):
        """Start a fresh conversation."""

        self.conversation.clear()

    async def close(self):
        """Close the AI provider connection."""

        await self.provider.close()
