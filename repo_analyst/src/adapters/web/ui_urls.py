"""
UI URL configuration.
"""
from django.urls import path

from . import views

urlpatterns = [
    # Dashboard
    path("", views.dashboard, name="dashboard"),

    # Repositories
    path("repositories/", views.RepositoryListView.as_view(), name="repository-list"),
    path("repositories/<int:pk>/", views.RepositoryDetailView.as_view(), name="repository-detail"),
    path("repositories/<int:pk>/assign/", views.repository_assign_application, name="repository-assign"),
    path("repositories/<int:pk>/toggle-active/", views.repository_toggle_active, name="repository-toggle-active"),
    path("repositories/<int:pk>/clone/", views.repository_clone, name="repository-clone"),
    path("repositories/<int:pk>/execute-prompt/", views.repository_execute_prompt, name="repository-execute-prompt"),

    # Applications
    path("applications/", views.ApplicationListView.as_view(), name="application-list"),
    path("applications/<int:pk>/", views.ApplicationDetailView.as_view(), name="application-detail"),
    path("applications/create/", views.ApplicationCreateView.as_view(), name="application-create"),
    path("applications/<int:pk>/edit/", views.ApplicationUpdateView.as_view(), name="application-update"),

    # ARTs
    path("arts/", views.ARTListView.as_view(), name="art-list"),
    path("arts/<int:pk>/", views.ARTDetailView.as_view(), name="art-detail"),
    path("arts/create/", views.ARTCreateView.as_view(), name="art-create"),
    path("arts/<int:pk>/edit/", views.ARTUpdateView.as_view(), name="art-update"),

    # Prompts
    path("prompts/", views.PromptListView.as_view(), name="prompt-list"),
    path("prompts/<int:pk>/", views.PromptDetailView.as_view(), name="prompt-detail"),
    path("prompts/create/", views.PromptCreateView.as_view(), name="prompt-create"),
    path("prompts/<int:pk>/edit/", views.PromptUpdateView.as_view(), name="prompt-update"),

    # KI Providers
    path("ki-providers/", views.KIProviderListView.as_view(), name="kiprovider-list"),
    path("ki-providers/create/", views.KIProviderCreateView.as_view(), name="kiprovider-create"),
    path("ki-providers/<int:pk>/edit/", views.KIProviderUpdateView.as_view(), name="kiprovider-update"),

    # Prompt Runs
    path("prompt-runs/<int:pk>/", views.PromptRunDetailView.as_view(), name="promptrun-detail"),
]
