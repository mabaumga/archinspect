"""
BDD step definitions for repository import.
"""
import pytest
from pytest_bdd import given, when, then, scenario, parsers

from adapters.git_platform.csv_adapter import CSVMockAdapter
from adapters.persistence.models import Repository
from application.services import RepositoryImportService


@scenario("import_repositories.feature", "Import repositories from CSV")
def test_import_repositories():
    """Import repositories from CSV."""
    pass


@scenario("import_repositories.feature", "Import is idempotent")
def test_import_idempotent():
    """Import is idempotent."""
    pass


@pytest.fixture
@given("a CSV file with repository data")
def csv_file_with_data(temp_csv_file):
    """Create CSV file with test data."""
    return temp_csv_file


@pytest.fixture
@given("repositories have been imported once")
def imported_once(csv_file_with_data):
    """Import repositories once."""
    adapter = CSVMockAdapter(csv_file_with_data)
    service = RepositoryImportService(adapter)
    service.import_repositories()


@pytest.fixture
@when("I run the import command")
def run_import(csv_file_with_data):
    """Run import command."""
    adapter = CSVMockAdapter(csv_file_with_data)
    service = RepositoryImportService(adapter)
    count = service.import_repositories()
    return count


@pytest.fixture
@when("I run the import command again")
def run_import_again(csv_file_with_data, imported_once):
    """Run import command again."""
    adapter = CSVMockAdapter(csv_file_with_data)
    service = RepositoryImportService(adapter)
    count = service.import_repositories()
    return count


@pytest.mark.django_db
@then("repositories should be created in the database")
def check_repositories_created():
    """Check that repositories were created."""
    assert Repository.objects.count() > 0


@pytest.mark.django_db
@then("each repository should have correct attributes")
def check_repository_attributes():
    """Check repository attributes."""
    repo = Repository.objects.first()
    assert repo.name is not None
    assert repo.external_id is not None


@pytest.mark.django_db
@then("no duplicate repositories should be created")
def check_no_duplicates():
    """Check that no duplicates were created."""
    # Should still have only the original repositories
    assert Repository.objects.count() == 1
