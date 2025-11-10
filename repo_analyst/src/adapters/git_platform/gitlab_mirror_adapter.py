"""
GitLab mirror adapter for cloning and updating repositories.
Uses python-gitlab and GitPython for repository operations.
"""
import logging
import os
from pathlib import Path
from urllib.parse import urlparse

import git
import gitlab
from git.exc import GitCommandError
from gitlab.exceptions import GitlabError, GitlabGetError

from domain.ports import RepositoryMirrorPort

logger = logging.getLogger(__name__)


def mask_token(token: str) -> str:
    """Mask token for logging purposes."""
    return (token[:4] + "...") if token else "<empty>"


def parse_repo_path(git_web_url: str) -> str:
    """
    Parse repository path from Git web URL.

    Args:
        git_web_url: Full web URL to the repository

    Returns:
        Repository path without .git suffix
    """
    u = urlparse(git_web_url)
    path = u.path.strip("/")
    if path.endswith(".git"):
        path = path[:-4]
    return path


class GitLabMirrorAdapter(RepositoryMirrorPort):
    """
    Adapter for mirroring GitLab repositories locally.
    Supports both clone and pull operations with authentication.

    Args:
        private_token: GitLab private access token
        gitlab_url: GitLab instance URL (e.g., 'https://gitlab.com')
        ssl_verify: Whether to verify SSL certificates (default: True)
    """

    def __init__(self, private_token: str, gitlab_url: str, ssl_verify: bool = True):
        """
        Initialize GitLab mirror adapter.

        Args:
            private_token: GitLab private access token for authentication
            gitlab_url: GitLab instance base URL
            ssl_verify: Whether to verify SSL certificates
        """
        logger.debug(f"Init GitLab Mirror: base='{gitlab_url}', token='{mask_token(private_token)}', ssl_verify={ssl_verify}")

        try:
            self.gl = gitlab.Gitlab(gitlab_url, private_token=private_token, ssl_verify=ssl_verify)
            self.access_token = private_token
            # Test authentication
            self.gl.auth()
            logger.info(f"Successfully authenticated GitLab mirror adapter at {gitlab_url}")
        except GitlabError as e:
            logger.error(f"Failed to authenticate with GitLab: {e}")
            raise

    def mirror_repository(self, repo_name: str, repo_url: str, namespace_path: str, target_dir: Path) -> Path:
        """
        Mirror repository from GitLab by cloning or pulling.

        Args:
            repo_name: Repository name
            repo_url: Repository web URL
            namespace_path: Repository namespace path (e.g., 'group/project')
            target_dir: Target directory for mirroring

        Returns:
            Path to mirrored repository
        """
        logger.info(f"Mirror repository: name='{repo_name}', url='{repo_url}', namespace='{namespace_path}'")

        try:
            # Use update_repository logic from provided GitLabRepositoryService
            return self.update_repository(repo_url, str(target_dir))

        except Exception as e:
            logger.error(f"Failed to mirror repository {repo_name}: {e}")
            raise

    def resolve_project(self, repo_path: str, git_web_url: str):
        """
        Resolve GitLab project by path or web URL.

        First tries to get project by path directly.
        If that fails, searches by name and compares URLs.

        Args:
            repo_path: Repository path (e.g., 'group/project')
            git_web_url: Repository web URL

        Returns:
            GitLab project object

        Raises:
            GitlabGetError: If project cannot be found
        """
        logger.debug(f"resolve_project: repo_path='{repo_path}', url='{git_web_url}'")

        try:
            return self.gl.projects.get(repo_path)

        except GitlabGetError as e:
            logger.debug(f"projects.get('{repo_path}') failed: {e} (code={getattr(e, 'response_code', 'unknown')})")

            # Fallback: search by name and compare URLs
            base = os.path.basename(repo_path)
            candidates = self.gl.projects.list(search=base, per_page=50)

            for p in candidates:
                web = getattr(p, "web_url", "")
                http = getattr(p, "http_url_to_repo", "").rstrip(".git")

                if web == git_web_url or http == git_web_url.rstrip(".git"):
                    logger.debug(f"Found candidate: id={p.id}, ns={getattr(p, 'path_with_namespace', '')}")
                    return p

            # If no match found, re-raise original exception
            raise

    def update_repository(self, git_web_url: str, base_directory: str) -> Path:
        """
        Clone or pull a GitLab repository.

        If repository exists locally, performs git pull.
        Otherwise, clones the repository.

        Args:
            git_web_url: Repository web URL
            base_directory: Base directory for repositories

        Returns:
            Path to repository directory

        Raises:
            GitCommandError: If git operations fail
            GitlabError: If GitLab API operations fail
        """
        repo_path = parse_repo_path(git_web_url)
        logger.info(f"Update repository: path='{repo_path}', base='{base_directory}', url='{git_web_url}'")

        try:
            # Resolve project from GitLab
            project = self.resolve_project(repo_path, git_web_url)
            repo_http = project.http_url_to_repo

            logger.debug(f"project.id={project.id}, ns={project.path_with_namespace}, http_url_to_repo={repo_http}")

            # Build authenticated URL
            auth_url = repo_http.replace("https://", f"https://oauth2:{self.access_token}@")

            # Determine target directory using namespace path
            target_directory = os.path.join(base_directory, project.path_with_namespace)
            logger.debug(f"Target: {target_directory}")

            # Create target directory if it doesn't exist
            os.makedirs(target_directory, exist_ok=True)

            # Check if repository already exists
            git_dir = os.path.join(target_directory, ".git")

            if os.path.isdir(git_dir):
                # Repository exists, perform pull
                logger.info(f"Repository exists at {target_directory}, performing git pull...")
                repo = git.Repo(target_directory)

                # Ensure we're on the default branch
                try:
                    origin = repo.remotes.origin
                    origin.pull()
                    logger.info("Pull completed successfully")
                except Exception as e:
                    logger.warning(f"Pull failed, will try to continue: {e}")

            else:
                # Repository doesn't exist, perform clone
                logger.info(f"Cloning repository to {target_directory}...")
                git.Repo.clone_from(auth_url, target_directory)
                logger.info("Clone completed successfully")

            return Path(target_directory)

        except GitCommandError as e:
            logger.exception(f"Git error while cloning/pulling '{repo_path}': {e}")
            raise

        except GitlabError as e:
            logger.exception(f"GitLab API error for '{repo_path}': {e}")
            raise

        except Exception as e:
            logger.exception(f"Unexpected error for '{repo_path}': {e}")
            raise
