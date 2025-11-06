"""
Domain ports (interfaces) for Repo-Analyst application.
These define the contracts that adapters must implement.
"""
from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Optional

from domain.entities import RepositoryDTO


class GitPlatformPort(ABC):
    """Port for Git platform integration (GitLab, GitHub, etc.)"""

    @abstractmethod
    def list_repositories(self, page_size: int = 100, page_token: Optional[str] = None) -> List[RepositoryDTO]:
        """
        List repositories from the Git platform.

        Args:
            page_size: Number of repositories per page
            page_token: Pagination token for next page

        Returns:
            List of RepositoryDTO objects
        """
        pass


class KIClientPort(ABC):
    """Port for KI/AI client integration"""

    @abstractmethod
    def analyze(self, prompt_text: str, context: str = "") -> dict:
        """
        Send analysis request to KI provider.

        Args:
            prompt_text: The prompt to send
            context: Additional context (e.g., code corpus)

        Returns:
            Dictionary with analysis results
        """
        pass


class MarkdownCorpusPort(ABC):
    """Port for generating markdown corpus from repository"""

    @abstractmethod
    def build_corpus(
        self,
        repo_path: Path,
        include_patterns: List[str],
        exclude_paths: List[str],
        max_bytes: int
    ) -> Path:
        """
        Build markdown corpus from repository source code.

        Args:
            repo_path: Path to repository
            include_patterns: File patterns to include (e.g., *.py)
            exclude_paths: Directories to exclude
            max_bytes: Maximum size in bytes (450KB limit)

        Returns:
            Path to generated markdown file
        """
        pass


class RepositoryMirrorPort(ABC):
    """Port for mirroring repository source code"""

    @abstractmethod
    def mirror_repository(self, repo_name: str, repo_url: str, namespace_path: str, target_dir: Path) -> Path:
        """
        Mirror repository source code locally.

        Args:
            repo_name: Repository name
            repo_url: Repository URL (for cloning)
            namespace_path: Namespace path for testdata lookup
            target_dir: Target directory for mirroring

        Returns:
            Path to mirrored repository
        """
        pass
