"""
Abstract Base Class for AI Providers
=====================================

All AI provider implementations must inherit from AIProvider
and implement the required methods.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
import time


@dataclass
class ProviderConfig:
    """Configuration for an AI provider"""
    api_key: str = ""
    api_base: str = ""
    vision_model: str = ""
    language_model: str = ""
    max_tokens: int = 4096
    temperature: float = 0.7
    top_p: float = 0.9
    max_retries: int = 3
    retry_delay: float = 1.0
    extra: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Validate configuration"""
        if self.max_tokens < 1:
            self.max_tokens = 4096
        if not 0 <= self.temperature <= 2:
            self.temperature = 0.7
        if not 0 <= self.top_p <= 1:
            self.top_p = 0.9


class AIProvider(ABC):
    """
    Abstract base class for AI providers.

    All providers must implement:
    - chat(): Text-to-text generation
    - vision(): Image + text to text generation

    Optional:
    - embed(): Text embedding
    - stream_chat(): Streaming text generation
    """

    def __init__(self, config: ProviderConfig):
        self.config = config
        self._client = None

    @property
    @abstractmethod
    def name(self) -> str:
        """Provider name (e.g., 'qwen', 'gemini', 'openai')"""
        pass

    @property
    @abstractmethod
    def supports_vision(self) -> bool:
        """Whether this provider supports vision tasks"""
        pass

    @abstractmethod
    def _initialize_client(self) -> None:
        """Initialize the API client"""
        pass

    @abstractmethod
    def chat(self, prompt: str, system_prompt: str = None) -> str:
        """
        Generate text response from a prompt.

        Args:
            prompt: User prompt/question
            system_prompt: Optional system instruction

        Returns:
            Generated text response
        """
        pass

    @abstractmethod
    def vision(self, image_data: bytes, prompt: str,
               image_format: str = "png") -> str:
        """
        Generate text response from an image and prompt.

        Args:
            image_data: Raw image bytes
            prompt: Question/instruction about the image
            image_format: Image format (png, jpg, etc.)

        Returns:
            Generated text response
        """
        pass

    def _retry_with_backoff(self, func, *args, **kwargs):
        """
        Execute a function with exponential backoff retry.

        Args:
            func: Function to execute
            *args, **kwargs: Arguments to pass to the function

        Returns:
            Function result

        Raises:
            Exception: If all retries fail
        """
        last_exception = None

        for attempt in range(self.config.max_retries):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                last_exception = e
                if attempt < self.config.max_retries - 1:
                    wait_time = self.config.retry_delay * (2 ** attempt)
                    print(f"  Retry {attempt + 1}/{self.config.max_retries} "
                          f"after {wait_time:.1f}s: {str(e)[:50]}...")
                    time.sleep(wait_time)

        raise RuntimeError(
            f"All {self.config.max_retries} retries failed for {self.name}: "
            f"{last_exception}"
        )

    def validate(self) -> bool:
        """
        Validate that the provider is properly configured.

        Returns:
            True if configuration is valid
        """
        if not self.config.api_key and self.name != "ollama":
            print(f"Warning: No API key configured for {self.name}")
            return False
        return True

    def __repr__(self) -> str:
        return (f"{self.__class__.__name__}("
                f"vision_model={self.config.vision_model!r}, "
                f"language_model={self.config.language_model!r})")
