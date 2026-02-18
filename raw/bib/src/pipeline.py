#!/usr/bin/env python3
"""
Book Digitization Pipeline
===========================

Complete workflow for digitizing books using multiple AI providers:
- Qwen (Alibaba DashScope)
- Gemini (Google)
- OpenAI (GPT-4)
- Anthropic (Claude)
- Ollama (Local)

Usage:
    python pipeline.py scan <pdf_path> [--provider gemini] [--output <yaml_path>]
    python pipeline.py translate <yaml_path> [--provider openai]
    python pipeline.py html <yaml_path> [--output <book_dir>]
    python pipeline.py pdf <yaml_path> [--output <pdf_dir>]
    python pipeline.py full <pdf_path> --title "Book Title" --provider qwen

Environment:
    Copy .env.example to .env and configure your API keys.
"""

import os
import sys
import argparse
import json
from typing import Optional, Dict, Any

# Add src to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import config, load_config
from providers import get_provider, list_providers
from modules.pdf_scanner import PDFScanner, scan_book
from modules.translator import Translator, translate_book_content
from modules.yaml_processor import (
    YAMLProcessor, BookContent, BookMetadata,
    Chapter, Section, create_book_yaml
)
from modules.html_generator import HTMLGenerator, generate_book_website
from modules.latex_generator import LaTeXGenerator, OutputMode, generate_book_pdfs


class BookPipeline:
    """
    Main pipeline for book digitization.
    Orchestrates the entire workflow from PDF to web/PDF output.
    Supports multiple AI providers.
    """

    def __init__(self, provider_name: str = None, api_key: str = None):
        """
        Initialize the pipeline.

        Args:
            provider_name: AI provider name (qwen, gemini, openai, anthropic, ollama)
            api_key: Optional API key override
        """
        # Update config if provider specified
        if provider_name:
            load_config(provider=provider_name, api_key=api_key)
        elif api_key:
            load_config(api_key=api_key)

        # Get the AI provider
        self.provider = get_provider(
            provider_name=provider_name,
            api_key=api_key
        )

        print(f"Pipeline initialized with provider: {self.provider.name}")
        print(f"  Vision model: {self.provider.config.vision_model}")
        print(f"  Language model: {self.provider.config.language_model}")

        # Initialize components with the provider
        self.scanner = PDFScanner(provider=self.provider)
        self.translator = Translator(provider=self.provider)
        self.yaml_processor = YAMLProcessor()
        self.html_generator = HTMLGenerator()
        self.latex_generator = LaTeXGenerator()

    def scan_pdf(self, pdf_path: str, output_yaml: str = None,
                 start_page: int = 0, end_page: int = None) -> str:
        """
        Step 1: Scan PDF and extract text using AI vision model.

        Args:
            pdf_path: Path to input PDF
            output_yaml: Optional path for YAML output
            start_page: Starting page (0-indexed)
            end_page: Ending page (exclusive)

        Returns:
            Path to generated YAML file
        """
        print("=" * 60)
        print("STEP 1: PDF SCANNING")
        print("=" * 60)
        print(f"Input PDF: {pdf_path}")
        print(f"Using provider: {self.provider.name}")
        print(f"Vision model: {self.provider.config.vision_model}")

        pages = self.scanner.scan_pdf(pdf_path, start_page, end_page)
        structure = self.scanner.identify_book_structure(pages)
        pages = self.scanner.merge_scripture_texts(pages)

        # Save raw scan results temporarily
        temp_data = {
            "pdf_path": pdf_path,
            "provider": self.provider.name,
            "pages": [
                {
                    "page_number": p.page_number,
                    "page_type": p.page_type,
                    "main_content": p.main_content,
                    "greek_hebrew_text": p.greek_hebrew_text,
                    "footnotes": p.footnotes
                }
                for p in pages
            ],
            "structure": structure
        }

        if output_yaml is None:
            basename = os.path.splitext(os.path.basename(pdf_path))[0]
            output_yaml = os.path.join(config.paths.yaml_dir, f"{basename}_scan.yaml")

        import yaml
        with open(output_yaml, 'w', encoding='utf-8') as f:
            yaml.dump(temp_data, f, allow_unicode=True, default_flow_style=False)

        print(f"\nScan complete! Pages scanned: {len(pages)}")
        print(f"Output saved to: {output_yaml}")

        return output_yaml

    def translate_content(self, yaml_path: str, output_yaml: str = None) -> str:
        """
        Step 2: Translate scanned content to Chinese using AI language model.

        Args:
            yaml_path: Path to scanned YAML file
            output_yaml: Optional path for translated YAML output

        Returns:
            Path to translated YAML file
        """
        print("=" * 60)
        print("STEP 2: TRANSLATION")
        print("=" * 60)
        print(f"Input YAML: {yaml_path}")
        print(f"Using provider: {self.provider.name}")
        print(f"Language model: {self.provider.config.language_model}")

        import yaml
        with open(yaml_path, 'r', encoding='utf-8') as f:
            scan_data = yaml.safe_load(f)

        # Extract content and translate
        sections = []
        section_id = 1

        for page_data in scan_data.get("pages", []):
            content = page_data.get("main_content", "").strip()
            if not content:
                continue

            # Split into paragraphs
            paragraphs = [p.strip() for p in content.split('\n\n') if p.strip()]

            for para in paragraphs:
                print(f"  Translating section {section_id}...")
                translation = self.translator.translate_paragraph(para)

                sections.append({
                    "id": section_id,
                    "en": para,
                    "cn": translation,
                    "footnotes": page_data.get("footnotes", [])
                })
                section_id += 1

        # Create book structure
        book_data = {
            "metadata": {
                "title": os.path.splitext(os.path.basename(yaml_path))[0].replace("_scan", ""),
                "title_cn": "",
                "author": "",
                "author_cn": "",
                "source": scan_data.get("pdf_path", ""),
                "language": "en",
                "processed_with": self.provider.name
            },
            "chapters": [
                {
                    "chapter_number": 1,
                    "title": "Content",
                    "title_cn": "内容",
                    "sections": sections
                }
            ]
        }

        if output_yaml is None:
            output_yaml = yaml_path.replace("_scan.yaml", "_translated.yaml")

        with open(output_yaml, 'w', encoding='utf-8') as f:
            yaml.dump(book_data, f, allow_unicode=True, default_flow_style=False, width=1000)

        print(f"\nTranslation complete! Sections translated: {len(sections)}")
        print(f"Output saved to: {output_yaml}")

        return output_yaml

    def generate_html(self, yaml_path: str, output_dir: str = None) -> str:
        """
        Step 3: Generate HTML website from translated YAML.

        Args:
            yaml_path: Path to translated YAML file
            output_dir: Optional output directory for HTML files

        Returns:
            Path to entry.html
        """
        print("=" * 60)
        print("STEP 3: HTML GENERATION")
        print("=" * 60)
        print(f"Input YAML: {yaml_path}")

        book = self.yaml_processor.load_book(yaml_path)

        if output_dir:
            self.html_generator.output_dir = output_dir

        entry_path = self.html_generator.generate_book(book)

        print(f"\nHTML website generated!")
        print(f"Entry point: {entry_path}")

        return entry_path

    def generate_pdfs(self, yaml_path: str, output_dir: str = None) -> Dict[str, str]:
        """
        Step 4: Generate LaTeX and compile PDFs in three versions.

        Args:
            yaml_path: Path to translated YAML file
            output_dir: Optional output directory for PDF files

        Returns:
            Dictionary mapping version name to PDF path
        """
        print("=" * 60)
        print("STEP 4: PDF GENERATION")
        print("=" * 60)
        print(f"Input YAML: {yaml_path}")

        book = self.yaml_processor.load_book(yaml_path)

        if output_dir:
            self.latex_generator.output_dir = output_dir

        results = self.latex_generator.generate_all_versions(book)

        print("\nPDF generation complete!")
        for version, path in results.items():
            print(f"  {version}: {path}")

        return results

    def run_full_pipeline(self, pdf_path: str,
                          title: str = None,
                          title_cn: str = None,
                          author: str = None,
                          author_cn: str = None,
                          year: str = None,
                          source: str = None,
                          description: str = None,
                          description_cn: str = None) -> Dict[str, Any]:
        """
        Run the complete pipeline from PDF to HTML and PDF outputs.

        Args:
            pdf_path: Path to input PDF
            title: Book title (English)
            title_cn: Book title (Chinese)
            author: Author name (English)
            author_cn: Author name (Chinese)
            year: Publication year
            source: Source URL
            description: Book description (English)
            description_cn: Book description (Chinese)

        Returns:
            Dictionary with paths to all generated outputs
        """
        print("=" * 60)
        print("FULL PIPELINE: PDF → YAML → HTML → PDF")
        print(f"Provider: {self.provider.name}")
        print("=" * 60)

        results = {}

        # Step 1: Scan PDF
        scan_yaml = self.scan_pdf(pdf_path)
        results["scan_yaml"] = scan_yaml

        # Step 2: Translate
        translated_yaml = self.translate_content(scan_yaml)

        # Update metadata if provided
        book = self.yaml_processor.load_book(translated_yaml)
        if title:
            book.metadata.title = title
        if title_cn:
            book.metadata.title_cn = title_cn
        if author:
            book.metadata.author = author
        if author_cn:
            book.metadata.author_cn = author_cn
        if year:
            book.metadata.year = year
        if source:
            book.metadata.source = source
        if description:
            book.metadata.description = description
        if description_cn:
            book.metadata.description_cn = description_cn

        # Save updated book
        final_yaml = self.yaml_processor.save_book(book)
        results["yaml"] = final_yaml

        # Step 3: Generate HTML
        html_path = self.html_generator.generate_book(book)
        results["html_entry"] = html_path

        # Step 4: Generate PDFs
        pdf_results = self.latex_generator.generate_all_versions(book)
        results["pdfs"] = pdf_results

        # Summary
        print("\n" + "=" * 60)
        print("PIPELINE COMPLETE!")
        print("=" * 60)
        print(f"\nProvider used: {self.provider.name}")
        print(f"\nYAML Data: {final_yaml}")
        print(f"\nHTML Website: {html_path}")
        print(f"\nPDF Files:")
        for version, path in pdf_results.items():
            print(f"  {version}: {path}")

        return results


def main():
    parser = argparse.ArgumentParser(
        description="Book Digitization Pipeline - Multi-Provider AI Support",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Scan a PDF file using Gemini
  python pipeline.py scan book.pdf --provider gemini

  # Translate using OpenAI
  python pipeline.py translate book_scan.yaml --provider openai

  # Generate HTML website
  python pipeline.py html book_translated.yaml

  # Generate PDF files
  python pipeline.py pdf book_translated.yaml

  # Run full pipeline with Qwen (default)
  python pipeline.py full book.pdf --title "My Book" --author "John Doe"

  # Run full pipeline with specific provider
  python pipeline.py full book.pdf --title "My Book" --provider anthropic

Available Providers:
  qwen      - Alibaba DashScope (DASHSCOPE_API_KEY)
  gemini    - Google Gemini (GEMINI_API_KEY)
  openai    - OpenAI GPT-4 (OPENAI_API_KEY)
  anthropic - Anthropic Claude (ANTHROPIC_API_KEY)
  ollama    - Local Ollama (no API key required)

Configuration:
  Copy .env.example to .env and add your API keys.
  Set AI_PROVIDER in .env to change the default provider.
        """
    )

    # Global options
    parser.add_argument('--provider', '-p',
                        choices=['qwen', 'gemini', 'openai', 'anthropic', 'ollama'],
                        help='AI provider to use (default: from .env or qwen)')
    parser.add_argument('--api-key', help='API key (overrides .env)')
    parser.add_argument('--list-providers', action='store_true',
                        help='List available providers and exit')

    subparsers = parser.add_subparsers(dest='command', help='Commands')

    # Scan command
    scan_parser = subparsers.add_parser('scan', help='Scan PDF and extract text')
    scan_parser.add_argument('pdf_path', help='Path to PDF file')
    scan_parser.add_argument('--output', '-o', help='Output YAML path')
    scan_parser.add_argument('--start-page', type=int, default=0, help='Start page (0-indexed)')
    scan_parser.add_argument('--end-page', type=int, help='End page (exclusive)')

    # Translate command
    translate_parser = subparsers.add_parser('translate', help='Translate scanned content')
    translate_parser.add_argument('yaml_path', help='Path to scanned YAML file')
    translate_parser.add_argument('--output', '-o', help='Output YAML path')

    # HTML command
    html_parser = subparsers.add_parser('html', help='Generate HTML website')
    html_parser.add_argument('yaml_path', help='Path to translated YAML file')
    html_parser.add_argument('--output', '-o', help='Output directory')

    # PDF command
    pdf_parser = subparsers.add_parser('pdf', help='Generate PDF files')
    pdf_parser.add_argument('yaml_path', help='Path to translated YAML file')
    pdf_parser.add_argument('--output', '-o', help='Output directory')

    # Full pipeline command
    full_parser = subparsers.add_parser('full', help='Run full pipeline')
    full_parser.add_argument('pdf_path', help='Path to PDF file')
    full_parser.add_argument('--title', help='Book title (English)')
    full_parser.add_argument('--title-cn', help='Book title (Chinese)')
    full_parser.add_argument('--author', help='Author name (English)')
    full_parser.add_argument('--author-cn', help='Author name (Chinese)')
    full_parser.add_argument('--year', help='Publication year')
    full_parser.add_argument('--source', help='Source URL')
    full_parser.add_argument('--description', help='Book description (English)')
    full_parser.add_argument('--description-cn', help='Book description (Chinese)')

    args = parser.parse_args()

    # Handle --list-providers
    if args.list_providers:
        print("Available AI Providers:")
        print("-" * 40)
        for provider in list_providers():
            from providers.factory import get_provider_info
            info = get_provider_info(provider)
            api_note = "(no API key required)" if not info["requires_api_key"] else ""
            print(f"  {provider:12} - Vision: {info['default_vision_model']}")
            print(f"              - Language: {info['default_language_model']} {api_note}")
        return

    if not args.command:
        parser.print_help()
        return

    # Initialize pipeline with provider
    pipeline = BookPipeline(
        provider_name=args.provider,
        api_key=args.api_key
    )

    # Execute command
    if args.command == 'scan':
        pipeline.scan_pdf(
            args.pdf_path,
            output_yaml=args.output,
            start_page=args.start_page,
            end_page=args.end_page
        )
    elif args.command == 'translate':
        pipeline.translate_content(args.yaml_path, output_yaml=args.output)
    elif args.command == 'html':
        pipeline.generate_html(args.yaml_path, output_dir=args.output)
    elif args.command == 'pdf':
        pipeline.generate_pdfs(args.yaml_path, output_dir=args.output)
    elif args.command == 'full':
        pipeline.run_full_pipeline(
            args.pdf_path,
            title=args.title,
            title_cn=args.title_cn,
            author=args.author,
            author_cn=args.author_cn,
            year=args.year,
            source=args.source,
            description=args.description,
            description_cn=args.description_cn
        )


if __name__ == "__main__":
    main()
