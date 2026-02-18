"""
Anthropic Claude Provider
==========================

Supports:
- claude-sonnet-4-20250514, claude-opus-4-20250514 (Vision + Language)
- claude-3-5-sonnet, claude-3-opus, claude-3-haiku (Vision + Language)

API Documentation: https://docs.anthropic.com/
"""

import base64
from typing import Optional

from .base import AIProvider, ProviderConfig


class AnthropicProvider(AIProvider):
    """
    Anthropic Claude provider.
    Uses the official Anthropic SDK.
    """

    @property
    def name(self) -> str:
        return "anthropic"

    @property
    def supports_vision(self) -> bool:
        return True  # All Claude 3+ models support vision

    def _initialize_client(self) -> None:
        """Initialize Anthropic client"""
        try:
            from anthropic import Anthropic
        except ImportError:
            raise ImportError(
                "anthropic package is required for Anthropic provider. "
                "Install with: pip install anthropic"
            )

        self._client = Anthropic(api_key=self.config.api_key)

    def chat(self, prompt: str, system_prompt: str = None) -> str:
        """Generate text response using Claude language model"""
        if self._client is None:
            self._initialize_client()

        messages = [{"role": "user", "content": prompt}]

        def _call():
            kwargs = {
                "model": self.config.language_model or "claude-sonnet-4-20250514",
                "max_tokens": self.config.max_tokens,
                "messages": messages,
                "temperature": self.config.temperature,
            }
            if system_prompt:
                kwargs["system"] = system_prompt

            response = self._client.messages.create(**kwargs)
            return response.content[0].text

        return self._retry_with_backoff(_call)

    def vision(self, image_data: bytes, prompt: str,
               image_format: str = "png") -> str:
        """Generate text response from image using Claude vision model"""
        if self._client is None:
            self._initialize_client()

        # Encode image to base64
        image_base64 = base64.standard_b64encode(image_data).decode("utf-8")

        # Map format to media type
        media_type_map = {
            "png": "image/png",
            "jpg": "image/jpeg",
            "jpeg": "image/jpeg",
            "gif": "image/gif",
            "webp": "image/webp"
        }
        media_type = media_type_map.get(image_format.lower(), "image/png")

        messages = [
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": media_type,
                            "data": image_base64
                        }
                    },
                    {
                        "type": "text",
                        "text": prompt
                    }
                ]
            }
        ]

        def _call():
            response = self._client.messages.create(
                model=self.config.vision_model or "claude-sonnet-4-20250514",
                max_tokens=self.config.max_tokens,
                messages=messages,
                temperature=0.1  # Low temperature for OCR accuracy
            )
            return response.content[0].text

        return self._retry_with_backoff(_call)


def create_anthropic_provider(
    api_key: str = None,
    vision_model: str = "claude-sonnet-4-20250514",
    language_model: str = "claude-sonnet-4-20250514",
    **kwargs
) -> AnthropicProvider:
    """
    Factory function to create an Anthropic provider.

    Args:
        api_key: Anthropic API key
        vision_model: Vision model name
        language_model: Language model name
        **kwargs: Additional configuration options

    Returns:
        Configured AnthropicProvider instance
    """
    import os

    config = ProviderConfig(
        api_key=api_key or os.environ.get("ANTHROPIC_API_KEY", ""),
        vision_model=vision_model,
        language_model=language_model,
        **kwargs
    )

    return AnthropicProvider(config)
