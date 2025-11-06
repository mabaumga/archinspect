# Repo-Analyst - Schnellstart

## Installation und erster Start

```bash
cd /home/marc/git/archinspect/repo_analyst

# 1. Setup (Virtual Environment, Dependencies, Migrations, Seed-Daten)
make setup

# 2. Repositories importieren
make import-repos

# 3. Server starten
make run
```

## Zugriff

- **Web-UI**: http://localhost:8000
- **Admin-Panel**: http://localhost:8000/admin (nach `make createsuperuser`)
- **API**: http://localhost:8000/api/v1/

## Importierte Test-Repositories

Die folgenden 10 Repositories wurden aus `/home/marc/git/archinspect/testdata/test_repositories.tsv` importiert:

1. **ArvenDatenKurier** (ID: 1778) - art-operations/krake
2. **bka-bff** (ID: 1269) - art-glu/bkv
3. **zahlungen-service** (ID: 7030) - art-makler-und-portale/dkk/dkk-zahlungen
4. **dokumente-service** (ID: 6910) - nele/vu/dokumente
5. **Flowhub Azure IaC** (ID: 4511) - art-operations/pathfinder/flowhub/infrastruktur
6. **YepWebSvc** (ID: 6468) - art-operations/pathfinder/flowhub/services
7. **AgentCommunicationSvc** (ID: 4583) - art-operations/pathfinder/flowhub/services
8. **abocomplete-bff** (ID: 1661) - kompositclassic/abschlussstrecken/onlinestrecken-kfz
9. **ContactManagementSvc** (ID: 4545) - art-operations/pathfinder/flowhub/services
10. **bpm-Dialogeinwilligung-v1** (ID: 3194) - art-doc/customer-data

## Quellcode-Spiegelung

Die Quellcode-Repositories befinden sich bereits extrahiert unter:
- `/home/marc/git/archinspect/testdata/repos/arvendatenkurier/`
- `/home/marc/git/archinspect/testdata/repos/bka-bff/`
- `/home/marc/git/archinspect/testdata/repos/zahlungen-service/`
- usw.

## Markdown-Korpus generieren

Für ein Repository einen Markdown-Korpus erstellen (max. 450 KB):

```bash
# Beispiel für Repository mit ID=1
make generate-md REPO_ID=1
```

Dies erstellt eine Markdown-Datei mit:
- Verzeichnisstruktur
- Priorisierte Dateiinhalte (README zuerst, dann Code, dann Config)
- Größenlimit von 450 KB

## Seed-Daten

Die folgenden Beispiel-Daten wurden automatisch erstellt:

**ARTs:**
- ART Operations
- ART Makler & Portale
- ART Gesundheit & Vorsorge

**Applications:**
- Krake Platform
- DKK Portal
- Flowhub

**Prompts:**
- Techstack-Analyse
- Hexagonale Architektur
- REST API Level 2
- Fachlichkeit

**KI-Provider:**
- OpenAI GPT-4
- Anthropic Claude
- **Mock Provider** (Standard - für Tests und Entwicklung)

## Weitere Befehle

```bash
# Superuser erstellen
make createsuperuser

# Tests ausführen
make test

# Code formatieren
make format

# Linting
make lint

# Coverage Report
make coverage

# Datenbank-Migrationen
make migrate
make makemigrations

# Statische Dateien sammeln
make collectstatic

# Aufräumen
make clean
```

## Architektur

Das Projekt folgt der **Hexagonalen Architektur**:

- **Domain** (`src/domain/`): Entities, Value Objects, Ports
- **Application** (`src/application/`): Use Cases, Services
- **Adapters** (`src/adapters/`):
  - `persistence/`: Django ORM Models
  - `git_platform/`: CSV-Import, Repository-Mirroring, Markdown-Builder
  - `ki/`: KI-Client (HTTP, Mock)
  - `web/`: DRF API, Views, Forms, Serializers
- **Infrastructure** (`src/infrastructure/`): Logging, Settings
- **UI** (`src/ui/templates/`): Bootstrap 5 Templates

## Konfiguration

### Standard-Einstellungen (App Settings)

Nach dem Seed-Prozess (`make setup`) sind folgende Einstellungen automatisch gesetzt:

- **Standard KI-Provider**: Mock Provider (für lokale Tests ohne API-Kosten)
- **Repo Download Root**: `/home/marc/git/archinspect/testdata/repos`
- **Max. Markdown-Korpus**: 450 KB (460.800 Bytes)
- **Include Patterns**: `*.py, *.md, *.txt, *.js, *.ts, *.java, *.yml, *.json` u.a.
- **Exclude Paths**: `.git, node_modules, dist, build, target, venv, .venv`

Diese Einstellungen können über das Django Admin-Panel unter "App Settings" angepasst werden.

### Umgebungsvariablen (.env)

Die Konfiguration erfolgt über die Datei `.env`:

```bash
# Beispiel .env
DJANGO_SECRET_KEY=your-secret-key
DJANGO_DEBUG=True
DATABASE_URL=sqlite:///db.sqlite3
TIME_ZONE=Europe/Berlin
LANGUAGE_CODE=de
LOG_LEVEL=INFO
REPO_DOWNLOAD_ROOT=/data/repos
MAX_CONCAT_BYTES=460800
```

## Bekannte Einschränkungen

1. **Keine Authentifizierung** im ersten Schritt (Intranet-Anwendung)
2. **Synchrone Operationen** - keine Celery/Redis
3. **SQLite für Development** - PostgreSQL für Production empfohlen
4. **Mock KI-Provider** - echte KI-Integration muss noch implementiert werden

## Nächste Schritte

1. Repositories einer Application zuordnen
2. Applications einem ART zuordnen
3. Markdown-Korpora für Repositories generieren
4. Prompts an Repositories ausführen
5. Ergebnisse analysieren und Historie einsehen

## Troubleshooting

### Port bereits belegt
```bash
pkill -f "manage.py runserver"
make run
```

### Migrationen fehlen
```bash
make makemigrations
make migrate
```

### Dependencies fehlen
```bash
make install
```

### Datenbank zurücksetzen
```bash
rm db.sqlite3
make migrate
make seed
make import-repos
```
