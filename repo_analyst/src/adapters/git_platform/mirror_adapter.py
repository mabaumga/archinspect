"""
Repository mirror adapter for copying source code locally.
Uses testdata if available, otherwise would clone from Git.
"""
import logging
import shutil
from pathlib import Path

from django.conf import settings

from domain.ports import RepositoryMirrorPort

logger = logging.getLogger(__name__)


class LocalMirrorAdapter(RepositoryMirrorPort):
    """
    Adapter for mirroring repository source code.
    Prefers testdata over actual git cloning.
    """

    def mirror_repository(self, repo_name: str, repo_url: str, namespace_path: str, target_dir: Path) -> Path:
        """
        Mirror repository source code locally.

        First checks if repository exists in testdata/repos/, if so copies it.
        Otherwise would clone from Git (not implemented in this version).

        Args:
            repo_name: Repository name
            repo_url: Repository URL (for cloning)
            namespace_path: Namespace path for testdata lookup
            target_dir: Target directory for mirroring

        Returns:
            Path to mirrored repository
        """
        # Check if repository exists in testdata
        testdata_path = settings.TESTDATA_REPOS_ROOT / repo_name

        if testdata_path.exists() and testdata_path.is_dir():
            logger.info(f"Using testdata for repository {repo_name} from {testdata_path}")
            return self._copy_from_testdata(testdata_path, repo_name, target_dir)
        else:
            # In production, this would clone from Git
            # For now, create empty directory
            logger.warning(f"Repository {repo_name} not found in testdata, creating empty directory")
            return self._create_empty_mirror(repo_name, target_dir)

    def _copy_from_testdata(self, source_path: Path, repo_name: str, target_dir: Path) -> Path:
        """
        Copy repository from testdata to target directory.

        Args:
            source_path: Source path in testdata
            repo_name: Repository name
            target_dir: Target directory

        Returns:
            Path to copied repository
        """
        target_path = target_dir / repo_name

        # Create target directory if it doesn't exist
        target_dir.mkdir(parents=True, exist_ok=True)

        # Remove existing if present
        if target_path.exists():
            logger.info(f"Removing existing mirror at {target_path}")
            shutil.rmtree(target_path)

        # Copy repository
        logger.info(f"Copying repository from {source_path} to {target_path}")
        shutil.copytree(source_path, target_path)

        logger.info(f"Repository {repo_name} mirrored to {target_path}")
        return target_path

    def _create_empty_mirror(self, repo_name: str, target_dir: Path) -> Path:
        """
        Create empty directory for repository (placeholder).

        Args:
            repo_name: Repository name
            target_dir: Target directory

        Returns:
            Path to created directory
        """
        target_path = target_dir / repo_name
        target_path.mkdir(parents=True, exist_ok=True)

        # Create README to indicate this is a placeholder
        readme_path = target_path / "README.md"
        readme_path.write_text(
            f"# {repo_name}\n\n"
            "This is a placeholder directory. Repository source not available.\n"
        )

        logger.info(f"Created empty mirror at {target_path}")
        return target_path
