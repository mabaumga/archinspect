"""
API URL configuration for v1.
"""
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .viewsets import (
    ARTViewSet,
    ApplicationViewSet,
    AppSettingsViewSet,
    KIProviderViewSet,
    MarkdownCorpusViewSet,
    PromptRunViewSet,
    PromptViewSet,
    RepositoryViewSet,
)

app_name = "v1"

router = DefaultRouter()
router.register(r"arts", ARTViewSet, basename="art")
router.register(r"applications", ApplicationViewSet, basename="application")
router.register(r"repositories", RepositoryViewSet, basename="repository")
router.register(r"prompts", PromptViewSet, basename="prompt")
router.register(r"ki-providers", KIProviderViewSet, basename="kiprovider")
router.register(r"prompt-runs", PromptRunViewSet, basename="promptrun")
router.register(r"settings", AppSettingsViewSet, basename="appsettings")
router.register(r"markdown-corpora", MarkdownCorpusViewSet, basename="markdowncorpus")

urlpatterns = [
    path("", include(router.urls)),
]
