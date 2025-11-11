"""
Django views for web UI.
"""
import logging

from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.views.generic import CreateView, DetailView, ListView, UpdateView

from adapters.git_platform.clone_service import GitCloneService
from adapters.ki.http_client import MockKIClient
from adapters.persistence.models import ART, Application, AppSettings, KIProvider, Prompt, PromptRun, Repository
from application.services import PromptExecutionService

from .forms import (
    ARTForm,
    ApplicationAssignForm,
    ApplicationForm,
    KIProviderForm,
    PromptExecuteForm,
    PromptForm,
    RepositoryAssignForm,
)

logger = logging.getLogger(__name__)


def dashboard(request):
    """Dashboard view with statistics."""
    context = {
        "total_repos": Repository.objects.count(),
        "active_repos": Repository.objects.filter(is_active=True).count(),
        "total_apps": Application.objects.count(),
        "total_arts": ART.objects.count(),
        "total_prompts": Prompt.objects.count(),
        "recent_runs": PromptRun.objects.select_related("repository", "prompt").order_by("-created_at")[:10],
    }
    return render(request, "dashboard.html", context)


# Repository Views
class RepositoryListView(ListView):
    """List all repositories."""
    model = Repository
    template_name = "repositories/list.html"
    context_object_name = "repositories"
    paginate_by = 20

    def get_queryset(self):
        from django.db.models import Q

        queryset = Repository.objects.select_related("application", "application__art")

        # Search by text
        search = self.request.GET.get("search")
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(url__icontains=search) |
                Q(namespace_path__icontains=search) |
                Q(description__icontains=search)
            )

        # Filter by active
        is_active = self.request.GET.get("is_active")
        if is_active:
            queryset = queryset.filter(is_active=(is_active == "true"))

        # Filter by flagged
        is_flagged = self.request.GET.get("is_flagged")
        if is_flagged:
            queryset = queryset.filter(is_flagged=(is_flagged == "true"))

        # Filter by application
        application_id = self.request.GET.get("application")
        if application_id:
            queryset = queryset.filter(application_id=application_id)

        # Filter by ART
        art_id = self.request.GET.get("art")
        if art_id:
            queryset = queryset.filter(application__art_id=art_id)

        return queryset.order_by("-updated_at")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["applications"] = Application.objects.all()
        context["arts"] = ART.objects.all()

        # Build query string for pagination (preserve all filters except page)
        query_params = self.request.GET.copy()
        if 'page' in query_params:
            query_params.pop('page')
        context["query_string"] = query_params.urlencode()

        return context


class RepositoryDetailView(DetailView):
    """Detail view for a repository."""
    model = Repository
    template_name = "repositories/detail.html"
    context_object_name = "repository"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        repository = self.get_object()

        # Get latest prompt runs
        latest_runs = {}
        for prompt in Prompt.objects.all():
            run = repository.prompt_runs.filter(prompt=prompt).first()
            if run:
                latest_runs[prompt.id] = run

        context["latest_runs"] = latest_runs
        context["all_prompts"] = Prompt.objects.all()
        context["prompt_history"] = repository.prompt_runs.select_related("prompt", "ki_provider").order_by("-created_at")[:20]
        context["execute_form"] = PromptExecuteForm()

        return context


def repository_assign_application(request, pk):
    """Assign repository to application."""
    repository = get_object_or_404(Repository, pk=pk)

    if request.method == "POST":
        form = RepositoryAssignForm(request.POST, instance=repository)
        if form.is_valid():
            form.save()
            messages.success(request, "Repository erfolgreich zugeordnet")
            return redirect("repository-detail", pk=pk)
    else:
        form = RepositoryAssignForm(instance=repository)

    return render(request, "repositories/assign.html", {"form": form, "repository": repository})


def repository_toggle_active(request, pk):
    """Toggle repository active status."""
    repository = get_object_or_404(Repository, pk=pk)
    repository.is_active = not repository.is_active
    repository.save()
    messages.success(request, f"Repository ist jetzt {'aktiv' if repository.is_active else 'inaktiv'}")
    return redirect("repository-detail", pk=pk)


def repository_clone(request, pk):
    """Clone/checkout repository from configured source code platform."""
    from infrastructure.adapter_factory import AdapterFactory
    from pathlib import Path

    repository = get_object_or_404(Repository, pk=pk)

    # Get app settings
    app_settings = AppSettings.objects.first()
    if not app_settings:
        messages.error(request, "App-Einstellungen nicht gefunden. Bitte führen Sie 'make seed' aus.")
        return redirect("repository-detail", pk=pk)

    target_root = Path(app_settings.repo_download_root)

    try:
        # Create adapter via factory
        adapter = AdapterFactory.create_source_code_repository_adapter()

        # Determine if we need to clone or update
        was_updated = False
        if repository.local_path and Path(repository.local_path).exists():
            # Update existing repository
            cloned_path = adapter.update_repository(Path(repository.local_path))
            was_updated = True
        else:
            # Clone new repository
            cloned_path = adapter.clone_repository(
                repo_name=repository.name,
                repo_url=repository.url,
                namespace_path=repository.namespace_path,
                target_dir=target_root
            )

        # Update repository with local path
        repository.local_path = str(cloned_path)
        repository.save()

        # Get status for user feedback
        file_count = sum(1 for _ in cloned_path.rglob('*') if _.is_file())
        size_bytes = sum(f.stat().st_size for f in cloned_path.rglob('*') if f.is_file())
        size_mb = round(size_bytes / (1024 * 1024), 2)

        # Different message for clone vs update
        action = "aktualisiert" if was_updated else "geklont"
        messages.success(
            request,
            f"Repository '{repository.name}' erfolgreich {action} nach {cloned_path}. "
            f"({file_count} Dateien, {size_mb} MB)"
        )
        logger.info(
            f"{'Updated' if was_updated else 'Cloned'} repository {repository.name}",
            extra={
                "repository_id": repository.id,
                "path": str(cloned_path),
                "file_count": file_count,
                "size_mb": size_mb,
                "was_updated": was_updated
            }
        )

    except FileNotFoundError as e:
        logger.error(f"Repository not found: {e}")
        messages.error(
            request,
            f"Repository '{repository.name}' konnte nicht geklont werden: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Error cloning repository: {e}", exc_info=True)
        messages.error(request, f"Fehler beim Klonen des Repositories: {e}")

    return redirect("repository-detail", pk=pk)


def repository_execute_prompt(request, pk):
    """Execute a prompt on a repository."""
    repository = get_object_or_404(Repository, pk=pk)

    if request.method == "POST":
        form = PromptExecuteForm(request.POST)
        if form.is_valid():
            prompt = form.cleaned_data["prompt"]
            ki_provider = form.cleaned_data.get("ki_provider")

            try:
                # Use mock client for development
                ki_client = MockKIClient()
                service = PromptExecutionService(ki_client)

                ki_provider_id = ki_provider.id if ki_provider else None
                prompt_run = service.execute_prompt(repository.id, prompt.id, ki_provider_id)

                messages.success(request, f"Prompt '{prompt.title}' erfolgreich ausgeführt")
                return redirect("promptrun-detail", pk=prompt_run.id)

            except Exception as e:
                logger.error(f"Error executing prompt: {e}")
                messages.error(request, f"Fehler beim Ausführen des Prompts: {e}")

    return redirect("repository-detail", pk=pk)


# Application Views
class ApplicationListView(ListView):
    """List all applications."""
    model = Application
    template_name = "applications/list.html"
    context_object_name = "applications"
    paginate_by = 20

    def get_queryset(self):
        queryset = Application.objects.select_related("art")

        # Filter by ART
        art_id = self.request.GET.get("art")
        if art_id:
            queryset = queryset.filter(art_id=art_id)

        return queryset.order_by("name")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["arts"] = ART.objects.all()
        return context


class ApplicationDetailView(DetailView):
    """Detail view for an application."""
    model = Application
    template_name = "applications/detail.html"
    context_object_name = "application"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        application = self.get_object()
        context["repositories"] = application.repositories.all()
        return context


class ApplicationCreateView(CreateView):
    """Create a new application."""
    model = Application
    form_class = ApplicationForm
    template_name = "applications/form.html"
    success_url = reverse_lazy("application-list")

    def form_valid(self, form):
        messages.success(self.request, "Anwendung erfolgreich erstellt")
        return super().form_valid(form)


class ApplicationUpdateView(UpdateView):
    """Update an application."""
    model = Application
    form_class = ApplicationForm
    template_name = "applications/form.html"
    success_url = reverse_lazy("application-list")

    def form_valid(self, form):
        messages.success(self.request, "Anwendung erfolgreich aktualisiert")
        return super().form_valid(form)


# ART Views
class ARTListView(ListView):
    """List all ARTs."""
    model = ART
    template_name = "arts/list.html"
    context_object_name = "arts"
    paginate_by = 20

    def get_queryset(self):
        return ART.objects.all().order_by("name")


class ARTDetailView(DetailView):
    """Detail view for an ART."""
    model = ART
    template_name = "arts/detail.html"
    context_object_name = "art"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        art = self.get_object()
        context["applications"] = art.applications.all()
        return context


class ARTCreateView(CreateView):
    """Create a new ART."""
    model = ART
    form_class = ARTForm
    template_name = "arts/form.html"
    success_url = reverse_lazy("art-list")

    def form_valid(self, form):
        messages.success(self.request, "ART erfolgreich erstellt")
        return super().form_valid(form)


class ARTUpdateView(UpdateView):
    """Update an ART."""
    model = ART
    form_class = ARTForm
    template_name = "arts/form.html"
    success_url = reverse_lazy("art-list")

    def form_valid(self, form):
        messages.success(self.request, "ART erfolgreich aktualisiert")
        return super().form_valid(form)


# Prompt Views
class PromptListView(ListView):
    """List all prompts."""
    model = Prompt
    template_name = "prompts/list.html"
    context_object_name = "prompts"
    paginate_by = 20

    def get_queryset(self):
        queryset = Prompt.objects.all()

        # Filter by category
        category = self.request.GET.get("category")
        if category:
            queryset = queryset.filter(category=category)

        return queryset.order_by("category", "title")


class PromptDetailView(DetailView):
    """Detail view for a prompt."""
    model = Prompt
    template_name = "prompts/detail.html"
    context_object_name = "prompt"


class PromptCreateView(CreateView):
    """Create a new prompt."""
    model = Prompt
    form_class = PromptForm
    template_name = "prompts/form.html"
    success_url = reverse_lazy("prompt-list")

    def form_valid(self, form):
        messages.success(self.request, "Prompt erfolgreich erstellt")
        return super().form_valid(form)


class PromptUpdateView(UpdateView):
    """Update a prompt."""
    model = Prompt
    form_class = PromptForm
    template_name = "prompts/form.html"
    success_url = reverse_lazy("prompt-list")

    def form_valid(self, form):
        messages.success(self.request, "Prompt erfolgreich aktualisiert")
        return super().form_valid(form)


# KI Provider Views
class KIProviderListView(ListView):
    """List all KI providers."""
    model = KIProvider
    template_name = "kiproviders/list.html"
    context_object_name = "providers"
    paginate_by = 20


class KIProviderCreateView(CreateView):
    """Create a new KI provider."""
    model = KIProvider
    form_class = KIProviderForm
    template_name = "kiproviders/form.html"
    success_url = reverse_lazy("kiprovider-list")

    def form_valid(self, form):
        messages.success(self.request, "KI Provider erfolgreich erstellt")
        return super().form_valid(form)


class KIProviderUpdateView(UpdateView):
    """Update a KI provider."""
    model = KIProvider
    form_class = KIProviderForm
    template_name = "kiproviders/form.html"
    success_url = reverse_lazy("kiprovider-list")

    def form_valid(self, form):
        messages.success(self.request, "KI Provider erfolgreich aktualisiert")
        return super().form_valid(form)


# PromptRun Views
class PromptRunDetailView(DetailView):
    """Detail view for a prompt run."""
    model = PromptRun
    template_name = "promptruns/detail.html"
    context_object_name = "prompt_run"



# Backup & Restore Views
def backup_list(request):
    """Backup and restore management page."""
    return render(request, "backup/list.html")

