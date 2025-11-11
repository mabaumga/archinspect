"""
Application services implementing use cases.
These orchestrate domain logic and coordinate with adapters.
"""
import logging
from pathlib import Path
from typing import List, Optional

from django.db import transaction

from adapters.persistence.models import Application as ApplicationModel
from adapters.persistence.models import KIProvider as KIProviderModel
from adapters.persistence.models import MarkdownCorpus as MarkdownCorpusModel
from adapters.persistence.models import Prompt as PromptModel
from adapters.persistence.models import PromptRun as PromptRunModel
from adapters.persistence.models import Repository as RepositoryModel
from domain.entities import RepositoryDTO
from domain.ports import GitPlatformPort, KIClientPort, MarkdownCorpusPort, RepositoryMirrorPort

logger = logging.getLogger(__name__)


class RepositoryImportService:
    """Service for importing repositories from Git platforms."""

    def __init__(self, git_platform: GitPlatformPort):
        self.git_platform = git_platform

    def import_repositories(self, page_size: int = 100) -> dict:
        """
        Import all repositories from configured Git platform with pagination.

        Args:
            page_size: Number of repositories to fetch per page

        Returns:
            Dictionary with import statistics (total, created, updated)
        """
        logger.info("Starting repository import with pagination")
        total_count = 0
        created_count = 0
        updated_count = 0
        page = 1

        while True:
            logger.info(f"Fetching page {page} (page_size={page_size})")
            repos = self.git_platform.list_repositories(
                page_size=page_size,
                page_token=str(page)
            )

            if not repos:
                logger.info(f"No more repositories found on page {page}. Import complete.")
                break

            logger.info(f"Processing {len(repos)} repositories from page {page}")

            with transaction.atomic():
                for repo_dto in repos:
                    repo, created = RepositoryModel.objects.update_or_create(
                        external_id=repo_dto.external_id,
                        defaults={
                            "name": repo_dto.name,
                            "url": repo_dto.url,
                            "description": repo_dto.description,
                            "tech_stack": repo_dto.tech_stack,
                            "namespace_path": repo_dto.namespace_path,
                            "visibility": repo_dto.visibility,
                            "is_active": repo_dto.is_active,
                        },
                    )
                    action = "created" if created else "updated"
                    logger.debug(f"Repository {repo.name} {action}")
                    total_count += 1
                    if created:
                        created_count += 1
                    else:
                        updated_count += 1

            logger.info(f"Page {page} completed: {len(repos)} repositories processed")

            # Break if we got fewer repositories than the page size
            # This indicates we've reached the last page
            if len(repos) < page_size:
                logger.info(f"Last page reached (got {len(repos)} < {page_size})")
                break

            page += 1

        result = {
            "total": total_count,
            "created": created_count,
            "updated": updated_count,
        }
        logger.info(f"Repository import completed: {result}")
        return result


class RepositoryAssignmentService:
    """Service for assigning repositories to applications and ARTs."""

    @transaction.atomic
    def assign_to_application(self, repository_id: int, application_id: Optional[int]) -> RepositoryModel:
        """
        Assign repository to an application.

        Args:
            repository_id: Repository ID
            application_id: Application ID (None to unassign)

        Returns:
            Updated repository
        """
        repo = RepositoryModel.objects.get(pk=repository_id)
        if application_id:
            application = ApplicationModel.objects.get(pk=application_id)
            repo.application = application
            logger.info(f"Assigned repository {repo.name} to application {application.name}")
        else:
            repo.application = None
            logger.info(f"Unassigned repository {repo.name} from application")
        repo.save()
        return repo

    @transaction.atomic
    def assign_application_to_art(self, application_id: int, art_id: Optional[int]) -> ApplicationModel:
        """
        Assign application to an ART.

        Args:
            application_id: Application ID
            art_id: ART ID (None to unassign)

        Returns:
            Updated application
        """
        app = ApplicationModel.objects.get(pk=application_id)
        if art_id:
            from adapters.persistence.models import ART as ARTModel
            art = ARTModel.objects.get(pk=art_id)
            app.art = art
            logger.info(f"Assigned application {app.name} to ART {art.name}")
        else:
            app.art = None
            logger.info(f"Unassigned application {app.name} from ART")
        app.save()
        return app


class MarkdownCorpusService:
    """Service for generating markdown corpus from repository source."""

    def __init__(self, markdown_builder: MarkdownCorpusPort, mirror: RepositoryMirrorPort):
        self.markdown_builder = markdown_builder
        self.mirror = mirror

    def generate_corpus(
        self,
        repository_id: int,
        include_patterns: List[str],
        exclude_paths: List[str],
        max_bytes: int
    ) -> MarkdownCorpusModel:
        """
        Generate markdown corpus for a repository.

        Args:
            repository_id: Repository ID
            include_patterns: File patterns to include
            exclude_paths: Directories to exclude
            max_bytes: Maximum size in bytes

        Returns:
            MarkdownCorpus instance
        """
        repo = RepositoryModel.objects.get(pk=repository_id)
        logger.info(f"Generating markdown corpus for repository {repo.name}")

        # Ensure repository is mirrored locally
        if not repo.local_path or not Path(repo.local_path).exists():
            logger.info(f"Mirroring repository {repo.name}")
            from django.conf import settings
            target_dir = settings.REPO_DOWNLOAD_ROOT
            local_path = self.mirror.mirror_repository(
                repo.name,
                repo.url,
                repo.namespace_path,
                target_dir
            )
            repo.local_path = str(local_path)
            repo.save()

        # Build markdown corpus
        corpus_path = self.markdown_builder.build_corpus(
            Path(repo.local_path),
            include_patterns,
            exclude_paths,
            max_bytes
        )

        # Save corpus metadata
        file_size = corpus_path.stat().st_size
        is_complete = file_size < max_bytes

        corpus = MarkdownCorpusModel.objects.create(
            repository=repo,
            file_path=str(corpus_path),
            file_size_bytes=file_size,
            file_count=0,  # Will be populated by markdown builder
            is_complete=is_complete,
        )

        logger.info(f"Markdown corpus generated: {corpus_path} ({file_size} bytes)")
        return corpus


class PromptExecutionService:
    """Service for executing prompts against repositories."""

    def __init__(self, ki_client: KIClientPort):
        self.ki_client = ki_client

    @transaction.atomic
    def execute_prompt(
        self,
        repository_id: int,
        prompt_id: int,
        ki_provider_id: Optional[int] = None
    ) -> PromptRunModel:
        """
        Execute a prompt against a repository.

        Args:
            repository_id: Repository ID
            prompt_id: Prompt ID
            ki_provider_id: KI Provider ID (uses default if None)

        Returns:
            PromptRun instance
        """
        repo = RepositoryModel.objects.get(pk=repository_id)
        prompt = PromptModel.objects.get(pk=prompt_id)

        if ki_provider_id:
            ki_provider = KIProviderModel.objects.get(pk=ki_provider_id)
        else:
            from adapters.persistence.models import AppSettings
            settings = AppSettings.load()
            ki_provider = settings.default_ki_provider
            if not ki_provider:
                raise ValueError("No KI provider specified and no default configured")

        logger.info(f"Executing prompt '{prompt.title}' on repository {repo.name}")

        # Build request text (could include corpus context)
        request_text = prompt.prompt_text

        # Get latest corpus if available
        latest_corpus = repo.markdown_corpora.first()
        if latest_corpus:
            context = f"Repository: {repo.name}\nCorpus available at: {latest_corpus.file_path}"
        else:
            context = f"Repository: {repo.name}\nNo corpus generated yet"

        # Execute prompt via KI client
        try:
            response = self.ki_client.analyze(request_text, context)

            # Extract fields from response
            score_pct = response.get("score_pct")
            summary = response.get("description", "")
            improvement_suggestions = response.get("improvement_suggestions", {})
            endpoints = response.get("endpoints", {})

            prompt_run = PromptRunModel.objects.create(
                repository=repo,
                prompt=prompt,
                prompt_text_snapshot=prompt.prompt_text,  # Save snapshot for auditability
                ki_provider=ki_provider,
                request_text=request_text,
                response_json=response,
                score_pct=score_pct,
                summary=summary,
                improvement_suggestions=improvement_suggestions,
                endpoints=endpoints,
            )

            logger.info(f"Prompt execution completed: score={score_pct}")
            return prompt_run

        except Exception as e:
            logger.error(f"Prompt execution failed: {e}")
            raise
