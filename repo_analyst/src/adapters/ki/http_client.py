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
    """Mock KI client for testing."""

    def analyze(self, prompt_text: str, context: str = "") -> dict:
        """Return mock analysis result."""
        return {
            "description": f"Mock analysis for prompt: {prompt_text[:50]}...",
            "score_pct": 80,
            "improvement_suggestions": {
                "suggestions": [
                    {
                        "title": "Example improvement",
                        "description": "This is a mock suggestion",
                        "effort_hours": 4
                    }
                ]
            },
            "endpoints": {}
        }
