"""
Management command to import repositories from CSV/TSV file.
"""
from django.conf import settings
from django.core.management.base import BaseCommand

from adapters.git_platform.csv_adapter import CSVMockAdapter
from application.services import RepositoryImportService


class Command(BaseCommand):
    help = "Import repositories from CSV/TSV file"

    def add_arguments(self, parser):
        parser.add_argument(
            "--file",
            type=str,
            default=None,
            help="Path to CSV/TSV file (defaults to testdata/test_repositories.tsv)",
        )

    def handle(self, *args, **options):
        csv_path = options["file"]
        if not csv_path:
            csv_path = settings.TESTDATA_CSV_PATH

        self.stdout.write(f"Importing repositories from: {csv_path}")

        try:
            # Create adapter and service
            adapter = CSVMockAdapter(csv_path)
            service = RepositoryImportService(adapter)

            # Import repositories
            count = service.import_repositories()

            self.stdout.write(
                self.style.SUCCESS(f"Successfully imported {count} repositories")
            )

        except FileNotFoundError as e:
            self.stdout.write(self.style.ERROR(f"File not found: {e}"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Import failed: {e}"))
            raise
