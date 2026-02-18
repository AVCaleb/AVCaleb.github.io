"""
Ollama Provider (Local Models)
===============================

Supports locally running models via Ollama:
- llava, llava-llama3 (Vision)
- llama3, mistral, codellama, etc. (Language)

No API key required - runs entirely locally.
Install Ollama from: https://ollama.ai/

API Documentation: https://github.com/ollama/ollama/blob/main/docs/api.md
"""

import base64
import json
from typing import Optional
import urllib.request
import urllib.error

from .base import AIProvider, ProviderConfig


class OllamaProvider(AIProvider):
    """
    Ollama provider for local model inference.
    No API key required.
    """

    @property
    def name(self) -> str:
        return "ollama"

    @property
    def supports_vision(self) -> bool:
        # LLaVA models support vision
        vision_models = ["llava", "bakllava", "moondream"]
        return any(m in self.config.vision_model.lower() for m in vision_models)

    def _initialize_client(self) -> None:
        """Verify Ollama is running"""
        base_url = self.config.api_base or "http://localhost:11434"
        self._base_url = base_url.rstrip("/")

        try:
            req = urllib.request.Request(f"{self._base_url}/api/tags")
            with urllib.request.urlopen(req, timeout=5) as response:
                if response.status != 200:
                    raise ConnectionError("Ollama is not responding")
        except urllib.error.URLError as e:
            raise ConnectionError(
                f"Cannot connect to Ollama at {self._base_url}. "
                f"Make sure Ollama is running: ollama serve\n"
                f"Error: {e}"
            )

        self._client = True  # Mark as initialized

    def _make_request(self, endpoint: str, data: dict) -> str:
        """Make HTTP request to Ollama API"""
        url = f"{self._base_url}{endpoint}"

        json_data = json.dumps(data).encode('utf-8')
        req = urllib.request.Request(
            url,
            data=json_data,
            headers={'Content-Type': 'application/json'},
            method='POST'
        )

        with urllib.request.urlopen(req, timeout=300) as response:
            # Handle streaming response
            full_response = ""
            for line in response:
                try:
                    chunk = json.loads(line.decode('utf-8'))
                    if 'response' in chunk:
                        full_response += chunk['response']
                    elif 'message' in chunk and 'content' in chunk['message']:
                        full_response += chunk['message']['content']
                except json.JSONDecodeError:
                    continue

            return full_response

    def chat(self, prompt: str, system_prompt: str = None) -> str:
        """Generate text response using local Ollama model"""
        if self._client is None:
            self._initialize_client()

        data = {
            "model": self.config.language_model or "llama3",
            "prompt": prompt,
            "stream": True,
            "options": {
                "temperature": self.config.temperature,
                "top_p": self.config.top_p,
                "num_predict": self.config.max_tokens
            }
        }

        if system_prompt:
            data["system"] = system_prompt

        def _call():
            return self._make_request("/api/generate", data)

        return self._retry_with_backoff(_call)

    def vision(self, image_data: bytes, prompt: str,
               image_format: str = "png") -> str:
        """Generate text response from image using local vision model"""
        if self._client is None:
            self._initialize_client()

        # Encode image to base64
        image_base64 = base64.standard_b64encode(image_data).decode("utf-8")

        data = {
            "model": self.config.vision_model or "llava",
            "prompt": prompt,
            "images": [image_base64],
            "stream": True,
            "options": {
                "temperature": 0.1,  # Low temperature for OCR
                "num_predict": self.config.max_tokens
            }
        }

        def _call():
            return self._make_request("/api/generate", data)

        return self._retry_with_backoff(_call)

    def validate(self) -> bool:
        """Check if Ollama is running and models are available"""
        try:
            self._initialize_client()
            return True
        except ConnectionError as e:
            print(f"Ollama validation failed: {e}")
            return False

    def list_models(self) -> list:
        """List available models in Ollama"""
        if self._client is None:
            self._initialize_client()

        req = urllib.request.Request(f"{self._base_url}/api/tags")
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode('utf-8'))
            return [model['name'] for model in data.get('models', [])]

    def pull_model(self, model_name: str) -> bool:
        """Pull a model from Ollama library"""
        if self._client is None:
            self._initialize_client()

        print(f"Pulling model: {model_name}")
        data = {"name": model_name, "stream": True}

        try:
            json_data = json.dumps(data).encode('utf-8')
            req = urllib.request.Request(
                f"{self._base_url}/api/pull",
                data=json_data,
                headers={'Content-Type': 'application/json'},
                method='POST'
            )

            with urllib.request.urlopen(req, timeout=600) as response:
                for line in response:
                    try:
                        chunk = json.loads(line.decode('utf-8'))
                        status = chunk.get('status', '')
                        if status:
                            print(f"  {status}")
                    except json.JSONDecodeError:
                        continue

            print(f"Model {model_name} pulled successfully")
            return True

        except Exception as e:
            print(f"Failed to pull model: {e}")
            return False


def create_ollama_provider(
    base_url: str = "http://localhost:11434",
    vision_model: str = "llava",
    language_model: str = "llama3",
    **kwargs
) -> OllamaProvider:
    """
    Factory function to create an Ollama provider.

    Args:
        base_url: Ollama API base URL
        vision_model: Vision model name
        language_model: Language model name
        **kwargs: Additional configuration options

    Returns:
        Configured OllamaProvider instance
    """
    import os

    config = ProviderConfig(
        api_key="",  # Not needed for Ollama
        api_base=base_url or os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434"),
        vision_model=vision_model,
        language_model=language_model,
        **kwargs
    )

    return OllamaProvider(config)
