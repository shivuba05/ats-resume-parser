"""Cleaner module for cleaning and normalizing resume text."""

import re
import unicodedata
from typing import List

# Regex patterns for common bullet and decorator symbols
BULLET_CHARS = r"[\u2022\u2023\u25E6\u2043\u2219\u25CB\u25CF\u25AA\u25AB\u25A0\u25A1\u25C6\u25C7\u25B8\u25B9\u27A2\u27A4\u2705\u2714\u2713\u2013\u2014·•*⁃‣▪▫°º]"
BULLET_REGEX = re.compile(rf"^[\s]*{BULLET_CHARS}+[\s]*", re.MULTILINE)

# Pattern for page numbers and headers/footers
PAGE_NUMBER_PATTERNS = [
    re.compile(r"^[\s]*page\s+\d+\s*(?:of|/)\s*\d+[\s]*$", re.IGNORECASE | re.MULTILINE),
    re.compile(r"^[\s]*page\s+\d+[\s]*$", re.IGNORECASE | re.MULTILINE),
    re.compile(r"^[\s]*\d+\s*/\s*\d+[\s]*$", re.MULTILINE),
    re.compile(r"^[\s]*\d+\s+of\s+\d+[\s]*$", re.IGNORECASE | re.MULTILINE),
    re.compile(r"^[\s]*[-—–]\s*\d+\s*[-—–][\s]*$", re.MULTILINE),
    re.compile(r"^[\s]*\[?\s*page\s*\d+\s*\]?[\s]*$", re.IGNORECASE | re.MULTILINE),
]

# Pattern for horizontal divider lines
DIVIDER_REGEX = re.compile(r"^[\s]*[-=_~*#]{3,}[\s]*$", re.MULTILINE)


def clean_non_ascii_artifacts(text: str) -> str:
    """Normalize unicode and clean corrupted artifacts while preserving meaningful punctuation and symbols."""
    if not text:
        return ""

    replacements = {
        "\u2018": "'",   # Left single quote
        "\u2019": "'",   # Right single quote
        "\u201C": '"',   # Left double quote
        "\u201D": '"',   # Right double quote
        "\u2013": "-",   # En dash
        "\u2014": "-",   # Em dash
        "\u2015": "-",   # Horizontal bar
        "\u2026": "...", # Ellipsis
        "\u00A0": " ",   # Non-breaking space
        "\u200B": "",    # Zero-width space
        "\uFEFF": "",    # BOM
        "\t": "    ",    # Tab to spaces
        "\r": "",        # Carriage return
    }
    for orig, target in replacements.items():
        text = text.replace(orig, target)

    text = unicodedata.normalize("NFKC", text)

    cleaned_chars = []
    for char in text:
        cat = unicodedata.category(char)
        if char == "\n" or (not cat.startswith("C") and ord(char) < 0x10000):
            cleaned_chars.append(char)
        else:
            cleaned_chars.append(" ")

    return "".join(cleaned_chars)


def strip_page_numbers_and_dividers(text: str) -> str:
    """Remove page numbers, header/footer noise, and decorative dividers."""
    for pattern in PAGE_NUMBER_PATTERNS:
        text = pattern.sub("", text)
    text = DIVIDER_REGEX.sub("", text)
    return text


def normalize_bullet_points(text: str) -> str:
    """Convert various bullet symbols into a standard '- ' format for uniform parsing."""
    lines = text.split("\n")
    cleaned_lines = []
    for line in lines:
        stripped_line = line.strip()
        if stripped_line:
            # If line is enclosed in decorator symbols like ° DETAILS °, do not convert to list bullet
            if re.match(r"^°\s*[A-Z\s]+\s*°$", stripped_line):
                cleaned_lines.append(stripped_line)
                continue

            match = re.match(rf"^({BULLET_CHARS}+)\s*(.*)", stripped_line)
            if match:
                content = match.group(2).strip()
                cleaned_lines.append(f"- {content}")
            else:
                cleaned_lines.append(stripped_line)
        else:
            cleaned_lines.append("")
    return "\n".join(cleaned_lines)


def normalize_whitespace(text: str) -> str:
    """Normalize horizontal spacing and collapse excessive empty lines."""
    lines = [re.sub(r"[ \t]+", " ", line).strip() for line in text.split("\n")]

    cleaned_lines: List[str] = []
    blank_count = 0
    for line in lines:
        if not line:
            blank_count += 1
            if blank_count <= 1:
                cleaned_lines.append("")
        else:
            blank_count = 0
            cleaned_lines.append(line)

    return "\n".join(cleaned_lines).strip()


def clean_text(raw_text: str) -> str:
    """Run complete cleaning pipeline on raw extracted resume text."""
    if not raw_text or not isinstance(raw_text, str):
        return ""

    text = clean_non_ascii_artifacts(raw_text)
    text = strip_page_numbers_and_dividers(text)
    text = normalize_bullet_points(text)
    text = normalize_whitespace(text)

    return text
