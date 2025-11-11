"""
GitLab adapter for source code repository operations.
Uses GitLab API for repository listing and git commands for cloning.
"""
import logging
import subprocess
from pathlib import Path
from typing import List, Optional
import os
from urllib.parse import urlparse
import git, gitlab
from git.exc import GitCommandError

from gitlab.exceptions import GitlabError

from domain.entities import RepositoryDTO
from domain.ports import SourceCodeRepositoryPort

logger = logging.getLogger(__name__)


def parse_repo_path(git_web_url: str) -> str:
    u = urlparse(git_web_url)
    path = u.path.strip("/")
    if path.endswith(".git"):
        path = path[:-4]
    return path



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
        self.access_token = private_token
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
                #membership=True,
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
        
    def resolve_project(self, repo_path: str, git_web_url: str):
        logger.debug(f"resolve_project: repo_path='{repo_path}', url='{git_web_url}'")
        try:
            return self.gl.projects.get(repo_path)
        except gitlab.exceptions.GitlabGetError as e:
            logger.debug(f"projects.get('{repo_path}') failed: {e} (code={getattr(e, 'response_code', 'unknown')})")
            # Fallback: suche über Namen und vergleiche URLs

            base = os.path.basename(repo_path)
            candidates = self.gl.projects.list(search=base, per_page=50)
            for p in candidates:
                web = getattr(p, "web_url", "")
                http = getattr(p, "http_url_to_repo", "").rstrip(".git")
                if web == git_web_url or http == git_web_url.rstrip(".git"):
                    logger.debug(f"Kandidat gefunden: id={p.id}, ns={getattr(p, 'path_with_namespace', '')}")
                    return p

            raise    

    def clone_repository(self, repo_name: str, repo_url: str, namespace_path: str, target_dir: Path) -> Path:        
        repo_path = parse_repo_path(repo_url)
        logger.info(f"Update repository: path='{repo_path}', base='{target_dir}', url='{repo_url}'")
        try:
            project = self.resolve_project(repo_path, repo_url)
            repo_http = project.http_url_to_repo
            logger.debug(f"project.id={project.id}, ns={project.path_with_namespace}, http_url_to_repo={repo_http}")
            auth_url = repo_http.replace("https://", f"https://oauth2:{self.access_token}@")
            target_directory = os.path.join(target_dir, project.path_with_namespace)
            logger.debug(f"Ziel: {target_directory}")
            os.makedirs(target_directory, exist_ok=True)
            if os.path.isdir(os.path.join(target_directory, ".git")):
                repo = git.Repo(target_directory)
                logger.info("git pull ...")
                repo.remotes.origin.pull()
                logger.info("Pull OK")
            else:
                logger.info("git clone ...")
                git.Repo.clone_from(auth_url, target_directory)
                logger.info("Clone OK")
            return target_dir

        except GitCommandError as e:
            logger.exception(f"Git-Fehler beim Clone/Pull für '{repo_path}': {e}")
            raise
        except Exception as e:
            logger.exception(f"Unerwarteter Fehler bei '{repo_path}': {e}")
            raise
               

    def update_repository(self, local_path: Path) -> Path:
        repo = git.Repo(local_path)
        logger.info("git pull ...")
        repo.remotes.origin.pull()
        logger.info("Pull OK")
        return Path(local_path)
    
       

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
