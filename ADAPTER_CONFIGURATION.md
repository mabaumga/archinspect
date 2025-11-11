# Source Code Repository Adapter Configuration

This document explains how to configure the source code repository adapter in Repo-Analyst.

## Overview

The application uses the **Factory Pattern** to create source code repository adapters. There are two implementations available:

1. **Mock Adapter** - For testing with local test data (CSV + local files)
2. **GitLab Adapter** - For production use with GitLab API

## Configuration

The adapter is configured via the `REPOSITORY_ADAPTER` environment variable.

### Using Mock Adapter (Default)

The mock adapter is useful for development and testing without access to GitLab.

```bash
# .env
REPOSITORY_ADAPTER=mock
```

**Requirements:**
- TSV file with repository metadata at `/testdata/test_repositories.tsv`
- Repository source code in `/testdata/repos/`

**Features:**
- Reads repository list from TSV file
- Copies repositories from local testdata directory
- No external API calls
- Fast and predictable

### Using GitLab Adapter

The GitLab adapter connects to a GitLab instance for production use.

```bash
# .env
REPOSITORY_ADAPTER=gitlab
GITLAB_URL=https://gitlab.example.com
GITLAB_ACCESS_TOKEN=your-access-token-here
GITLAB_SSL_VERIFY=true
```

**Requirements:**
- GitLab instance URL
- GitLab Personal Access Token with `read_api` and `read_repository` scopes
- Git installed on the system

**Features:**
- Fetches repository list from GitLab API
- Clones repositories using `git clone`
- Updates repositories using `git pull`
- Supports pagination for large repository lists

## GitLab Access Token

To create a GitLab Personal Access Token:

1. Go to GitLab → Settings → Access Tokens
2. Create a new token with these scopes:
   - `read_api` - To list repositories
   - `read_repository` - To clone repositories
3. Copy the token and add it to your `.env` file

## Usage in Code

The adapter is created automatically via the factory:

```python
from infrastructure.adapter_factory import AdapterFactory

# Create adapter based on configuration
adapter = AdapterFactory.create_source_code_repository_adapter()

# List repositories
repositories = adapter.list_repositories(page_size=100, page_token="1")

# Clone repository
path = adapter.clone_repository(
    repo_name="my-repo",
    repo_url="https://gitlab.com/group/my-repo.git",
    namespace_path="group/my-repo",
    target_dir=Path("/data/repos")
)

# Update repository
path = adapter.update_repository(Path("/data/repos/group/my-repo"))
```

## Architecture

The adapter system follows **Hexagonal Architecture** (Ports & Adapters):

```
Domain Layer:
  ├── SourceCodeRepositoryPort (Interface)

Adapter Layer:
  ├── MockSourceCodeRepositoryAdapter (Implementation)
  └── GitLabSourceCodeRepositoryAdapter (Implementation)

Infrastructure Layer:
  └── AdapterFactory (Factory)
```

### Port Interface

The `SourceCodeRepositoryPort` defines three operations:

```python
class SourceCodeRepositoryPort(ABC):
    def list_repositories(self, page_size, page_token) -> List[RepositoryDTO]
    def clone_repository(self, repo_name, repo_url, namespace_path, target_dir) -> Path
    def update_repository(self, local_path) -> Path
```

## Switching Adapters

To switch between adapters, simply change the environment variable:

```bash
# Development/Testing
export REPOSITORY_ADAPTER=mock

# Production
export REPOSITORY_ADAPTER=gitlab
export GITLAB_URL=https://gitlab.ruv.de
export GITLAB_ACCESS_TOKEN=your-token
```

Then restart the application. No code changes required!

## Troubleshooting

### Mock Adapter Issues

**Error: "CSV file not found"**
- Ensure `/testdata/test_repositories.tsv` exists
- Check file permissions

**Error: "Repository not found in testdata"**
- Verify repository exists in `/testdata/repos/`
- Check namespace path matches directory structure

### GitLab Adapter Issues

**Error: "GITLAB_URL environment variable is required"**
- Set `GITLAB_URL` in your `.env` file

**Error: "Failed to authenticate with GitLab"**
- Verify your `GITLAB_ACCESS_TOKEN` is valid
- Check token has required scopes (`read_api`, `read_repository`)

**Error: "Git clone failed"**
- Ensure `git` is installed: `git --version`
- Check GitLab URL is accessible
- Verify network connectivity

## Adding New Adapters

To add a new adapter (e.g., GitHub):

1. Create implementation class:
   ```python
   # src/adapters/git_platform/github_source_adapter.py
   class GitHubSourceCodeRepositoryAdapter(SourceCodeRepositoryPort):
       def list_repositories(self, ...): ...
       def clone_repository(self, ...): ...
       def update_repository(self, ...): ...
   ```

2. Add to factory:
   ```python
   # src/infrastructure/adapter_factory.py
   elif adapter_type == "github":
       return AdapterFactory._create_github_adapter()
   ```

3. Update environment variables:
   ```bash
   REPOSITORY_ADAPTER=github
   GITHUB_TOKEN=your-token
   ```
