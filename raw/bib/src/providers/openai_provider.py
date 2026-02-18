"""
OpenAI Provider
================

Supports:
- gpt-4o, gpt-4-turbo (Vision + Language)
- gpt-4, gpt-3.5-turbo (Language only)

API Documentation: https://platform.openai.com/docs
"""

import base64
from typing import Optional

from .base import AIProvider, ProviderConfig


class OpenAIProvider(AIProvider):
    """
    OpenAI provider using the official OpenAI API.
    """

    @property
    def name(self) -> str:
        return "openai"

    @property
    def supports_vision(self) -> bool:
        # GPT-4 Vision models support vision
        vision_models = ["gpt-4o", "gpt-4-turbo", "gpt-4-vision"]
        return any(m in self.config.vision_model.lower() for m in vision_models)

    def _initialize_client(self) -> None:
        """Initialize OpenAI client"""
        try:
            from openai import OpenAI
        except ImportError:
            raise ImportError(
                "openai package is required for OpenAI provider. "
                "Install with: pip install openai"
            )

        self._client = OpenAI(api_key=self.config.api_key)

    def chat(self, prompt: str, system_prompt: str = None) -> str:
        """Generate text response using OpenAI language model"""
        if self._client is None:
            self._initialize_client()

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        def _call():
            response = self._client.chat.completions.create(
                model=self.config.language_model or "gpt-4o",
                messages=messages,
                max_tokens=self.config.max_tokens,
                temperature=self.config.temperature,
                top_p=self.config.top_p
            )
            return response.choices[0].message.content

        return self._retry_with_backoff(_call)

    def vision(self, image_data: bytes, prompt: str,
               image_format: str = "png") -> str:
        """Generate text response from image using OpenAI vision model"""
        if self._client is None:
            self._initialize_client()

        # Encode image to base64
        image_base64 = base64.standard_b64encode(image_data).decode("utf-8")

        messages = [
            {
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/{image_format};base64,{image_base64}",
                            "detail": "high"  # High detail for OCR
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
            response = self._client.chat.completions.create(
                model=self.config.vision_model or "gpt-4o",
                messages=messages,
                max_tokens=self.config.max_tokens,
                temperature=0.1  # Low temperature for OCR accuracy
            )
            return response.choices[0].message.content

        return self._retry_with_backoff(_call)


def create_openai_provider(
    api_key: str = None,
    vision_model: str = "gpt-4o",
    language_model: str = "gpt-4o",
    **kwargs
) -> OpenAIProvider:
    """
    Factory function to create an OpenAI provider.

    Args:
        api_key: OpenAI API key
        vision_model: Vision model name
        language_model: Language model name
        **kwargs: Additional configuration options

    Returns:
        Configured OpenAIProvider instance
    """
    import os

    config = ProviderConfig(
        api_key=api_key or os.environ.get("OPENAI_API_KEY", ""),
        vision_model=vision_model,
        language_model=language_model,
        **kwargs
    )

    return OpenAIProvider(config)
