"""
Qwen AI Provider (Alibaba DashScope)
=====================================

Supports:
- qwen-vl-plus, qwen-vl-max (Vision)
- qwen-max, qwen-plus, qwen-turbo (Language)

API Documentation: https://help.aliyun.com/document_detail/2712576.html
"""

import base64
from typing import Optional

from .base import AIProvider, ProviderConfig


class QwenProvider(AIProvider):
    """
    Qwen AI provider using Alibaba DashScope API.
    Uses OpenAI-compatible API format.
    """

    @property
    def name(self) -> str:
        return "qwen"

    @property
    def supports_vision(self) -> bool:
        return True

    def _initialize_client(self) -> None:
        """Initialize OpenAI-compatible client for DashScope"""
        try:
            from openai import OpenAI
        except ImportError:
            raise ImportError(
                "openai package is required for Qwen provider. "
                "Install with: pip install openai"
            )

        api_base = self.config.api_base or "https://dashscope.aliyuncs.com/compatible-mode/v1"

        self._client = OpenAI(
            api_key=self.config.api_key,
            base_url=api_base
        )

    def chat(self, prompt: str, system_prompt: str = None) -> str:
        """Generate text response using Qwen language model"""
        if self._client is None:
            self._initialize_client()

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        def _call():
            response = self._client.chat.completions.create(
                model=self.config.language_model or "qwen-max",
                messages=messages,
                max_tokens=self.config.max_tokens,
                temperature=self.config.temperature,
                top_p=self.config.top_p
            )
            return response.choices[0].message.content

        return self._retry_with_backoff(_call)

    def vision(self, image_data: bytes, prompt: str,
               image_format: str = "png") -> str:
        """Generate text response from image using Qwen vision model"""
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
                            "url": f"data:image/{image_format};base64,{image_base64}"
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
                model=self.config.vision_model or "qwen-vl-plus",
                messages=messages,
                max_tokens=self.config.max_tokens,
                temperature=0.1  # Low temperature for OCR accuracy
            )
            return response.choices[0].message.content

        return self._retry_with_backoff(_call)


def create_qwen_provider(
    api_key: str = None,
    vision_model: str = "qwen-vl-plus",
    language_model: str = "qwen-max",
    **kwargs
) -> QwenProvider:
    """
    Factory function to create a Qwen provider.

    Args:
        api_key: DashScope API key
        vision_model: Vision model name
        language_model: Language model name
        **kwargs: Additional configuration options

    Returns:
        Configured QwenProvider instance
    """
    import os

    config = ProviderConfig(
        api_key=api_key or os.environ.get("DASHSCOPE_API_KEY", ""),
        api_base="https://dashscope.aliyuncs.com/compatible-mode/v1",
        vision_model=vision_model,
        language_model=language_model,
        **kwargs
    )

    return QwenProvider(config)
