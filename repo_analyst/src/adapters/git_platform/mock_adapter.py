"""
Mock adapter for source code repository operations.
Uses TSV file for repository listing and local testdata for cloning.
"""
import csv
import logging
import shutil
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from dateutil import parser as date_parser

from domain.entities import RepositoryDTO
from domain.ports import SourceCodeRepositoryPort

logger = logging.getLogger(__name__)


class MockSourceCodeRepositoryAdapter(SourceCodeRepositoryPort):
    """
    Mock implementation for testing without external dependencies.

    - Reads repository list from TSV file
    - Copies repositories from local testdata directory
    """

    def __init__(self, csv_path: Path, testdata_repos_root: Path):
        """
        Initialize mock adapter.

        Args:
            csv_path: Path to TSV file with repository metadata
            testdata_repos_root: Path to directory containing test repositories
        """
        self.csv_path = csv_path
        self.testdata_repos_root = testdata_repos_root

        if not csv_path.exists():
            raise FileNotFoundError(f"CSV file not found: {csv_path}")

        logger.info(f"Mock adapter initialized: csv={csv_path}, testdata={testdata_repos_root}")

    def list_repositories(self, page_size: int = 100, page_token: Optional[str] = None) -> List[RepositoryDTO]:
        """
        Read repositories from TSV file with pagination support.

        Args:
            page_size: Number of repositories per page
            page_token: Page number (as string) for pagination (default: "1")

        Returns:
            List of RepositoryDTO objects for the requested page
        """
        page = int(page_token) if page_token else 1
        logger.info(f"Reading repositories from {self.csv_path} (page={page}, page_size={page_size})")
        all_repositories = []

        try:
            with open(self.csv_path, 'r', encoding='utf-8') as f:
                # TSV file with TAB delimiter
                reader = csv.DictReader(f, delimiter='\t')

                for row in reader:
                    try:
                        # Parse is_active (convert to boolean)
                        is_active_str = row.get('is_active', '1').strip()
                        is_active = is_active_str in ('1', 'true', 'True', 'yes')

                        # Parse dates with flexible format
                        created_at = self._parse_date(row.get('created_at', ''))
                        updated_at = self._parse_date(row.get('updated_at', ''))

                        # Create DTO
                        repo = RepositoryDTO(
                            external_id=row['external_id'].strip(),
                            name=row['name'].strip(),
                            url=row['web_url'].strip(),
                            description=row.get('description', '').strip(),
                            namespace_path=row.get('namespace_path', '').strip(),
                            visibility=row.get('visibility', 'internal').strip(),
                            is_active=is_active,
                            created_at=created_at,
                            updated_at=updated_at,
                        )

                        all_repositories.append(repo)
                        logger.debug(f"Parsed repository: {repo.name}")

                    except Exception as e:
                        logger.error(f"Error parsing row: {row}, error: {e}")
                        continue

        except Exception as e:
            logger.error(f"Error reading CSV file: {e}")
            raise

        # Apply pagination
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        paginated_repositories = all_repositories[start_idx:end_idx]

        logger.info(
            f"Loaded {len(all_repositories)} total repositories, "
            f"returning {len(paginated_repositories)} for page {page}"
        )
        return paginated_repositories

    def clone_repository(self, repo_name: str, repo_url: str, namespace_path: str, target_dir: Path) -> Path:
        """
        Copy repository from testdata directory.

        Args:
            repo_name: Repository name
            repo_url: Repository URL (ignored in mock)
            namespace_path: Namespace path for locating testdata
            target_dir: Target directory for copying

        Returns:
            Path to copied repository
        """
        logger.info(f"Cloning repository '{repo_name}' (mock)")

        # Try to find repository in testdata
        # Strategy 1: Look for full namespace path
        source_path_1 = self.testdata_repos_root / namespace_path
        # Strategy 2: Look for just the repo name
        source_path_2 = self.testdata_repos_root / repo_name

        source_path = None
        if source_path_1.exists():
            source_path = source_path_1
        elif source_path_2.exists():
            source_path = source_path_2
        else:
            raise FileNotFoundError(
                f"Repository '{repo_name}' not found in testdata. "
                f"Expected at: {source_path_1} or {source_path_2}"
            )

        # Create target directory structure
        target_path = target_dir / namespace_path
        target_path.parent.mkdir(parents=True, exist_ok=True)

        # Copy repository
        if target_path.exists():
            logger.warning(f"Target path already exists, removing: {target_path}")
            shutil.rmtree(target_path)

        shutil.copytree(source_path, target_path)
        logger.info(f"Repository cloned from {source_path} to {target_path}")

        return target_path

    def update_repository(self, local_path: Path) -> Path:
        """
        Update repository (no-op in mock, just returns path).

        Args:
            local_path: Path to local repository

        Returns:
            Path to repository
        """
        logger.info(f"Updating repository '{local_path}' (mock - no-op)")
        if not local_path.exists():
            raise FileNotFoundError(f"Repository not found: {local_path}")
        return local_path

    def _parse_date(self, date_str: str) -> Optional[datetime]:
        """
        Parse date string with flexible format support.
        Handles ISO-8601 with/without timezone offset.

        Args:
            date_str: Date string to parse

        Returns:
            datetime object or None
        """
        if not date_str or not date_str.strip():
            return None

        try:
            # Use dateutil parser for flexible parsing
            dt = date_parser.parse(date_str)
            return dt
        except Exception as e:
            logger.warning(f"Could not parse date '{date_str}': {e}")
            return None
