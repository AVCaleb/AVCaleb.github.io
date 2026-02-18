"""
PDF Scanner Module
Uses AI vision models to extract text from PDF pages.
Supports multiple providers: Qwen, Gemini, OpenAI, Anthropic, Ollama.
Handles special formatting for Bible commentary books with Greek/Hebrew text.
"""

import os
import re
import time
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass

import fitz  # PyMuPDF

import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import config, PipelineConfig


@dataclass
class PageContent:
    """Represents extracted content from a single page"""
    page_number: int
    raw_text: str
    greek_hebrew_text: Optional[str] = None  # Top scripture text if present
    main_content: str = ""
    footnotes: List[Dict[str, str]] = None
    page_type: str = "content"  # content, preface, toc, title, etc.

    def __post_init__(self):
        if self.footnotes is None:
            self.footnotes = []


class PDFScanner:
    """
    Scans PDF documents using AI vision models.
    Extracts text, identifies structure, and handles special formatting.
    """

    def __init__(self, cfg: PipelineConfig = None, provider=None):
        """
        Initialize the PDF scanner.

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

        print(f"PDFScanner using provider: {self.provider.name}")

    def _pdf_page_to_bytes(self, pdf_path: str, page_num: int, dpi: int = 200) -> bytes:
        """Convert a PDF page to image bytes"""
        doc = fitz.open(pdf_path)
        page = doc.load_page(page_num)

        # Render page to image
        mat = fitz.Matrix(dpi / 72, dpi / 72)
        pix = page.get_pixmap(matrix=mat)
        img_bytes = pix.tobytes("png")

        doc.close()
        return img_bytes

    def _extract_page_content(self, pdf_path: str, page_num: int) -> PageContent:
        """Extract content from a single PDF page using vision model"""
        image_bytes = self._pdf_page_to_bytes(pdf_path, page_num)

        # Detailed prompt for text extraction
        prompt = """Please carefully OCR this page and extract all text content.

Important instructions:
1. Preserve the original text exactly as shown, including any Greek (Ελληνικά), Hebrew (עברית), or Latin text.
2. If this is a Bible commentary page with Greek/Hebrew scripture text at the top (usually in larger font), please clearly mark it with [SCRIPTURE_START] and [SCRIPTURE_END] tags.
3. Identify any footnotes and mark them with [FOOTNOTE_START:marker] and [FOOTNOTE_END] tags.
4. Identify the page type:
   - "title" for title pages
   - "preface" for preface/introduction pages
   - "toc" for table of contents
   - "content" for regular content pages
   - "index" for index pages

Please format your response as:
[PAGE_TYPE: type_here]

[If scripture text exists:]
[SCRIPTURE_START]
scripture text here
[SCRIPTURE_END]

[MAIN_CONTENT_START]
main body text here
[MAIN_CONTENT_END]

[If footnotes exist:]
[FOOTNOTES_START]
[FOOTNOTE_START:1] footnote content [FOOTNOTE_END]
[FOOTNOTE_START:2] footnote content [FOOTNOTE_END]
[FOOTNOTES_END]

Extract all text accurately, preserving the original language and formatting."""

        raw_response = self.provider.vision(image_bytes, prompt, "png")

        return self._parse_ocr_response(raw_response, page_num)

    def _parse_ocr_response(self, response: str, page_num: int) -> PageContent:
        """Parse the structured OCR response into PageContent"""
        content = PageContent(page_number=page_num, raw_text=response)

        # Extract page type
        type_match = re.search(r'\[PAGE_TYPE:\s*(\w+)\]', response)
        if type_match:
            content.page_type = type_match.group(1).lower()

        # Extract scripture text (Greek/Hebrew)
        scripture_match = re.search(
            r'\[SCRIPTURE_START\](.*?)\[SCRIPTURE_END\]',
            response, re.DOTALL
        )
        if scripture_match:
            content.greek_hebrew_text = scripture_match.group(1).strip()

        # Extract main content
        main_match = re.search(
            r'\[MAIN_CONTENT_START\](.*?)\[MAIN_CONTENT_END\]',
            response, re.DOTALL
        )
        if main_match:
            content.main_content = main_match.group(1).strip()
        else:
            # Fallback: use entire response minus markers as main content
            cleaned = re.sub(r'\[.*?\]', '', response)
            content.main_content = cleaned.strip()

        # Extract footnotes
        footnotes_section = re.search(
            r'\[FOOTNOTES_START\](.*?)\[FOOTNOTES_END\]',
            response, re.DOTALL
        )
        if footnotes_section:
            footnote_matches = re.findall(
                r'\[FOOTNOTE_START:([^\]]+)\](.*?)\[FOOTNOTE_END\]',
                footnotes_section.group(1), re.DOTALL
            )
            for marker, text in footnote_matches:
                content.footnotes.append({
                    "marker": f"[{marker}]",
                    "content": text.strip()
                })

        return content

    def scan_pdf(self, pdf_path: str,
                 start_page: int = 0,
                 end_page: int = None,
                 progress_callback=None) -> List[PageContent]:
        """
        Scan entire PDF or specified page range.

        Args:
            pdf_path: Path to the PDF file
            start_page: Starting page number (0-indexed)
            end_page: Ending page number (exclusive), None for all pages
            progress_callback: Optional callback function(current, total)

        Returns:
            List of PageContent objects
        """
        doc = fitz.open(pdf_path)
        total_pages = doc.page_count
        doc.close()

        if end_page is None:
            end_page = total_pages

        results = []

        for i, page_num in enumerate(range(start_page, min(end_page, total_pages))):
            if progress_callback:
                progress_callback(i + 1, end_page - start_page)

            print(f"  Scanning page {page_num + 1}/{total_pages}...")
            page_content = self._extract_page_content(pdf_path, page_num)
            results.append(page_content)

            # Small delay to avoid rate limiting
            if i < end_page - start_page - 1:
                time.sleep(0.5)

        return results

    def identify_book_structure(self, pages: List[PageContent]) -> Dict[str, Any]:
        """
        Analyze scanned pages to identify book structure.
        Returns chapter divisions, preface location, etc.
        """
        structure = {
            "title_pages": [],
            "preface_pages": [],
            "toc_pages": [],
            "content_sections": [],
            "index_pages": []
        }

        current_chapter = None
        chapter_start = None

        for page in pages:
            if page.page_type == "title":
                structure["title_pages"].append(page.page_number)
            elif page.page_type == "preface":
                structure["preface_pages"].append(page.page_number)
            elif page.page_type == "toc":
                structure["toc_pages"].append(page.page_number)
            elif page.page_type == "index":
                structure["index_pages"].append(page.page_number)
            else:
                # Detect chapter boundaries from content
                chapter_match = re.search(
                    r'(?:CHAPTER|Chapter|第.{1,3}章|SECTION|Section)\s*([IVXLCDM\d]+)?',
                    page.main_content[:500]
                )
                if chapter_match:
                    if current_chapter is not None:
                        structure["content_sections"].append({
                            "chapter": current_chapter,
                            "start_page": chapter_start,
                            "end_page": page.page_number - 1
                        })
                    current_chapter = chapter_match.group(0)
                    chapter_start = page.page_number

        # Add the last chapter
        if current_chapter is not None and pages:
            structure["content_sections"].append({
                "chapter": current_chapter,
                "start_page": chapter_start,
                "end_page": pages[-1].page_number
            })

        return structure

    def merge_scripture_texts(self, pages: List[PageContent]) -> List[PageContent]:
        """
        For Bible commentary books, merge consecutive scripture texts
        that span multiple pages into single blocks.
        """
        merged = []
        pending_scripture = ""
        pending_pages = []

        for page in pages:
            if page.greek_hebrew_text:
                pending_scripture += " " + page.greek_hebrew_text
                pending_pages.append(page.page_number)
            else:
                if pending_scripture and pending_pages:
                    # Attach merged scripture to the first commentary page
                    page.greek_hebrew_text = pending_scripture.strip()
                    page.main_content = f"[Scripture from pages {pending_pages}]\n{page.greek_hebrew_text}\n\n{page.main_content}"
                    pending_scripture = ""
                    pending_pages = []
                merged.append(page)

        # Handle case where scripture is at the end
        if pending_scripture and merged:
            merged[-1].greek_hebrew_text = pending_scripture.strip()

        return merged


def scan_book(pdf_path: str, provider=None) -> Tuple[List[PageContent], Dict[str, Any]]:
    """
    Convenience function to scan a complete book.

    Args:
        pdf_path: Path to the PDF file
        provider: Optional AI provider instance

    Returns:
        Tuple of (list of page contents, book structure dict)
    """
    scanner = PDFScanner(provider=provider)

    print(f"Scanning PDF: {pdf_path}")
    pages = scanner.scan_pdf(pdf_path)

    print("Identifying book structure...")
    structure = scanner.identify_book_structure(pages)

    print("Merging scripture texts...")
    pages = scanner.merge_scripture_texts(pages)

    return pages, structure


if __name__ == "__main__":
    # Example usage
    import sys
    import json

    if len(sys.argv) > 1:
        pdf_file = sys.argv[1]

        # Optionally specify provider
        provider_name = sys.argv[2] if len(sys.argv) > 2 else None

        if provider_name:
            from providers import get_provider
            provider = get_provider(provider_name)
        else:
            provider = None

        pages, structure = scan_book(pdf_file, provider=provider)
        print(f"\nScanned {len(pages)} pages")
        print(f"Structure: {json.dumps(structure, indent=2)}")
    else:
        print("Usage: python pdf_scanner.py <pdf_path> [provider_name]")
        print("Providers: qwen, gemini, openai, anthropic, ollama")
