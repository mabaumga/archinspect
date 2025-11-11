"""
Adapter Factory for creating source code repository adapters.
Provides central configuration point for switching between implementations.
"""
import logging
import os
from pathlib import Path

from domain.ports import SourceCodeRepositoryPort

logger = logging.getLogger(__name__)


class AdapterFactory:
    """
    Factory for creating source code repository adapters.

    Configuration via environment variables:
    - REPOSITORY_ADAPTER: "mock" or "gitlab" (default: "mock")
    - GITLAB_URL: GitLab instance URL
    - GITLAB_ACCESS_TOKEN: GitLab access token
    - GITLAB_SSL_VERIFY: SSL verification (default: "true")
    """

    @staticmethod
    def create_source_code_repository_adapter() -> SourceCodeRepositoryPort:
        """
        Create source code repository adapter based on configuration.

        Returns:
            SourceCodeRepositoryPort implementation

        Raises:
            ValueError: If adapter type is unknown or configuration is invalid
        """
        adapter_type = os.getenv("REPOSITORY_ADAPTER", "mock").lower()

        logger.info(f"Creating source code repository adapter: type={adapter_type}")

        if adapter_type == "mock":
            return AdapterFactory._create_mock_adapter()
        elif adapter_type == "gitlab":
            return AdapterFactory._create_gitlab_adapter()
        else:
            raise ValueError(
                f"Unknown adapter type: {adapter_type}. "
                f"Supported types: 'mock', 'gitlab'"
            )

    @staticmethod
    def _create_mock_adapter() -> SourceCodeRepositoryPort:
        """
        Create mock adapter for testing.

        Returns:
            MockSourceCodeRepositoryAdapter instance
        """
        from adapters.git_platform.mock_adapter import MockSourceCodeRepositoryAdapter
        from django.conf import settings

        csv_path = settings.TESTDATA_CSV_PATH
        testdata_repos_root = settings.TESTDATA_REPOS_ROOT

        logger.info(f"Creating mock adapter: csv={csv_path}, repos={testdata_repos_root}")

        if not csv_path.exists():
            raise FileNotFoundError(
                f"Test data CSV not found: {csv_path}. "
                f"Please ensure testdata is available."
            )

        return MockSourceCodeRepositoryAdapter(
            csv_path=csv_path,
            testdata_repos_root=testdata_repos_root
        )

    @staticmethod
    def _create_gitlab_adapter() -> SourceCodeRepositoryPort:
        """
        Create GitLab adapter for production use.

        Returns:
            GitLabSourceCodeRepositoryAdapter instance

        Raises:
            ValueError: If required GitLab configuration is missing
        """
        from adapters.git_platform.gitlab_source_adapter import GitLabSourceCodeRepositoryAdapter

        gitlab_url = os.getenv("GITLAB_URL")
        gitlab_token = os.getenv("GITLAB_ACCESS_TOKEN")
        ssl_verify = os.getenv("GITLAB_SSL_VERIFY", "true").lower() == "true"

        if not gitlab_url:
            raise ValueError(
                "GITLAB_URL environment variable is required when using GitLab adapter"
            )

        if not gitlab_token:
            raise ValueError(
                "GITLAB_ACCESS_TOKEN environment variable is required when using GitLab adapter"
            )

        logger.info(f"Creating GitLab adapter: url={gitlab_url}, ssl_verify={ssl_verify}")

        return GitLabSourceCodeRepositoryAdapter(
            private_token=gitlab_token,
            gitlab_url=gitlab_url,
            ssl_verify=ssl_verify
        )
