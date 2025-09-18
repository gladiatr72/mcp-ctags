"""Symbol Search Functions

Functional approach to searching and filtering ctags symbols.
"""

import re
from typing import List, Optional, Dict, Set
from .ctags_parser import CtagsEntry


def find_symbol_by_name(
    entries: List[CtagsEntry], symbol_name: str
) -> List[CtagsEntry]:
    """Find symbols with exact name match.

    Args:
        entries: List of ctags entries to search.
        symbol_name: Exact symbol name to find.

    Returns:
        List of matching CtagsEntry objects.
    """
    return [entry for entry in entries if entry.symbol == symbol_name]


def find_symbols_by_pattern(
    entries: List[CtagsEntry], pattern: str, case_sensitive: bool = False
) -> List[CtagsEntry]:
    """Find symbols matching a regex pattern.

    Args:
        entries: List of ctags entries to search.
        pattern: Regular expression pattern to match against symbol names.
        case_sensitive: Whether to perform case-sensitive matching.

    Returns:
        List of matching CtagsEntry objects.
    """
    flags = 0 if case_sensitive else re.IGNORECASE
    try:
        regex = re.compile(pattern, flags)
        return [entry for entry in entries if regex.search(entry.symbol)]
    except re.error:
        # Invalid regex pattern, return empty list
        return []


def filter_by_symbol_type(
    entries: List[CtagsEntry], symbol_type: str
) -> List[CtagsEntry]:
    """Filter entries by symbol type.

    Args:
        entries: List of ctags entries to filter.
        symbol_type: Symbol type to filter by (f, c, m, v, etc.).

    Returns:
        List of CtagsEntry objects matching the type.
    """
    return [entry for entry in entries if entry.type == symbol_type]


def filter_by_file_pattern(
    entries: List[CtagsEntry], file_pattern: str
) -> List[CtagsEntry]:
    """Filter entries by file path pattern.

    Args:
        entries: List of ctags entries to filter.
        file_pattern: Pattern to match against file paths.

    Returns:
        List of CtagsEntry objects from matching files.
    """
    try:
        regex = re.compile(file_pattern, re.IGNORECASE)
        return [entry for entry in entries if regex.search(entry.file)]
    except re.error:
        # Invalid regex pattern, return empty list
        return []


def filter_by_scope(entries: List[CtagsEntry], scope_pattern: str) -> List[CtagsEntry]:
    """Filter entries by scope pattern.

    Args:
        entries: List of ctags entries to filter.
        scope_pattern: Pattern to match against scope information.

    Returns:
        List of CtagsEntry objects with matching scopes.
    """
    try:
        regex = re.compile(scope_pattern, re.IGNORECASE)
        return [entry for entry in entries if entry.scope and regex.search(entry.scope)]
    except re.error:
        # Invalid regex pattern, return empty list
        return []


def group_by_file(entries: List[CtagsEntry]) -> Dict[str, List[CtagsEntry]]:
    """Group entries by file path.

    Args:
        entries: List of ctags entries to group.

    Returns:
        Dictionary mapping file paths to lists of entries.
    """
    groups = {}
    for entry in entries:
        if entry.file not in groups:
            groups[entry.file] = []
        groups[entry.file].append(entry)
    return groups


def group_by_type(entries: List[CtagsEntry]) -> Dict[str, List[CtagsEntry]]:
    """Group entries by symbol type.

    Args:
        entries: List of ctags entries to group.

    Returns:
        Dictionary mapping symbol types to lists of entries.
    """
    groups = {}
    for entry in entries:
        if entry.type not in groups:
            groups[entry.type] = []
        groups[entry.type].append(entry)
    return groups


def get_symbol_types(entries: List[CtagsEntry]) -> Set[str]:
    """Get all unique symbol types from entries.

    Args:
        entries: List of ctags entries.

    Returns:
        Set of unique symbol type strings.
    """
    return {entry.type for entry in entries}


def get_file_paths(entries: List[CtagsEntry]) -> Set[str]:
    """Get all unique file paths from entries.

    Args:
        entries: List of ctags entries.

    Returns:
        Set of unique file path strings.
    """
    return {entry.file for entry in entries}


def sort_by_symbol_name(entries: List[CtagsEntry]) -> List[CtagsEntry]:
    """Sort entries by symbol name alphabetically.

    Args:
        entries: List of ctags entries to sort.

    Returns:
        New list of entries sorted by symbol name.
    """
    return sorted(entries, key=lambda e: e.symbol.lower())


def sort_by_file_path(entries: List[CtagsEntry]) -> List[CtagsEntry]:
    """Sort entries by file path alphabetically.

    Args:
        entries: List of ctags entries to sort.

    Returns:
        New list of entries sorted by file path.
    """
    return sorted(entries, key=lambda e: e.file)


def find_functions(entries: List[CtagsEntry]) -> List[CtagsEntry]:
    """Find all function entries.

    Args:
        entries: List of ctags entries to search.

    Returns:
        List of function entries.
    """
    return filter_by_symbol_type(entries, "f")


def find_classes(entries: List[CtagsEntry]) -> List[CtagsEntry]:
    """Find all class entries.

    Args:
        entries: List of ctags entries to search.

    Returns:
        List of class entries.
    """
    return filter_by_symbol_type(entries, "c")


def find_methods(entries: List[CtagsEntry]) -> List[CtagsEntry]:
    """Find all method entries.

    Args:
        entries: List of ctags entries to search.

    Returns:
        List of method entries.
    """
    return filter_by_symbol_type(entries, "m")


def find_variables(entries: List[CtagsEntry]) -> List[CtagsEntry]:
    """Find all variable entries.

    Args:
        entries: List of ctags entries to search.

    Returns:
        List of variable entries.
    """
    return filter_by_symbol_type(entries, "v")


def search_symbols(
    entries: List[CtagsEntry],
    query: str,
    symbol_types: Optional[List[str]] = None,
    file_pattern: Optional[str] = None,
    case_sensitive: bool = False,
    exact_match: bool = False,
) -> List[CtagsEntry]:
    """Comprehensive symbol search with multiple filters.

    Args:
        entries: List of ctags entries to search.
        query: Symbol name or pattern to search for.
        symbol_types: List of symbol types to include (f, c, m, v, etc.).
        file_pattern: Optional file path pattern to filter by.
        case_sensitive: Whether to perform case-sensitive search.
        exact_match: Whether to match exact symbol name or use pattern matching.

    Returns:
        List of matching CtagsEntry objects.
    """
    # Start with all entries
    results = entries.copy()

    # Apply symbol name filter
    if exact_match:
        if case_sensitive:
            results = [e for e in results if e.symbol == query]
        else:
            results = [e for e in results if e.symbol.lower() == query.lower()]
    else:
        results = find_symbols_by_pattern(results, query, case_sensitive)

    # Apply symbol type filter
    if symbol_types:
        results = [e for e in results if e.type in symbol_types]

    # Apply file pattern filter
    if file_pattern:
        results = filter_by_file_pattern(results, file_pattern)

    return results
