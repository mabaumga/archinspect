"""
Backup and restore service for database tables.
Exports/imports all business data as JSON files.
"""
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List

from django.core import serializers
from django.db import transaction

from adapters.persistence.models import (
    ART,
    Application,
    AppSettings,
    KIProvider,
    MarkdownCorpus,
    Prompt,
    PromptRun,
    Repository,
)

logger = logging.getLogger(__name__)


class BackupService:
    """Service for creating and restoring database backups."""

    # Models to backup (in dependency order for restore)
    MODELS = [
        ART,
        Application,
        Repository,
        Prompt,
        KIProvider,
        PromptRun,
        AppSettings,
        MarkdownCorpus,
    ]

    def __init__(self, backup_root: Path):
        """
        Initialize backup service.

        Args:
            backup_root: Root directory for backups
        """
        self.backup_root = Path(backup_root)
        self.backup_root.mkdir(parents=True, exist_ok=True)

    def create_backup(self, name: str = None) -> Path:
        """
        Create a backup of all business tables.

        Args:
            name: Optional name for the backup (defaults to timestamp)

        Returns:
            Path to backup directory

        Raises:
            Exception: If backup creation fails
        """
        # Generate backup name
        if not name:
            name = datetime.now().strftime("%Y%m%d_%H%M%S")

        backup_dir = self.backup_root / name
        backup_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f"Creating backup: {backup_dir}")

        try:
            # Backup each model
            for model in self.MODELS:
                model_name = model._meta.model_name
                file_path = backup_dir / f"{model_name}.json"

                # Serialize all objects
                queryset = model.objects.all()
                data = serializers.serialize('json', queryset, indent=2)

                # Write to file
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(data)

                count = queryset.count()
                logger.info(f"Backed up {count} {model_name} records")

            # Create metadata file
            metadata = {
                "created_at": datetime.now().isoformat(),
                "name": name,
                "models": [m._meta.model_name for m in self.MODELS],
                "counts": {m._meta.model_name: m.objects.count() for m in self.MODELS}
            }

            metadata_path = backup_dir / "metadata.json"
            with open(metadata_path, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2)

            logger.info(f"Backup completed: {backup_dir}")
            return backup_dir

        except Exception as e:
            logger.error(f"Backup failed: {e}", exc_info=True)
            # Clean up failed backup
            if backup_dir.exists():
                import shutil
                shutil.rmtree(backup_dir)
            raise

    @transaction.atomic
    def restore_backup(self, backup_name: str, clear_existing: bool = True) -> Dict[str, int]:
        """
        Restore a backup.

        Args:
            backup_name: Name of backup to restore
            clear_existing: Whether to clear existing data before restore

        Returns:
            Dictionary with counts of restored objects per model

        Raises:
            FileNotFoundError: If backup doesn't exist
            Exception: If restore fails
        """
        backup_dir = self.backup_root / backup_name

        if not backup_dir.exists():
            raise FileNotFoundError(f"Backup not found: {backup_dir}")

        logger.info(f"Restoring backup: {backup_dir}")

        counts = {}

        try:
            # Clear existing data if requested
            if clear_existing:
                logger.info("Clearing existing data...")
                for model in reversed(self.MODELS):
                    count = model.objects.count()
                    model.objects.all().delete()
                    logger.info(f"Deleted {count} {model._meta.model_name} records")

            # Restore each model
            for model in self.MODELS:
                model_name = model._meta.model_name
                file_path = backup_dir / f"{model_name}.json"

                if not file_path.exists():
                    logger.warning(f"Backup file not found: {file_path}, skipping")
                    counts[model_name] = 0
                    continue

                # Read and deserialize
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = f.read()

                objects = serializers.deserialize('json', data)

                # Save all objects
                restored_count = 0
                for obj in objects:
                    obj.save()
                    restored_count += 1

                counts[model_name] = restored_count
                logger.info(f"Restored {restored_count} {model_name} records")

            logger.info(f"Restore completed: {counts}")
            return counts

        except Exception as e:
            logger.error(f"Restore failed: {e}", exc_info=True)
            raise

    def list_backups(self) -> List[Dict]:
        """
        List all available backups.

        Returns:
            List of backup metadata dictionaries
        """
        backups = []

        for backup_dir in sorted(self.backup_root.iterdir(), reverse=True):
            if not backup_dir.is_dir():
                continue

            metadata_path = backup_dir / "metadata.json"

            if metadata_path.exists():
                with open(metadata_path, 'r', encoding='utf-8') as f:
                    metadata = json.load(f)
            else:
                # Fallback for backups without metadata
                metadata = {
                    "name": backup_dir.name,
                    "created_at": datetime.fromtimestamp(backup_dir.stat().st_mtime).isoformat(),
                    "counts": {}
                }

            # Add size information
            total_size = sum(f.stat().st_size for f in backup_dir.rglob('*') if f.is_file())
            metadata["size_mb"] = round(total_size / (1024 * 1024), 2)

            backups.append(metadata)

        return backups

    def delete_backup(self, backup_name: str):
        """
        Delete a backup.

        Args:
            backup_name: Name of backup to delete

        Raises:
            FileNotFoundError: If backup doesn't exist
        """
        backup_dir = self.backup_root / backup_name

        if not backup_dir.exists():
            raise FileNotFoundError(f"Backup not found: {backup_dir}")

        logger.info(f"Deleting backup: {backup_dir}")

        import shutil
        shutil.rmtree(backup_dir)

        logger.info("Backup deleted successfully")
