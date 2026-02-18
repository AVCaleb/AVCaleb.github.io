"""
Configuration for the Book Digitization Pipeline.
Supports multiple AI providers via .env file configuration.
"""

import os
from dataclasses import dataclass, field
from typing import Optional, Dict, Any


def _load_env():
    """Load .env file if it exists"""
    env_paths = [
        ".env",
        os.path.join(os.path.dirname(__file__), ".env"),
        os.path.join(os.path.dirname(__file__), "..", ".env"),
    ]

    for env_path in env_paths:
        if os.path.exists(env_path):
            with open(env_path, 'r') as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith('#'):
                        continue
                    if '=' in line:
                        key, value = line.split('=', 1)
                        key = key.strip()
                        value = value.strip().strip('"').strip("'")
                        os.environ.setdefault(key, value)
            break


# Load .env file on module import
_load_env()


@dataclass
class AIProviderConfig:
    """Configuration for AI provider"""
    provider: str = ""  # qwen, gemini, openai, anthropic, ollama
    api_key: str = ""
    vision_model: str = ""
    language_model: str = ""
    max_tokens: int = 32768
    temperature: float = 0.7
    top_p: float = 0.9

    def __post_init__(self):
        # Load from environment if not set
        if not self.provider:
            self.provider = os.environ.get("AI_PROVIDER", "qwen")

        # Load provider-specific API key
        if not self.api_key:
            key_env_map = {
                "qwen": "DASHSCOPE_API_KEY",
                "gemini": "GEMINI_API_KEY",
                "openai": "OPENAI_API_KEY",
                "anthropic": "ANTHROPIC_API_KEY",
            }
            env_key = key_env_map.get(self.provider.lower())
            if env_key:
                self.api_key = os.environ.get(env_key, "")

        # Load model names from environment
        prefix = self.provider.upper()
        if not self.vision_model:
            self.vision_model = os.environ.get(f"{prefix}_VISION_MODEL", "")
        if not self.language_model:
            self.language_model = os.environ.get(f"{prefix}_LANGUAGE_MODEL", "")

        # Load common settings
        if self.max_tokens == 4096:
            self.max_tokens = int(os.environ.get("MAX_TOKENS", "4096"))
        if self.temperature == 0.7:
            self.temperature = float(os.environ.get("TEMPERATURE", "0.7"))


@dataclass
class PathConfig:
    """Configuration for file paths"""
    base_dir: str = ""
    books_dir: str = ""
    yaml_dir: str = ""
    pdf_output_dir: str = ""
    temp_dir: str = ""

    def __post_init__(self):
        if not self.base_dir:
            self.base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

        if not self.books_dir:
            self.books_dir = os.path.join(self.base_dir, "books")
        if not self.yaml_dir:
            self.yaml_dir = os.path.join(self.base_dir, "yaml_data")
        if not self.pdf_output_dir:
            self.pdf_output_dir = os.path.join(self.base_dir, "pdf_output")
        if not self.temp_dir:
            self.temp_dir = os.path.join(self.base_dir, "temp")

        # Ensure directories exist
        for dir_path in [self.books_dir, self.yaml_dir, self.pdf_output_dir, self.temp_dir]:
            os.makedirs(dir_path, exist_ok=True)


@dataclass
class LatexConfig:
    """Configuration for LaTeX PDF generation"""
    # Font settings (dynamically determining defaults if not set)
    main_font_cn: str = ""
    sans_font_cn: str = ""
    main_font_en: str = "Times New Roman"
    mono_font: str = "Palatino"

    # Page settings
    paper_size: str = "a4paper"
    margin: str = "2.5cm"

    # Paragraph settings
    para_skip: str = "0.8em"
    bilingual_para_skip: str = "0.3em"
    line_spread: float = 1.3

    def __post_init__(self):
        # Load from environment if available
        self.main_font_cn = os.environ.get("MAIN_FONT_CN", self.main_font_cn)
        self.sans_font_cn = os.environ.get("SANS_FONT_CN", self.sans_font_cn)
        self.main_font_en = os.environ.get("MAIN_FONT_EN", self.main_font_en)
        self.mono_font = os.environ.get("MONO_FONT", self.mono_font)

        # Auto-detect CJK fonts if still not specified
        if not self.main_font_cn or not self.sans_font_cn:
            import platform
            system = platform.system()
            
            # Default to modern macOS
            main_font = "Songti SC"
            sans_font = "Heiti SC"

            if system == "Darwin":
                # Check for modern macOS (El Capitan+) via PingFang
                if os.path.exists("/System/Library/Fonts/PingFang.ttc"):
                    main_font = "Songti SC"
                    sans_font = "Heiti SC"
                else:
                    # Legacy macOS
                    main_font = "STSong"
                    sans_font = "STHeiti"
            elif system == "Windows":
                 main_font = "SimSun"
                 sans_font = "SimHei"
            # Linux/Others might use Fandol or similar, but defaulting to the user's specific Windows request for "others"
            # The snippet showed Windows/Other -> SimSun/SimHei
            else:
                 main_font = "SimSun"
                 sans_font = "SimHei"

            if not self.main_font_cn:
                self.main_font_cn = main_font
            if not self.sans_font_cn:
                self.sans_font_cn = sans_font


@dataclass
class PipelineConfig:
    """Main configuration combining all settings"""
    ai: AIProviderConfig = None
    paths: PathConfig = None
    latex: LatexConfig = None

    # Processing settings
    batch_size: int = 5
    max_retries: int = 3
    retry_delay: float = 1.0

    # Legacy alias for backward compatibility
    @property
    def qwen(self):
        """Backward compatibility: access AI config via .qwen"""
        return self.ai

    def __post_init__(self):
        if self.ai is None:
            self.ai = AIProviderConfig()
        if self.paths is None:
            self.paths = PathConfig()
        if self.latex is None:
            self.latex = LatexConfig()

        # Load from environment
        self.max_retries = int(os.environ.get("MAX_RETRIES", str(self.max_retries)))
        self.retry_delay = float(os.environ.get("RETRY_DELAY", str(self.retry_delay)))

    def get_provider(self):
        """Get the configured AI provider instance"""
        from providers import get_provider
        return get_provider(
            provider_name=self.ai.provider,
            api_key=self.ai.api_key if self.ai.api_key else None,
            vision_model=self.ai.vision_model if self.ai.vision_model else None,
            language_model=self.ai.language_model if self.ai.language_model else None,
            max_tokens=self.ai.max_tokens,
            temperature=self.ai.temperature,
            max_retries=self.max_retries,
            retry_delay=self.retry_delay
        )


# Global configuration instance
config = PipelineConfig()


def load_config(
    provider: str = None,
    api_key: str = None,
    vision_model: str = None,
    language_model: str = None
) -> PipelineConfig:
    """
    Load/update configuration.

    Args:
        provider: AI provider name
        api_key: API key (optional override)
        vision_model: Vision model name
        language_model: Language model name

    Returns:
        Updated PipelineConfig
    """
    global config

    if provider:
        config.ai.provider = provider
    if api_key:
        config.ai.api_key = api_key
    if vision_model:
        config.ai.vision_model = vision_model
    if language_model:
        config.ai.language_model = language_model

    return config


def get_provider():
    """Convenience function to get the configured AI provider"""
    return config.get_provider()
