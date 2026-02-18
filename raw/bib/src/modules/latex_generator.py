"""
LaTeX Generator Module
Generates LaTeX documents for PDF compilation in three versions:
1. Original text only
2. Chinese translation only
3. Bilingual parallel view (original paragraph + translation paragraph)

Output structure:
  ./pdf_output/Book_Name/original/main.tex
  ./pdf_output/Book_Name/translation/main.tex
  ./pdf_output/Book_Name/bilingual/main.tex

Optimized for macOS with Chinese font support.
"""

import os
import re
import subprocess
from typing import List, Dict, Any, Optional
from enum import Enum

import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import config
from modules.yaml_processor import BookContent, Chapter, Section


class OutputMode(Enum):
    """PDF output mode"""
    ORIGINAL = "original"        # Original text only
    TRANSLATION = "translation"  # Chinese translation only
    BILINGUAL = "bilingual"      # Parallel original + translation


class LaTeXGenerator:
    """
    Generates LaTeX documents for book PDFs.
    Supports three output modes with beautiful typography.

    Directory structure:
        pdf_output/
        └── Book_Name/
            ├── original/
            │   └── main.tex
            ├── translation/
            │   └── main.tex
            └── bilingual/
                └── main.tex
    """

    def __init__(self, output_dir: str = None):
        self.output_dir = output_dir or config.paths.pdf_output_dir
        self.latex_config = config.latex
        os.makedirs(self.output_dir, exist_ok=True)

    def _sanitize_dirname(self, name: str) -> str:
        """Sanitize book name for use as directory name"""
        # Remove special characters, replace spaces with underscores
        clean = re.sub(r'[^\w\s-]', '', name).strip()
        return clean.replace(' ', '_')

    def _get_book_dir(self, book: BookContent, mode: OutputMode) -> str:
        """
        Get the output directory for a specific book and mode.

        Returns path like: pdf_output/Book_Name/original/
        """
        book_dirname = self._sanitize_dirname(book.metadata.title)
        mode_dir = os.path.join(self.output_dir, book_dirname, mode.value)
        os.makedirs(mode_dir, exist_ok=True)
        return mode_dir

    def _get_preamble(self, mode: OutputMode, book_title: str, book_title_cn: str) -> str:
        """Generate LaTeX preamble with appropriate settings"""
        # Font settings for macOS
        cn_font = self.latex_config.main_font_cn
        cn_sans_font = self.latex_config.sans_font_cn
        en_font = self.latex_config.main_font_en
        mono_font = self.latex_config.mono_font

        preamble = rf'''% !TEX program = xelatex
\documentclass[12pt, {self.latex_config.paper_size}]{{book}}

% Geometry
\usepackage[margin={self.latex_config.margin}]{{geometry}}

% ============================================
% IMPORTANT: Load these packages BEFORE polyglossia/bidi
% The bidi package (loaded by polyglossia for Hebrew) requires
% xcolor and graphicx to be loaded first.
% It also requires hyperref, fancyhdr, pgf, tikz, titlesec to be loaded BEFORE it.
% ============================================
\usepackage{{graphicx}}
\usepackage{{xcolor}}
\definecolor{{accentcolor}}{{RGB}}{{52, 152, 219}}
\definecolor{{lightgray}}{{RGB}}{{245, 245, 245}}

% Unicode and fonts
\usepackage{{fontspec}}
\usepackage{{xeCJK}}

% Set fonts
\setmainfont{{{en_font}}}
\setsansfont{{Helvetica Neue}}
\setmonofont{{{mono_font}}}
\setCJKmainfont{{{cn_font}}}
\setCJKsansfont{{{cn_sans_font}}}
\setCJKmonofont{{{cn_sans_font}}} % Use CJK sans (Heiti) for monospaced Chinese text

% Typography
\usepackage{{setspace}}
\setstretch{{{self.latex_config.line_spread}}}
\setlength{{\parskip}}{{{self.latex_config.para_skip}}}
\setlength{{\parindent}}{{2em}}
\raggedbottom
% Headers and footers
\usepackage{{fancyhdr}}
\pagestyle{{fancy}}
\fancyhf{{}}
\fancyhead[LE,RO]{{\footnotesize T. Austin Sparks}}
\fancyhead[RE]{{\footnotesize {self._escape_latex(book_title_cn or book_title)}}}
\fancyhead[LO]{{\footnotesize \leftmark}}
\fancyfoot[C]{{\footnotesize \thepage}}
\renewcommand{{\headrulewidth}}{{0.4pt}}

% Chapter styling
\usepackage{{titlesec}}
\titleformat{{\chapter}}[display]
  {{\normalfont\huge\bfseries\centering}}
  {{\chaptertitlename\ \thechapter}}{{20pt}}{{\Huge}}
\titlespacing*{{\chapter}}{{0pt}}{{50pt}}{{40pt}}

% Boxes for scripture
\usepackage{{tcolorbox}}
\tcbuselibrary{{skins,breakable}}

% For parallel text
\usepackage{{paracol}}

% Hyperlinks
\usepackage[bookmarks=true]{{hyperref}}
\hypersetup{{
    colorlinks=true,
    linkcolor=black,
    urlcolor=accentcolor,
    pdfauthor={{{self._escape_latex(book_title)}}},
    pdftitle={{{self._escape_latex(book_title_cn or book_title)}}}
}}

% Greek and Hebrew support (loads bidi package internally)
% MUST BE LOADED AFTER hyperref, fancyhdr, etc.
\usepackage{{polyglossia}}
\setmainlanguage{{english}}
\setotherlanguage{{greek}}
\setotherlanguage{{hebrew}}
\newfontfamily\greekfont{{Times New Roman}}
\newfontfamily\hebrewfont{{Times New Roman}}

% Table of contents depth
\setcounter{{tocdepth}}{{2}}

% Custom commands
\newcommand{{\scripture}}[1]{{%
    \begin{{tcolorbox}}[
        enhanced,
        colback=accentcolor!8,
        colframe=white,
        boxrule=0.5pt,
        sharp corners,
        left=10pt,
        right=0pt,
        top=10pt,
        bottom=10pt,
        boxsep=0pt,
        breakable
    ]
    \ttfamily #1
    \end{{tcolorbox}}
}}

\newenvironment{{outline}}{{%
    \par
    \setlength{{\parindent}}{{0pt}}%
    \obeylines
}}{{%
    \par
}}

'''
        # Add mode-specific commands
        if mode == OutputMode.BILINGUAL:
            preamble += rf'''
% Bilingual paragraph environment
\newenvironment{{bilingualblock}}{{%
    \par\vspace{{0.5em}}
    \begin{{tcolorbox}}[
        colback=lightgray,
        colframe=lightgray,
        arc=2mm,
        boxrule=0pt,
        left=12pt,
        right=12pt,
        top=10pt,
        bottom=10pt,
        breakable
    ]
}}{{%
    \end{{tcolorbox}}
    \par\vspace{{0.5em}}
}}

\newcommand{{\originaltext}}[1]{{%
    \noindent\textcolor{{accentcolor}}{{\rule{{3pt}}{{1em}}}}\hspace{{8pt}}%
    #1\par\vspace{{{self.latex_config.bilingual_para_skip}}}
}}

\newcommand{{\translatedtext}}[1]{{%
    \noindent\textcolor{{gray}}{{\rule{{3pt}}{{1em}}}}\hspace{{8pt}}%
    #1\par
}}
'''

        preamble += r'''
% Footnotes
\usepackage[bottom]{footmisc}
\renewcommand{\footnoterule}{\vfill\kern-3pt\hrule width 0.4\columnwidth\kern2.6pt}

\begin{document}
'''
        return preamble

    def _escape_latex(self, text: str) -> str:
        """Escape special LaTeX characters"""
        if not text:
            return ""
        # Characters that need escaping
        special_chars = {
            '&': r'\&',
            '%': r'\%',
            '$': r'\$',
            '#': r'\#',
            '_': r'\_',
            '{': r'\{',
            '}': r'\}',
            '~': r'\textasciitilde{}',
            '^': r'\textasciicircum{}',
            '\\': r'\textbackslash{}',
        }
        for char, escape in special_chars.items():
            text = text.replace(char, escape)
        return text

    def _format_section(self, section: Section, mode: OutputMode) -> str:
        """Format a section based on output mode"""
        original = self._escape_latex(section.en)
        chinese = self._escape_latex(section.cn)

        if mode == OutputMode.ORIGINAL:
            return f"{original}\n\n"
        elif mode == OutputMode.TRANSLATION:
            return f"{chinese}\n\n"
        else:  # BILINGUAL
            return rf'''
\begin{{bilingualblock}}
\originaltext{{{original}}}
\translatedtext{{{chinese}}}
\end{{bilingualblock}}
'''

    def _format_chapter(self, chapter: Chapter, mode: OutputMode) -> str:
        """Format a chapter"""
        # Chapter title
        if mode == OutputMode.ORIGINAL:
            title = chapter.title or f"Chapter {chapter.chapter_number}"
        elif mode == OutputMode.TRANSLATION:
            title = chapter.title_cn or f"第{chapter.chapter_number}章"
        else:
            title = f"{chapter.title_cn or f'第{chapter.chapter_number}章'}"
            if chapter.title:
                title += rf" \\ \normalsize\textit{{{self._escape_latex(chapter.title)}}}"

        content = rf'''
\chapter{{{title}}}
'''

        # Scripture block if present
        if chapter.scripture_text:
            scripture = self._escape_latex(chapter.scripture_text)
            if mode == OutputMode.TRANSLATION and chapter.scripture_translation:
                scripture = self._escape_latex(chapter.scripture_translation)
            elif mode == OutputMode.BILINGUAL:
                scripture += rf" \\ \textit{{{self._escape_latex(chapter.scripture_translation)}}}"

            content += rf'''
\scripture{{{scripture}}}

'''

        # Sections
        for section in chapter.sections:
            content += self._format_section(section, mode)

        # Footnotes at end of chapter
        footnotes = []
        for section in chapter.sections:
            footnotes.extend(section.footnotes)

        if footnotes:
            content += r'''
\vspace{1em}
\noindent\rule{\textwidth}{0.4pt}
\small
\begin{enumerate}
'''
            for fn in footnotes:
                marker = fn.get("marker", "").strip("[]")
                fn_content = self._escape_latex(fn.get("content", ""))
                original_fn = self._escape_latex(fn.get("original", fn_content))

                if mode == OutputMode.ORIGINAL:
                    content += rf"\item[{marker}] {original_fn}" + "\n"
                elif mode == OutputMode.TRANSLATION:
                    content += rf"\item[{marker}] {fn_content}" + "\n"
                else:
                    content += rf"\item[{marker}] {original_fn} / {fn_content}" + "\n"

            content += r'''
\end{enumerate}
\normalsize
'''

        return content

    def _generate_title_page(self, book: BookContent, mode: OutputMode) -> str:
        """Generate title page"""
        title = self._escape_latex(book.metadata.title)
        title_cn = self._escape_latex(book.metadata.title_cn)
        author = self._escape_latex(book.metadata.author)
        author_cn = self._escape_latex(book.metadata.author_cn)
        year = self._escape_latex(book.metadata.year)

        mode_label = {
            OutputMode.ORIGINAL: "Original Text / 原文版",
            OutputMode.TRANSLATION: "Chinese Translation / 中文译本",
            OutputMode.BILINGUAL: "Bilingual Edition / 中英对照版"
        }[mode]

        # Determine title display based on mode
        if mode == OutputMode.ORIGINAL:
            title_block = rf"{{\Huge\bfseries {title}}}"
            author_block = rf"{{\large {author}}}"
            publisher_block = rf"{{\large \ttfamily Published in {year}}}"
        elif mode == OutputMode.TRANSLATION:
            title_block = rf"{{\Huge\bfseries {title_cn}}}"
            author_block = rf"{{\large {author_cn}}}" 
            publisher_block = rf"{{\large {year} 年版}}"
        else: # BILINGUAL
            title_block = rf"{{\Huge\bfseries {title_cn}}}" + "\n\n" + \
                         rf"\vspace{{0.5cm}}" + "\n\n" + \
                         rf"{{\Large\textit{{{title}}}}}"
            author_block = rf"{{\large {author_cn}}}" + "\n\n" + \
                          rf"\vspace{{0.5cm}}" + "\n\n" + \
                          rf"{{\large {author}}}"
            publisher_block = rf"{{\large {year} 年版  \n\n \ttfamily Published in {year}}}"
        return rf'''
\begin{{titlepage}}
\centering
\vspace*{{3cm}}

{title_block}

\vspace{{2cm}}

{author_block}

\vfill

{publisher_block}

\end{{titlepage}}
'''

    def _generate_preface(self, book: BookContent, mode: OutputMode) -> str:
        """Generate preface section"""
        if not book.preface:
            return ""

        if mode == OutputMode.ORIGINAL:
            title = "Preface"
        elif mode == OutputMode.TRANSLATION:
            title = "前言"
        else:
            title = "前言 / Preface"

        content = rf'''
\chapter*{{{title}}}
\addcontentsline{{toc}}{{chapter}}{{{title}}}

'''
        for section in book.preface:
            content += self._format_section(section, mode)

        return content

    def generate_latex(self, book: BookContent, mode: OutputMode) -> str:
        """
        Generate complete LaTeX document.

        Args:
            book: BookContent object
            mode: Output mode (ORIGINAL, TRANSLATION, or BILINGUAL)

        Returns:
            Complete LaTeX document as string
        """
        document = self._get_preamble(mode, book.metadata.title, book.metadata.title_cn)

        # Title page
        document += self._generate_title_page(book, mode)

        # Table of contents
        document += r'''
\tableofcontents
\newpage
'''

        # Preface
        document += self._generate_preface(book, mode)

        # Chapters
        for chapter in book.chapters:
            document += self._format_chapter(chapter, mode)

        # End document
        document += r'''
\end{document}
'''
        return document

    def save_latex(self, book: BookContent, mode: OutputMode) -> str:
        """
        Save LaTeX document to file in the new directory structure.

        Directory structure:
            pdf_output/Book_Name/original/main.tex
            pdf_output/Book_Name/translation/main.tex
            pdf_output/Book_Name/bilingual/main.tex

        Args:
            book: BookContent object
            mode: Output mode

        Returns:
            Path to saved main.tex file
        """
        # Get the mode-specific directory
        mode_dir = self._get_book_dir(book, mode)

        # Always use main.tex as the entry file
        filepath = os.path.join(mode_dir, "main.tex")

        latex_content = self.generate_latex(book, mode)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(latex_content)

        print(f"LaTeX file saved: {filepath}")
        return filepath

    def compile_pdf(self, tex_path: str, clean: bool = True) -> Optional[str]:
        """
        Compile LaTeX file to PDF using xelatex.

        Args:
            tex_path: Path to .tex file
            clean: Whether to clean auxiliary files

        Returns:
            Path to generated PDF or None if compilation failed
        """
        if not os.path.exists(tex_path):
            print(f"Error: TeX file not found: {tex_path}")
            return None

        output_dir = os.path.dirname(tex_path)
        basename = os.path.splitext(os.path.basename(tex_path))[0]

        try:
            # Run xelatex twice for proper cross-references
            for i in range(2):
                print(f"Running xelatex (pass {i + 1}/2)...")
                result = subprocess.run(
                    ['xelatex', '-interaction=nonstopmode', '-output-directory', output_dir, tex_path],
                    capture_output=True,
                    text=True,
                    timeout=120
                )

                if result.returncode != 0:
                    print(f"xelatex error:\n{result.stderr}")
                    # Don't fail immediately, sometimes warnings don't stop compilation

            pdf_path = os.path.join(output_dir, f"{basename}.pdf")

            if os.path.exists(pdf_path):
                print(f"PDF generated: {pdf_path}")

                # Clean auxiliary files
                if clean:
                    aux_extensions = ['.aux', '.log', '.toc', '.out', '.fls', '.fdb_latexmk']
                    for ext in aux_extensions:
                        aux_file = os.path.join(output_dir, f"{basename}{ext}")
                        if os.path.exists(aux_file):
                            os.remove(aux_file)

                return pdf_path
            else:
                print(f"PDF not generated. Check {basename}.log for errors.")
                return None

        except subprocess.TimeoutExpired:
            print("LaTeX compilation timed out")
            return None
        except FileNotFoundError:
            print("xelatex not found. Please install TeX Live or MacTeX.")
            return None

    def generate_all_versions(self, book: BookContent) -> Dict[str, str]:
        """
        Generate all three LaTeX versions for a book.

        Output structure:
            pdf_output/Book_Name/original/main.tex
            pdf_output/Book_Name/translation/main.tex
            pdf_output/Book_Name/bilingual/main.tex

        Args:
            book: BookContent object

        Returns:
            Dictionary mapping mode to main.tex path
        """
        results = {}
        book_dirname = self._sanitize_dirname(book.metadata.title)

        for mode in OutputMode:
            print(f"\nGenerating {mode.value} version...")
            tex_path = self.save_latex(book, mode)
            results[mode.value] = tex_path

            # Optionally compile PDF
            # pdf_path = self.compile_pdf(tex_path)
            # if pdf_path:
            #     results[f"{mode.value}_pdf"] = pdf_path

        print(f"\nAll LaTeX files generated in: {os.path.join(self.output_dir, book_dirname)}/")
        return results

    def compile_all_versions(self, book: BookContent) -> Dict[str, str]:
        """
        Generate and compile all three PDF versions for a book.

        Args:
            book: BookContent object

        Returns:
            Dictionary mapping mode to PDF path
        """
        tex_results = self.generate_all_versions(book)
        pdf_results = {}

        for mode_name, tex_path in tex_results.items():
            print(f"\nCompiling {mode_name} PDF...")
            pdf_path = self.compile_pdf(tex_path)
            if pdf_path:
                pdf_results[mode_name] = pdf_path

        return pdf_results


def generate_book_pdfs(book: BookContent, output_dir: str = None) -> Dict[str, str]:
    """
    Convenience function to generate all LaTeX files for a book.

    Args:
        book: BookContent object
        output_dir: Optional output directory override

    Returns:
        Dictionary mapping version name to main.tex path
    """
    generator = LaTeXGenerator(output_dir)
    return generator.generate_all_versions(book)


if __name__ == "__main__":
    # Test with sample data
    from yaml_processor import BookMetadata, Chapter, Section, BookContent

    metadata = BookMetadata(
        title="Bible Synopsis",
        title_cn="圣经概要",
        author="J. N. Darby",
        author_cn="达秘",
        year="1900"
    )

    section1 = Section(
        id=1,
        en="In the beginning God created the heaven and the earth.",
        cn="起初，神创造天地。",
        footnotes=[{"marker": "[1]", "content": "创造万有", "original": "Creation ex nihilo"}]
    )

    chapter1 = Chapter(
        chapter_number=1,
        title="The Creation",
        title_cn="创造",
        sections=[section1],
        scripture_text="Ἐν ἀρχῇ ἐποίησεν ὁ θεὸς τὸν οὐρανὸν καὶ τὴν γῆν",
        scripture_translation="In the beginning God created the heaven and the earth"
    )

    book = BookContent(
        metadata=metadata,
        chapters=[chapter1]
    )

    generator = LaTeXGenerator()
    results = generator.generate_all_versions(book)

    print("\nGenerated files:")
    for mode, path in results.items():
        print(f"  {mode}: {path}")
