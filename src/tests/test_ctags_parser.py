"""Tests for ctags parser functions."""

import pytest
from pathlib import Path
from tempfile import NamedTemporaryFile, TemporaryDirectory

from ctags_mcp.ctags_parser import (
    CtagsEntry,
    detect_tags_file,
    parse_tags_line,
    parse_tags_file,
    validate_tags_format,
    extract_symbol_type,
    extract_line_number,
    extract_scope,
    extract_language,
    is_function,
    is_class,
    is_method,
    is_variable,
)


@pytest.fixture
def sample_ctags_content():
    """Sample ctags file content for testing."""
    return """!_TAG_FILE_FORMAT	2	/extended format; --format=1 will not append ;" to lines/
!_TAG_FILE_SORTED	1	/0=unsorted, 1=sorted, 2=foldcase/
!_TAG_PROGRAM_NAME	Exuberant Ctags	//
!_TAG_PROGRAM_VERSION	5.9~svn20110310	//
_async_inspect	src/ecreshore/cli/cluster/inspect.py	/^        async def _async_inspect():$/;"	f	function:inspect
AsyncBatchProcessor	src/ecreshore/services/async_batch_processor.py	/^class AsyncBatchProcessor:$/;"	c
BatchConfig	src/ecreshore/services/batch_config.py	/^class BatchConfig:$/;"	c
DEFAULT_TIMEOUT	src/ecreshore/services/batch_config.py	/^DEFAULT_TIMEOUT = 300$/;"	v
validate_config	src/ecreshore/services/batch_config.py	/^    def validate_config(self) -> bool:$/;"	m	class:BatchConfig
"""


@pytest.fixture
def sample_tags_file(sample_ctags_content):
    """Create a temporary tags file with sample content."""
    with NamedTemporaryFile(mode="w", suffix="tags", delete=False) as f:
        f.write(sample_ctags_content)
        f.flush()
        yield Path(f.name)
    Path(f.name).unlink(missing_ok=True)


def test_ctags_entry_model():
    """Test CtagsEntry model creation and properties."""
    entry = CtagsEntry(
        symbol="test_function",
        file="test.py",
        pattern="/^def test_function():$/",
        type="f",
        line_number=42,
        scope="TestClass",
        language="python",
    )

    assert entry.symbol == "test_function"
    assert entry.file == "test.py"
    assert entry.type == "f"
    assert entry.line_number == 42
    assert entry.scope == "TestClass"
    assert entry.language == "python"


def test_is_function_helpers():
    """Test helper functions for checking entry types."""
    func_entry = CtagsEntry(symbol="func", file="test.py", pattern="", type="f")
    class_entry = CtagsEntry(symbol="cls", file="test.py", pattern="", type="c")
    method_entry = CtagsEntry(symbol="method", file="test.py", pattern="", type="m")
    var_entry = CtagsEntry(symbol="var", file="test.py", pattern="", type="v")

    assert is_function(func_entry)
    assert not is_function(class_entry)

    assert is_class(class_entry)
    assert not is_class(func_entry)

    assert is_method(method_entry)
    assert not is_method(func_entry)

    assert is_variable(var_entry)
    assert not is_variable(func_entry)


def test_extract_symbol_type():
    """Test symbol type extraction from ctags fields."""
    # Extended format
    assert extract_symbol_type(';"	f') == "f"
    assert extract_symbol_type(';"	c') == "c"
    assert extract_symbol_type(';"	m') == "m"

    # Simple format
    assert extract_symbol_type("f") == "f"
    assert extract_symbol_type("c") == "c"

    # Invalid formats
    assert extract_symbol_type("") is None
    assert extract_symbol_type("invalid") is None
    assert extract_symbol_type("123") is None


def test_extract_line_number():
    """Test line number extraction from patterns."""
    # Numeric patterns
    assert extract_line_number("42") == 42
    assert extract_line_number("100") == 100

    # Regex patterns (no line number)
    assert extract_line_number("/^def test():$/") is None
    assert extract_line_number("/^class Test:$/") is None

    # Invalid patterns
    assert extract_line_number("invalid") is None


def test_extract_scope():
    """Test scope extraction from extra fields."""
    assert extract_scope(["class:TestClass"]) == "TestClass"
    assert extract_scope(["function:test_func"]) == "test_func"
    assert extract_scope(["namespace:TestNamespace"]) == "TestNamespace"
    assert extract_scope(["other:value", "class:MyClass"]) == "MyClass"
    assert extract_scope(["invalid"]) is None
    assert extract_scope([]) is None


def test_extract_language():
    """Test language extraction from extra fields."""
    assert extract_language(["language:python"]) == "python"
    assert extract_language(["language:javascript"]) == "javascript"
    assert extract_language(["other:value", "language:go"]) == "go"
    assert extract_language(["invalid"]) is None
    assert extract_language([]) is None


def test_parse_tags_line():
    """Test parsing individual ctags lines."""
    # Function entry
    line = '_async_inspect	src/ecreshore/cli/cluster/inspect.py	/^        async def _async_inspect():$/;"	f	function:inspect'
    entry = parse_tags_line(line)

    assert entry is not None
    assert entry.symbol == "_async_inspect"
    assert entry.file == "src/ecreshore/cli/cluster/inspect.py"
    assert entry.type == "f"
    assert entry.scope == "inspect"

    # Class entry
    line = 'AsyncBatchProcessor	src/ecreshore/services/async_batch_processor.py	/^class AsyncBatchProcessor:$/;"	c'
    entry = parse_tags_line(line)

    assert entry is not None
    assert entry.symbol == "AsyncBatchProcessor"
    assert entry.file == "src/ecreshore/services/async_batch_processor.py"
    assert entry.type == "c"

    # Variable entry with line number
    line = "DEFAULT_TIMEOUT	src/ecreshore/services/batch_config.py	42	v"
    entry = parse_tags_line(line)

    assert entry is not None
    assert entry.symbol == "DEFAULT_TIMEOUT"
    assert entry.type == "v"
    assert entry.line_number == 42

    # Invalid lines
    assert parse_tags_line("") is None
    assert parse_tags_line("incomplete	line") is None
    assert parse_tags_line("no	type	info	here") is None


def test_detect_tags_file():
    """Test tags file detection."""
    with TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)

        # Test with tags file in current directory
        tags_file = tmpdir / "tags"
        tags_file.write_text("test content")

        result = detect_tags_file(str(tmpdir))
        assert result == tags_file

        # Test with .tags file
        tags_file.unlink()
        hidden_tags = tmpdir / ".tags"
        hidden_tags.write_text("test content")

        result = detect_tags_file(str(tmpdir))
        assert result == hidden_tags

        # Test with no tags file
        hidden_tags.unlink()
        result = detect_tags_file(str(tmpdir))
        assert result is None


def test_parse_tags_file(sample_tags_file):
    """Test parsing a complete tags file."""
    entries = parse_tags_file(sample_tags_file)

    assert len(entries) == 5  # 5 non-header entries in sample

    # Check function entry
    func_entries = [e for e in entries if e.type == "f"]
    assert len(func_entries) == 1
    assert func_entries[0].symbol == "_async_inspect"

    # Check class entries
    class_entries = [e for e in entries if e.type == "c"]
    assert len(class_entries) == 2
    class_names = {e.symbol for e in class_entries}
    assert "AsyncBatchProcessor" in class_names
    assert "BatchConfig" in class_names

    # Check variable entry
    var_entries = [e for e in entries if e.type == "v"]
    assert len(var_entries) == 1
    assert var_entries[0].symbol == "DEFAULT_TIMEOUT"

    # Check method entry
    method_entries = [e for e in entries if e.type == "m"]
    assert len(method_entries) == 1
    assert method_entries[0].symbol == "validate_config"
    assert method_entries[0].scope == "BatchConfig"


def test_parse_tags_file_not_found():
    """Test parsing non-existent tags file."""
    with pytest.raises(FileNotFoundError):
        parse_tags_file(Path("/nonexistent/tags"))


def test_validate_tags_format(sample_tags_file):
    """Test tags file format validation."""
    info = validate_tags_format(sample_tags_file)

    assert info["valid"]
    assert info["format"] == "exuberant"
    assert info["sorted"]
    assert info["total_entries"] == 5
    assert info["symbol_types"]["f"] == 1
    assert info["symbol_types"]["c"] == 2
    assert info["symbol_types"]["v"] == 1
    assert info["symbol_types"]["m"] == 1


def test_validate_tags_format_invalid_file():
    """Test validation of invalid tags file."""
    with NamedTemporaryFile(mode="w", delete=False) as f:
        f.write("invalid content\nno tabs here\n")
        f.flush()

        info = validate_tags_format(Path(f.name))
        assert info["total_entries"] == 2  # Two lines counted
        # File is considered valid if it has entries, even if they don't parse correctly
        # The parsing happens separately and filters out invalid entries

    Path(f.name).unlink(missing_ok=True)


def test_parse_tags_file_auto_detect(sample_ctags_content):
    """Test auto-detection of tags file."""
    with TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)

        # Create tags file in directory
        tags_file = tmpdir / "tags"
        tags_file.write_text(sample_ctags_content)

        # Parse without specifying file path
        entries = parse_tags_file(working_dir=str(tmpdir))
        assert len(entries) == 5
