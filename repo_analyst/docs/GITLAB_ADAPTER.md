# GitLab Adapter Documentation

Diese Dokumentation beschreibt die GitLab-Adapter für das Repo-Analyst-Projekt.

## Übersicht

Es wurden zwei GitLab-Adapter implementiert, die die hexagonale Architektur des Projekts befolgen:

1. **GitLabAdapter**: Implementiert `GitPlatformPort` zum Abrufen von Repository-Listen
2. **GitLabMirrorAdapter**: Implementiert `RepositoryMirrorPort` zum Clonen/Aktualisieren von Repositories

## Installation

### Dependencies

Fügen Sie folgende Dependencies zur `requirements.txt` hinzu (bereits erledigt):

```
python-gitlab>=4.0,<5.0
GitPython>=3.1,<4.0
```

Installation:

```bash
pip install -r requirements.txt
```

oder mit Poetry:

```bash
poetry install
```

## Konfiguration

### GitLab Access Token

Erstellen Sie einen GitLab Personal Access Token mit folgenden Berechtigungen:

- `read_api` - Zum Abrufen von Projekt-Informationen
- `read_repository` - Zum Clonen von Repositories

Der Token kann auf zwei Arten bereitgestellt werden:

1. **Umgebungsvariable** (empfohlen):
   ```bash
   export GITLAB_TOKEN="your-token-here"
   export GITLAB_URL="https://gitlab.com"  # Optional, Standard: https://gitlab.com
   ```

2. **Command-Line Parameter**:
   ```bash
   --token your-token-here
   --url https://gitlab.com
   ```

## Nutzung

### 1. GitLabAdapter - Repositories importieren

Der `GitLabAdapter` implementiert `GitPlatformPort` und ruft Repository-Listen von GitLab ab.

#### Management Command

```bash
# Mit Umgebungsvariablen
export GITLAB_TOKEN="your-token"
python manage.py import_from_gitlab

# Mit Command-Line Parametern
python manage.py import_from_gitlab --token your-token --url https://gitlab.com

# Mit privatem GitLab (ohne SSL-Verifikation)
python manage.py import_from_gitlab --token your-token --url https://gitlab.internal.company.com --no-ssl-verify

# Mit custom page size
python manage.py import_from_gitlab --token your-token --page-size 50
```

#### Programmatische Nutzung

```python
from adapters.git_platform.gitlab_adapter import GitLabAdapter
from application.services import RepositoryImportService

# GitLab Adapter erstellen
adapter = GitLabAdapter(
    private_token="your-token",
    gitlab_url="https://gitlab.com",
    ssl_verify=True  # False für self-signed certificates
)

# Service erstellen und Repositories importieren
service = RepositoryImportService(adapter)
count = service.import_repositories()

print(f"Imported {count} repositories")
```

#### Rückgabewerte

Der `GitLabAdapter` konvertiert GitLab-Projekte in `RepositoryDTO` Objekte:

```python
@dataclass
class RepositoryDTO:
    external_id: str           # GitLab Project ID
    name: str                  # Projektname
    url: str                   # Web URL zum Projekt
    description: str           # Projektbeschreibung
    tech_stack: str            # Aus Topics/Tags
    namespace_path: str        # z.B. "group/subgroup/project"
    visibility: str            # public, internal, private
    is_active: bool            # Nicht archiviert
    created_at: datetime       # Erstellungsdatum
    updated_at: datetime       # Letztes Update
```

### 2. GitLabMirrorAdapter - Repositories clonen

Der `GitLabMirrorAdapter` implementiert `RepositoryMirrorPort` und clont/aktualisiert Repositories lokal.

#### Management Command

```bash
# Alle aktiven Repositories clonen
export GITLAB_TOKEN="your-token"
python manage.py clone_from_gitlab

# Ein einzelnes Repository clonen
python manage.py clone_from_gitlab --repo-id 123

# Mit custom Target-Directory
python manage.py clone_from_gitlab --target-dir /path/to/repos

# Von privatem GitLab
python manage.py clone_from_gitlab --token your-token --url https://gitlab.internal.company.com --no-ssl-verify
```

#### Programmatische Nutzung

```python
from pathlib import Path
from adapters.git_platform.gitlab_mirror_adapter import GitLabMirrorAdapter

# Mirror Adapter erstellen
mirror = GitLabMirrorAdapter(
    private_token="your-token",
    gitlab_url="https://gitlab.com",
    ssl_verify=True
)

# Repository clonen oder aktualisieren
local_path = mirror.mirror_repository(
    repo_name="my-project",
    repo_url="https://gitlab.com/group/my-project",
    namespace_path="group/my-project",
    target_dir=Path("/data/repos")
)

print(f"Repository cloned to: {local_path}")
```

#### Features

- **Automatische Clone/Pull Erkennung**: Wenn Repository bereits existiert, wird `git pull` ausgeführt
- **Namespace-basierte Pfade**: Repositories werden in ihrer Namespace-Struktur gespeichert (z.B. `/data/repos/group/subgroup/project`)
- **Authentifizierung**: Nutzt OAuth2-Token für HTTPS-Clone
- **Fehlerbehandlung**: Robuste Error-Handling mit Logging
- **Fallback-Suche**: Wenn Projekt-ID nicht funktioniert, sucht nach Namen und vergleicht URLs

## Architektur

### Hexagonale Architektur

Die GitLab-Adapter folgen dem Port-Adapter-Pattern:

```
┌─────────────────────────────────────────────────────┐
│                   Application Layer                 │
│                                                      │
│  RepositoryImportService  MarkdownCorpusService     │
│         │                        │                   │
│         ▼                        ▼                   │
└─────────────────────────────────────────────────────┘
           │                        │
           │ Uses Port              │ Uses Port
           ▼                        ▼
┌─────────────────────┐   ┌──────────────────────┐
│  GitPlatformPort    │   │ RepositoryMirrorPort │
│   (Interface)       │   │    (Interface)       │
└─────────────────────┘   └──────────────────────┘
           ▲                        ▲
           │ Implements             │ Implements
           │                        │
┌──────────────────────┐  ┌──────────────────────┐
│   GitLabAdapter      │  │ GitLabMirrorAdapter  │
│                      │  │                      │
│ - list_repositories()│  │ - mirror_repository()│
└──────────────────────┘  └──────────────────────┘
           │                        │
           ▼                        ▼
    GitLab API              GitLab + Git Clone
```

### Vorteile

- **Austauschbar**: CSV, GitLab oder andere Plattformen können ohne Änderung der Business-Logik verwendet werden
- **Testbar**: Adapter können durch Mocks ersetzt werden
- **Unabhängig**: Domain-Layer hat keine Abhängigkeit zu GitLab

## Beispiel-Workflows

### Workflow 1: Repositories von GitLab importieren und clonen

```bash
# Schritt 1: Token setzen
export GITLAB_TOKEN="your-token"
export GITLAB_URL="https://gitlab.com"

# Schritt 2: Repositories von GitLab importieren
python manage.py import_from_gitlab

# Schritt 3: Repositories lokal clonen
python manage.py clone_from_gitlab --target-dir /data/repos

# Schritt 4: Markdown Corpus generieren
python manage.py generate_markdown --repo-id 1
```

### Workflow 2: Nur bestimmte Repositories

```bash
# Repository-Liste mit Filter importieren (im Code anpassen)
# Dann einzelne Repositories clonen
python manage.py clone_from_gitlab --repo-id 42
```

### Workflow 3: Mit privatem GitLab ohne SSL-Verifikation

```bash
export GITLAB_TOKEN="your-token"
export GITLAB_URL="https://gitlab.internal.company.com"

python manage.py import_from_gitlab --no-ssl-verify
python manage.py clone_from_gitlab --no-ssl-verify
```

## Fehlerbehandlung

### Häufige Fehler

1. **Authentication failed**
   - Prüfen Sie, ob der Token gültig ist
   - Prüfen Sie, ob der Token die richtigen Permissions hat (`read_api`, `read_repository`)

2. **SSL Certificate verification failed**
   - Bei self-signed Certificates: `--no-ssl-verify` verwenden
   - Oder Zertifikat zum System-Trust-Store hinzufügen

3. **Project not found**
   - Prüfen Sie, ob der User Zugriff auf das Projekt hat
   - Der Adapter versucht Fallback-Suche über Namen

4. **Git clone failed**
   - Prüfen Sie Netzwerk-Verbindung
   - Prüfen Sie, ob genug Speicherplatz vorhanden ist
   - Prüfen Sie Token-Permissions

### Logging

Alle Adapter nutzen Python's `logging` Modul:

```python
import logging

# Debug-Level für detaillierte Ausgaben
logging.basicConfig(level=logging.DEBUG)

# Oder nur für GitLab-Adapter
logging.getLogger('adapters.git_platform.gitlab_adapter').setLevel(logging.DEBUG)
logging.getLogger('adapters.git_platform.gitlab_mirror_adapter').setLevel(logging.DEBUG)
```

## Sicherheit

### Best Practices

1. **Token-Speicherung**
   - Nutzen Sie Umgebungsvariablen, nicht Hardcoding
   - Nutzen Sie `.env` Dateien (nicht in Git committen!)
   - Für Produktion: Nutzen Sie Secret-Management (Vault, AWS Secrets Manager, etc.)

2. **SSL-Verifikation**
   - Deaktivieren Sie SSL-Verifikation nur in Entwicklungsumgebungen
   - In Produktion: Installieren Sie gültige Zertifikate

3. **Token-Permissions**
   - Nutzen Sie Token mit minimalen Permissions (`read_api`, `read_repository`)
   - Keine `write` oder `admin` Permissions, außer unbedingt nötig

4. **Token-Rotation**
   - Rotieren Sie Token regelmäßig
   - Widerrufen Sie alte Token

## Testing

### Unit Tests

Erstellen Sie Mock-Implementierungen für Tests:

```python
# test_gitlab_adapter.py
from unittest.mock import Mock, patch
from adapters.git_platform.gitlab_adapter import GitLabAdapter

def test_list_repositories():
    with patch('gitlab.Gitlab') as mock_gitlab:
        # Mock GitLab API
        mock_project = Mock()
        mock_project.id = 123
        mock_project.name = "test-repo"
        mock_project.web_url = "https://gitlab.com/test/repo"

        mock_gitlab.return_value.projects.list.return_value = [mock_project]

        # Test adapter
        adapter = GitLabAdapter("token", "https://gitlab.com")
        repos = adapter.list_repositories()

        assert len(repos) == 1
        assert repos[0].name == "test-repo"
```

## Migration von CSV zu GitLab

Wenn Sie von CSV auf GitLab migrieren möchten:

1. **Vorher**: CSV-basierter Import
   ```python
   adapter = CSVMockAdapter(csv_path)
   service = RepositoryImportService(adapter)
   ```

2. **Nachher**: GitLab-basierter Import
   ```python
   adapter = GitLabAdapter(token, gitlab_url)
   service = RepositoryImportService(adapter)
   ```

3. **Hybrid**: Beide parallel nutzen
   ```python
   # Development: CSV
   if settings.DEBUG:
       adapter = CSVMockAdapter(csv_path)
   # Production: GitLab
   else:
       adapter = GitLabAdapter(token, gitlab_url)

   service = RepositoryImportService(adapter)
   ```

## Weiterführende Dokumentation

- [GitLab API Dokumentation](https://docs.gitlab.com/ee/api/)
- [python-gitlab Dokumentation](https://python-gitlab.readthedocs.io/)
- [GitPython Dokumentation](https://gitpython.readthedocs.io/)
- [Hexagonal Architecture](https://alistair.cockburn.us/hexagonal-architecture/)

## Support

Bei Fragen oder Problemen:

1. Prüfen Sie die Logs (mit `--debug` Flag)
2. Prüfen Sie die GitLab API Dokumentation
3. Öffnen Sie ein Issue im Projekt-Repository
