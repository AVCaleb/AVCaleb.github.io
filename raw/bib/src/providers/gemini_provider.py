"""
Google Gemini AI Provider
==========================

Supports:
- gemini-2.0-flash, gemini-1.5-pro, gemini-1.5-flash (Vision + Language)

API Documentation: https://ai.google.dev/docs
"""

import base64
from typing import Optional

from .base import AIProvider, ProviderConfig


class GeminiProvider(AIProvider):
    """
    Google Gemini AI provider.
    Uses the google-generativeai SDK.
    """

    @property
    def name(self) -> str:
        return "gemini"

    @property
    def supports_vision(self) -> bool:
        return True

    def _initialize_client(self) -> None:
        """Initialize Google Generative AI client"""
        try:
            import google.generativeai as genai
        except ImportError:
            raise ImportError(
                "google-generativeai package is required for Gemini provider. "
                "Install with: pip install google-generativeai"
            )

        genai.configure(api_key=self.config.api_key)
        self._genai = genai

        # Initialize models
        self._vision_model = genai.GenerativeModel(
            self.config.vision_model or "gemini-2.0-flash"
        )
        self._language_model = genai.GenerativeModel(
            self.config.language_model or "gemini-2.0-flash"
        )

    def chat(self, prompt: str, system_prompt: str = None) -> str:
        """Generate text response using Gemini language model"""
        if self._client is None:
            self._initialize_client()

        # Combine system prompt and user prompt
        full_prompt = prompt
        if system_prompt:
            full_prompt = f"{system_prompt}\n\n{prompt}"

        generation_config = {
            "temperature": self.config.temperature,
            "top_p": self.config.top_p,
            "max_output_tokens": self.config.max_tokens,
        }

        def _call():
            response = self._language_model.generate_content(
                full_prompt,
                generation_config=generation_config
            )
            return response.text

        return self._retry_with_backoff(_call)

    def vision(self, image_data: bytes, prompt: str,
               image_format: str = "png") -> str:
        """Generate text response from image using Gemini vision model"""
        if self._client is None:
            self._initialize_client()

        # Create image part
        image_part = {
            "mime_type": f"image/{image_format}",
            "data": image_data
        }

        generation_config = {
            "temperature": 0.1,  # Low temperature for OCR
            "max_output_tokens": self.config.max_tokens,
        }

        def _call():
            response = self._vision_model.generate_content(
                [image_part, prompt],
                generation_config=generation_config
            )
            return response.text

        return self._retry_with_backoff(_call)


def create_gemini_provider(
    api_key: str = None,
    vision_model: str = "gemini-2.0-flash",
    language_model: str = "gemini-2.0-flash",
    **kwargs
) -> GeminiProvider:
    """
    Factory function to create a Gemini provider.

    Args:
        api_key: Google AI API key
        vision_model: Vision model name
        language_model: Language model name
        **kwargs: Additional configuration options

    Returns:
        Configured GeminiProvider instance
    """
    import os

    config = ProviderConfig(
        api_key=api_key or os.environ.get("GEMINI_API_KEY", ""),
        vision_model=vision_model,
        language_model=language_model,
        **kwargs
    )

    return GeminiProvider(config)
