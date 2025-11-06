"""
Django admin configuration for Repo-Analyst models.
"""
from django.contrib import admin

from .models import ART, Application, AppSettings, KIProvider, MarkdownCorpus, Prompt, PromptRun, Repository


@admin.register(ART)
class ARTAdmin(admin.ModelAdmin):
    list_display = ["name", "business_owner_it", "created_at"]
    search_fields = ["name", "business_owner_it"]
    ordering = ["name"]


@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    list_display = ["name", "alphabet_id", "art", "created_at"]
    list_filter = ["art"]
    search_fields = ["name", "alphabet_id", "description"]
    ordering = ["name"]


@admin.register(Repository)
class RepositoryAdmin(admin.ModelAdmin):
    list_display = ["name", "namespace_path", "external_id", "is_active", "application", "updated_at"]
    list_filter = ["is_active", "visibility", "application__art"]
    search_fields = ["name", "namespace_path", "external_id", "description"]
    ordering = ["-updated_at"]
    readonly_fields = ["created_at", "updated_at"]


@admin.register(Prompt)
class PromptAdmin(admin.ModelAdmin):
    list_display = ["title", "category", "short_description", "created_at"]
    list_filter = ["category"]
    search_fields = ["title", "short_description", "prompt_text"]
    ordering = ["category", "title"]


@admin.register(KIProvider)
class KIProviderAdmin(admin.ModelAdmin):
    list_display = ["name", "model_name", "base_url", "is_active", "timeout_s"]
    list_filter = ["is_active"]
    search_fields = ["name", "model_name"]
    ordering = ["name"]


@admin.register(PromptRun)
class PromptRunAdmin(admin.ModelAdmin):
    list_display = ["repository", "prompt", "ki_provider", "score_pct", "created_at"]
    list_filter = ["prompt", "ki_provider", "created_at"]
    search_fields = ["repository__name", "prompt__title"]
    ordering = ["-created_at"]
    readonly_fields = ["created_at"]


@admin.register(AppSettings)
class AppSettingsAdmin(admin.ModelAdmin):
    list_display = ["default_ki_provider", "repo_download_root", "max_concat_bytes"]

    def has_add_permission(self, request):
        # Singleton: only one instance allowed
        return not AppSettings.objects.exists()

    def has_delete_permission(self, request, obj=None):
        # Don't allow deletion of singleton
        return False


@admin.register(MarkdownCorpus)
class MarkdownCorpusAdmin(admin.ModelAdmin):
    list_display = ["repository", "file_size_bytes", "file_count", "is_complete", "created_at"]
    list_filter = ["is_complete", "created_at"]
    search_fields = ["repository__name"]
    ordering = ["-created_at"]
    readonly_fields = ["created_at"]
