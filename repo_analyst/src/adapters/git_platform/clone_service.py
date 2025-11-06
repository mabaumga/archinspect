"""
Git Clone Service - simulates cloning repositories from GitLab.
In production, this would use actual git commands.
For testing, it copies from testdata directory.
"""
import logging
import os
import shutil
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


class GitCloneService:
    """
    Service for cloning repositories.
    Mock implementation that copies from testdata directory.
    """

    def __init__(self, testdata_root: str = "/home/marc/git/archinspect/testdata/repos"):
        self.testdata_root = Path(testdata_root)

    def clone_repository(
        self,
        repo_name: str,
        namespace_path: str,
        target_root: str,
        source_url: Optional[str] = None
    ) -> Path:
        """
        Clone a repository to the target location.

        Args:
            repo_name: Name of the repository (e.g., "arvendatenkurier")
            namespace_path: GitLab namespace path (e.g., "art-operations/krake")
            target_root: Root directory where repos are cloned (e.g., "/data/repos")
            source_url: GitLab URL (ignored in mock, used for logging)

        Returns:
            Path to the cloned repository

        Raises:
            FileNotFoundError: If source repository not found in testdata
            IOError: If copy operation fails
        """
        # Normalize repository name for testdata lookup
        # Handle variations like "ArvenDatenKurier" -> "arvendatenkurier"
        normalized_name = self._normalize_repo_name(repo_name)

        # Source: testdata directory
        source_path = self.testdata_root / normalized_name

        if not source_path.exists():
            # Try original name if normalized doesn't exist
            source_path = self.testdata_root / repo_name

        if not source_path.exists():
            raise FileNotFoundError(
                f"Repository '{repo_name}' not found in testdata. "
                f"Expected at: {source_path} or {self.testdata_root / normalized_name}"
            )

        # Target: organized by namespace
        target_root_path = Path(target_root)
        target_path = target_root_path / namespace_path / repo_name

        logger.info(
            f"Cloning repository '{repo_name}' from {source_path} to {target_path}",
            extra={"source": str(source_path), "target": str(target_path), "url": source_url}
        )

        # Remove existing directory if present
        if target_path.exists():
            logger.info(f"Removing existing directory: {target_path}")
            shutil.rmtree(target_path)

        # Create parent directories
        target_path.parent.mkdir(parents=True, exist_ok=True)

        # Copy repository (simulates git clone)
        try:
            shutil.copytree(source_path, target_path)
            logger.info(
                f"Successfully cloned repository '{repo_name}'",
                extra={"target": str(target_path), "size_mb": self._get_dir_size(target_path) / 1024 / 1024}
            )
        except Exception as e:
            logger.error(f"Failed to clone repository '{repo_name}': {e}")
            raise IOError(f"Failed to clone repository: {e}") from e

        return target_path

    def _normalize_repo_name(self, name: str) -> str:
        """
        Normalize repository name for testdata lookup.
        Handles different naming conventions.
        """
        # Convert to lowercase
        normalized = name.lower()

        # Remove common suffixes
        for suffix in ["-main", "-develop", "-dev", "-master"]:
            if normalized.endswith(suffix):
                normalized = normalized[:-len(suffix)]
                break

        # Handle special cases
        name_mappings = {
            "arvendatenkurier": "arvendatenkurier",
            "flowhub azure iac": "flowhub-azure-iac",
            "yepwebsvc": "yepwebsvc",
            "agentcommunicationsvc": "agentcommunicationsvc",
            "contactmanagementsvc": "contactmanagementsvc",
        }

        return name_mappings.get(normalized, normalized)

    def _get_dir_size(self, path: Path) -> int:
        """Calculate total size of directory in bytes."""
        total = 0
        try:
            for entry in path.rglob("*"):
                if entry.is_file():
                    total += entry.stat().st_size
        except Exception:
            pass
        return total

    def is_cloned(self, local_path: str) -> bool:
        """Check if repository is already cloned at the given path."""
        if not local_path:
            return False
        path = Path(local_path)
        return path.exists() and path.is_dir() and any(path.iterdir())

    def update_or_clone_repository(
        self,
        repo_name: str,
        namespace_path: str,
        target_root: str,
        source_url: Optional[str] = None,
        local_path: Optional[str] = None
    ) -> tuple[Path, bool]:
        """
        Update repository if it exists, otherwise clone it.

        Args:
            repo_name: Name of the repository
            namespace_path: GitLab namespace path
            target_root: Root directory where repos are cloned
            source_url: GitLab URL (ignored in mock)
            local_path: Existing local path if already cloned

        Returns:
            Tuple of (Path to repository, was_updated: bool)
            was_updated is True if repository was updated, False if newly cloned

        Raises:
            FileNotFoundError: If source repository not found in testdata
            IOError: If copy operation fails
        """
        # Check if repository is already cloned
        is_already_cloned = self.is_cloned(local_path) if local_path else False

        if is_already_cloned:
            logger.info(f"Updating existing repository '{repo_name}' at {local_path}")
        else:
            logger.info(f"Cloning new repository '{repo_name}'")

        # Both update and clone use the same operation in mock
        # (In production, update would use 'git pull' instead)
        cloned_path = self.clone_repository(
            repo_name=repo_name,
            namespace_path=namespace_path,
            target_root=target_root,
            source_url=source_url
        )

        return cloned_path, is_already_cloned

    def get_clone_status(self, local_path: str) -> dict:
        """
        Get status information about a cloned repository.

        Returns:
            Dictionary with status information (exists, file_count, size_mb, etc.)
        """
        if not local_path:
            return {"exists": False}

        path = Path(local_path)

        if not path.exists():
            return {"exists": False}

        try:
            file_count = sum(1 for _ in path.rglob("*") if _.is_file())
            size_bytes = self._get_dir_size(path)

            return {
                "exists": True,
                "path": str(path),
                "file_count": file_count,
                "size_mb": round(size_bytes / 1024 / 1024, 2),
                "size_bytes": size_bytes,
            }
        except Exception as e:
            logger.error(f"Error getting clone status for {local_path}: {e}")
            return {
                "exists": True,
                "error": str(e)
            }
