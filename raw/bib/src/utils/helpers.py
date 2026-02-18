"""
Helper utilities for the Book Digitization Pipeline
"""

import os
import re
import sys
from typing import Optional


def sanitize_filename(name: str, max_length: int = 100) -> str:
    """
    Sanitize a string for use as a filename.

    Args:
        name: Original string
        max_length: Maximum length of output

    Returns:
        Safe filename string
    """
    # Remove or replace invalid characters
    clean = re.sub(r'[<>:"/\\|?*]', '', name)
    clean = re.sub(r'\s+', '_', clean)
    clean = re.sub(r'_+', '_', clean)
    clean = clean.strip('._')

    if len(clean) > max_length:
        clean = clean[:max_length]

    return clean or "unnamed"


def ensure_directory(path: str) -> str:
    """
    Ensure a directory exists, creating it if necessary.

    Args:
        path: Directory path

    Returns:
        The same path (for chaining)
    """
    os.makedirs(path, exist_ok=True)
    return path


def format_file_size(size_bytes: int) -> str:
    """
    Format file size in human-readable format.

    Args:
        size_bytes: Size in bytes

    Returns:
        Formatted string (e.g., "1.5 MB")
    """
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f} PB"


def progress_bar(current: int, total: int, width: int = 40,
                 prefix: str = "", suffix: str = "") -> None:
    """
    Display a progress bar in the terminal.

    Args:
        current: Current progress value
        total: Total value
        width: Width of the progress bar
        prefix: Text before the bar
        suffix: Text after the bar
    """
    if total == 0:
        percent = 100
    else:
        percent = int(100 * current / total)

    filled = int(width * current / total) if total > 0 else width
    bar = '█' * filled + '░' * (width - filled)

    sys.stdout.write(f'\r{prefix} |{bar}| {percent}% {suffix}')
    sys.stdout.flush()

    if current >= total:
        print()


def split_into_paragraphs(text: str, min_length: int = 50) -> list:
    """
    Split text into paragraphs, merging short ones.

    Args:
        text: Input text
        min_length: Minimum paragraph length

    Returns:
        List of paragraphs
    """
    raw_paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]

    result = []
    buffer = ""

    for para in raw_paragraphs:
        if len(para) < min_length and buffer:
            buffer += " " + para
        elif len(para) < min_length:
            buffer = para
        else:
            if buffer:
                result.append(buffer)
                buffer = ""
            result.append(para)

    if buffer:
        result.append(buffer)

    return result


def detect_language(text: str) -> str:
    """
    Simple language detection based on character ranges.

    Args:
        text: Input text

    Returns:
        Language code ('en', 'zh', 'el', 'he', 'mixed')
    """
    if not text:
        return 'unknown'

    chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', text))
    greek_chars = len(re.findall(r'[\u0370-\u03ff\u1f00-\u1fff]', text))
    hebrew_chars = len(re.findall(r'[\u0590-\u05ff]', text))
    latin_chars = len(re.findall(r'[a-zA-Z]', text))

    total = chinese_chars + greek_chars + hebrew_chars + latin_chars

    if total == 0:
        return 'unknown'

    if chinese_chars / total > 0.5:
        return 'zh'
    if greek_chars / total > 0.3:
        return 'el'
    if hebrew_chars / total > 0.3:
        return 'he'
    if latin_chars / total > 0.5:
        return 'en'

    return 'mixed'


def roman_to_int(roman: str) -> int:
    """
    Convert Roman numeral to integer.

    Args:
        roman: Roman numeral string

    Returns:
        Integer value
    """
    values = {'I': 1, 'V': 5, 'X': 10, 'L': 50, 'C': 100, 'D': 500, 'M': 1000}
    result = 0
    prev = 0

    for char in reversed(roman.upper()):
        value = values.get(char, 0)
        if value < prev:
            result -= value
        else:
            result += value
        prev = value

    return result


def int_to_roman(num: int) -> str:
    """
    Convert integer to Roman numeral.

    Args:
        num: Integer value (1-3999)

    Returns:
        Roman numeral string
    """
    if not 0 < num < 4000:
        return str(num)

    values = [
        (1000, 'M'), (900, 'CM'), (500, 'D'), (400, 'CD'),
        (100, 'C'), (90, 'XC'), (50, 'L'), (40, 'XL'),
        (10, 'X'), (9, 'IX'), (5, 'V'), (4, 'IV'), (1, 'I')
    ]

    result = ""
    for value, numeral in values:
        while num >= value:
            result += numeral
            num -= value

    return result


def chinese_numeral(num: int) -> str:
    """
    Convert integer to Chinese numeral for chapter numbers.

    Args:
        num: Integer value

    Returns:
        Chinese numeral string
    """
    numerals = ['零', '一', '二', '三', '四', '五', '六', '七', '八', '九', '十']

    if num <= 10:
        return numerals[num]
    elif num < 20:
        return f"十{numerals[num - 10]}" if num > 10 else "十"
    elif num < 100:
        tens = num // 10
        ones = num % 10
        return f"{numerals[tens]}十{numerals[ones] if ones else ''}"
    else:
        return str(num)
