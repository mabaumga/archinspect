"""
Django REST Framework ViewSets for API v1.
"""
import logging

from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from adapters.ki.http_client import HTTPKIClient, MockKIClient
from adapters.persistence.models import (
    ART,
    Application,
    AppSettings,
    KIProvider,
    MarkdownCorpus,
    Prompt,
    PromptRun,
    QualityAnalysis,
    Repository,
    ServiceEndpoint,
)
from application.services import PromptExecutionService

from .serializers import (
    ARTSerializer,
    ApplicationSerializer,
    AppSettingsSerializer,
    KIProviderSerializer,
    MarkdownCorpusSerializer,
    PromptRunCreateSerializer,
    PromptRunSerializer,
    PromptSerializer,
    QualityAnalysisSerializer,
    RepositoryDetailSerializer,
    RepositorySerializer,
    ServiceEndpointSerializer,
)

logger = logging.getLogger(__name__)


class ARTViewSet(viewsets.ModelViewSet):
    """ViewSet for ART management."""
    queryset = ART.objects.all()
    serializer_class = ARTSerializer
    filterset_fields = ["name"]
    search_fields = ["name", "business_owner_it"]
    ordering_fields = ["name", "created_at"]


class ApplicationViewSet(viewsets.ModelViewSet):
    """ViewSet for Application management."""
    queryset = Application.objects.all()
    serializer_class = ApplicationSerializer
    filterset_fields = ["art", "alphabet_id"]
    search_fields = ["name", "alphabet_id", "description"]
    ordering_fields = ["name", "created_at"]


class RepositoryViewSet(viewsets.ModelViewSet):
    """ViewSet for Repository management."""
    queryset = Repository.objects.all()
    serializer_class = RepositorySerializer
    filterset_fields = ["is_active", "is_flagged", "application", "visibility"]
    search_fields = ["name", "namespace_path", "external_id", "description"]
    ordering_fields = ["name", "updated_at", "created_at"]

    def get_serializer_class(self):
        if self.action == "retrieve":
            return RepositoryDetailSerializer
        return RepositorySerializer

    @action(detail=True, methods=["post"])
    def assign_application(self, request, pk=None):
        """Assign repository to an application."""
        repository = self.get_object()
        application_id = request.data.get("application_id")

        if application_id:
            try:
                application = Application.objects.get(pk=application_id)
                repository.application = application
            except Application.DoesNotExist:
                return Response(
                    {"error": "Application not found"},
                    status=status.HTTP_404_NOT_FOUND
                )
        else:
            repository.application = None

        repository.save()
        serializer = self.get_serializer(repository)
        return Response(serializer.data)

    @action(detail=True, methods=["post"])
    def toggle_active(self, request, pk=None):
        """Toggle repository active status."""
        repository = self.get_object()
        repository.is_active = not repository.is_active
        repository.save()
        serializer = self.get_serializer(repository)
        return Response(serializer.data)

    @action(detail=True, methods=["post"])
    def toggle_flag(self, request, pk=None):
        """Toggle repository flag status."""
        repository = self.get_object()
        repository.is_flagged = not repository.is_flagged
        repository.save()
        serializer = self.get_serializer(repository)
        return Response(serializer.data)

    @action(detail=False, methods=["post"])
    def import_from_platform(self, request):
        """Import all repositories from configured source code platform."""
        from application.services import RepositoryImportService
        from infrastructure.adapter_factory import AdapterFactory

        try:
            # Get page size from request or use default
            page_size = int(request.data.get("page_size", 100))

            # Create adapter via factory
            adapter = AdapterFactory.create_source_code_repository_adapter()

            # Create import service and execute
            service = RepositoryImportService(adapter)
            result = service.import_repositories(page_size=page_size)

            return Response({
                "status": "success",
                "message": f"Import completed: {result['total']} repositories processed",
                "statistics": result
            }, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"Error importing repositories: {e}")
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class PromptViewSet(viewsets.ModelViewSet):
    """ViewSet for Prompt management."""
    queryset = Prompt.objects.all()
    serializer_class = PromptSerializer
    filterset_fields = ["category"]
    search_fields = ["title", "short_description", "prompt_text"]
    ordering_fields = ["title", "category", "created_at"]


class KIProviderViewSet(viewsets.ModelViewSet):
    """ViewSet for KI Provider management."""
    queryset = KIProvider.objects.all()
    serializer_class = KIProviderSerializer
    filterset_fields = ["is_active"]
    search_fields = ["name", "model_name"]
    ordering_fields = ["name", "created_at"]


class PromptRunViewSet(viewsets.ModelViewSet):
    """ViewSet for PromptRun management."""
    queryset = PromptRun.objects.all()
    serializer_class = PromptRunSerializer
    filterset_fields = ["repository", "prompt", "ki_provider"]
    search_fields = ["repository__name", "prompt__title"]
    ordering_fields = ["created_at"]

    def create(self, request, *args, **kwargs):
        """Create a new prompt run by executing the prompt."""
        serializer = PromptRunCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        repository_id = serializer.validated_data["repository_id"]
        prompt_id = serializer.validated_data["prompt_id"]
        ki_provider_id = serializer.validated_data.get("ki_provider_id")

        try:
            # Get KI provider
            if ki_provider_id:
                ki_provider = KIProvider.objects.get(pk=ki_provider_id)
            else:
                settings = AppSettings.load()
                ki_provider = settings.default_ki_provider
                if not ki_provider:
                    return Response(
                        {"error": "No KI provider specified and no default configured"},
                        status=status.HTTP_400_BAD_REQUEST
                    )

            # Create KI client
            # For now, use mock client for development
            ki_client = MockKIClient()
            # In production:
            # ki_client = HTTPKIClient(
            #     ki_provider.base_url,
            #     ki_provider.model_name,
            #     ki_provider.auth_token_env_var,
            #     ki_provider.timeout_s
            # )

            # Execute prompt
            service = PromptExecutionService(ki_client)
            prompt_run = service.execute_prompt(repository_id, prompt_id, ki_provider.id)

            # Return result
            result_serializer = PromptRunSerializer(prompt_run)
            return Response(result_serializer.data, status=status.HTTP_201_CREATED)

        except (Repository.DoesNotExist, Prompt.DoesNotExist, KIProvider.DoesNotExist) as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            logger.error(f"Error executing prompt: {e}")
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class AppSettingsViewSet(viewsets.ModelViewSet):
    """ViewSet for AppSettings management."""
    queryset = AppSettings.objects.all()
    serializer_class = AppSettingsSerializer

    def get_queryset(self):
        # Always return singleton
        return AppSettings.objects.filter(pk=1)


class MarkdownCorpusViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for MarkdownCorpus (read-only)."""
    queryset = MarkdownCorpus.objects.all()
    serializer_class = MarkdownCorpusSerializer
    filterset_fields = ["repository", "is_complete"]
    ordering_fields = ["created_at"]


class BackupViewSet(viewsets.ViewSet):
    """ViewSet for backup and restore operations."""

    @action(detail=False, methods=["get"])
    def list_backups(self, request):
        """List all available backups."""
        from application.backup_service import BackupService
        from django.conf import settings

        try:
            service = BackupService(settings.BACKUP_DIR)
            backups = service.list_backups()

            return Response({
                "status": "success",
                "backups": backups
            }, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"Error listing backups: {e}")
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=["post"])
    def create_backup(self, request):
        """Create a new backup."""
        from application.backup_service import BackupService
        from django.conf import settings

        try:
            backup_name = request.data.get("name")
            service = BackupService(settings.BACKUP_DIR)
            backup_dir = service.create_backup(name=backup_name)

            return Response({
                "status": "success",
                "message": f"Backup created successfully",
                "backup_name": backup_dir.name,
                "path": str(backup_dir)
            }, status=status.HTTP_201_CREATED)

        except Exception as e:
            logger.error(f"Error creating backup: {e}")
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=["post"])
    def restore_backup(self, request, pk=None):
        """Restore a backup."""
        from application.backup_service import BackupService
        from django.conf import settings

        try:
            backup_name = pk
            clear_existing = request.data.get("clear_existing", True)

            service = BackupService(settings.BACKUP_DIR)
            counts = service.restore_backup(backup_name, clear_existing=clear_existing)

            return Response({
                "status": "success",
                "message": f"Backup restored successfully",
                "counts": counts
            }, status=status.HTTP_200_OK)

        except FileNotFoundError as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            logger.error(f"Error restoring backup: {e}")
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=["delete"])
    def delete_backup(self, request, pk=None):
        """Delete a backup."""
        from application.backup_service import BackupService
        from django.conf import settings

        try:
            backup_name = pk
            service = BackupService(settings.BACKUP_DIR)
            service.delete_backup(backup_name)

            return Response({
                "status": "success",
                "message": f"Backup deleted successfully"
            }, status=status.HTTP_200_OK)

        except FileNotFoundError as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            logger.error(f"Error deleting backup: {e}")
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ServiceEndpointViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for Service Endpoints (read-only)."""
    queryset = ServiceEndpoint.objects.select_related(
        "prompt_run__repository__application"
    ).all()
    serializer_class = ServiceEndpointSerializer
    filterset_fields = ["endpoint_type", "prompt_run__repository"]
    search_fields = ["url", "operation_name", "description"]
    ordering_fields = ["created_at", "endpoint_type", "maturity_score_pct"]


class QualityAnalysisViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for Quality Analyses (read-only)."""
    queryset = QualityAnalysis.objects.select_related(
        "prompt_run__repository__application"
    ).all()
    serializer_class = QualityAnalysisSerializer
    filterset_fields = ["analysis_type", "prompt_run__repository"]
    search_fields = ["assessment_text"]
    ordering_fields = ["created_at", "score_pct", "analysis_type"]
