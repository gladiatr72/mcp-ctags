"""Ctags File Parser

Functional approach to parsing ctags files and extracting symbol information.
"""

import re
from pathlib import Path
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class CtagsEntry(BaseModel):
    """Represents a single ctags entry with symbol information."""

    symbol: str = Field(description="Symbol name")
    file: str = Field(description="Source file path")
    pattern: str = Field(description="Search pattern or line number")
    type: str = Field(description="Symbol type (f=function, c=class, etc.)")
    line_number: Optional[int] = Field(
        default=None, description="Line number if available"
    )
    scope: Optional[str] = Field(default=None, description="Containing scope")
    language: Optional[str] = Field(default=None, description="Programming language")


# Standard ctags file names to search for
STANDARD_TAGS_NAMES = ["tags", ".tags", "TAGS"]


def is_function(entry: CtagsEntry) -> bool:
    """Check if entry represents a function."""
    return entry.type == "f"


def is_class(entry: CtagsEntry) -> bool:
    """Check if entry represents a class."""
    return entry.type == "c"


def is_method(entry: CtagsEntry) -> bool:
    """Check if entry represents a method."""
    return entry.type == "m"


def is_variable(entry: CtagsEntry) -> bool:
    """Check if entry represents a variable."""
    return entry.type == "v"


def detect_tags_file(working_dir: Optional[str] = None) -> Optional[Path]:
    """Detect ctags file in current directory or parents.

    Args:
        working_dir: Directory to start search from. Defaults to current directory.

    Returns:
        Path to tags file if found, None otherwise.
    """
    start_dir = Path(working_dir) if working_dir else Path.cwd()

    # Check current directory first
    for tags_name in STANDARD_TAGS_NAMES:
        tags_path = start_dir / tags_name
        if tags_path.exists() and tags_path.is_file():
            return tags_path

    # Check parent directories up to root
    current_dir = start_dir
    while current_dir != current_dir.parent:
        current_dir = current_dir.parent
        for tags_name in STANDARD_TAGS_NAMES:
            tags_path = current_dir / tags_name
            if tags_path.exists() and tags_path.is_file():
                return tags_path

    return None


def extract_symbol_type(type_info: str) -> Optional[str]:
    """Extract symbol type from type information field."""
    # Look for pattern like ';"<TAB>f' or just 'f'
    if ';"' in type_info:
        # Extended format: ;"<TAB>f
        match = re.search(r';"(?:\s+|\t)([a-z])', type_info)
        if match:
            return match.group(1)
    else:
        # Simple format: just the type character
        if len(type_info) == 1 and type_info.isalpha():
            return type_info

    return None


def extract_line_number(pattern: str) -> Optional[int]:
    """Extract line number from pattern if it's numeric."""
    try:
        # If pattern is just a number, it's a line number
        return int(pattern)
    except ValueError:
        # Pattern contains regex - no line number available
        return None


def extract_scope(extra_fields: List[str]) -> Optional[str]:
    """Extract scope information from extra fields."""
    for field in extra_fields:
        if field.startswith("class:"):
            return field[6:]  # Remove 'class:' prefix
        elif field.startswith("function:"):
            return field[9:]  # Remove 'function:' prefix
        elif field.startswith("namespace:"):
            return field[10:]  # Remove 'namespace:' prefix
    return None


def extract_language(extra_fields: List[str]) -> Optional[str]:
    """Extract language information from extra fields."""
    for field in extra_fields:
        if field.startswith("language:"):
            return field[9:]  # Remove 'language:' prefix
    return None


def parse_tags_line(line: str) -> Optional[CtagsEntry]:
    """Parse a single line from ctags file.

    Args:
        line: Raw line from tags file.

    Returns:
        CtagsEntry if parsing successful, None otherwise.
    """
    try:
        # Standard ctags format: symbol<TAB>file<TAB>pattern/line<TAB>type[<TAB>extras]
        parts = line.split("\t")
        if len(parts) < 4:
            return None

        symbol = parts[0]
        file_path = parts[1]
        pattern = parts[2]
        type_info = parts[3]

        # Extract symbol type (single character after ;" if present)
        symbol_type = extract_symbol_type(type_info)
        if not symbol_type:
            return None

        # Try to extract line number from pattern
        line_number = extract_line_number(pattern)

        # Extract additional fields
        extra_fields = parts[4:] if len(parts) > 4 else []
        scope = extract_scope(extra_fields)
        language = extract_language(extra_fields)

        return CtagsEntry(
            symbol=symbol,
            file=file_path,
            pattern=pattern,
            type=symbol_type,
            line_number=line_number,
            scope=scope,
            language=language,
        )

    except Exception:
        # Skip malformed lines
        return None


def parse_tags_file(
    tags_file: Optional[Path] = None, working_dir: Optional[str] = None
) -> List[CtagsEntry]:
    """Parse ctags file and return list of entries.

    Args:
        tags_file: Path to tags file. If None, attempts auto-detection.
        working_dir: Directory to start search from if tags_file is None.

    Returns:
        List of CtagsEntry objects.

    Raises:
        FileNotFoundError: If tags file not found.
        ValueError: If tags file format is invalid.
    """
    if tags_file is None:
        tags_file = detect_tags_file(working_dir)
        if tags_file is None:
            raise FileNotFoundError("No ctags file found")

    entries = []

    try:
        with open(tags_file, "r", encoding="utf-8", errors="replace") as f:
            for line in f:
                line = line.strip()

                # Skip empty lines and header comments
                if not line or line.startswith("!_TAG_"):
                    continue

                entry = parse_tags_line(line)
                if entry:
                    entries.append(entry)

    except FileNotFoundError:
        raise FileNotFoundError(f"Tags file not found: {tags_file}")
    except Exception as e:
        raise ValueError(f"Error parsing tags file {tags_file}: {e}")

    return entries


def validate_tags_format(tags_file: Path) -> Dict[str, Any]:
    """Validate and analyze tags file format.

    Args:
        tags_file: Path to tags file to validate.

    Returns:
        Dictionary with format information and statistics.
    """
    info = {
        "file_path": str(tags_file),
        "format": "unknown",
        "sorted": False,
        "total_entries": 0,
        "symbol_types": {},
        "valid": False,
    }

    try:
        with open(tags_file, "r", encoding="utf-8", errors="replace") as f:
            lines = f.readlines()

        # Check header for format information
        for line in lines[:10]:  # Check first 10 lines for headers
            if line.startswith("!_TAG_PROGRAM_NAME"):
                if "Exuberant Ctags" in line:
                    info["format"] = "exuberant"
                elif "Universal Ctags" in line:
                    info["format"] = "universal"
            elif line.startswith("!_TAG_FILE_SORTED"):
                info["sorted"] = "1" in line

        # Count entries and types
        for line in lines:
            line = line.strip()
            if not line or line.startswith("!_TAG_"):
                continue

            info["total_entries"] += 1
            entry = parse_tags_line(line)
            if entry:
                symbol_type = entry.type
                info["symbol_types"][symbol_type] = (
                    info["symbol_types"].get(symbol_type, 0) + 1
                )

        info["valid"] = info["total_entries"] > 0

    except Exception as e:
        info["error"] = str(e)

    return info
