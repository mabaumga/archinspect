"""
Django ORM models for Repo-Analyst application.
These are the persistence adapters for domain entities.
"""
from django.db import models
from django.utils import timezone


class ART(models.Model):
    """Agile Release Train"""
    name = models.CharField(max_length=200, unique=True)
    business_owner_it = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "ART"
        verbose_name_plural = "ARTs"
        ordering = ["name"]

    def __str__(self):
        return self.name


class Application(models.Model):
    """Application within an ART"""
    name = models.CharField(max_length=200, unique=True)
    alphabet_id = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True)
    art = models.ForeignKey(ART, on_delete=models.SET_NULL, null=True, blank=True, related_name="applications")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} ({self.alphabet_id})"


class Repository(models.Model):
    """Code repository"""
    name = models.CharField(max_length=200)
    external_id = models.CharField(max_length=100, unique=True, db_index=True)
    url = models.URLField(max_length=500)
    description = models.TextField(blank=True)
    tech_stack = models.TextField(blank=True)
    namespace_path = models.CharField(max_length=500, blank=True)
    visibility = models.CharField(max_length=50, default="internal")
    is_active = models.BooleanField(default=True, db_index=True)
    is_flagged = models.BooleanField(default=False, db_index=True, help_text="Mark as important repository")
    local_path = models.CharField(max_length=500, blank=True)
    application = models.ForeignKey(
        Application,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="repositories"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Repositories"
        ordering = ["-updated_at"]
        indexes = [
            models.Index(fields=["external_id", "is_active"]),
            models.Index(fields=["namespace_path"]),
        ]

    def __str__(self):
        return f"{self.namespace_path}/{self.name}" if self.namespace_path else self.name


class Prompt(models.Model):
    """Analysis prompt template"""
    CATEGORY_CHOICES = [
        ("techstack", "Techstack"),
        ("fachlichkeit", "Fachlichkeit"),
        ("hexagonal", "Hexagonale Architektur"),
        ("rest_l2", "REST Level 2"),
        ("security", "Security"),
        ("performance", "Performance"),
        ("other", "Sonstiges"),
    ]

    title = models.CharField(max_length=200)
    short_description = models.TextField()
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, default="other")
    prompt_text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["category", "title"]

    def __str__(self):
        return f"{self.title} ({self.category})"


class KIProvider(models.Model):
    """AI/KI provider configuration"""
    name = models.CharField(max_length=200, unique=True)
    base_url = models.URLField(max_length=500)
    model_name = models.CharField(max_length=200)
    auth_token_env_var = models.CharField(max_length=100, help_text="Environment variable name for auth token")
    timeout_s = models.IntegerField(default=30)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "KI Provider"
        verbose_name_plural = "KI Providers"
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} ({self.model_name})"


class PromptRun(models.Model):
    """Result of running a prompt against a repository"""
    repository = models.ForeignKey(Repository, on_delete=models.CASCADE, related_name="prompt_runs")
    prompt = models.ForeignKey(Prompt, on_delete=models.CASCADE, related_name="runs")
    prompt_text_snapshot = models.TextField(
        help_text="Snapshot of prompt text at execution time for auditability"
    )
    ki_provider = models.ForeignKey(KIProvider, on_delete=models.CASCADE, related_name="runs")
    request_text = models.TextField()
    response_json = models.JSONField()
    score_pct = models.IntegerField(null=True, blank=True, help_text="Score 0-100")
    summary = models.TextField(blank=True)
    improvement_suggestions = models.JSONField(default=dict, blank=True)
    endpoints = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["repository", "prompt", "-created_at"]),
        ]

    def __str__(self):
        return f"{self.repository.name} - {self.prompt.title} ({self.created_at.strftime('%Y-%m-%d %H:%M')})"


class AppSettings(models.Model):
    """Application settings (singleton)"""
    default_ki_provider = models.ForeignKey(
        KIProvider,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="+"
    )
    repo_download_root = models.CharField(max_length=500, default="/data/repos")
    include_patterns = models.TextField(default="*.py,*.md,*.txt,*.js,*.ts")
    exclude_paths = models.TextField(default=".git,node_modules,dist,build,target,venv,.venv")
    max_concat_bytes = models.IntegerField(default=460800)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "App Settings"
        verbose_name_plural = "App Settings"

    def __str__(self):
        return "Application Settings"

    def save(self, *args, **kwargs):
        # Singleton pattern: ensure only one instance
        self.pk = 1
        super().save(*args, **kwargs)

    @classmethod
    def load(cls):
        """Load or create settings singleton"""
        obj, created = cls.objects.get_or_create(pk=1)
        return obj


class MarkdownCorpus(models.Model):
    """Generated markdown corpus for a repository"""
    repository = models.ForeignKey(Repository, on_delete=models.CASCADE, related_name="markdown_corpora")
    file_path = models.CharField(max_length=500)
    file_size_bytes = models.IntegerField()
    file_count = models.IntegerField()
    is_complete = models.BooleanField(default=True, help_text="False if size limit was reached")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = "Markdown Corpora"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.repository.name} - {self.created_at.strftime('%Y-%m-%d %H:%M')}"


class ServiceEndpoint(models.Model):
    """
    Service endpoint discovered in repository (REST/SOAP).
    Extracted from PromptRun analysis.
    """
    ENDPOINT_TYPE_CHOICES = [
        ("REST", "REST API"),
        ("SOAP", "SOAP Service"),
    ]

    HTTP_METHOD_CHOICES = [
        ("GET", "GET"),
        ("POST", "POST"),
        ("PUT", "PUT"),
        ("DELETE", "DELETE"),
        ("PATCH", "PATCH"),
        ("HEAD", "HEAD"),
        ("OPTIONS", "OPTIONS"),
    ]

    prompt_run = models.ForeignKey(PromptRun, on_delete=models.CASCADE, related_name="service_endpoints")
    endpoint_type = models.CharField(max_length=10, choices=ENDPOINT_TYPE_CHOICES)
    url = models.CharField(max_length=1000, help_text="URL path or WSDL URL")
    http_method = models.CharField(max_length=10, choices=HTTP_METHOD_CHOICES, blank=True, null=True, help_text="HTTP method (REST only)")
    operation_name = models.CharField(max_length=200, blank=True, help_text="Operation name (SOAP only)")
    description = models.TextField(blank=True)
    assessment = models.TextField(blank=True, help_text="Quality assessment of this endpoint")

    # Maturity Model
    target_maturity_level = models.IntegerField(default=2, help_text="Target maturity level (e.g., 2 for REST Level 2)")
    actual_maturity_level = models.IntegerField(null=True, blank=True, help_text="Actual achieved maturity level (0-3 for REST)")
    maturity_score_pct = models.IntegerField(null=True, blank=True, help_text="How well target is met (0-100%)")

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at", "url"]
        indexes = [
            models.Index(fields=["prompt_run", "endpoint_type"]),
            models.Index(fields=["endpoint_type", "-created_at"]),
        ]

    def __str__(self):
        if self.endpoint_type == "REST":
            return f"{self.http_method} {self.url}"
        else:
            return f"{self.operation_name or self.url}"

    @property
    def repository(self):
        """Helper to get repository from prompt_run"""
        return self.prompt_run.repository


class QualityAnalysis(models.Model):
    """
    Quality analysis result for a repository.
    Covers BDD, Security, Hexagonal Architecture, Performance, etc.
    """
    ANALYSIS_TYPE_CHOICES = [
        ("BDD", "Behavior Driven Development"),
        ("SECURITY", "Security Analysis"),
        ("HEXAGONAL", "Hexagonal Architecture"),
        ("PERFORMANCE", "Performance Analysis"),
        ("REST", "REST API Quality"),
        ("SOAP", "SOAP Service Quality"),
        ("TESTING", "Test Coverage & Quality"),
        ("DOCUMENTATION", "Documentation Quality"),
        ("CODE_QUALITY", "Code Quality"),
        ("OTHER", "Other"),
    ]

    prompt_run = models.ForeignKey(PromptRun, on_delete=models.CASCADE, related_name="quality_analyses")
    analysis_type = models.CharField(max_length=20, choices=ANALYSIS_TYPE_CHOICES)
    score_pct = models.IntegerField(help_text="Overall score 0-100")
    assessment_text = models.TextField(help_text="Detailed assessment description")

    # Structured data
    advantages = models.JSONField(default=list, blank=True, help_text="List of identified advantages")
    improvement_suggestions = models.JSONField(default=list, blank=True, help_text="List of improvement suggestions with effort")
    effort_estimate_days = models.DecimalField(
        max_digits=6,
        decimal_places=1,
        null=True,
        blank=True,
        help_text="Total effort estimate in person-days"
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = "Quality Analyses"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["prompt_run", "analysis_type"]),
            models.Index(fields=["analysis_type", "-created_at"]),
            models.Index(fields=["score_pct"]),
        ]

    def __str__(self):
        return f"{self.get_analysis_type_display()} - {self.prompt_run.repository.name} ({self.score_pct}%)"

    @property
    def repository(self):
        """Helper to get repository from prompt_run"""
        return self.prompt_run.repository
