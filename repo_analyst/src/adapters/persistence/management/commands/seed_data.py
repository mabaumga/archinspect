"""
Management command to seed initial data.
"""
from django.core.management.base import BaseCommand

from adapters.persistence.models import ART, Application, AppSettings, KIProvider, Prompt


class Command(BaseCommand):
    help = "Seed initial data (ARTs, Applications, Prompts, KI Providers)"

    def handle(self, *args, **options):
        self.stdout.write("Seeding initial data...")

        # Create ARTs
        self.stdout.write("Creating ARTs...")
        art1, _ = ART.objects.get_or_create(
            name="ART Operations",
            defaults={"business_owner_it": "IT Operations Team"}
        )
        art2, _ = ART.objects.get_or_create(
            name="ART GLU",
            defaults={"business_owner_it": "Group Life & Health Team"}
        )
        art3, _ = ART.objects.get_or_create(
            name="ART Makler und Portale",
            defaults={"business_owner_it": "Broker & Portals Team"}
        )

        # Create Applications
        self.stdout.write("Creating Applications...")
        app1, _ = Application.objects.get_or_create(
            alphabet_id="KRAKE",
            defaults={"name": "Krake", "description": "Data Courier System", "art": art1}
        )
        app2, _ = Application.objects.get_or_create(
            alphabet_id="BKV",
            defaults={"name": "Betriebskrankenversicherung", "description": "Company Health Insurance", "art": art2}
        )
        app3, _ = Application.objects.get_or_create(
            alphabet_id="DKK",
            defaults={"name": "Digital Customer Contact", "description": "Payment Services", "art": art3}
        )

        # Create Prompts
        self.stdout.write("Creating Prompts...")
        Prompt.objects.get_or_create(
            title="Techstack-Analyse",
            defaults={
                "short_description": "Analysiert den verwendeten Technologie-Stack",
                "category": "techstack",
                "prompt_text": (
                    "Analysiere den Technologie-Stack dieses Repositories. "
                    "Identifiziere verwendete Programmiersprachen, Frameworks, "
                    "Bibliotheken und Tools. Bewerte die Aktualität und gib "
                    "Empfehlungen für Verbesserungen."
                )
            }
        )

        Prompt.objects.get_or_create(
            title="Hexagonale Architektur Check",
            defaults={
                "short_description": "Prüft die Umsetzung hexagonaler Architektur",
                "category": "hexagonal",
                "prompt_text": (
                    "Analysiere, ob und wie gut dieses Repository das Pattern "
                    "der hexagonalen Architektur (Ports & Adapters) umsetzt. "
                    "Identifiziere Domain, Application Services, Ports und Adapters. "
                    "Gib einen Score und Verbesserungsvorschläge."
                )
            }
        )

        Prompt.objects.get_or_create(
            title="REST Level 2 Compliance",
            defaults={
                "short_description": "Prüft REST API auf Richardson Maturity Level 2",
                "category": "rest_l2",
                "prompt_text": (
                    "Analysiere die REST API dieses Repositories auf Konformität "
                    "mit Richardson Maturity Model Level 2. Prüfe HTTP-Verben, "
                    "Statuscodes, Ressourcen-Modellierung. Liste alle Endpoints auf "
                    "und gib Verbesserungsvorschläge."
                )
            }
        )

        Prompt.objects.get_or_create(
            title="Security Audit",
            defaults={
                "short_description": "Sicherheitsüberprüfung des Codes",
                "category": "security",
                "prompt_text": (
                    "Führe ein Security Audit durch. Suche nach potentiellen "
                    "Sicherheitslücken, unsicheren Praktiken, fehlenden Validierungen, "
                    "SQL Injection Risiken, XSS-Problemen, etc. Gib konkrete "
                    "Empfehlungen."
                )
            }
        )

        # Create KI Providers
        self.stdout.write("Creating KI Providers...")
        KIProvider.objects.get_or_create(
            name="OpenAI GPT-4",
            defaults={
                "base_url": "https://api.openai.com/v1/chat/completions",
                "model_name": "gpt-4",
                "auth_token_env_var": "OPENAI_API_KEY",
                "timeout_s": 30,
                "is_active": True
            }
        )

        KIProvider.objects.get_or_create(
            name="Anthropic Claude",
            defaults={
                "base_url": "https://api.anthropic.com/v1/messages",
                "model_name": "claude-3-sonnet-20240229",
                "auth_token_env_var": "ANTHROPIC_API_KEY",
                "timeout_s": 30,
                "is_active": True
            }
        )

        mock_provider, _ = KIProvider.objects.get_or_create(
            name="Mock Provider",
            defaults={
                "base_url": "http://localhost:8000/mock",
                "model_name": "mock-model",
                "auth_token_env_var": "MOCK_API_KEY",
                "timeout_s": 10,
                "is_active": True
            }
        )

        # Create or update AppSettings with Mock Provider as default
        self.stdout.write("Creating/updating AppSettings...")
        settings, created = AppSettings.objects.get_or_create(
            pk=1,
            defaults={
                "default_ki_provider": mock_provider,
                "repo_download_root": "/home/marc/git/archinspect/testdata/repos",
                "include_patterns": "*.py,*.md,*.txt,*.js,*.ts,*.tsx,*.jsx,*.java,*.kt,*.go,*.yml,*.yaml,*.json",
                "exclude_paths": ".git,node_modules,dist,build,target,venv,.venv,__pycache__",
                "max_concat_bytes": 460800
            }
        )

        if not created and settings.default_ki_provider != mock_provider:
            settings.default_ki_provider = mock_provider
            settings.save()
            self.stdout.write("  Updated default KI provider to Mock Provider")
        else:
            self.stdout.write(f"  Default KI provider: {settings.default_ki_provider.name}")

        self.stdout.write(self.style.SUCCESS("Successfully seeded initial data"))
