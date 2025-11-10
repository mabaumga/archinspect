"""
CSV adapter for importing repositories from TSV file.
This is a mock adapter for testing with local data.
"""
import csv
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from dateutil import parser as date_parser

from domain.entities import RepositoryDTO
from domain.ports import GitPlatformPort

logger = logging.getLogger(__name__)


class CSVMockAdapter(GitPlatformPort):
    """
    Mock adapter that reads repositories from a TSV file.

    The file should be TAB-delimited with columns:
    name, description, created_at, updated_at, visibility, is_active, web_url, namespace_path, external_id
    """

    def __init__(self, csv_path: Path):
        self.csv_path = csv_path
        if not csv_path.exists():
            raise FileNotFoundError(f"CSV file not found: {csv_path}")

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

        logger.info(f"Loaded {len(all_repositories)} total repositories, returning {len(paginated_repositories)} for page {page}")
        return paginated_repositories

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
