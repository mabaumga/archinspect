"""
Pytest configuration and fixtures.
"""
import pytest
from pathlib import Path

# Configure Django
import os
import sys

# Add src to path
src_path = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(src_path))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

import django
django.setup()


@pytest.fixture
def sample_repository_dto():
    """Sample RepositoryDTO for testing."""
    from domain.entities import RepositoryDTO
    from datetime import datetime

    return RepositoryDTO(
        external_id="1234",
        name="test-repo",
        url="https://git.example.com/test-repo",
        description="Test repository",
        tech_stack="python,django",
        namespace_path="test-org/test-project",
        visibility="internal",
        is_active=True,
        created_at=datetime.now(),
        updated_at=datetime.now()
    )


@pytest.fixture
def temp_csv_file(tmp_path):
    """Create a temporary CSV file for testing."""
    csv_content = """name\tdescription\tcreated_at\tupdated_at\tvisibility\tis_active\tweb_url\tnamespace_path\texternal_id
test-repo\tTest Repository\t2024-01-01T10:00:00+01:00\t2024-01-02T10:00:00+01:00\tinternal\t1\thttps://git.example.com/test-repo\ttest-org/test-project\t1234
"""
    csv_path = tmp_path / "test_repos.tsv"
    csv_path.write_text(csv_content)
    return csv_path
