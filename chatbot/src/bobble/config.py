
import os
from pathlib import Path

from dotenv import load_dotenv


# Locate chatbot/.env independently of the working directory.
CHATBOT_DIR = Path(__file__).resolve().parents[2]
ENV_FILE = CHATBOT_DIR / ".env"

# Load environment variables without overwriting existing system variables.
load_dotenv(dotenv_path=ENV_FILE)


class Config:
    """Central configuration for Bobble."""

    # Gemini API credentials
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

    # Gemini model configuration
    GEMINI_MODEL = os.getenv(
        "GEMINI_MODEL",
        "gemini-3.8-flash"
    )

    @classmethod
    def require_gemini_api_key(cls) -> str:
        """Return the API key or raise an error if it is missing."""

        if not cls.GEMINI_API_KEY:
            raise ValueError(
                "GEMINI_API_KEY is missing. "
                "Check your chatbot/.env file."
            )

        return cls.GEMINI_API_KEY
