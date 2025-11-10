"""
Management command to clone repositories from GitLab.
"""
import os
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand

from adapters.git_platform.gitlab_mirror_adapter import GitLabMirrorAdapter
from adapters.persistence.models import Repository


class Command(BaseCommand):
    help = "Clone or update repositories from GitLab"

    def add_arguments(self, parser):
        parser.add_argument(
            "--url",
            type=str,
            required=False,
            default=os.environ.get("GITLAB_URL", "https://gitlab.com"),
            help="GitLab instance URL (default: https://gitlab.com or GITLAB_URL env var)",
        )
        parser.add_argument(
            "--token",
            type=str,
            required=False,
            default=os.environ.get("GITLAB_TOKEN"),
            help="GitLab private access token (or use GITLAB_TOKEN env var)",
        )
        parser.add_argument(
            "--no-ssl-verify",
            action="store_true",
            help="Disable SSL certificate verification (not recommended)",
        )
        parser.add_argument(
            "--repo-id",
            type=int,
            required=False,
            help="Repository ID to clone (if not specified, clones all active repositories)",
        )
        parser.add_argument(
            "--target-dir",
            type=str,
            required=False,
            default=None,
            help="Target directory for cloning (default: REPO_DOWNLOAD_ROOT from settings)",
        )

    def handle(self, *args, **options):
        gitlab_url = options["url"]
        token = options["token"]
        ssl_verify = not options["no_ssl_verify"]
        repo_id = options["repo_id"]
        target_dir = options["target_dir"]

        # Use default target directory if not specified
        if not target_dir:
            target_dir = getattr(settings, "REPO_DOWNLOAD_ROOT", "/data/repos")

        # Validate token
        if not token:
            self.stdout.write(
                self.style.ERROR(
                    "GitLab token is required. Provide via --token or GITLAB_TOKEN environment variable."
                )
            )
            return

        self.stdout.write(f"GitLab instance: {gitlab_url}")
        self.stdout.write(f"Target directory: {target_dir}")
        self.stdout.write(f"SSL verification: {ssl_verify}")

        try:
            # Create GitLab mirror adapter
            mirror_adapter = GitLabMirrorAdapter(
                private_token=token,
                gitlab_url=gitlab_url,
                ssl_verify=ssl_verify
            )

            # Get repositories to clone
            if repo_id:
                repositories = [Repository.objects.get(pk=repo_id)]
                self.stdout.write(f"Cloning single repository (ID: {repo_id})")
            else:
                repositories = Repository.objects.filter(is_active=True)
                self.stdout.write(f"Cloning {repositories.count()} active repositories")

            # Clone each repository
            success_count = 0
            error_count = 0

            for repo in repositories:
                try:
                    self.stdout.write(f"\nProcessing: {repo.name} ({repo.namespace_path})")
                    self.stdout.write(f"  URL: {repo.url}")

                    # Clone or update repository
                    local_path = mirror_adapter.mirror_repository(
                        repo_name=repo.name,
                        repo_url=repo.url,
                        namespace_path=repo.namespace_path,
                        target_dir=Path(target_dir)
                    )

                    # Update repository model with local path
                    repo.local_path = str(local_path)
                    repo.save()

                    self.stdout.write(
                        self.style.SUCCESS(f"  ✓ Successfully mirrored to: {local_path}")
                    )
                    success_count += 1

                except Repository.DoesNotExist:
                    self.stdout.write(
                        self.style.ERROR(f"  ✗ Repository with ID {repo_id} not found")
                    )
                    error_count += 1

                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(f"  ✗ Failed to clone {repo.name}: {e}")
                    )
                    error_count += 1
                    # Continue with next repository

            # Summary
            self.stdout.write("\n" + "=" * 60)
            self.stdout.write(
                self.style.SUCCESS(f"Cloning completed: {success_count} successful, {error_count} failed")
            )

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Command failed: {e}"))
            raise
