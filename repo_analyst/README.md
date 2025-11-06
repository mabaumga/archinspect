# Repo-Analyst

Eine Django-Webanwendung zur Analyse und Verwaltung von Code-Repositories mit KI-Unterstützung, aufgebaut nach den Prinzipien der Hexagonalen Architektur.

## Überblick

Repo-Analyst ermöglicht:
- Import von Repositories aus GitLab (via CSV/TSV im ersten Schritt)
- Zuordnung von Repositories zu Anwendungen und ARTs (Agile Release Trains)
- Spiegelung von Repository-Quellen (aus Testdaten oder Git)
- Generierung von Markdown-Korpora (max. 450 KB, priorisierte Dateiaufnahme)
- Verwaltung von Analyse-Prompts und KI-Providern
- Ausführung von KI-Analysen auf Repositories
- Speicherung und Visualisierung von Analyseergebnissen (Score, Verbesserungsvorschläge, Endpoints)

## Architektur

Das Projekt folgt der **Hexagonalen Architektur** (Ports & Adapters):

```
src/
├── config/              # Django-Konfiguration (Settings, URLs, WSGI/ASGI)
├── domain/              # Domain-Schicht (Entities, Ports)
│   ├── entities.py      # Reine Domain-Objekte (ART, Application, Repository, etc.)
│   └── ports.py         # Port-Interfaces (GitPlatformPort, KIClientPort, etc.)
├── application/         # Application-Schicht (Use Cases, Services)
│   └── services.py      # Services (Import, Assignment, Markdown, Prompt Execution)
├── adapters/
│   ├── persistence/     # Django ORM Models & Admin
│   ├── git_platform/    # Git-Plattform-Adapter (CSV, Mirror, Markdown Builder)
│   ├── ki/              # KI-Client-Adapter (HTTP, Mock)
│   └── web/             # Web-Adapter (DRF API, Views, Forms, Templates)
├── infrastructure/      # Infrastruktur (Logging, Settings)
├── ui/                  # Templates (Bootstrap 5) & Static Files
└── tests/               # Tests (Unit, Integration, BDD)
```

## Technologie-Stack

- **Framework**: Django 5.0, Django REST Framework
- **UI**: Bootstrap 5, django-crispy-forms
- **Datenbank**: PostgreSQL (Fallback: SQLite für Entwicklung)
- **Testing**: pytest, pytest-django, pytest-bdd
- **Code Quality**: ruff, black
- **Dependency Management**: Poetry
- **Lokalisierung**: Zeitzone Europe/Berlin, Sprache Deutsch

## Voraussetzungen

- Python 3.11+
- Poetry (für Dependency Management)
- PostgreSQL (optional, SQLite für Dev)

## Schnellstart

### 1. Repository klonen und ins Verzeichnis wechseln

```bash
cd /home/marc/git/archinspect/repo_analyst
```

### 2. Umgebungsvariablen konfigurieren

```bash
cp .env.example .env
# .env bearbeiten und anpassen
```

Wichtige Variablen:
```env
DJANGO_SECRET_KEY=your-secret-key
DJANGO_DEBUG=True
DATABASE_URL=sqlite:///db.sqlite3
TIME_ZONE=Europe/Berlin
LANGUAGE_CODE=de
REPO_DOWNLOAD_ROOT=/data/repos
MAX_CONCAT_BYTES=460800  # 450 KB
```

### 3. Projekt aufsetzen

```bash
make setup
```

Dies installiert Dependencies, führt Migrationen aus und seedet Initialdaten.

### 4. Superuser erstellen (für Admin-Zugang)

```bash
make createsuperuser
```

### 5. Repositories importieren

```bash
make import-repos
```

Dies importiert Repositories aus `/home/marc/git/archinspect/testdata/test_repositories.tsv`.

### 6. Development Server starten

```bash
make run
```

Die Anwendung ist nun erreichbar unter:
- **Web-UI**: http://localhost:8000
- **Admin**: http://localhost:8000/admin
- **API**: http://localhost:8000/api/v1/

## Makefile-Targets

Das Projekt enthält ein umfassendes Makefile mit folgenden Targets:

### Setup & Installation
- `make help` - Zeigt alle verfügbaren Targets
- `make setup` - Komplettes Setup (install + migrate + seed)
- `make install` - Installiert Dependencies via Poetry
- `make quickstart` - Interaktive Schnellstart-Anleitung

### Datenbank
- `make migrate` - Führt Migrations aus
- `make makemigrations` - Erstellt neue Migrations
- `make createsuperuser` - Erstellt Django Superuser

### Development
- `make run` - Startet Development Server

### Tests
- `make test` - Führt alle Tests aus
- `make test-unit` - Nur Unit-Tests
- `make test-integration` - Nur Integrationstests
- `make test-bdd` - Nur BDD-Tests (pytest-bdd)
- `make coverage` - Tests mit Coverage-Report

### Code-Qualität
- `make lint` - Führt Linter aus (ruff)
- `make format` - Formatiert Code (black + ruff)

### Daten-Management
- `make seed` - Seedet Initialdaten (ARTs, Apps, Prompts, KI-Provider)
- `make import-repos` - Importiert Repositories aus CSV/TSV
- `make generate-md REPO_ID=<id>` - Generiert Markdown-Korpus für Repository

### Sonstiges
- `make collectstatic` - Sammelt Static Files
- `make clean` - Entfernt generierte Dateien

## Verwendung

### Web-UI Navigation

- **Dashboard**: Übersicht mit Statistiken und letzten Prompt-Ausführungen
- **Repositories**: Liste und Verwaltung aller Repositories
  - Filter nach Status, Anwendung, ART
  - Detail-Ansicht mit Prompt-Ausführung und Historie
- **Anwendungen**: CRUD für Applications, Zuordnung zu ARTs
- **ARTs**: CRUD für Agile Release Trains
- **Prompts**: CRUD für Analyse-Prompts (Kategorien: Techstack, Hexagonal, REST L2, Security, etc.)
- **KI Provider**: CRUD für KI-Provider-Konfigurationen

### Repository-Workflow

1. **Import**: Repositories via `make import-repos` oder Management-Command importieren
2. **Zuordnung**: Repositories zu Anwendungen und Anwendungen zu ARTs zuordnen
3. **Spiegelung**: Quellcode wird bei Bedarf aus testdata oder via Git gespiegelt
4. **Markdown-Korpus**: Generierung eines priorisierten Markdown-Dokuments
5. **Prompt-Ausführung**: Analyse-Prompts auf Repository anwenden
6. **Ergebnisse**: Scores, Zusammenfassungen, Verbesserungsvorschläge einsehen

### API (REST Level 2)

Die API ist unter `/api/v1/` verfügbar. Verfügbare Endpoints:

- `GET/POST /api/v1/arts/` - ARTs
- `GET/POST /api/v1/applications/` - Anwendungen
- `GET/POST /api/v1/repositories/` - Repositories
  - `POST /api/v1/repositories/{id}/assign_application/` - Zuordnung ändern
  - `POST /api/v1/repositories/{id}/toggle_active/` - Status wechseln
- `GET/POST /api/v1/prompts/` - Prompts
- `GET/POST /api/v1/ki-providers/` - KI Provider
- `GET/POST /api/v1/prompt-runs/` - Prompt-Ausführungen
- `GET /api/v1/markdown-corpora/` - Markdown-Korpora (read-only)
- `GET /api/v1/settings/` - App-Einstellungen

Alle Endpoints unterstützen:
- Pagination (20 Items per Page)
- Filtering (siehe filterset_fields)
- Searching (siehe search_fields)
- Ordering (siehe ordering_fields)

### Management Commands

#### Repository-Import

```bash
python manage.py import_repositories [--file /path/to/file.tsv]
```

Importiert Repositories aus TSV-Datei. Format:
```
name	description	created_at	updated_at	visibility	is_active	web_url	namespace_path	external_id
```

#### Markdown-Korpus generieren

```bash
python manage.py generate_markdown --repo-id <id> [--max-bytes <bytes>]
```

Generiert priorisierten Markdown-Korpus:
1. README/LICENSE (höchste Priorität)
2. Application Code (.py, .js, .java, etc.)
3. Konfiguration (.yml, .json, .toml)
4. Dokumentation & Scripts
5. Frontend (.html, .css)

Größenlimit: 450 KB (konfigurierbar). Bei Überschreitung wird Unvollständigkeit markiert.

#### Seed Initialdaten

```bash
python manage.py seed_data
```

Erstellt Beispieldaten für ARTs, Applications, Prompts und KI Provider.

## Tests

Das Projekt enthält drei Test-Typen:

### Unit-Tests
```bash
make test-unit
```

Testen isolierte Komponenten (Domain Entities, Adapter-Logik).

### Integrationstests
```bash
make test-integration
```

Testen Zusammenspiel von Services und Datenbank.

### BDD-Tests (pytest-bdd)
```bash
make test-bdd
```

Feature-Files in `src/tests/bdd/*.feature`:
- `import_repositories.feature` - Repository-Import

## Konfiguration

### Umgebungsvariablen (.env)

```env
# Django
DJANGO_SECRET_KEY=your-secret-key-change-in-production
DJANGO_DEBUG=True
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1

# Database
DATABASE_URL=postgresql://user:password@localhost:5432/repo_analyst
# Oder SQLite für Dev:
# DATABASE_URL=sqlite:///db.sqlite3

# Locale
TIME_ZONE=Europe/Berlin
LANGUAGE_CODE=de

# Logging
LOG_LEVEL=INFO
LOG_JSON=1

# Repository Settings
REPO_DOWNLOAD_ROOT=/data/repos
INCLUDE_PATTERNS=*.py,*.md,*.txt,*.js,*.ts,*.tsx,*.jsx,*.java,*.kt,*.go,*.yml,*.yaml,*.json
EXCLUDE_PATHS=.git,node_modules,dist,build,target,venv,.venv,__pycache__
MAX_CONCAT_BYTES=460800  # 450 KB

# KI Provider Tokens (Beispiele)
OPENAI_API_KEY=sk-...
AZURE_OPENAI_KEY=...
ANTHROPIC_API_KEY=...
```

### Testdaten

Testdaten liegen in:
- **Repositories**: `/home/marc/git/archinspect/testdata/repos/`
- **Repository-Liste**: `/home/marc/git/archinspect/testdata/test_repositories.tsv`

Beim Repository-Mirror wird zuerst in testdata gesucht, dann würde Git-Clone erfolgen (derzeit Placeholder).

## Deployment

### Produktion

Für Produktion sollten folgende Anpassungen vorgenommen werden:

1. **Secret Key**: Neuen Secret Key generieren
2. **Debug**: `DJANGO_DEBUG=False` setzen
3. **Allowed Hosts**: Produktions-Hosts eintragen
4. **Database**: PostgreSQL verwenden
5. **Static Files**: `make collectstatic` und Webserver-Config
6. **Logging**: JSON-Logging aktiviert lassen
7. **KI-Tokens**: Via Secrets Management, nicht in .env

### Docker (optional)

Ein `Dockerfile` und `docker-compose.yml` können ergänzt werden für Container-Deployment.

## Projektstruktur (Details)

```
repo_analyst/
├── manage.py                # Django Management Script
├── pyproject.toml          # Poetry Dependencies & Config
├── Makefile                # Build & Task Automation
├── .env.example            # Beispiel-Umgebungsvariablen
├── README.md               # Diese Datei
└── src/
    ├── config/             # Django-Konfiguration
    │   ├── settings.py
    │   ├── urls.py
    │   ├── wsgi.py
    │   └── asgi.py
    ├── domain/             # Domain Layer
    │   ├── entities.py     # ART, Application, Repository, etc.
    │   └── ports.py        # GitPlatformPort, KIClientPort, etc.
    ├── application/        # Application Layer
    │   └── services.py     # Use Case Services
    ├── adapters/
    │   ├── persistence/    # Django ORM
    │   │   ├── models.py
    │   │   ├── admin.py
    │   │   └── management/commands/
    │   ├── git_platform/   # Git-Adapter
    │   │   ├── csv_adapter.py
    │   │   ├── mirror_adapter.py
    │   │   └── markdown_builder.py
    │   ├── ki/             # KI-Adapter
    │   │   └── http_client.py
    │   └── web/            # Web-Adapter
    │       ├── serializers.py
    │       ├── viewsets.py
    │       ├── views.py
    │       ├── forms.py
    │       ├── api_urls.py
    │       └── ui_urls.py
    ├── infrastructure/     # Infrastruktur
    │   ├── logging/        # Structured Logging
    │   └── settings/
    ├── ui/
    │   ├── templates/      # Bootstrap 5 Templates
    │   └── static/         # CSS, JS
    ├── tests/              # Tests
    │   ├── unit/
    │   ├── integration/
    │   └── bdd/
    └── seeds/              # Seed-Daten
        └── mock_repos.json
```

## Hexagonale Architektur - Komponenten

### Domain Layer
- **Entities**: Reine Business-Objekte ohne Framework-Dependencies
- **Ports**: Interfaces für Adapter (GitPlatformPort, KIClientPort, etc.)

### Application Layer
- **Services**: Orchestrierung von Use Cases
  - `RepositoryImportService`
  - `RepositoryAssignmentService`
  - `MarkdownCorpusService`
  - `PromptExecutionService`

### Adapters
- **Persistence**: Django ORM Models
- **Git Platform**: CSV Reader, Repository Mirror, Markdown Builder
- **KI**: HTTP Client (OpenAI, Anthropic, etc.), Mock Client
- **Web**: DRF ViewSets, Django Views, Forms, Templates

### Infrastructure
- **Logging**: JSON-Logging mit Request-IDs
- **Settings**: django-environ basierte Konfiguration

## Besonderheiten

### CSV-Import
- **Delimiter**: TAB (\t)
- **Datums-Parsing**: Flexibel via dateutil (ISO-8601 mit/ohne Offset)
- **Idempotenz**: Upsert via `external_id`

### Markdown-Korpus
- **Priorisierung**: README → App-Code → Config → Docs → Frontend
- **Größenlimit**: 450 KB (konfigurierbar)
- **Strukturerhalt**: Directory Tree + Datei-Inhalte in Codeblöcken
- **Ausschlüsse**: Binary, Media, .git, node_modules, etc.

### KI-Integration
- **Generisch**: HTTP-Client für beliebige APIs (OpenAI, Anthropic, Azure, etc.)
- **Auth**: Token via Umgebungsvariablen (Name in DB gespeichert)
- **Mock**: Mock-Client für Entwicklung ohne echte API
- **Response-Format**: JSON mit description, score_pct, improvement_suggestions, endpoints

## Troubleshooting

### Import schlägt fehl
- Prüfen, ob TSV-Datei existiert: `/home/marc/git/archinspect/testdata/test_repositories.tsv`
- Delimiter muss TAB sein, nicht Komma

### Markdown-Generierung schlägt fehl
- Repository muss existieren und Quellen müssen verfügbar sein
- Prüfen: `/home/marc/git/archinspect/testdata/repos/<repo_name>/`

### Tests schlagen fehl
- Django-Settings richtig konfiguriert?
- Database-URL korrekt in .env?
- Dependencies installiert? (`make install`)

## Lizenz

Internes Projekt.

## Kontakt

Bei Fragen: R+V Team

---

**Version**: 0.1.0
**Erstellt**: 2025-11-04
**Django**: 5.0
**Python**: 3.11+
