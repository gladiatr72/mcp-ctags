"""MCP Ctags Server

FastMCP server providing ctags-based code navigation tools.
"""

import re
from pathlib import Path
from typing import List, Optional, Dict, Any
from mcp.server import FastMCP
from pydantic import BaseModel, Field

from .ctags_parser import (
    CtagsEntry,
    parse_tags_file,
    detect_tags_file,
    validate_tags_format,
)
from .symbol_search import (
    search_symbols,
    find_functions,
    find_classes,
    find_methods,
    find_variables,
    group_by_file,
)


# MCP server instance
mcp = FastMCP("ctags")


class SymbolSearchResult(BaseModel):
    """Result of symbol search operation."""

    symbol: str = Field(description="Symbol name")
    type: str = Field(description="Symbol type (f=function, c=class, etc.)")
    file: str = Field(description="Source file path")
    pattern: str = Field(description="Search pattern or line reference")
    line_number: Optional[int] = Field(
        default=None, description="Line number if available"
    )
    scope: Optional[str] = Field(default=None, description="Containing scope")


class TagsInfo(BaseModel):
    """Information about tags file."""

    file_path: str = Field(description="Path to tags file")
    format: str = Field(description="Ctags format (exuberant, universal, etc.)")
    total_entries: int = Field(description="Total number of entries")
    symbol_types: Dict[str, int] = Field(description="Count by symbol type")
    valid: bool = Field(description="Whether file is valid")


def entries_to_results(entries: List[CtagsEntry]) -> List[SymbolSearchResult]:
    """Convert CtagsEntry objects to SymbolSearchResult objects."""
    return [
        SymbolSearchResult(
            symbol=entry.symbol,
            type=entry.type,
            file=entry.file,
            pattern=entry.pattern,
            line_number=entry.line_number,
            scope=entry.scope,
        )
        for entry in entries
    ]


@mcp.tool()
def ctags_detect(working_dir: Optional[str] = None) -> Dict[str, Any]:
    """Detect and validate ctags file in working directory.

    Args:
        working_dir: Directory to search in. Defaults to current directory.

    Returns:
        Information about detected tags file or error if not found.
    """
    try:
        tags_file = detect_tags_file(working_dir)

        if tags_file is None:
            return {
                "found": False,
                "error": "No ctags file found",
                "searched_paths": ["tags", ".tags", "TAGS"],
            }

        # Validate the found file
        info = validate_tags_format(tags_file)

        return {
            "found": True,
            "file_path": str(tags_file),
            "format": info["format"],
            "total_entries": info["total_entries"],
            "symbol_types": info["symbol_types"],
            "valid": info["valid"],
        }

    except Exception as e:
        return {"found": False, "error": str(e)}


@mcp.tool()
def ctags_find_symbol(
    query: str,
    symbol_type: str = "all",
    file_pattern: Optional[str] = None,
    exact_match: bool = False,
    case_sensitive: bool = False,
    working_dir: Optional[str] = None,
) -> List[SymbolSearchResult]:
    """Find symbols by name or pattern.

    Args:
        query: Symbol name or regex pattern to search for.
        symbol_type: Type of symbol to find (f, c, m, v, or "all").
        file_pattern: Optional regex pattern to filter files.
        exact_match: Whether to match exact symbol name.
        case_sensitive: Whether search is case sensitive.
        working_dir: Directory containing tags file.

    Returns:
        List of matching symbols.
    """
    try:
        # Parse tags file
        entries = parse_tags_file(working_dir=working_dir)

        # Filter by symbol types
        symbol_types = None if symbol_type == "all" else [symbol_type]

        # Search symbols
        results = search_symbols(
            entries=entries,
            query=query,
            symbol_types=symbol_types,
            file_pattern=file_pattern,
            case_sensitive=case_sensitive,
            exact_match=exact_match,
        )

        return entries_to_results(results)

    except Exception as e:
        mcp.logger.error(f"Error in ctags_find_symbol: {e}")
        return []


@mcp.tool()
def ctags_list_symbols(
    symbol_type: str,
    file_pattern: Optional[str] = None,
    limit: int = 100,
    working_dir: Optional[str] = None,
) -> List[SymbolSearchResult]:
    """List all symbols of a specific type.

    Args:
        symbol_type: Type of symbol to list (f, c, m, v).
        file_pattern: Optional regex pattern to filter files.
        limit: Maximum number of results to return.
        working_dir: Directory containing tags file.

    Returns:
        List of symbols of the specified type.
    """
    try:
        # Parse tags file
        entries = parse_tags_file(working_dir=working_dir)

        # Filter by type
        if symbol_type == "f":
            filtered = find_functions(entries)
        elif symbol_type == "c":
            filtered = find_classes(entries)
        elif symbol_type == "m":
            filtered = find_methods(entries)
        elif symbol_type == "v":
            filtered = find_variables(entries)
        else:
            filtered = [e for e in entries if e.type == symbol_type]

        # Apply file filter if provided
        if file_pattern:
            try:
                regex = re.compile(file_pattern, re.IGNORECASE)
                filtered = [e for e in filtered if regex.search(e.file)]
            except re.error:
                mcp.logger.warning(f"Invalid file pattern: {file_pattern}")

        # Apply limit
        filtered = filtered[:limit]

        return entries_to_results(filtered)

    except Exception as e:
        mcp.logger.error(f"Error in ctags_list_symbols: {e}")
        return []


@mcp.tool()
def ctags_get_location(
    symbol: str, context_lines: int = 10, working_dir: Optional[str] = None
) -> Dict[str, Any]:
    """Get file location and source context for a symbol.

    Args:
        symbol: Exact symbol name to locate.
        context_lines: Number of context lines to include around symbol.
        working_dir: Directory containing tags file.

    Returns:
        Symbol location with source code context.
    """
    try:
        # Parse tags file
        entries = parse_tags_file(working_dir=working_dir)

        # Find exact symbol match
        matches = [e for e in entries if e.symbol == symbol]

        if not matches:
            return {"found": False, "error": f"Symbol '{symbol}' not found"}

        # Use first match if multiple (shouldn't happen in well-formed tags)
        entry = matches[0]

        # Try to read source file and extract context
        try:
            base_dir = Path(working_dir) if working_dir else Path.cwd()
            source_file = base_dir / entry.file

            if not source_file.exists():
                return {
                    "found": True,
                    "symbol": entry.symbol,
                    "type": entry.type,
                    "file": entry.file,
                    "pattern": entry.pattern,
                    "line_number": entry.line_number,
                    "scope": entry.scope,
                    "context": None,
                    "error": f"Source file not found: {source_file}",
                }

            # Read file and find symbol
            with open(source_file, "r", encoding="utf-8", errors="replace") as f:
                lines = f.readlines()

            # Try to find line number
            target_line = None
            if entry.line_number:
                target_line = entry.line_number - 1  # Convert to 0-based
            else:
                # Try to find using pattern
                pattern = entry.pattern.strip("/")
                if pattern.startswith("^") and pattern.endswith("$"):
                    # Remove regex anchors for search
                    search_pattern = pattern[1:-1]
                    for i, line in enumerate(lines):
                        if search_pattern in line:
                            target_line = i
                            break

            # Extract context
            context = None
            if target_line is not None and 0 <= target_line < len(lines):
                start = max(0, target_line - context_lines // 2)
                end = min(len(lines), target_line + context_lines // 2 + 1)
                context_lines_list = []

                for i in range(start, end):
                    line_num = i + 1
                    line_content = lines[i].rstrip()
                    marker = " -> " if i == target_line else "    "
                    context_lines_list.append(f"{line_num:4d}{marker}{line_content}")

                context = "\\n".join(context_lines_list)

            return {
                "found": True,
                "symbol": entry.symbol,
                "type": entry.type,
                "file": entry.file,
                "pattern": entry.pattern,
                "line_number": entry.line_number,
                "scope": entry.scope,
                "context": context,
                "target_line": target_line + 1 if target_line is not None else None,
            }

        except Exception as file_error:
            return {
                "found": True,
                "symbol": entry.symbol,
                "type": entry.type,
                "file": entry.file,
                "pattern": entry.pattern,
                "line_number": entry.line_number,
                "scope": entry.scope,
                "context": None,
                "error": f"Error reading source file: {file_error}",
            }

    except Exception as e:
        mcp.logger.error(f"Error in ctags_get_location: {e}")
        return {"found": False, "error": str(e)}


@mcp.tool()
def ctags_search_in_files(
    query: str,
    file_patterns: List[str],
    symbol_types: Optional[List[str]] = None,
    case_sensitive: bool = False,
    working_dir: Optional[str] = None,
) -> Dict[str, List[SymbolSearchResult]]:
    """Search for symbols within specific files or file patterns.

    Args:
        query: Symbol name or pattern to search for.
        file_patterns: List of file path patterns to search in.
        symbol_types: List of symbol types to include.
        case_sensitive: Whether search is case sensitive.
        working_dir: Directory containing tags file.

    Returns:
        Dictionary mapping file patterns to matching symbols.
    """
    try:
        # Parse tags file
        entries = parse_tags_file(working_dir=working_dir)

        results = {}

        for pattern in file_patterns:
            # Search in files matching this pattern
            matching_entries = search_symbols(
                entries=entries,
                query=query,
                symbol_types=symbol_types,
                file_pattern=pattern,
                case_sensitive=case_sensitive,
                exact_match=False,
            )

            results[pattern] = entries_to_results(matching_entries)

        return results

    except Exception as e:
        mcp.logger.error(f"Error in ctags_search_in_files: {e}")
        return {}


if __name__ == "__main__":
    # Run the MCP server
    mcp.run(transport="stdio")
