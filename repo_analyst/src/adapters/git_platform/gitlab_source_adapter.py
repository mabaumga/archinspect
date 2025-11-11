"""
GitLab adapter for source code repository operations.
Uses GitLab API for repository listing and git commands for cloning.
"""
import logging
import subprocess
from pathlib import Path
from typing import List, Optional

import gitlab
from gitlab.exceptions import GitlabError

from domain.entities import RepositoryDTO
from domain.ports import SourceCodeRepositoryPort

logger = logging.getLogger(__name__)


def mask_token(token: str) -> str:
    """Mask token for logging purposes."""
    return (token[:4] + "...") if token else "<empty>"


class GitLabSourceCodeRepositoryAdapter(SourceCodeRepositoryPort):
    """
    GitLab implementation for source code repository operations.

    - Uses GitLab API for listing repositories
    - Uses git clone/pull for repository operations
    """

    def __init__(self, private_token: str, gitlab_url: str, ssl_verify: bool = True):
        """
        Initialize GitLab adapter.

        Args:
            private_token: GitLab private access token
            gitlab_url: GitLab instance URL
            ssl_verify: Whether to verify SSL certificates
        """
        logger.debug(
            f"Init GitLab: base='{gitlab_url}', "
            f"token='{mask_token(private_token)}', ssl_verify={ssl_verify}"
        )

        try:
            self.gl = gitlab.Gitlab(gitlab_url, private_token=private_token, ssl_verify=ssl_verify)
            # Test authentication
            self.gl.auth()
            logger.info(f"Successfully authenticated with GitLab at {gitlab_url}")
        except GitlabError as e:
            logger.error(f"Failed to authenticate with GitLab: {e}")
            raise

        self.gitlab_url = gitlab_url
        self.ssl_verify = ssl_verify

    def list_repositories(self, page_size: int = 100, page_token: Optional[str] = None) -> List[RepositoryDTO]:
        """
        List all accessible repositories from GitLab.

        Args:
            page_size: Number of repositories per page (default: 100)
            page_token: Page number for pagination (default: None for first page)

        Returns:
            List of RepositoryDTO objects
        """
        logger.info(f"Fetching repositories from GitLab (page_size={page_size}, page={page_token or 1})")
        repositories = []

        try:
            # Determine page number
            page = int(page_token) if page_token else 1

            # Fetch projects with pagination
            projects = self.gl.projects.list(
                page=page,
                per_page=page_size,
                # Get all projects the user has access to
                membership=True,
                # Include archived projects
                archived=False,
                # Order by last activity
                order_by='last_activity_at',
                sort='desc'
            )

            logger.info(f"Retrieved {len(projects)} projects from GitLab")

            # Convert GitLab projects to RepositoryDTO
            for project in projects:
                try:
                    repo_dto = self._convert_project_to_dto(project)
                    repositories.append(repo_dto)
                    logger.debug(f"Converted project: {repo_dto.name}")

                except Exception as e:
                    logger.error(f"Error converting project {getattr(project, 'id', 'unknown')}: {e}")
                    continue

            logger.info(f"Successfully converted {len(repositories)} repositories")

        except GitlabError as e:
            logger.error(f"GitLab API error: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error fetching repositories: {e}")
            raise

        return repositories

    def clone_repository(self, repo_name: str, repo_url: str, namespace_path: str, target_dir: Path) -> Path:
        """
        Clone repository using git clone.

        Args:
            repo_name: Repository name
            repo_url: Repository URL (HTTP or SSH)
            namespace_path: Namespace path
            target_dir: Target directory for cloning

        Returns:
            Path to cloned repository
        """
        target_path = target_dir / namespace_path
        target_path.parent.mkdir(parents=True, exist_ok=True)

        if target_path.exists():
            logger.warning(f"Repository already exists at {target_path}, updating instead")
            return self.update_repository(target_path)

        logger.info(f"Cloning repository '{repo_name}' from {repo_url}")

        try:
            # Clone repository
            cmd = ["git", "clone", repo_url, str(target_path)]
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=600  # 10 minutes timeout
            )

            if result.returncode != 0:
                raise RuntimeError(
                    f"Git clone failed with exit code {result.returncode}: {result.stderr}"
                )

            logger.info(f"Successfully cloned repository to {target_path}")
            return target_path

        except subprocess.TimeoutExpired:
            logger.error(f"Git clone timed out for {repo_url}")
            raise
        except Exception as e:
            logger.error(f"Error cloning repository: {e}")
            raise

    def update_repository(self, local_path: Path) -> Path:
        """
        Update repository using git pull.

        Args:
            local_path: Path to local repository

        Returns:
            Path to updated repository
        """
        if not local_path.exists():
            raise FileNotFoundError(f"Repository not found: {local_path}")

        logger.info(f"Updating repository at {local_path}")

        try:
            # Pull latest changes
            cmd = ["git", "-C", str(local_path), "pull"]
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300  # 5 minutes timeout
            )

            if result.returncode != 0:
                logger.warning(
                    f"Git pull failed with exit code {result.returncode}: {result.stderr}"
                )
                # Don't raise error, just log warning - repository might be dirty
            else:
                logger.info(f"Successfully updated repository at {local_path}")

            return local_path

        except subprocess.TimeoutExpired:
            logger.error(f"Git pull timed out for {local_path}")
            raise
        except Exception as e:
            logger.error(f"Error updating repository: {e}")
            raise

    def _convert_project_to_dto(self, project) -> RepositoryDTO:
        """
        Convert GitLab project object to RepositoryDTO.

        Args:
            project: GitLab project object

        Returns:
            RepositoryDTO object
        """
        # Extract visibility level
        visibility = getattr(project, 'visibility', 'internal')

        # Determine if project is active (not archived)
        is_active = not getattr(project, 'archived', False)

        # Extract dates
        created_at = getattr(project, 'created_at', None)
        updated_at = getattr(project, 'last_activity_at', None)

        # Parse dates if they are strings
        if created_at and isinstance(created_at, str):
            from dateutil import parser as date_parser
            try:
                created_at = date_parser.parse(created_at)
            except Exception as e:
                logger.warning(f"Could not parse created_at '{created_at}': {e}")
                created_at = None

        if updated_at and isinstance(updated_at, str):
            from dateutil import parser as date_parser
            try:
                updated_at = date_parser.parse(updated_at)
            except Exception as e:
                logger.warning(f"Could not parse updated_at '{updated_at}': {e}")
                updated_at = None

        # Build RepositoryDTO
        repo_dto = RepositoryDTO(
            external_id=str(project.id),
            name=project.name,
            url=project.web_url,
            description=getattr(project, 'description', '') or '',
            namespace_path=getattr(project, 'path_with_namespace', ''),
            visibility=visibility,
            is_active=is_active,
            created_at=created_at,
            updated_at=updated_at,
            # Tech stack could be derived from topics/tags if available
            tech_stack=', '.join(getattr(project, 'topics', []) or getattr(project, 'tag_list', []))
        )

        return repo_dto
