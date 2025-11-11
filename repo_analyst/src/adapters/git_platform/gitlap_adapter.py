
from pathlib import Path

from domain.ports import RepositoryMirrorPort,GitPlatformPort  # Passe ggf. deinen Import-Pfad an

class GitLabRepositoryService(RepositoryMirrorPort,GitPlatformPort):
    def __init__(self, private_token: str, gitlab_url: str):
        logger.debug(f"Init GitLab: base='{gitlab_url}', token='{mask_token(private_token)}'")
        self.gl = gitlab.Gitlab(gitlab_url, private_token=private_token, ssl_verify=True)
        self.access_token = private_token

    # ... (resolve_project und parse_repo_path wie gehabt) ...
    
    
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
    
    
    
    
    
    

    def mirror_repository(
        self, 
        repo_name: str, 
        repo_url: str, 
        namespace_path: str, 
        target_dir: Path

    ) -> Path:
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
        # Kombiniere Zielverzeichnis mit Namespace-Path

        target_directory = target_dir / namespace_path

        try:
            # Hole Projekt und auth_url wie bisher

            repo_path = parse_repo_path(repo_url)
            project = self.resolve_project(repo_path, repo_url)
            repo_http = project.http_url_to_repo

            auth_url = repo_http.replace("https://", f"https://oauth2:{self.access_token}@")

            logger.debug(f"Ziel: {target_directory}")
            os.makedirs(target_directory, exist_ok=True)
            git_dir = target_directory / ".git"
            if git_dir.is_dir():
                repo = git.Repo(str(target_directory))
                logger.info("git pull ...")
                repo.remotes.origin.pull()
                logger.info("Pull OK")
            else:
                logger.info("git clone ...")
                git.Repo.clone_from(auth_url, str(target_directory))
                logger.info("Clone OK")

            return target_directory

        except GitCommandError as e:
            logger.exception(f"Git-Fehler beim Clone/Pull für '{repo_name}': {e}")
            raise

        except Exception as e:
            logger.exception(f"Unerwarteter Fehler bei '{repo_name}': {e}")
            raise

