
from abc import ABC, abstractmethod


class BaseProvider(ABC):
    """
    Abstract interface that every AI provider must implement.
    """

    @abstractmethod
    async def generate(
        self,
        messages: list[dict[str, str]],
        instructions: str | None = None
    ) -> str:
        """
        Generate a response using the provider.

        Args:
            messages: Conversation history in Bobble's standard format.
            instructions: Optional system-level instructions.

        Returns:
            The provider's generated response as a string.
        """
        pass
