"""
Management command to import repositories from GitLab instance.
"""
import os

from django.core.management.base import BaseCommand

from adapters.git_platform.gitlab_adapter import GitLabAdapter
from application.services import RepositoryImportService


class Command(BaseCommand):
    help = "Import repositories from GitLab instance"

    def add_arguments(self, parser):
        parser.add_argument(
            "--url",
            type=str,
            required=False,
            default=os.environ.get("GITLAB_URL", "https://gitlab.com"),
            help="GitLab instance URL (default: https://gitlab.com or GITLAB_URL env var)",
        )
        parser.add_argument(
            "--token",
            type=str,
            required=False,
            default=os.environ.get("GITLAB_TOKEN"),
            help="GitLab private access token (or use GITLAB_TOKEN env var)",
        )
        parser.add_argument(
            "--no-ssl-verify",
            action="store_true",
            help="Disable SSL certificate verification (not recommended)",
        )
        parser.add_argument(
            "--page-size",
            type=int,
            default=100,
            help="Number of repositories to fetch per page (default: 100)",
        )

    def handle(self, *args, **options):
        gitlab_url = options["url"]
        token = options["token"]
        ssl_verify = not options["no_ssl_verify"]
        page_size = options["page_size"]

        # Validate token
        if not token:
            self.stdout.write(
                self.style.ERROR(
                    "GitLab token is required. Provide via --token or GITLAB_TOKEN environment variable."
                )
            )
            return

        self.stdout.write(f"Importing repositories from GitLab: {gitlab_url}")
        self.stdout.write(f"SSL verification: {ssl_verify}")

        try:
            # Create GitLab adapter
            adapter = GitLabAdapter(
                private_token=token,
                gitlab_url=gitlab_url,
                ssl_verify=ssl_verify
            )

            # Create import service
            service = RepositoryImportService(adapter)

            # Import repositories
            self.stdout.write("Fetching repositories from GitLab...")
            count = service.import_repositories()

            self.stdout.write(
                self.style.SUCCESS(f"Successfully imported {count} repositories from GitLab")
            )

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Import failed: {e}"))
            raise
