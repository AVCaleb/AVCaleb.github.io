"""
AI Provider Factory
====================

Factory for creating AI provider instances based on configuration.
Automatically loads settings from .env file.
"""

import os
from typing import Optional, Dict, Type

from .base import AIProvider, ProviderConfig
from .qwen_provider import QwenProvider, create_qwen_provider
from .gemini_provider import GeminiProvider, create_gemini_provider
from .openai_provider import OpenAIProvider, create_openai_provider
from .anthropic_provider import AnthropicProvider, create_anthropic_provider
from .ollama_provider import OllamaProvider, create_ollama_provider


# Provider registry
PROVIDERS: Dict[str, Type[AIProvider]] = {
    "qwen": QwenProvider,
    "gemini": GeminiProvider,
    "openai": OpenAIProvider,
    "anthropic": AnthropicProvider,
    "ollama": OllamaProvider,
}

# Factory functions
FACTORY_FUNCTIONS = {
    "qwen": create_qwen_provider,
    "gemini": create_gemini_provider,
    "openai": create_openai_provider,
    "anthropic": create_anthropic_provider,
    "ollama": create_ollama_provider,
}

# Default models for each provider
DEFAULT_MODELS = {
    "qwen": {
        "vision": "qwen-vl-plus",
        "language": "qwen-max"
    },
    "gemini": {
        "vision": "gemini-2.0-flash",
        "language": "gemini-2.0-flash"
    },
    "openai": {
        "vision": "gpt-4o",
        "language": "gpt-4o"
    },
    "anthropic": {
        "vision": "claude-sonnet-4-20250514",
        "language": "claude-sonnet-4-20250514"
    },
    "ollama": {
        "vision": "llava",
        "language": "llama3"
    }
}


def _load_env_file(env_path: str = None) -> Dict[str, str]:
    """
    Load environment variables from .env file.

    Args:
        env_path: Path to .env file (default: .env in current or parent directory)

    Returns:
        Dictionary of environment variables
    """
    env_vars = {}

    # Search paths for .env
    search_paths = [
        env_path,
        ".env",
        os.path.join(os.path.dirname(__file__), "..", ".env"),
        os.path.join(os.path.dirname(__file__), "..", "..", ".env"),
    ]

    env_file = None
    for path in search_paths:
        if path and os.path.exists(path):
            env_file = path
            break

    if not env_file:
        return env_vars

    with open(env_file, 'r') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            if '=' in line:
                key, value = line.split('=', 1)
                key = key.strip()
                value = value.strip().strip('"').strip("'")
                env_vars[key] = value
                # Also set in os.environ for other modules
                os.environ.setdefault(key, value)

    return env_vars


def get_provider(
    provider_name: str = None,
    api_key: str = None,
    vision_model: str = None,
    language_model: str = None,
    env_file: str = None,
    **kwargs
) -> AIProvider:
    """
    Get an AI provider instance.

    Loads configuration from environment variables and .env file.

    Args:
        provider_name: Provider name ('qwen', 'gemini', 'openai', 'anthropic', 'ollama')
                      If None, uses AI_PROVIDER from environment
        api_key: API key (overrides environment variable)
        vision_model: Vision model name (overrides environment variable)
        language_model: Language model name (overrides environment variable)
        env_file: Path to .env file
        **kwargs: Additional provider-specific options

    Returns:
        Configured AIProvider instance

    Raises:
        ValueError: If provider name is invalid
    """
    # Load .env file
    env_vars = _load_env_file(env_file)

    # Determine provider
    if provider_name is None:
        provider_name = os.environ.get("AI_PROVIDER", env_vars.get("AI_PROVIDER", "qwen"))

    provider_name = provider_name.lower()

    if provider_name not in PROVIDERS:
        raise ValueError(
            f"Unknown provider: {provider_name}. "
            f"Available providers: {', '.join(PROVIDERS.keys())}"
        )

    # Get API key from environment
    api_key_env_map = {
        "qwen": "DASHSCOPE_API_KEY",
        "gemini": "GEMINI_API_KEY",
        "openai": "OPENAI_API_KEY",
        "anthropic": "ANTHROPIC_API_KEY",
        "ollama": None  # No API key needed
    }

    if api_key is None and api_key_env_map[provider_name]:
        env_key = api_key_env_map[provider_name]
        api_key = os.environ.get(env_key, env_vars.get(env_key, ""))

    # Get model names from environment
    prefix = provider_name.upper()
    if vision_model is None:
        vision_model = os.environ.get(
            f"{prefix}_VISION_MODEL",
            env_vars.get(f"{prefix}_VISION_MODEL", DEFAULT_MODELS[provider_name]["vision"])
        )
    if language_model is None:
        language_model = os.environ.get(
            f"{prefix}_LANGUAGE_MODEL",
            env_vars.get(f"{prefix}_LANGUAGE_MODEL", DEFAULT_MODELS[provider_name]["language"])
        )

    # Get common settings
    max_tokens = int(os.environ.get("MAX_TOKENS", env_vars.get("MAX_TOKENS", 4096)))
    temperature = float(os.environ.get("TEMPERATURE", env_vars.get("TEMPERATURE", 0.7)))
    max_retries = int(os.environ.get("MAX_RETRIES", env_vars.get("MAX_RETRIES", 3)))
    retry_delay = float(os.environ.get("RETRY_DELAY", env_vars.get("RETRY_DELAY", 1.0)))

    # Create provider using factory function
    factory_fn = FACTORY_FUNCTIONS[provider_name]

    provider_kwargs = {
        "vision_model": vision_model,
        "language_model": language_model,
        "max_tokens": max_tokens,
        "temperature": temperature,
        "max_retries": max_retries,
        "retry_delay": retry_delay,
        **kwargs
    }

    if provider_name == "ollama":
        base_url = os.environ.get("OLLAMA_BASE_URL", env_vars.get("OLLAMA_BASE_URL"))
        if base_url:
            provider_kwargs["base_url"] = base_url
    else:
        provider_kwargs["api_key"] = api_key

    return factory_fn(**provider_kwargs)


def list_providers() -> list:
    """List all available provider names"""
    return list(PROVIDERS.keys())


def get_default_provider() -> str:
    """Get the default provider name from environment"""
    env_vars = _load_env_file()
    return os.environ.get("AI_PROVIDER", env_vars.get("AI_PROVIDER", "qwen"))


def get_provider_info(provider_name: str) -> Dict:
    """
    Get information about a provider.

    Args:
        provider_name: Provider name

    Returns:
        Dictionary with provider details
    """
    if provider_name not in PROVIDERS:
        raise ValueError(f"Unknown provider: {provider_name}")

    return {
        "name": provider_name,
        "class": PROVIDERS[provider_name].__name__,
        "default_vision_model": DEFAULT_MODELS[provider_name]["vision"],
        "default_language_model": DEFAULT_MODELS[provider_name]["language"],
        "requires_api_key": provider_name != "ollama"
    }
