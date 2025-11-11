"""
HTTP-based KI/AI client adapter.
Generic adapter for HTTP-based AI APIs (OpenAI, Anthropic, Azure, etc.)
"""
import logging
import os
from typing import Optional

import requests

from domain.ports import KIClientPort

logger = logging.getLogger(__name__)


class HTTPKIClient(KIClientPort):
    """
    Generic HTTP client for AI/KI providers.
    Configurable via KIProvider model.
    """

    def __init__(
        self,
        base_url: str,
        model_name: str,
        auth_token_env_var: str,
        timeout_s: int = 30
    ):
        self.base_url = base_url
        self.model_name = model_name
        self.auth_token_env_var = auth_token_env_var
        self.timeout_s = timeout_s

        # Get token from environment
        self.auth_token = os.getenv(auth_token_env_var)
        if not self.auth_token:
            logger.warning(f"Auth token not found in environment: {auth_token_env_var}")

    def analyze(self, prompt_text: str, context: str = "") -> dict:
        """
        Send analysis request to KI provider.

        Args:
            prompt_text: The prompt to send
            context: Additional context (e.g., code corpus)

        Returns:
            Dictionary with analysis results
        """
        logger.info(f"Sending prompt to {self.base_url} (model: {self.model_name})")

        # Build request payload (generic format)
        full_prompt = f"{prompt_text}\n\nContext:\n{context}" if context else prompt_text

        payload = {
            "model": self.model_name,
            "messages": [
                {"role": "user", "content": full_prompt}
            ],
            "temperature": 0.7,
            "max_tokens": 2000,
        }

        headers = {
            "Content-Type": "application/json",
        }

        if self.auth_token:
            headers["Authorization"] = f"Bearer {self.auth_token}"

        try:
            response = requests.post(
                self.base_url,
                json=payload,
                headers=headers,
                timeout=self.timeout_s
            )
            response.raise_for_status()

            result = response.json()
            logger.info("Received response from KI provider")

            # Extract response (format may vary by provider)
            return self._parse_response(result)

        except requests.exceptions.RequestException as e:
            logger.error(f"Error calling KI provider: {e}")
            # Return mock response for development
            return self._mock_response()

    def _parse_response(self, result: dict) -> dict:
        """
        Parse provider response into standard format.

        Expected output format:
        {
            "description": str,
            "score_pct": int,
            "improvement_suggestions": dict,
            "endpoints": dict (optional)
        }
        """
        # Try to extract content from various response formats
        content = ""

        # OpenAI format
        if "choices" in result:
            content = result["choices"][0]["message"]["content"]
        # Generic format
        elif "content" in result:
            content = result["content"]
        # Raw text
        elif isinstance(result, str):
            content = result

        # For now, return structured mock data
        # In production, would parse actual AI response
        return {
            "description": content if content else "Analysis completed",
            "score_pct": 75,
            "improvement_suggestions": {
                "suggestions": [
                    {
                        "title": "Improve error handling",
                        "description": "Add comprehensive error handling",
                        "effort_hours": 8
                    }
                ]
            },
            "endpoints": {}
        }

    def _mock_response(self) -> dict:
        """Return mock response for development/testing."""
        return {
            "description": "Mock analysis result (KI provider not available)",
            "score_pct": 70,
            "improvement_suggestions": {
                "suggestions": [
                    {
                        "title": "Add unit tests",
                        "description": "Increase test coverage",
                        "effort_hours": 16
                    },
                    {
                        "title": "Improve documentation",
                        "description": "Add API documentation",
                        "effort_hours": 8
                    }
                ]
            },
            "endpoints": {
                "rest_endpoints": [
                    {"method": "GET", "path": "/api/v1/repositories"},
                    {"method": "POST", "path": "/api/v1/repositories"}
                ]
            }
        }


class MockKIClient(KIClientPort):
    """
    Mock KI client for testing and development.
    Returns realistic mock responses based on prompt content.
    """

    def analyze(self, prompt_text: str, context: str = "") -> dict:
        """
        Return mock analysis result with realistic data.

        Detects prompt type from keywords and returns appropriate mock data:
        - BDD/Testing → Quality analysis with test coverage
        - REST/API → Service endpoints with maturity levels
        - Security → Security analysis with vulnerabilities
        - Hexagonal/Architecture → Architecture assessment
        - Performance → Performance metrics
        """
        prompt_lower = prompt_text.lower()

        # Detect prompt type
        if "bdd" in prompt_lower or "test" in prompt_lower:
            return self._mock_bdd_analysis()
        elif "rest" in prompt_lower or "api" in prompt_lower:
            return self._mock_rest_analysis()
        elif "soap" in prompt_lower or "wsdl" in prompt_lower:
            return self._mock_soap_analysis()
        elif "security" in prompt_lower or "sicherheit" in prompt_lower:
            return self._mock_security_analysis()
        elif "hexagonal" in prompt_lower or "architecture" in prompt_lower or "architektur" in prompt_lower:
            return self._mock_architecture_analysis()
        elif "performance" in prompt_lower or "performanz" in prompt_lower:
            return self._mock_performance_analysis()
        else:
            return self._mock_generic_analysis()

    def _mock_bdd_analysis(self) -> dict:
        """Mock response for BDD/Testing analysis."""
        return {
            "description": """
            Das Repository zeigt eine moderate Testabdeckung mit grundlegenden Unit-Tests.
            BDD-Praktiken sind teilweise implementiert, könnten aber ausgebaut werden.
            """,
            "score_pct": 65,
            "improvement_suggestions": {
                "suggestions": [
                    {
                        "title": "BDD-Framework einführen",
                        "description": "Cucumber oder Behave für behavior-driven Tests verwenden",
                        "effort_hours": 24
                    },
                    {
                        "title": "Testabdeckung erhöhen",
                        "description": "Testabdeckung von aktuell ~40% auf mindestens 80% steigern",
                        "effort_hours": 40
                    },
                    {
                        "title": "Integration Tests ergänzen",
                        "description": "End-to-End Tests für kritische User-Journeys implementieren",
                        "effort_hours": 32
                    }
                ]
            },
            "endpoints": {}
        }

    def _mock_rest_analysis(self) -> dict:
        """Mock response for REST API analysis."""
        return {
            "description": """
            Die REST API zeigt gute Grundstrukturen, erreicht aber noch nicht Level 2
            des Richardson Maturity Models. Verbesserungspotenzial bei HTTP-Methoden
            und Statuscodes.
            """,
            "score_pct": 55,
            "improvement_suggestions": {
                "suggestions": [
                    {
                        "title": "HTTP-Methoden korrekt verwenden",
                        "description": "GET für Abfragen, POST für Erstellung, PUT für Updates, DELETE für Löschungen",
                        "effort_hours": 16
                    },
                    {
                        "title": "Statuscodes konsistent nutzen",
                        "description": "201 Created, 204 No Content, 404 Not Found korrekt einsetzen",
                        "effort_hours": 8
                    },
                    {
                        "title": "HATEOAS einführen",
                        "description": "Hypermedia-Links für Navigation zu Level 3 aufsteigen",
                        "effort_hours": 40
                    }
                ]
            },
            "endpoints": {
                "rest_endpoints": [
                    {
                        "method": "GET",
                        "path": "/api/v1/repositories",
                        "maturity_level": 2,
                        "description": "Liste aller Repositories"
                    },
                    {
                        "method": "POST",
                        "path": "/api/v1/repositories",
                        "maturity_level": 2,
                        "description": "Neues Repository erstellen"
                    },
                    {
                        "method": "GET",
                        "path": "/api/v1/repositories/{id}",
                        "maturity_level": 2,
                        "description": "Repository-Details"
                    }
                ]
            }
        }

    def _mock_soap_analysis(self) -> dict:
        """Mock response for SOAP service analysis."""
        return {
            "description": """
            SOAP-Services sind grundlegend implementiert mit WSDL-Definitionen.
            WS-Security könnte verbessert werden.
            """,
            "score_pct": 70,
            "improvement_suggestions": {
                "suggestions": [
                    {
                        "title": "WS-Security implementieren",
                        "description": "Username/Password Tokens und Message Signing hinzufügen",
                        "effort_hours": 24
                    },
                    {
                        "title": "WSDL-Dokumentation verbessern",
                        "description": "Detaillierte Beschreibungen für Operations und Datentypen",
                        "effort_hours": 16
                    }
                ]
            },
            "endpoints": {
                "soap_endpoints": [
                    {
                        "operation": "GetRepository",
                        "namespace": "http://example.com/repository/v1",
                        "description": "Ruft Repository-Details ab"
                    }
                ]
            }
        }

    def _mock_security_analysis(self) -> dict:
        """Mock response for security analysis."""
        return {
            "description": """
            Sicherheitsanalyse zeigt einige kritische Schwachstellen, die behoben werden sollten.
            Authentifizierung und Autorisierung sind implementiert, aber Input-Validierung fehlt teilweise.
            """,
            "score_pct": 45,
            "improvement_suggestions": {
                "suggestions": [
                    {
                        "title": "Input-Validierung verstärken",
                        "description": "Alle Eingaben gegen SQL-Injection und XSS absichern",
                        "effort_hours": 32,
                        "priority": "HIGH"
                    },
                    {
                        "title": "Secrets aus Code entfernen",
                        "description": "Hardcodierte Passwörter und API-Keys in Environment-Variablen verschieben",
                        "effort_hours": 8,
                        "priority": "CRITICAL"
                    },
                    {
                        "title": "HTTPS durchgehend verwenden",
                        "description": "Alle HTTP-Verbindungen auf HTTPS umstellen",
                        "effort_hours": 16,
                        "priority": "HIGH"
                    }
                ]
            },
            "endpoints": {}
        }

    def _mock_architecture_analysis(self) -> dict:
        """Mock response for architecture analysis."""
        return {
            "description": """
            Die Architektur zeigt Ansätze von Hexagonaler Architektur (Ports & Adapters).
            Trennung von Domain-Logik und Infrastruktur ist teilweise umgesetzt.
            """,
            "score_pct": 70,
            "improvement_suggestions": {
                "suggestions": [
                    {
                        "title": "Domain-Logik isolieren",
                        "description": "Geschäftslogik vollständig von Framework-Abhängigkeiten trennen",
                        "effort_hours": 40
                    },
                    {
                        "title": "Adapter-Pattern konsequent nutzen",
                        "description": "Alle externen Abhängigkeiten (DB, API) hinter Ports abstrahieren",
                        "effort_hours": 32
                    },
                    {
                        "title": "Dependency Injection einführen",
                        "description": "DI-Container für bessere Testbarkeit einsetzen",
                        "effort_hours": 24
                    }
                ]
            },
            "endpoints": {}
        }

    def _mock_performance_analysis(self) -> dict:
        """Mock response for performance analysis."""
        return {
            "description": """
            Performance-Analyse zeigt Optimierungspotenzial bei Datenbankabfragen
            und Caching. Response-Zeiten sind akzeptabel, könnten aber verbessert werden.
            """,
            "score_pct": 60,
            "improvement_suggestions": {
                "suggestions": [
                    {
                        "title": "Datenbankabfragen optimieren",
                        "description": "N+1 Queries vermeiden, Eager Loading einsetzen",
                        "effort_hours": 24
                    },
                    {
                        "title": "Redis-Cache implementieren",
                        "description": "Häufig abgerufene Daten cachen",
                        "effort_hours": 32
                    },
                    {
                        "title": "API-Response-Kompression",
                        "description": "Gzip-Kompression für API-Responses aktivieren",
                        "effort_hours": 8
                    }
                ]
            },
            "endpoints": {}
        }

    def _mock_generic_analysis(self) -> dict:
        """Generic mock response for unspecified prompts."""
        return {
            "description": """
            Allgemeine Code-Qualitätsanalyse zeigt solide Grundlagen mit
            Verbesserungspotenzial in mehreren Bereichen.
            """,
            "score_pct": 75,
            "improvement_suggestions": {
                "suggestions": [
                    {
                        "title": "Code-Dokumentation erweitern",
                        "description": "Docstrings für alle öffentlichen Funktionen hinzufügen",
                        "effort_hours": 16
                    },
                    {
                        "title": "Linting-Regeln verschärfen",
                        "description": "ESLint/Pylint mit strengeren Regeln konfigurieren",
                        "effort_hours": 8
                    },
                    {
                        "title": "CI/CD Pipeline verbessern",
                        "description": "Automatisierte Tests und Deployments einrichten",
                        "effort_hours": 24
                    }
                ]
            },
            "endpoints": {}
        }
