"""
Integration tests for repository import service.
"""
import pytest
from django.test import TestCase

from adapters.git_platform.csv_adapter import CSVMockAdapter
from adapters.persistence.models import Repository as RepositoryModel
from application.services import RepositoryImportService


@pytest.mark.django_db
class TestRepositoryImport(TestCase):
    """Test repository import functionality."""

    def test_import_creates_repositories(self, temp_csv_file):
        """Test that import service creates repositories in database."""
        adapter = CSVMockAdapter(temp_csv_file)
        service = RepositoryImportService(adapter)

        count = service.import_repositories()

        assert count == 1
        assert RepositoryModel.objects.count() == 1

        repo = RepositoryModel.objects.first()
        assert repo.name == "test-repo"
        assert repo.external_id == "1234"

    def test_import_is_idempotent(self, temp_csv_file):
        """Test that importing same data twice doesn't create duplicates."""
        adapter = CSVMockAdapter(temp_csv_file)
        service = RepositoryImportService(adapter)

        # Import twice
        service.import_repositories()
        service.import_repositories()

        # Should still have only one repository
        assert RepositoryModel.objects.count() == 1
