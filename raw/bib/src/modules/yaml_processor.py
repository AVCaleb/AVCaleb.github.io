"""
YAML Processor Module
Handles reading, writing, and manipulation of YAML book data files.
Supports the standardized format for bilingual book content.
"""

import os
import re
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime

import yaml

import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import config


@dataclass
class BookMetadata:
    """Book metadata information"""
    title: str
    title_cn: str = ""
    author: str = ""
    author_cn: str = ""
    year: str = ""
    source: str = ""  # Original source (e.g., Archive.org URL)
    description: str = ""
    description_cn: str = ""
    language: str = "en"
    created_date: str = ""
    last_modified: str = ""

    def __post_init__(self):
        if not self.created_date:
            self.created_date = datetime.now().isoformat()
        if not self.last_modified:
            self.last_modified = datetime.now().isoformat()

    def to_dict(self) -> Dict[str, str]:
        return {
            "title": self.title,
            "title_cn": self.title_cn,
            "author": self.author,
            "author_cn": self.author_cn,
            "year": self.year,
            "source": self.source,
            "description": self.description,
            "description_cn": self.description_cn,
            "language": self.language,
            "created_date": self.created_date,
            "last_modified": self.last_modified
        }


@dataclass
class Section:
    """A content section with original and translated text"""
    id: int
    en: str  # Original text (could be English or other language)
    cn: str  # Chinese translation
    footnotes: List[Dict[str, str]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        result = {
            "id": self.id,
            "en": self.en,
            "cn": self.cn
        }
        if self.footnotes:
            result["footnotes"] = self.footnotes
        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Section':
        return cls(
            id=data.get("id", 0),
            en=data.get("en", ""),
            cn=data.get("cn", ""),
            footnotes=data.get("footnotes", [])
        )


@dataclass
class Chapter:
    """A book chapter containing multiple sections"""
    chapter_number: int
    title: str = ""
    title_cn: str = ""
    sections: List[Section] = field(default_factory=list)
    scripture_text: str = ""  # Greek/Hebrew text for Bible commentaries
    scripture_translation: str = ""

    def to_dict(self) -> Dict[str, Any]:
        result = {
            "chapter_number": self.chapter_number,
            "title": self.title,
            "title_cn": self.title_cn,
            "sections": [s.to_dict() for s in self.sections]
        }
        if self.scripture_text:
            result["scripture_text"] = self.scripture_text
            result["scripture_translation"] = self.scripture_translation
        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Chapter':
        return cls(
            chapter_number=data.get("chapter_number", 0),
            title=data.get("title", ""),
            title_cn=data.get("title_cn", ""),
            sections=[Section.from_dict(s) for s in data.get("sections", [])],
            scripture_text=data.get("scripture_text", ""),
            scripture_translation=data.get("scripture_translation", "")
        )


@dataclass
class BookContent:
    """Complete book content structure"""
    metadata: BookMetadata
    preface: List[Section] = field(default_factory=list)
    table_of_contents: List[Dict[str, str]] = field(default_factory=list)
    chapters: List[Chapter] = field(default_factory=list)
    appendix: List[Section] = field(default_factory=list)
    index: List[Dict[str, str]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "metadata": self.metadata.to_dict(),
            "preface": [s.to_dict() for s in self.preface],
            "table_of_contents": self.table_of_contents,
            "chapters": [c.to_dict() for c in self.chapters],
            "appendix": [s.to_dict() for s in self.appendix],
            "index": self.index
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'BookContent':
        metadata = BookMetadata(**data.get("metadata", {"title": "Unknown"}))
        return cls(
            metadata=metadata,
            preface=[Section.from_dict(s) for s in data.get("preface", [])],
            table_of_contents=data.get("table_of_contents", []),
            chapters=[Chapter.from_dict(c) for c in data.get("chapters", [])],
            appendix=[Section.from_dict(s) for s in data.get("appendix", [])],
            index=data.get("index", [])
        )


class YAMLProcessor:
    """
    Handles YAML file operations for book data.
    """

    def __init__(self, yaml_dir: str = None):
        self.yaml_dir = yaml_dir or config.paths.yaml_dir
        os.makedirs(self.yaml_dir, exist_ok=True)

    def _get_yaml_path(self, book_name: str) -> str:
        """Get the YAML file path for a book"""
        # Sanitize book name for filesystem
        safe_name = re.sub(r'[^\w\s-]', '', book_name).strip().replace(' ', '_')
        return os.path.join(self.yaml_dir, f"{safe_name}.yaml")

    def save_book(self, book: BookContent, book_name: str = None) -> str:
        """
        Save book content to YAML file.

        Args:
            book: BookContent object to save
            book_name: Optional custom filename (defaults to book title)

        Returns:
            Path to the saved YAML file
        """
        if book_name is None:
            book_name = book.metadata.title

        yaml_path = self._get_yaml_path(book_name)

        # Update last modified timestamp
        book.metadata.last_modified = datetime.now().isoformat()

        # Custom YAML representer for multi-line strings
        def str_representer(dumper, data):
            if '\n' in data:
                return dumper.represent_scalar('tag:yaml.org,2002:str', data, style='|')
            return dumper.represent_scalar('tag:yaml.org,2002:str', data)

        yaml.add_representer(str, str_representer)

        with open(yaml_path, 'w', encoding='utf-8') as f:
            yaml.dump(book.to_dict(), f, allow_unicode=True, default_flow_style=False,
                      sort_keys=False, width=1000)

        print(f"Book saved to: {yaml_path}")
        return yaml_path

    def load_book(self, yaml_path: str) -> BookContent:
        """
        Load book content from YAML file.

        Args:
            yaml_path: Path to the YAML file

        Returns:
            BookContent object
        """
        with open(yaml_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)

        return BookContent.from_dict(data)

    def load_book_by_name(self, book_name: str) -> Optional[BookContent]:
        """
        Load book by name (searches in yaml_dir).

        Args:
            book_name: Name of the book

        Returns:
            BookContent object or None if not found
        """
        yaml_path = self._get_yaml_path(book_name)

        if not os.path.exists(yaml_path):
            # Try to find similar files
            for filename in os.listdir(self.yaml_dir):
                if book_name.lower().replace(' ', '_') in filename.lower():
                    yaml_path = os.path.join(self.yaml_dir, filename)
                    break

        if os.path.exists(yaml_path):
            return self.load_book(yaml_path)
        return None

    def list_books(self) -> List[str]:
        """List all available book YAML files"""
        books = []
        for filename in os.listdir(self.yaml_dir):
            if filename.endswith('.yaml') or filename.endswith('.yml'):
                books.append(filename[:-5] if filename.endswith('.yaml') else filename[:-4])
        return sorted(books)

    def update_section(self, book_name: str, chapter_num: int,
                       section_id: int, updates: Dict[str, Any]) -> bool:
        """
        Update a specific section in a book.

        Args:
            book_name: Name of the book
            chapter_num: Chapter number
            section_id: Section ID within the chapter
            updates: Dictionary of fields to update

        Returns:
            True if successful, False otherwise
        """
        book = self.load_book_by_name(book_name)
        if book is None:
            return False

        for chapter in book.chapters:
            if chapter.chapter_number == chapter_num:
                for section in chapter.sections:
                    if section.id == section_id:
                        for key, value in updates.items():
                            if hasattr(section, key):
                                setattr(section, key, value)
                        self.save_book(book, book_name)
                        return True
        return False

    def merge_books(self, book1: BookContent, book2: BookContent) -> BookContent:
        """
        Merge two book contents (e.g., combining partial translations).

        Args:
            book1: First book (base)
            book2: Second book (additions/updates)

        Returns:
            Merged BookContent
        """
        merged = BookContent(
            metadata=book1.metadata,
            preface=book1.preface or book2.preface,
            table_of_contents=book1.table_of_contents or book2.table_of_contents,
            chapters=book1.chapters.copy(),
            appendix=book1.appendix or book2.appendix,
            index=book1.index or book2.index
        )

        # Update Chinese translations if empty in book1
        for i, chapter in enumerate(merged.chapters):
            if i < len(book2.chapters):
                book2_chapter = book2.chapters[i]
                if not chapter.title_cn and book2_chapter.title_cn:
                    chapter.title_cn = book2_chapter.title_cn
                for j, section in enumerate(chapter.sections):
                    if j < len(book2_chapter.sections):
                        if not section.cn and book2_chapter.sections[j].cn:
                            section.cn = book2_chapter.sections[j].cn

        return merged


def create_book_yaml(pages, translated_sections, metadata: Dict[str, str],
                     api_key: str = None) -> BookContent:
    """
    Create a BookContent object from scanned pages and translated sections.

    Args:
        pages: List of PageContent objects from PDF scanner
        translated_sections: List of TranslatedSection objects
        metadata: Book metadata dictionary

    Returns:
        BookContent object ready to be saved
    """
    book_metadata = BookMetadata(
        title=metadata.get("title", "Unknown"),
        title_cn=metadata.get("title_cn", ""),
        author=metadata.get("author", ""),
        author_cn=metadata.get("author_cn", ""),
        year=metadata.get("year", ""),
        source=metadata.get("source", ""),
        description=metadata.get("description", ""),
        description_cn=metadata.get("description_cn", ""),
        language=metadata.get("language", "en")
    )

    # Convert translated sections to Section objects
    sections = [
        Section(
            id=ts.section_id,
            en=ts.original,
            cn=ts.chinese,
            footnotes=ts.footnotes if hasattr(ts, 'footnotes') else []
        )
        for ts in translated_sections
    ]

    # Create a single chapter for now (can be enhanced to detect chapters)
    chapter = Chapter(
        chapter_number=1,
        title=metadata.get("title", ""),
        title_cn=metadata.get("title_cn", ""),
        sections=sections
    )

    book = BookContent(
        metadata=book_metadata,
        chapters=[chapter]
    )

    return book


if __name__ == "__main__":
    # Example usage
    processor = YAMLProcessor()

    # Create sample book
    metadata = BookMetadata(
        title="Sample Book",
        title_cn="样本书籍",
        author="Test Author",
        author_cn="测试作者"
    )

    section1 = Section(
        id=1,
        en="In the beginning God created the heaven and the earth.",
        cn="起初，神创造天地。"
    )

    chapter1 = Chapter(
        chapter_number=1,
        title="Genesis",
        title_cn="创世记",
        sections=[section1]
    )

    book = BookContent(
        metadata=metadata,
        chapters=[chapter1]
    )

    # Save and reload
    yaml_path = processor.save_book(book, "sample_book")
    loaded_book = processor.load_book(yaml_path)
    print(f"Loaded book: {loaded_book.metadata.title}")
