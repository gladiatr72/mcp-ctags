"""Tests for symbol search functions."""

import pytest
from typing import List

from ctags_mcp.ctags_parser import CtagsEntry
from ctags_mcp.symbol_search import (
    find_symbol_by_name,
    find_symbols_by_pattern,
    filter_by_symbol_type,
    filter_by_file_pattern,
    filter_by_scope,
    group_by_file,
    group_by_type,
    get_symbol_types,
    get_file_paths,
    sort_by_symbol_name,
    sort_by_file_path,
    find_functions,
    find_classes,
    find_methods,
    find_variables,
    search_symbols,
)


@pytest.fixture
def sample_entries() -> List[CtagsEntry]:
    """Create sample ctags entries for testing."""
    return [
        CtagsEntry(
            symbol="async_transfer_image",
            file="src/services/transfer.py",
            pattern="/^async def async_transfer_image():$/",
            type="f",
        ),
        CtagsEntry(
            symbol="TransferService",
            file="src/services/transfer.py",
            pattern="/^class TransferService:$/",
            type="c",
        ),
        CtagsEntry(
            symbol="BatchProcessor",
            file="src/services/batch.py",
            pattern="/^class BatchProcessor:$/",
            type="c",
        ),
        CtagsEntry(
            symbol="process_batch",
            file="src/services/batch.py",
            pattern="/^    def process_batch(self):$/",
            type="m",
            scope="BatchProcessor",
        ),
        CtagsEntry(
            symbol="DEFAULT_TIMEOUT",
            file="src/config/settings.py",
            pattern="/^DEFAULT_TIMEOUT = 300$/",
            type="v",
        ),
        CtagsEntry(
            symbol="validate_input",
            file="src/utils/validation.py",
            pattern="/^def validate_input():$/",
            type="f",
        ),
        CtagsEntry(
            symbol="auth_required",
            file="src/auth/decorators.py",
            pattern="/^def auth_required():$/",
            type="f",
        ),
        CtagsEntry(
            symbol="authenticate_user",
            file="src/auth/service.py",
            pattern="/^def authenticate_user():$/",
            type="f",
        ),
    ]


def test_find_symbol_by_name(sample_entries):
    """Test finding symbols by exact name."""
    results = find_symbol_by_name(sample_entries, "TransferService")
    assert len(results) == 1
    assert results[0].symbol == "TransferService"
    assert results[0].type == "c"

    # Test non-existent symbol
    results = find_symbol_by_name(sample_entries, "NonExistent")
    assert len(results) == 0

    # Test multiple matches (shouldn't happen in real ctags, but test anyway)
    duplicate_entries = sample_entries + [
        CtagsEntry(symbol="TransferService", file="other.py", pattern="", type="f")
    ]
    results = find_symbol_by_name(duplicate_entries, "TransferService")
    assert len(results) == 2


def test_find_symbols_by_pattern(sample_entries):
    """Test finding symbols by regex pattern."""
    # Find all symbols containing "auth"
    results = find_symbols_by_pattern(sample_entries, "auth")
    assert len(results) == 2
    symbols = {e.symbol for e in results}
    assert "auth_required" in symbols
    assert "authenticate_user" in symbols

    # Case insensitive search
    results = find_symbols_by_pattern(sample_entries, "TRANSFER", case_sensitive=False)
    assert len(results) == 2  # async_transfer_image and TransferService

    # Case sensitive search
    results = find_symbols_by_pattern(sample_entries, "TRANSFER", case_sensitive=True)
    assert len(results) == 0

    # Pattern with special regex characters
    results = find_symbols_by_pattern(sample_entries, "^async_")
    assert len(results) == 1
    assert results[0].symbol == "async_transfer_image"

    # Invalid regex pattern
    results = find_symbols_by_pattern(sample_entries, "[invalid")
    assert len(results) == 0


def test_filter_by_symbol_type(sample_entries):
    """Test filtering by symbol type."""
    # Functions
    functions = filter_by_symbol_type(sample_entries, "f")
    assert len(functions) == 4
    func_names = {e.symbol for e in functions}
    assert "async_transfer_image" in func_names
    assert "validate_input" in func_names
    assert "auth_required" in func_names
    assert "authenticate_user" in func_names

    # Classes
    classes = filter_by_symbol_type(sample_entries, "c")
    assert len(classes) == 2
    class_names = {e.symbol for e in classes}
    assert "TransferService" in class_names
    assert "BatchProcessor" in class_names

    # Methods
    methods = filter_by_symbol_type(sample_entries, "m")
    assert len(methods) == 1
    assert methods[0].symbol == "process_batch"

    # Variables
    variables = filter_by_symbol_type(sample_entries, "v")
    assert len(variables) == 1
    assert variables[0].symbol == "DEFAULT_TIMEOUT"

    # Non-existent type
    results = filter_by_symbol_type(sample_entries, "z")
    assert len(results) == 0


def test_filter_by_file_pattern(sample_entries):
    """Test filtering by file path pattern."""
    # Files in services directory
    results = filter_by_file_pattern(sample_entries, "services")
    assert len(results) == 4

    # Specific file
    results = filter_by_file_pattern(sample_entries, "transfer\\.py$")
    assert len(results) == 2

    # Auth-related files
    results = filter_by_file_pattern(sample_entries, "auth")
    assert len(results) == 2

    # Case insensitive
    results = filter_by_file_pattern(sample_entries, "SERVICES")
    assert len(results) == 4  # Should match due to case insensitive default

    # Invalid regex
    results = filter_by_file_pattern(sample_entries, "[invalid")
    assert len(results) == 0


def test_filter_by_scope(sample_entries):
    """Test filtering by scope pattern."""
    results = filter_by_scope(sample_entries, "BatchProcessor")
    assert len(results) == 1
    assert results[0].symbol == "process_batch"

    # Pattern matching
    results = filter_by_scope(sample_entries, ".*Processor")
    assert len(results) == 1

    # No scope entries
    results = filter_by_scope(sample_entries, "NonExistent")
    assert len(results) == 0

    # Invalid regex
    results = filter_by_scope(sample_entries, "[invalid")
    assert len(results) == 0


def test_group_by_file(sample_entries):
    """Test grouping entries by file."""
    groups = group_by_file(sample_entries)

    assert "src/services/transfer.py" in groups
    assert len(groups["src/services/transfer.py"]) == 2

    assert "src/services/batch.py" in groups
    assert len(groups["src/services/batch.py"]) == 2

    assert "src/config/settings.py" in groups
    assert len(groups["src/config/settings.py"]) == 1

    # Check total entries preserved
    total_entries = sum(len(entries) for entries in groups.values())
    assert total_entries == len(sample_entries)


def test_group_by_type(sample_entries):
    """Test grouping entries by symbol type."""
    groups = group_by_type(sample_entries)

    assert "f" in groups
    assert len(groups["f"]) == 4

    assert "c" in groups
    assert len(groups["c"]) == 2

    assert "m" in groups
    assert len(groups["m"]) == 1

    assert "v" in groups
    assert len(groups["v"]) == 1

    # Check total entries preserved
    total_entries = sum(len(entries) for entries in groups.values())
    assert total_entries == len(sample_entries)


def test_get_symbol_types(sample_entries):
    """Test getting unique symbol types."""
    types = get_symbol_types(sample_entries)
    assert types == {"f", "c", "m", "v"}


def test_get_file_paths(sample_entries):
    """Test getting unique file paths."""
    paths = get_file_paths(sample_entries)
    expected_paths = {
        "src/services/transfer.py",
        "src/services/batch.py",
        "src/config/settings.py",
        "src/utils/validation.py",
        "src/auth/decorators.py",
        "src/auth/service.py",
    }
    assert paths == expected_paths


def test_sort_by_symbol_name(sample_entries):
    """Test sorting by symbol name."""
    sorted_entries = sort_by_symbol_name(sample_entries)

    # Check that original list is not modified
    assert len(sample_entries) == 8  # Original length preserved

    # Check sorting - symbols should be in alphabetical order (case insensitive)
    symbols = [e.symbol for e in sorted_entries]
    expected_order = sorted([e.symbol for e in sample_entries], key=str.lower)
    assert symbols == expected_order


def test_sort_by_file_path(sample_entries):
    """Test sorting by file path."""
    sorted_entries = sort_by_file_path(sample_entries)

    # Check that original list is not modified
    assert len(sample_entries) == 8

    # Check sorting
    paths = [e.file for e in sorted_entries]
    assert paths == sorted([e.file for e in sample_entries])


def test_find_functions(sample_entries):
    """Test finding all functions."""
    functions = find_functions(sample_entries)
    assert len(functions) == 4
    assert all(e.type == "f" for e in functions)


def test_find_classes(sample_entries):
    """Test finding all classes."""
    classes = find_classes(sample_entries)
    assert len(classes) == 2
    assert all(e.type == "c" for e in classes)


def test_find_methods(sample_entries):
    """Test finding all methods."""
    methods = find_methods(sample_entries)
    assert len(methods) == 1
    assert all(e.type == "m" for e in methods)


def test_find_variables(sample_entries):
    """Test finding all variables."""
    variables = find_variables(sample_entries)
    assert len(variables) == 1
    assert all(e.type == "v" for e in variables)


def test_search_symbols_exact_match(sample_entries):
    """Test comprehensive symbol search with exact matching."""
    # Exact match, case sensitive
    results = search_symbols(
        sample_entries, "TransferService", exact_match=True, case_sensitive=True
    )
    assert len(results) == 1
    assert results[0].symbol == "TransferService"

    # Exact match, case insensitive
    results = search_symbols(
        sample_entries, "transferservice", exact_match=True, case_sensitive=False
    )
    assert len(results) == 1
    assert results[0].symbol == "TransferService"

    # No match for exact search
    results = search_symbols(sample_entries, "Transfer", exact_match=True)
    assert len(results) == 0


def test_search_symbols_pattern_match(sample_entries):
    """Test comprehensive symbol search with pattern matching."""
    # Pattern matching
    results = search_symbols(sample_entries, "auth", exact_match=False)
    assert len(results) == 2

    # Pattern with type filter
    results = search_symbols(
        sample_entries, "auth", symbol_types=["f"], exact_match=False
    )
    assert len(results) == 2
    assert all(e.type == "f" for e in results)

    # Pattern with file filter
    results = search_symbols(
        sample_entries, ".*", file_pattern="services", exact_match=False
    )
    assert len(results) == 4

    # Combined filters
    results = search_symbols(
        sample_entries,
        ".*",
        symbol_types=["f", "c"],
        file_pattern="transfer",
        exact_match=False,
    )
    assert len(results) == 2  # async_transfer_image and TransferService


def test_search_symbols_empty_results(sample_entries):
    """Test search scenarios that return no results."""
    # No matching symbol
    results = search_symbols(sample_entries, "nonexistent")
    assert len(results) == 0

    # No matching type
    results = search_symbols(sample_entries, ".*", symbol_types=["z"])
    assert len(results) == 0

    # No matching file pattern
    results = search_symbols(sample_entries, ".*", file_pattern="nonexistent")
    assert len(results) == 0
