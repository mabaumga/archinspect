"""
Domain entities for Repo-Analyst application.
These are pure domain objects without any framework dependencies.
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class ART:
    """Agile Release Train"""
    name: str
    business_owner_it: str
    id: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


@dataclass
class Application:
    """Application within an ART"""
    name: str
    alphabet_id: str
    description: str = ""
    art_id: Optional[int] = None
    id: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


@dataclass
class Repository:
    """Code repository"""
    name: str
    external_id: str
    url: str
    description: str = ""
    tech_stack: str = ""
    is_active: bool = True
    namespace_path: str = ""
    visibility: str = "internal"
    application_id: Optional[int] = None
    id: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    local_path: Optional[str] = None


@dataclass
class Prompt:
    """Analysis prompt template"""
    title: str
    short_description: str
    category: str
    prompt_text: str
    id: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


@dataclass
class KIProvider:
    """AI/KI provider configuration"""
    name: str
    base_url: str
    model_name: str
    auth_token_env_var: str
    timeout_s: int = 30
    id: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


@dataclass
class PromptRun:
    """Result of running a prompt against a repository"""
    repository_id: int
    prompt_id: int
    ki_provider_id: int
    request_text: str
    response_json: dict
    score_pct: Optional[int] = None
    summary: str = ""
    improvement_suggestions: dict = field(default_factory=dict)
    endpoints: dict = field(default_factory=dict)
    id: Optional[int] = None
    created_at: Optional[datetime] = None


@dataclass
class RepositoryDTO:
    """Data Transfer Object for repository import"""
    external_id: str
    name: str
    url: str
    description: str = ""
    tech_stack: str = ""
    namespace_path: str = ""
    visibility: str = "internal"
    is_active: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
