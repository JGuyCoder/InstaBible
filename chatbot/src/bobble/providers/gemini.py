
from google import genai
from google.genai import types

from bobble.providers.base import BaseProvider
from bobble.config import Config


class GeminiProvider(BaseProvider):
    """
    Connects Bobble to Google's Gemini API.
    """

    def __init__(self):
        api_key = Config.require_gemini_api_key()

        self.model = Config.GEMINI_MODEL

        self.client = genai.Client(api_key=api_key)
        self.async_client = self.client.aio

    async def generate(
        self,
        messages: list[dict[str, str]],
        instructions: str | None = None
    ) -> str:
        """
        Generate a response using Gemini.

        Args:
            messages: Bobble's standardized conversation history.
            instructions: Optional system-level instructions.

        Returns:
            Gemini's generated text response.
        """

        if not messages:
            raise ValueError("Conversation history cannot be empty.")

        # Convert Bobble's message format into Gemini's format.
        contents = []

        for message in messages:
            role = message["role"]
            content = message["content"]

            if role == "assistant":
                role = "model"
            elif role != "user":
                raise ValueError(
                    f"Unsupported conversation role: {role}"
                )

            contents.append({
                "role": role,
                "parts": [{"text": content}]
            })

        # Apply system instructions separately from conversation history.
        config = (
            types.GenerateContentConfig(
                system_instruction=instructions
            )
            if instructions is not None
            else None
        )

        response = await self.async_client.models.generate_content(
            model=self.model,
            contents=contents,
            config=config
        )

        if response.text is None:
            raise RuntimeError("Gemini returned an empty response.")

        return response.text

    async def close(self):
        """Close the asynchronous API client."""
        await self.async_client.aclose()
