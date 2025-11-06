"""
URL configuration for repo_analyst project.
"""
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/v1/", include("adapters.web.api_urls", namespace="v1")),
    path("", include("adapters.web.ui_urls")),
]
