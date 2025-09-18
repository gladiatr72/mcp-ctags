"""MCP Ctags Server Module

Provides ctags-based code navigation capabilities through Model Context Protocol.
"""

from .ctags_parser import (
    CtagsEntry,
    parse_tags_file,
    detect_tags_file,
    validate_tags_format,
    is_function,
    is_class,
    is_method,
    is_variable,
)

from .symbol_search import (
    find_symbol_by_name,
    find_symbols_by_pattern,
    filter_by_symbol_type,
    filter_by_file_pattern,
    search_symbols,
    find_functions,
    find_classes,
    find_methods,
    find_variables,
)

__all__ = [
    "CtagsEntry",
    "parse_tags_file",
    "detect_tags_file",
    "validate_tags_format",
    "is_function",
    "is_class",
    "is_method",
    "is_variable",
    "find_symbol_by_name",
    "find_symbols_by_pattern",
    "filter_by_symbol_type",
    "filter_by_file_pattern",
    "search_symbols",
    "find_functions",
    "find_classes",
    "find_methods",
    "find_variables",
]
