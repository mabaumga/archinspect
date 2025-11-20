# ArcInspect - Repository Analyst

Django-basierte Webanwendung zur Analyse von Code-Repositories mit KI-Unterstützung.

## 📋 Überblick

**ArcInspect** (Repo-Analyst) ist eine Anwendung zur systematischen Analyse von Git-Repositories aus GitLab oder anderen Quellen. Sie ermöglicht:

- **Repository-Import** aus GitLab oder CSV-Testdaten
- **Zuordnung** zu Anwendungen und Agile Release Trains (ARTs)
- **Quellcode-Spiegelung** und lokales Caching
- **Markdown-Korpus-Generierung** für KI-Analysen
- **KI-gestützte Analyse** mit konfigurierbaren Prompts und Providern
- **Qualitätsanalysen** für Architektur, Security, Testing und mehr

### Architektur

Das Projekt folgt **Hexagonaler Architektur** (Ports & Adapters) mit klarer Trennung:

```
domain/          # Domain-Logik (framework-unabhängig)
application/     # Use Cases und Services
adapters/        # Adapter für Datenbank, APIs, Git, KI
infrastructure/  # Logging, Settings, Factory
ui/              # Templates und Static Files
```

Siehe auch: [Hexagonal Architecture Documentation](docs/architecture/hexagonal-architecture.md)

---

## 🚀 Quick Start

### Voraussetzungen

- Python 3.11+
- PostgreSQL (optional, SQLite für Development)
- Git

### Setup

```bash
# 1. Repository klonen
git clone <repository-url>
cd archinspect/repo_analyst

# 2. Umgebung einrichten
make setup

# 3. .env-Datei erstellen
cp .env.example .env
# Bearbeite .env und passe Konfiguration an

# 4. Superuser erstellen
make createsuperuser

# 5. Testdaten importieren (optional)
make import-repos

# 6. Server starten
make run
```

Die Anwendung ist nun verfügbar unter:
- **Web UI:** http://localhost:8000
- **Admin:** http://localhost:8000/admin
- **API:** http://localhost:8000/api/v1/

---

## 🔧 Konfiguration

### Adapter-Konfiguration

Das System unterstützt zwei Repository-Adapter:

**Mock Adapter (Standard):**
```bash
# .env
REPOSITORY_ADAPTER=mock
```
Nutzt Testdaten aus `/testdata/` - ideal für Entwicklung und Tests.

**GitLab Adapter:**
```bash
# .env
REPOSITORY_ADAPTER=gitlab
GITLAB_URL=https://gitlab.example.com
GITLAB_ACCESS_TOKEN=your-token-here
GITLAB_SSL_VERIFY=true
```

Siehe [ADAPTER_CONFIGURATION.md](ADAPTER_CONFIGURATION.md) für Details.

### Weitere Konfiguration

```bash
# Django
DJANGO_SECRET_KEY=your-secret-key
DJANGO_DEBUG=False

# Datenbank
DATABASE_URL=postgresql://user:pass@localhost/repo_analyst

# Korpus-Generierung
REPO_DOWNLOAD_ROOT=/data/repos
CORPUS_OUTPUT_DIR=/data/corpus
MAX_CONCAT_BYTES=460800
```

---

## 📦 Makefile Targets

```bash
make help              # Zeigt alle verfügbaren Targets

# Development
make setup             # Erstellt venv, installiert Dependencies, führt Migrationen aus
make run               # Startet Development Server
make migrate           # Führt Migrationen aus
make createsuperuser   # Erstellt Django Superuser

# Testing & Qualität
make test              # Führt alle Tests aus
make test-unit         # Nur Unit Tests
make test-integration  # Nur Integration Tests
make test-bdd          # Nur BDD Tests
make coverage          # Test Coverage Report
make check-dod         # Definition of Done Check (Linting, Tests, Coverage)

# Code Quality
make lint              # Linter (ruff)
make format            # Code formatieren (black + ruff)
make typecheck         # Type checking (mypy)

# Daten
make seed              # Seed initial data
make import-repos      # Importiert Repositories
make generate-md       # Generiert Markdown-Korpus (REPO_ID=<id>)
```

---

## 🧪 Tests

Das Projekt nutzt eine **Test-Pyramide** mit drei Ebenen:

```bash
# Unit Tests (schnell, isoliert)
make test-unit

# Integration Tests (Adapter, Datenbank)
make test-integration

# BDD Tests (Feature-basiert)
make test-bdd

# Kompletter Test-Durchlauf mit Coverage
make coverage
```

**Definition of Done Check:**
```bash
make check-dod
```
Führt alle Quality Gates aus:
- ✅ Linting
- ✅ Unit Tests
- ✅ Integration Tests
- ✅ BDD Tests
- ✅ Domain Coverage ≥ 80%

---

## 📚 Dokumentation

### Architektur
- [Hexagonal Architecture](docs/architecture/hexagonal-architecture.md)
- [Architecture Decision Records (ADRs)](docs/architecture/adr/)

### Entwicklung
- [Coding Standards](docs/development/coding-standards.md)
- [Testing Strategy](docs/development/testing-strategy.md)
- [Git Workflow](docs/development/git-workflow.md)
- [Security Guidelines](docs/development/security-guidelines.md)

### Prozesse
- [Definition of Done](docs/processes/definition-of-done.md)
- [Definition of Ready](docs/processes/definition-of-ready.md)
- [Deployment Guide](docs/processes/deployment-guide.md)

---

## 🔌 API

Die Anwendung bietet eine RESTful API (Level 2):

**Base URL:** `http://localhost:8000/api/v1/`

**Verfügbare Endpoints:**
- `/api/v1/repositories/` - Repository-Verwaltung
- `/api/v1/applications/` - Anwendungen
- `/api/v1/arts/` - Agile Release Trains
- `/api/v1/prompts/` - Analyse-Prompts
- `/api/v1/ki-providers/` - KI-Provider
- `/api/v1/prompt-runs/` - Analyse-Ergebnisse

**API Browser:** http://localhost:8000/api/v1/

---

## 🏗️ Projektstruktur

```
archinspect/
├── repo_analyst/                   # Django-Projekt
│   ├── manage.py
│   ├── Makefile
│   ├── requirements.txt
│   ├── pyproject.toml
│   └── src/
│       ├── config/                 # Django Settings, URLs
│       ├── domain/                 # Domain Layer (Entities, Ports)
│       ├── application/            # Application Services
│       ├── adapters/
│       │   ├── persistence/        # Django Models & Repositories
│       │   ├── git_platform/       # Git-Adapter (GitLab, Mock)
│       │   ├── ki/                 # KI-Client-Adapter
│       │   └── web/                # Views, ViewSets, Serializer
│       ├── infrastructure/         # Logging, Factory, Settings
│       ├── ui/                     # Templates, Static Files
│       └── tests/                  # Unit, Integration, BDD Tests
├── testdata/                       # Testdaten für Mock-Adapter
│   ├── test_repositories.tsv
│   └── repos/
├── docs/                           # Projektdokumentation
└── README.md
```

---

## 🛠️ Entwicklung

### Pre-commit Hooks (empfohlen)

```bash
# Pre-commit installieren
pip install pre-commit
pre-commit install

# Manuell ausführen
pre-commit run --all-files
```

### Neue Migration erstellen

```bash
make makemigrations
make migrate
```

### Neue Tests schreiben

```python
# tests/unit/test_my_feature.py
import pytest

def test_my_feature():
    # Arrange
    # Act
    # Assert
    pass
```

### Code-Qualität sicherstellen

Vor jedem Commit:
```bash
make format      # Code formatieren
make lint        # Linting
make typecheck   # Type Checking
make test        # Tests
```

Oder alles auf einmal:
```bash
make check-dod
```

---

## 🐛 Troubleshooting

### Import schlägt fehl

**Problem:** `CSV file not found`

**Lösung:**
```bash
# Stelle sicher, dass Testdaten existieren
ls testdata/test_repositories.tsv
```

### GitLab-Authentifizierung fehlgeschlagen

**Problem:** `Failed to authenticate with GitLab`

**Lösung:**
1. Token in `.env` prüfen
2. Token-Berechtigungen prüfen (`read_api`, `read_repository`)
3. GitLab-URL korrekt? (mit `https://`)

### Tests schlagen fehl

**Problem:** `django.db.utils.OperationalError`

**Lösung:**
```bash
# Migrations ausführen
make migrate

# Oder Datenbank zurücksetzen
rm db.sqlite3
make migrate
```

---

## 📄 Lizenz

Internes Projekt - R+V Versicherung

---

## 🤝 Beitragen

Bitte folge diesen Schritten:

1. Feature-Branch erstellen: `git checkout -b feature/my-feature`
2. Änderungen committen: `git commit -m "Add my feature"`
3. Tests schreiben und DoD erfüllen: `make check-dod`
4. Pull Request erstellen

Siehe [Git Workflow](docs/development/git-workflow.md) für Details.

---

## 📧 Kontakt

Bei Fragen oder Problemen wende dich an das Entwicklerteam.
