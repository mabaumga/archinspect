"""
Integration tests for repository import service.
"""
import pytest
from pathlib import Path
#from django.test import TestCase

from adapters.git_platform.gitlab_source_adapter import  GitLabSourceCodeRepositoryAdapter


#@pytest.mark.django_db
class TestGitLabAdapter():
    """Test repository import functionality."""

    def test_gitlab_adapter(self):
        """Test that import service creates repositories in database."""
        
        from dotenv import load_dotenv
        import os
        # Laden aller Umgebungsvariablen aus der .env-Datei
        load_dotenv()
        # Auslesen einer spezifischen Variablen
        gitlabu_url = str(os.getenv("GITLAB_URL"))
        gitlab_token = str(os.getenv("GITLAB_ACCESS_TOKEN"))
        
        if (gitlab_token and gitlabu_url):        
            adapter =  GitLabSourceCodeRepositoryAdapter(gitlab_url=gitlabu_url,private_token=gitlab_token,ssl_verify=True)        
            list = adapter.list_repositories(10)           
            adapter.clone_repository(repo_name="contactmanagementsvc",repo_url="https://gitlab.ruv.de/art-operations/pathfinder/flowhub/services/contactmanagementsvc",namespace_path="art-operations",target_dir=Path("/home/marc/gitlab/"))                             
            assert list is not None
        else:
            print("Umgebungsvariablen nicht gesetzt")
        

        
    
