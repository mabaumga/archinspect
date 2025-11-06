"""
Unit tests for CSV adapter.
"""
import pytest
from pathlib import Path

from adapters.git_platform.csv_adapter import CSVMockAdapter
from domain.entities import RepositoryDTO


def test_csv_adapter_reads_file(temp_csv_file):
    """Test that CSV adapter can read and parse TSV file."""
    adapter = CSVMockAdapter(temp_csv_file)
    repos = adapter.list_repositories()

    assert len(repos) == 1
    assert isinstance(repos[0], RepositoryDTO)
    assert repos[0].name == "test-repo"
    assert repos[0].external_id == "1234"
    assert repos[0].namespace_path == "test-org/test-project"
    assert repos[0].is_active is True


def test_csv_adapter_file_not_found():
    """Test that adapter raises error for non-existent file."""
    with pytest.raises(FileNotFoundError):
        CSVMockAdapter(Path("/non/existent/file.tsv"))


def test_csv_adapter_parses_dates(temp_csv_file):
    """Test that adapter parses ISO-8601 dates correctly."""
    adapter = CSVMockAdapter(temp_csv_file)
    repos = adapter.list_repositories()

    assert repos[0].created_at is not None
    assert repos[0].updated_at is not None
