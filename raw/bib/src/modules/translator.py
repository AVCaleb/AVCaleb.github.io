"""
Translation Module
Uses AI language models to translate text to Chinese.
Supports multiple providers: Qwen, Gemini, OpenAI, Anthropic, Ollama.
Handles paragraph-by-paragraph translation for alignment.
"""

import os
import re
import time
import json
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass

import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import config, PipelineConfig


@dataclass
class TranslatedSection:
    """Represents a translated section with original and Chinese text"""
    section_id: int
    original: str
    chinese: str
    footnotes: List[Dict[str, str]] = None

    def __post_init__(self):
        if self.footnotes is None:
            self.footnotes = []

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for YAML serialization"""
        result = {
            "id": self.section_id,
            "en": self.original,
            "cn": self.chinese
        }
        if self.footnotes:
            result["footnotes"] = self.footnotes
        return result


class Translator:
    """
    Translates text using AI language models.
    Maintains paragraph alignment between original and translation.
    """

    def __init__(self, cfg: PipelineConfig = None, provider=None):
        """
        Initialize the translator.

        Args:
            cfg: Pipeline configuration (uses global config if not provided)
            provider: AI provider instance (creates from config if not provided)
        """
        self.config = cfg or config

        # Get AI provider
        if provider is not None:
            self.provider = provider
        else:
            from providers import get_provider
            self.provider = get_provider()

        print(f"Translator using provider: {self.provider.name}")

    def translate_paragraph(self, text: str, context: str = "") -> str:
        """
        Translate a single paragraph to Chinese.

        Args:
            text: The text to translate
            context: Optional surrounding context for better translation

        Returns:
            Translated Chinese text
        """
        system_prompt = """你是一位专业的翻译专家，专门翻译基督教神学和圣经研究相关的文献。
请将给定的英文文本翻译成流畅、准确的中文。

翻译要求：
1. 保持原文的神学术语准确性
2. 专有名词（如人名、地名）采用通用中文译法
3. 圣经经文引用使用和合本译法
4. 希腊文和希伯来文保留原文，并在括号内提供音译
5. 保持原文的段落结构
6. 译文应该流畅自然，符合中文表达习惯"""

        user_prompt = f"""请翻译以下文本为中文：

{text}"""

        if context:
            user_prompt += f"\n\n上下文参考：\n{context}"

        response = self.provider.chat(user_prompt, system_prompt)
        return response.strip()

    def translate_with_alignment(self, paragraphs: List[str],
                                 progress_callback=None) -> List[Tuple[str, str]]:
        """
        Translate multiple paragraphs while maintaining alignment.

        Args:
            paragraphs: List of paragraphs to translate
            progress_callback: Optional callback function(current, total)

        Returns:
            List of (original, translated) tuples
        """
        results = []
        context_window = 2  # Number of previous paragraphs for context

        for i, para in enumerate(paragraphs):
            if progress_callback:
                progress_callback(i + 1, len(paragraphs))

            # Build context from previous paragraphs
            context_start = max(0, i - context_window)
            context = "\n\n".join(paragraphs[context_start:i])

            print(f"  Translating paragraph {i + 1}/{len(paragraphs)}...")
            translation = self.translate_paragraph(para, context)
            results.append((para, translation))

            # Rate limiting
            if i < len(paragraphs) - 1:
                time.sleep(0.3)

        return results

    def translate_batch(self, texts: List[str], batch_size: int = 5) -> List[str]:
        """
        Translate texts in batches for efficiency.
        Uses a single API call to translate multiple short texts.
        """
        results = []

        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]

            system_prompt = """你是一位专业的翻译专家。请将给定的多段英文文本翻译成中文。
每段翻译用 [TRANS_N] 标记，其中 N 是段落编号（从1开始）。
保持原文的格式和含义。"""

            # Build numbered input
            numbered_input = "\n\n".join([
                f"[TEXT_{j+1}]\n{text}"
                for j, text in enumerate(batch)
            ])

            user_prompt = f"请翻译以下{len(batch)}段文本：\n\n{numbered_input}"

            response = self.provider.chat(user_prompt, system_prompt)

            # Parse response
            for j in range(len(batch)):
                pattern = rf'\[TRANS_{j+1}\](.*?)(?=\[TRANS_|\Z)'
                match = re.search(pattern, response, re.DOTALL)
                if match:
                    results.append(match.group(1).strip())
                else:
                    # Fallback: translate individually
                    results.append(self.translate_paragraph(batch[j]))

            time.sleep(0.5)

        return results

    def translate_footnotes(self, footnotes: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """
        Translate footnotes while preserving markers.
        """
        if not footnotes:
            return []

        translated = []
        contents = [fn["content"] for fn in footnotes]
        translations = self.translate_batch(contents)

        for fn, trans in zip(footnotes, translations):
            translated.append({
                "marker": fn["marker"],
                "content": trans,
                "original": fn["content"]
            })

        return translated

    def create_sections_from_pages(self, pages, progress_callback=None) -> List[TranslatedSection]:
        """
        Create translated sections from scanned page contents.

        Args:
            pages: List of PageContent objects from PDF scanner
            progress_callback: Optional callback function

        Returns:
            List of TranslatedSection objects
        """
        sections = []
        section_id = 1

        total_items = sum(1 for p in pages if p.main_content.strip())

        for idx, page in enumerate(pages):
            if not page.main_content.strip():
                continue

            if progress_callback:
                progress_callback(idx + 1, total_items)

            # Split into paragraphs
            paragraphs = [p.strip() for p in page.main_content.split('\n\n') if p.strip()]

            for para in paragraphs:
                print(f"  Processing section {section_id}...")
                translation = self.translate_paragraph(para)

                section = TranslatedSection(
                    section_id=section_id,
                    original=para,
                    chinese=translation
                )

                # Handle footnotes for this section
                if page.footnotes:
                    section.footnotes = self.translate_footnotes(page.footnotes)

                sections.append(section)
                section_id += 1

                time.sleep(0.3)

        return sections

    def detect_and_translate_scripture(self, text: str) -> Dict[str, str]:
        """
        Detect and translate scripture references, preserving original.
        """
        system_prompt = """你是圣经翻译专家。请识别文本中的希腊文或希伯来文经文，
并提供：
1. 原文（保持不变）
2. 音译
3. 中文翻译（参考和合本）

以JSON格式返回：
{
  "original": "原文",
  "transliteration": "音译",
  "chinese": "中文翻译",
  "reference": "经文出处（如果能识别）"
}"""

        user_prompt = f"请分析以下经文：\n\n{text}"

        response = self.provider.chat(user_prompt, system_prompt)

        try:
            # Try to parse JSON response
            json_match = re.search(r'\{[^{}]*\}', response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
        except json.JSONDecodeError:
            pass

        # Fallback
        return {
            "original": text,
            "transliteration": "",
            "chinese": self.translate_paragraph(text)
        }


def translate_book_content(pages, provider=None) -> List[TranslatedSection]:
    """
    Convenience function to translate all content from scanned pages.

    Args:
        pages: List of PageContent objects
        provider: Optional AI provider instance

    Returns:
        List of TranslatedSection objects
    """
    translator = Translator(provider=provider)
    print("Translating book content...")
    sections = translator.create_sections_from_pages(pages)

    return sections


if __name__ == "__main__":
    # Test translation
    import sys

    provider_name = sys.argv[1] if len(sys.argv) > 1 else None

    if provider_name:
        from providers import get_provider
        provider = get_provider(provider_name)
    else:
        provider = None

    translator = Translator(provider=provider)
    test_text = "In the beginning God created the heaven and the earth."
    result = translator.translate_paragraph(test_text)
    print(f"Original: {test_text}")
    print(f"Translation: {result}")
