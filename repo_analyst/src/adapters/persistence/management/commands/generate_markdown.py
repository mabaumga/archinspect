"""
Management command to generate markdown corpus for a repository.
"""
from django.conf import settings
from django.core.management.base import BaseCommand

from adapters.git_platform.markdown_builder import MarkdownCorpusBuilder
from adapters.git_platform.mirror_adapter import LocalMirrorAdapter
from adapters.persistence.models import Repository
from application.services import MarkdownCorpusService


class Command(BaseCommand):
    help = "Generate markdown corpus for a repository"

    def add_arguments(self, parser):
        parser.add_argument(
            "--repo-id",
            type=int,
            required=True,
            help="Repository ID",
        )
        parser.add_argument(
            "--max-bytes",
            type=int,
            default=None,
            help="Maximum size in bytes (default: from settings)",
        )

    def handle(self, *args, **options):
        repo_id = options["repo_id"]
        max_bytes = options["max_bytes"] or settings.MAX_CONCAT_BYTES

        try:
            repo = Repository.objects.get(pk=repo_id)
            self.stdout.write(f"Generating markdown corpus for repository: {repo.name}")

            # Create adapters and service
            markdown_builder = MarkdownCorpusBuilder()
            mirror_adapter = LocalMirrorAdapter()
            service = MarkdownCorpusService(markdown_builder, mirror_adapter)

            # Generate corpus
            corpus = service.generate_corpus(
                repo_id,
                settings.INCLUDE_PATTERNS,
                settings.EXCLUDE_PATHS,
                max_bytes
            )

            self.stdout.write(
                self.style.SUCCESS(
                    f"Successfully generated markdown corpus:\n"
                    f"  Path: {corpus.file_path}\n"
                    f"  Size: {corpus.file_size_bytes} bytes\n"
                    f"  Files: {corpus.file_count}\n"
                    f"  Complete: {corpus.is_complete}"
                )
            )

        except Repository.DoesNotExist:
            self.stdout.write(self.style.ERROR(f"Repository with ID {repo_id} not found"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Markdown generation failed: {e}"))
            raise
