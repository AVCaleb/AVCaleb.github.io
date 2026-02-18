"""
HTML Generator Module
Generates web pages for books with three display modes:
1. Original text only
2. Chinese translation only
3. Bilingual parallel view (original paragraph + translation paragraph)
"""

import os
import re
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from string import Template

import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import config
from modules.yaml_processor import BookContent, Chapter, Section


class HTMLGenerator:
    """
    Generates HTML pages for digitized books.
    Creates a complete web-based reading experience with language switching.
    """

    def __init__(self, output_dir: str = None):
        self.output_dir = output_dir or config.paths.books_dir
        self.templates = self._load_templates()

    def _load_templates(self) -> Dict[str, str]:
        """Load HTML templates"""
        return {
            "base": self._get_base_template(),
            "entry": self._get_entry_template(),
            "toc": self._get_toc_template(),
            "chapter": self._get_chapter_template(),
            "preface": self._get_preface_template(),
        }

    def _get_base_template(self) -> str:
        """Base HTML template with language switching functionality"""
        return '''<!DOCTYPE html>
<html lang="zh-Hant">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>${title}</title>
    <style>
        /* --- 通用樣式 --- */
        :root {
            --primary-color: #2c3e50;
            --secondary-color: #34495e;
            --accent-color: #3498db;
            --bg-color: #fdfdfd;
            --text-color: #333;
            --light-border: #eee;
        }

        * {
            box-sizing: border-box;
        }

        body {
            font-family: "PingFang TC", "Helvetica Neue", "Helvetica", "Arial", "Microsoft YaHei", sans-serif;
            line-height: 1.8;
            color: var(--text-color);
            background-color: var(--bg-color);
            margin: 0;
            padding: 0;
        }

        /* --- 導航欄 --- */
        .navbar {
            position: sticky;
            top: 0;
            background: white;
            padding: 10px 20px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            z-index: 1000;
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
        }

        .nav-title {
            font-size: 1.2em;
            font-weight: bold;
            color: var(--primary-color);
            text-decoration: none;
        }

        .nav-links {
            display: flex;
            gap: 15px;
            align-items: center;
        }

        .nav-links a {
            color: var(--secondary-color);
            text-decoration: none;
            padding: 5px 10px;
            border-radius: 4px;
            transition: background 0.2s;
        }

        .nav-links a:hover {
            background: #f0f0f0;
        }

        /* --- 語言切換按鈕 --- */
        .lang-switcher {
            display: flex;
            gap: 5px;
            background: #f5f5f5;
            padding: 4px;
            border-radius: 8px;
        }

        .lang-btn {
            padding: 8px 16px;
            border: none;
            background: transparent;
            cursor: pointer;
            border-radius: 6px;
            font-size: 0.9em;
            transition: all 0.2s;
            color: var(--secondary-color);
        }

        .lang-btn:hover {
            background: #e0e0e0;
        }

        .lang-btn.active {
            background: var(--accent-color);
            color: white;
        }

        /* --- 內容容器 --- */
        .container {
            max-width: 800px;
            margin: 20px auto;
            padding: 30px 40px;
            background-color: #ffffff;
            box-shadow: 0 2px 8px rgba(0,0,0,0.05);
            border-radius: 8px;
        }

        /* --- 排版樣式 --- */
        h1 {
            text-align: center;
            font-size: 2.2em;
            margin-bottom: 0.3em;
            color: var(--primary-color);
        }

        .subtitle {
            text-align: center;
            font-size: 1.3em;
            color: #666;
            margin-bottom: 2em;
        }

        h2 {
            font-size: 1.8em;
            margin-top: 2em;
            text-align: center;
            border-bottom: 2px solid var(--light-border);
            padding-bottom: 10px;
            color: var(--primary-color);
        }

        h3 {
            font-size: 1.4em;
            margin-top: 1.5em;
            color: var(--secondary-color);
        }

        p {
            text-indent: 2em;
            margin-bottom: 1em;
            text-align: justify;
        }

        /* --- 段落顯示控制 --- */
        .para-group {
            margin-bottom: 1.5em;
        }

        .para-en, .para-cn {
            margin-bottom: 0.8em;
        }

        .para-en {
            font-family: "Times New Roman", Georgia, serif;
        }

        .para-cn {
            font-family: "PingFang TC", "Microsoft YaHei", sans-serif;
        }

        /* 雙語對照模式 */
        .bilingual .para-group {
            padding: 15px;
            background: #fafafa;
            border-radius: 6px;
            margin-bottom: 1.5em;
        }

        .bilingual .para-en {
            color: #333;
            border-left: 3px solid var(--accent-color);
            padding-left: 15px;
            margin-bottom: 0.5em;
        }

        .bilingual .para-cn {
            color: #555;
            border-left: 3px solid #95a5a6;
            padding-left: 15px;
        }

        /* 語言顯示切換 */
        .mode-en .para-cn { display: none; }
        .mode-cn .para-en { display: none; }
        .mode-bilingual .para-en,
        .mode-bilingual .para-cn { display: block; }

        /* --- 腳註 --- */
        .footnote-ref {
            color: var(--accent-color);
            cursor: pointer;
            font-size: 0.8em;
            vertical-align: super;
        }

        .footnotes {
            margin-top: 3em;
            padding-top: 1em;
            border-top: 1px solid var(--light-border);
            font-size: 0.9em;
        }

        .footnote-item {
            margin-bottom: 0.8em;
            padding-left: 2em;
            text-indent: -2em;
        }

        .footnote-marker {
            font-weight: bold;
            color: var(--accent-color);
        }

        /* --- 經文引用（希臘文/希伯來文） --- */
        .scripture-block {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px 25px;
            border-radius: 8px;
            margin: 1.5em 0;
            font-size: 1.1em;
            line-height: 1.6;
        }

        .scripture-block .greek,
        .scripture-block .hebrew {
            font-family: "SBL Greek", "Times New Roman", serif;
            direction: ltr;
        }

        .scripture-block .hebrew {
            font-family: "SBL Hebrew", "Times New Roman", serif;
            direction: rtl;
        }

        /* --- 目錄 --- */
        .toc-list {
            list-style: none;
            padding: 0;
        }

        .toc-list li {
            padding: 10px 15px;
            border-bottom: 1px solid var(--light-border);
        }

        .toc-list a {
            color: var(--secondary-color);
            text-decoration: none;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        .toc-list a:hover {
            color: var(--accent-color);
        }

        .toc-chapter-num {
            color: var(--accent-color);
            font-weight: bold;
            margin-right: 10px;
        }

        /* --- 分頁導航 --- */
        .page-nav {
            display: flex;
            justify-content: space-between;
            margin-top: 3em;
            padding-top: 1em;
            border-top: 1px solid var(--light-border);
        }

        .page-nav a {
            color: var(--accent-color);
            text-decoration: none;
            padding: 10px 20px;
            border: 1px solid var(--accent-color);
            border-radius: 4px;
            transition: all 0.2s;
        }

        .page-nav a:hover {
            background: var(--accent-color);
            color: white;
        }

        .page-nav .disabled {
            color: #ccc;
            border-color: #ccc;
            pointer-events: none;
        }

        /* --- 響應式設計 --- */
        @media (max-width: 768px) {
            .container {
                margin: 10px;
                padding: 20px;
            }

            .navbar {
                flex-direction: column;
                gap: 10px;
            }

            h1 { font-size: 1.8em; }
            h2 { font-size: 1.5em; }
        }

        @media print {
            .navbar, .lang-switcher, .page-nav {
                display: none;
            }
            .container {
                box-shadow: none;
                max-width: 100%;
            }
        }
    </style>
</head>
<body>
    ${navbar}
    <div class="container ${display_mode}">
        ${content}
    </div>
    <script>
        // 語言切換功能
        function setDisplayMode(mode) {
            const container = document.querySelector('.container');
            container.classList.remove('mode-en', 'mode-cn', 'mode-bilingual', 'bilingual');
            container.classList.add('mode-' + mode);
            if (mode === 'bilingual') {
                container.classList.add('bilingual');
            }

            // 更新按鈕狀態
            document.querySelectorAll('.lang-btn').forEach(btn => {
                btn.classList.remove('active');
            });
            document.querySelector('.lang-btn[data-mode="' + mode + '"]').classList.add('active');

            // 保存偏好
            localStorage.setItem('displayMode', mode);
        }

        // 頁面載入時恢復偏好設置
        document.addEventListener('DOMContentLoaded', function() {
            const savedMode = localStorage.getItem('displayMode') || 'bilingual';
            setDisplayMode(savedMode);
        });
    </script>
</body>
</html>'''

    def _get_entry_template(self) -> str:
        """Entry page template"""
        return '''
<h1>${title}</h1>
<p class="subtitle">${title_cn}</p>

<div style="text-align: center; margin: 2em 0;">
    <p><strong>作者:</strong> ${author} / ${author_cn}</p>
    <p><strong>出版年份:</strong> ${year}</p>
</div>

<div class="para-group">
    <p class="para-en">${description}</p>
    <p class="para-cn">${description_cn}</p>
</div>

<h2>目錄 / Table of Contents</h2>
<ul class="toc-list">
    ${toc_items}
</ul>

<div style="text-align: center; margin-top: 2em;">
    <p><small>原文來源: <a href="${source}" target="_blank">${source}</a></small></p>
</div>
'''

    def _get_toc_template(self) -> str:
        """Table of contents template"""
        return '''
<h1>目錄</h1>
<p class="subtitle">Table of Contents</p>

<ul class="toc-list">
    ${toc_items}
</ul>
'''

    def _get_chapter_template(self) -> str:
        """Chapter content template"""
        return '''
<h1>${chapter_title}</h1>
<p class="subtitle">${chapter_title_cn}</p>

${scripture_block}

${sections}

${footnotes_section}

<div class="page-nav">
    <a href="${prev_link}" class="${prev_class}">← 上一章</a>
    <a href="toc.html">目錄</a>
    <a href="${next_link}" class="${next_class}">下一章 →</a>
</div>
'''

    def _get_preface_template(self) -> str:
        """Preface template"""
        return '''
<h1>前言</h1>
<p class="subtitle">Preface</p>

${sections}

<div class="page-nav">
    <a href="entry.html">← 返回首頁</a>
    <a href="toc.html">目錄 →</a>
</div>
'''

    def _get_navbar_html(self, book_title: str, book_title_cn: str) -> str:
        """Generate navigation bar HTML"""
        return f'''
<nav class="navbar">
    <a href="entry.html" class="nav-title">{book_title_cn or book_title}</a>
    <div class="nav-links">
        <a href="entry.html">首頁</a>
        <a href="toc.html">目錄</a>
        <a href="preface.html">前言</a>
    </div>
    <div class="lang-switcher">
        <button class="lang-btn" data-mode="en" onclick="setDisplayMode('en')">English</button>
        <button class="lang-btn" data-mode="cn" onclick="setDisplayMode('cn')">中文</button>
        <button class="lang-btn active" data-mode="bilingual" onclick="setDisplayMode('bilingual')">對照</button>
    </div>
</nav>'''

    def _render_section(self, section: Section) -> str:
        """Render a single section as HTML"""
        footnote_refs = ""
        if section.footnotes:
            for fn in section.footnotes:
                marker = fn.get("marker", "").strip("[]")
                footnote_refs += f'<span class="footnote-ref" onclick="document.getElementById(\'fn-{marker}\').scrollIntoView()">[{marker}]</span>'

        return f'''
<div class="para-group">
    <p class="para-en">{self._escape_html(section.en)}{footnote_refs}</p>
    <p class="para-cn">{self._escape_html(section.cn)}</p>
</div>'''

    def _render_footnotes(self, footnotes: List[Dict[str, str]]) -> str:
        """Render footnotes section"""
        if not footnotes:
            return ""

        items = ""
        for fn in footnotes:
            marker = fn.get("marker", "").strip("[]")
            content = fn.get("content", "")
            original = fn.get("original", "")
            items += f'''
<div class="footnote-item" id="fn-{marker}">
    <span class="footnote-marker">[{marker}]</span>
    <span class="para-en">{self._escape_html(original or content)}</span>
    <span class="para-cn">{self._escape_html(content)}</span>
</div>'''

        return f'''
<div class="footnotes">
    <h3>腳註 / Footnotes</h3>
    {items}
</div>'''

    def _render_scripture_block(self, scripture_text: str, scripture_translation: str) -> str:
        """Render Greek/Hebrew scripture block"""
        if not scripture_text:
            return ""

        return f'''
<div class="scripture-block">
    <div class="greek">{self._escape_html(scripture_text)}</div>
    <div style="margin-top: 10px; font-style: italic;">{self._escape_html(scripture_translation)}</div>
</div>'''

    def _escape_html(self, text: str) -> str:
        """Escape HTML special characters while preserving newlines"""
        if not text:
            return ""
        text = text.replace("&", "&amp;")
        text = text.replace("<", "&lt;")
        text = text.replace(">", "&gt;")
        text = text.replace('"', "&quot;")
        text = text.replace("\n", "<br>")
        return text

    def _sanitize_dirname(self, name: str) -> str:
        """Sanitize book name for use as directory name"""
        # Remove special characters, replace spaces with underscores
        clean = re.sub(r'[^\w\s-]', '', name).strip()
        return clean.replace(' ', '_')

    def generate_book(self, book: BookContent) -> str:
        """
        Generate complete HTML website for a book.

        Args:
            book: BookContent object

        Returns:
            Path to the entry HTML file
        """
        # Create book directory
        book_dirname = self._sanitize_dirname(book.metadata.title)
        book_dir = os.path.join(self.output_dir, book_dirname)
        os.makedirs(book_dir, exist_ok=True)

        navbar = self._get_navbar_html(book.metadata.title, book.metadata.title_cn)

        # Generate entry page
        self._generate_entry_page(book, book_dir, navbar)

        # Generate TOC page
        self._generate_toc_page(book, book_dir, navbar)

        # Generate preface page
        self._generate_preface_page(book, book_dir, navbar)

        # Generate chapter pages
        self._generate_chapter_pages(book, book_dir, navbar)

        entry_path = os.path.join(book_dir, "entry.html")
        print(f"Book website generated at: {entry_path}")
        return entry_path

    def _generate_entry_page(self, book: BookContent, book_dir: str, navbar: str):
        """Generate the entry/index page"""
        # Build TOC items
        toc_items = ""

        if book.preface:
            toc_items += '<li><a href="preface.html"><span>前言 / Preface</span></a></li>'

        for chapter in book.chapters:
            chapter_file = f"chapter_{chapter.chapter_number}.html"
            title_display = f"{chapter.title}" if chapter.title else f"Chapter {chapter.chapter_number}"
            title_cn_display = chapter.title_cn or ""

            toc_items += f'''
<li>
    <a href="{chapter_file}">
        <span class="toc-chapter-num">第{chapter.chapter_number}章</span>
        <span class="para-en">{self._escape_html(title_display)}</span>
        <span class="para-cn">{self._escape_html(title_cn_display)}</span>
    </a>
</li>'''

        content = Template(self.templates["entry"]).substitute(
            title=self._escape_html(book.metadata.title),
            title_cn=self._escape_html(book.metadata.title_cn),
            author=self._escape_html(book.metadata.author),
            author_cn=self._escape_html(book.metadata.author_cn),
            year=self._escape_html(book.metadata.year),
            description=self._escape_html(book.metadata.description),
            description_cn=self._escape_html(book.metadata.description_cn),
            source=self._escape_html(book.metadata.source),
            toc_items=toc_items
        )

        html = Template(self.templates["base"]).substitute(
            title=f"{book.metadata.title} - {book.metadata.title_cn}",
            navbar=navbar,
            display_mode="mode-bilingual bilingual",
            content=content
        )

        with open(os.path.join(book_dir, "entry.html"), 'w', encoding='utf-8') as f:
            f.write(html)

    def _generate_toc_page(self, book: BookContent, book_dir: str, navbar: str):
        """Generate table of contents page"""
        toc_items = ""

        if book.preface:
            toc_items += '<li><a href="preface.html">前言 / Preface</a></li>'

        for chapter in book.chapters:
            chapter_file = f"chapter_{chapter.chapter_number}.html"
            toc_items += f'''
<li>
    <a href="{chapter_file}">
        <span>第{chapter.chapter_number}章: {self._escape_html(chapter.title_cn or chapter.title)}</span>
        <span class="para-en" style="font-size: 0.9em; color: #666;">{self._escape_html(chapter.title)}</span>
    </a>
</li>'''

        content = Template(self.templates["toc"]).substitute(toc_items=toc_items)

        html = Template(self.templates["base"]).substitute(
            title=f"目錄 - {book.metadata.title_cn}",
            navbar=navbar,
            display_mode="mode-bilingual bilingual",
            content=content
        )

        with open(os.path.join(book_dir, "toc.html"), 'w', encoding='utf-8') as f:
            f.write(html)

    def _generate_preface_page(self, book: BookContent, book_dir: str, navbar: str):
        """Generate preface page"""
        sections_html = "".join([self._render_section(s) for s in book.preface])

        if not sections_html:
            sections_html = "<p style='text-align: center; color: #999;'>No preface available / 暫無前言</p>"

        content = Template(self.templates["preface"]).substitute(sections=sections_html)

        html = Template(self.templates["base"]).substitute(
            title=f"前言 - {book.metadata.title_cn}",
            navbar=navbar,
            display_mode="mode-bilingual bilingual",
            content=content
        )

        with open(os.path.join(book_dir, "preface.html"), 'w', encoding='utf-8') as f:
            f.write(html)

    def _generate_chapter_pages(self, book: BookContent, book_dir: str, navbar: str):
        """Generate individual chapter pages"""
        total_chapters = len(book.chapters)

        for i, chapter in enumerate(book.chapters):
            # Render sections
            sections_html = "".join([self._render_section(s) for s in chapter.sections])

            # Collect all footnotes from sections
            all_footnotes = []
            for section in chapter.sections:
                all_footnotes.extend(section.footnotes)
            footnotes_html = self._render_footnotes(all_footnotes)

            # Scripture block
            scripture_html = self._render_scripture_block(
                chapter.scripture_text,
                chapter.scripture_translation
            )

            # Navigation links
            prev_link = f"chapter_{chapter.chapter_number - 1}.html" if i > 0 else "toc.html"
            prev_class = "" if i > 0 else "disabled"
            next_link = f"chapter_{chapter.chapter_number + 1}.html" if i < total_chapters - 1 else "toc.html"
            next_class = "" if i < total_chapters - 1 else "disabled"

            content = Template(self.templates["chapter"]).substitute(
                chapter_title=self._escape_html(chapter.title or f"Chapter {chapter.chapter_number}"),
                chapter_title_cn=self._escape_html(chapter.title_cn or f"第{chapter.chapter_number}章"),
                scripture_block=scripture_html,
                sections=sections_html,
                footnotes_section=footnotes_html,
                prev_link=prev_link,
                prev_class=prev_class,
                next_link=next_link,
                next_class=next_class
            )

            html = Template(self.templates["base"]).substitute(
                title=f"第{chapter.chapter_number}章 - {book.metadata.title_cn}",
                navbar=navbar,
                display_mode="mode-bilingual bilingual",
                content=content
            )

            filename = f"chapter_{chapter.chapter_number}.html"
            with open(os.path.join(book_dir, filename), 'w', encoding='utf-8') as f:
                f.write(html)


def generate_book_website(book: BookContent, output_dir: str = None) -> str:
    """
    Convenience function to generate HTML website for a book.

    Args:
        book: BookContent object
        output_dir: Optional output directory override

    Returns:
        Path to entry.html
    """
    generator = HTMLGenerator(output_dir)
    return generator.generate_book(book)


if __name__ == "__main__":
    # Test with sample data
    from yaml_processor import BookMetadata, Chapter, Section, BookContent

    metadata = BookMetadata(
        title="Sample Commentary",
        title_cn="示例注释书",
        author="Test Author",
        author_cn="测试作者",
        year="1900",
        source="https://archive.org/example",
        description="A sample book for testing the HTML generator.",
        description_cn="用于测试HTML生成器的示例书籍。"
    )

    section1 = Section(
        id=1,
        en="In the beginning God created the heaven and the earth. And the earth was without form, and void; and darkness was upon the face of the deep.",
        cn="起初，神创造天地。地是空虚混沌，渊面黑暗。",
        footnotes=[{"marker": "[1]", "content": "Creation ex nihilo."}]
    )

    section2 = Section(
        id=2,
        en="And the Spirit of God moved upon the face of the waters. And God said, Let there be light: and there was light.",
        cn="神的灵运行在水面上。神说：「要有光」，就有了光。"
    )

    chapter1 = Chapter(
        chapter_number=1,
        title="The Creation",
        title_cn="创造",
        sections=[section1, section2],
        scripture_text="Ἐν ἀρχῇ ἐποίησεν ὁ θεὸς τὸν οὐρανὸν καὶ τὴν γῆν",
        scripture_translation="In the beginning God created the heaven and the earth"
    )

    book = BookContent(
        metadata=metadata,
        chapters=[chapter1]
    )

    entry_path = generate_book_website(book)
    print(f"Generated: {entry_path}")
