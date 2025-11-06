"""
Django forms for web UI.
"""
from django import forms

from adapters.persistence.models import ART, Application, KIProvider, Prompt, Repository


class RepositoryAssignForm(forms.ModelForm):
    """Form for assigning repository to application."""

    class Meta:
        model = Repository
        fields = ["application"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["application"].required = False
        self.fields["application"].empty_label = "-- Keine Zuordnung --"


class ApplicationAssignForm(forms.ModelForm):
    """Form for assigning application to ART."""

    class Meta:
        model = Application
        fields = ["art"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["art"].required = False
        self.fields["art"].empty_label = "-- Keine Zuordnung --"


class PromptExecuteForm(forms.Form):
    """Form for executing a prompt."""
    prompt = forms.ModelChoiceField(
        queryset=Prompt.objects.all(),
        label="Prompt",
        help_text="Wählen Sie einen Prompt aus"
    )
    ki_provider = forms.ModelChoiceField(
        queryset=KIProvider.objects.filter(is_active=True),
        label="KI Provider",
        required=False,
        help_text="Leer lassen für Standard-Provider"
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["ki_provider"].empty_label = "-- Standard-Provider --"


class ARTForm(forms.ModelForm):
    """Form for creating/editing ARTs."""

    class Meta:
        model = ART
        fields = ["name", "business_owner_it"]
        widgets = {
            "business_owner_it": forms.Textarea(attrs={"rows": 3}),
        }


class ApplicationForm(forms.ModelForm):
    """Form for creating/editing Applications."""

    class Meta:
        model = Application
        fields = ["name", "alphabet_id", "description", "art"]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 3}),
        }


class PromptForm(forms.ModelForm):
    """Form for creating/editing Prompts."""

    class Meta:
        model = Prompt
        fields = ["title", "short_description", "category", "prompt_text"]
        widgets = {
            "short_description": forms.Textarea(attrs={"rows": 2}),
            "prompt_text": forms.Textarea(attrs={"rows": 10}),
        }


class KIProviderForm(forms.ModelForm):
    """Form for creating/editing KI Providers."""

    class Meta:
        model = KIProvider
        fields = ["name", "base_url", "model_name", "auth_token_env_var", "timeout_s", "is_active"]
