"""
Django REST Framework serializers.
"""
from rest_framework import serializers

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


class ARTSerializer(serializers.ModelSerializer):
    class Meta:
        model = ART
        fields = ["id", "name", "business_owner_it", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]


class ApplicationSerializer(serializers.ModelSerializer):
    art_name = serializers.CharField(source="art.name", read_only=True)

    class Meta:
        model = Application
        fields = ["id", "name", "alphabet_id", "description", "art", "art_name", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]


class RepositorySerializer(serializers.ModelSerializer):
    application_name = serializers.CharField(source="application.name", read_only=True)
    art_name = serializers.CharField(source="application.art.name", read_only=True)

    class Meta:
        model = Repository
        fields = [
            "id", "name", "external_id", "url", "description", "tech_stack",
            "namespace_path", "visibility", "is_active", "is_flagged", "local_path",
            "application", "application_name", "art_name",
            "created_at", "updated_at"
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class RepositoryDetailSerializer(RepositorySerializer):
    """Extended serializer with related data."""
    latest_prompt_runs = serializers.SerializerMethodField()

    class Meta(RepositorySerializer.Meta):
        fields = RepositorySerializer.Meta.fields + ["latest_prompt_runs"]

    def get_latest_prompt_runs(self, obj):
        """Get latest prompt run for each prompt."""
        latest_runs = []
        prompts = Prompt.objects.all()

        for prompt in prompts:
            run = obj.prompt_runs.filter(prompt=prompt).first()
            if run:
                latest_runs.append({
                    "prompt_id": prompt.id,
                    "prompt_title": prompt.title,
                    "score_pct": run.score_pct,
                    "created_at": run.created_at,
                })

        return latest_runs


class PromptSerializer(serializers.ModelSerializer):
    class Meta:
        model = Prompt
        fields = ["id", "title", "short_description", "category", "prompt_text", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]


class KIProviderSerializer(serializers.ModelSerializer):
    class Meta:
        model = KIProvider
        fields = [
            "id", "name", "base_url", "model_name", "auth_token_env_var",
            "timeout_s", "is_active", "created_at", "updated_at"
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class PromptRunSerializer(serializers.ModelSerializer):
    repository_name = serializers.CharField(source="repository.name", read_only=True)
    prompt_title = serializers.CharField(source="prompt.title", read_only=True)
    ki_provider_name = serializers.CharField(source="ki_provider.name", read_only=True)

    class Meta:
        model = PromptRun
        fields = [
            "id", "repository", "repository_name", "prompt", "prompt_title",
            "ki_provider", "ki_provider_name", "request_text", "response_json",
            "score_pct", "summary", "improvement_suggestions", "endpoints", "created_at"
        ]
        read_only_fields = ["id", "created_at"]


class PromptRunCreateSerializer(serializers.Serializer):
    """Serializer for creating a prompt run."""
    repository_id = serializers.IntegerField()
    prompt_id = serializers.IntegerField()
    ki_provider_id = serializers.IntegerField(required=False, allow_null=True)


class AppSettingsSerializer(serializers.ModelSerializer):
    default_ki_provider_name = serializers.CharField(source="default_ki_provider.name", read_only=True)

    class Meta:
        model = AppSettings
        fields = [
            "id", "default_ki_provider", "default_ki_provider_name",
            "repo_download_root", "include_patterns", "exclude_paths",
            "max_concat_bytes", "created_at", "updated_at"
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class MarkdownCorpusSerializer(serializers.ModelSerializer):
    repository_name = serializers.CharField(source="repository.name", read_only=True)

    class Meta:
        model = MarkdownCorpus
        fields = [
            "id", "repository", "repository_name", "file_path",
            "file_size_bytes", "file_count", "is_complete", "created_at"
        ]
        read_only_fields = ["id", "created_at"]
