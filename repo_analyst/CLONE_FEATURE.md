# Repository Clone Feature

## Überblick

Die Clone-Funktionalität ermöglicht es, Repositories von GitLab zu "klonen" (simuliert). Das System kopiert dabei transparent Quellcode aus dem Testdaten-Verzeichnis an einen organisierten Speicherort, als wäre es ein echter Git-Clone.

## Architektur

### Transparenz-Prinzip

Das System arbeitet vollständig transparent:
- **Aus Sicht der Anwendung**: Ein Repository wird von GitLab geklont
- **Tatsächliche Implementation**: Dateien werden von `testdata/repos/` nach `/data/repos/` kopiert
- **Vorteil**: Einfacher Austausch des Mock-Services gegen echten Git-Clone in Produktion

### Komponenten

1. **GitCloneService** (`src/adapters/git_platform/clone_service.py`)
   - Kopiert Repository von `testdata/repos/{repo_name}/`
   - Nach `/data/repos/{namespace_path}/{repo_name}/`
   - Organisiert nach GitLab-Namespaces
   - Normalisiert Repository-Namen automatisch

2. **Repository Model** (`src/adapters/persistence/models.py`)
   - Feld `local_path`: Speichert Pfad zum geklonten Repository
   - Wird nach erfolgreichem Clone gesetzt

3. **View** (`src/adapters/web/views.py`)
   - Funktion `repository_clone(request, pk)`
   - Orchestriert den Clone-Prozess
   - Gibt Feedback über Dateianzahl und Größe

4. **UI** (`src/ui/templates/repositories/detail.html`)
   - Button "Klonen" (wenn noch nicht geklont)
   - Status "Geklont" (wenn bereits vorhanden)
   - Anzeige des lokalen Pfads in Repository-Info

## Verwendung

### Via Web-UI

#### Repository-Detailseite

1. Repository-Detailseite öffnen (z.B. http://localhost:8000/repositories/1/)
2. Button **"Klonen"** anklicken (wenn noch nicht geklont) oder **"Aktualisieren"** (wenn bereits geklont)
3. Repository wird kopiert/aktualisiert und lokaler Pfad wird angezeigt

Der Button wechselt automatisch:
- **"Klonen"** (blau, Download-Icon) - wenn Repository noch nicht lokal vorhanden
- **"Aktualisieren"** (grau, Refresh-Icon) - wenn Repository bereits geklont ist

#### Repository-Liste

1. Repository-Liste öffnen (http://localhost:8000/repositories/)
2. Clone-Status-Spalte zeigt aktuellen Zustand:
   - ✓ **Geklont** (grünes Badge) - Repository ist lokal vorhanden
   - ✗ **Nicht geklont** (graues Badge) - Repository noch nicht geklont
3. Aktionen-Buttons:
   - Download-Icon (blau) - zum erstmaligen Klonen
   - Refresh-Icon (grau) - zum Aktualisieren
   - Auge-Icon - zur Detailansicht

### Via Python/Management Command

```python
from adapters.git_platform.clone_service import GitCloneService
from adapters.persistence.models import Repository

# Repository holen
repo = Repository.objects.get(pk=1)

# Clone Service initialisieren
clone_service = GitCloneService()

# Repository klonen oder aktualisieren
cloned_path, was_updated = clone_service.update_or_clone_repository(
    repo_name=repo.name,
    namespace_path=repo.namespace_path,
    target_root='/data/repos',
    source_url=repo.url,
    local_path=repo.local_path  # Optional: vorhandener Pfad
)

# Pfad in DB speichern
repo.local_path = str(cloned_path)
repo.save()

# Check ob aktualisiert oder neu geklont
if was_updated:
    print(f"Repository {repo.name} wurde aktualisiert")
else:
    print(f"Repository {repo.name} wurde neu geklont")
```

**Alternativ: Nur Klonen (ohne Auto-Update-Logik)**

```python
# Direkt klonen (überschreibt existierende Version)
cloned_path = clone_service.clone_repository(
    repo_name=repo.name,
    namespace_path=repo.namespace_path,
    target_root='/data/repos',
    source_url=repo.url
)
```

## Verzeichnisstruktur

### Quelle (Testdaten)
```
/home/marc/git/archinspect/testdata/repos/
├── arvendatenkurier/
│   ├── ArvenDatenKurier.Api/
│   └── ...
├── bka-bff/
├── zahlungen-service/
└── ...
```

### Ziel (Geklonte Repos)
```
/data/repos/
├── art-operations/
│   └── krake/
│       └── ArvenDatenKurier/    # ← Geklont von testdata
│           ├── ArvenDatenKurier.Api/
│           └── ...
├── art-glu/
│   └── bkv/
│       └── bka-bff/
└── ...
```

## Name-Normalisierung

Der Clone-Service normalisiert Repository-Namen automatisch:

| Repository-Name (GitLab) | Testdata-Verzeichnis | Normalisiert zu |
|--------------------------|----------------------|-----------------|
| ArvenDatenKurier         | arvendatenkurier     | arvendatenkurier |
| Flowhub Azure IaC        | flowhub-azure-iac    | flowhub-azure-iac |
| YepWebSvc                | yepwebsvc            | yepwebsvc |

Mapping erfolgt in `GitCloneService._normalize_repo_name()`.

## Integration mit Markdown-Generator

Der Markdown-Generator (`MarkdownCorpusService`) nutzt automatisch den geklonten Pfad:

```python
# generate_markdown.py Command
repo = Repository.objects.get(pk=repo_id)

# Prüft automatisch ob repo.local_path existiert
if not repo.local_path or not Path(repo.local_path).exists():
    # Klont Repository falls nötig
    local_path = self.mirror.mirror_repository(...)
    repo.local_path = str(local_path)
    repo.save()

# Nutzt geklonten Pfad für Markdown-Generierung
corpus = markdown_builder.build_corpus(Path(repo.local_path), ...)
```

## Status-Abfrage

```python
clone_service = GitCloneService()

# Prüfen ob Repository geklont ist
is_cloned = clone_service.is_cloned(repo.local_path)

# Detaillierte Status-Info
status = clone_service.get_clone_status(repo.local_path)
# Returns: {
#   'exists': True,
#   'path': '/data/repos/...',
#   'file_count': 77,
#   'size_mb': 0.14,
#   'size_bytes': 142336
# }
```

## Fehlerbehandlung

### Repository nicht in Testdaten gefunden

```
FileNotFoundError: Repository 'xyz' not found in testdata.
Expected at: /home/marc/git/archinspect/testdata/repos/xyz
```

**Lösung**: Repository-Quellcode in `testdata/repos/` bereitstellen.

### Zielverzeichnis nicht beschreibbar

```
PermissionError: [Errno 13] Permission denied: '/data/repos'
```

**Lösung**: Verzeichnis erstellen und Rechte setzen:
```bash
sudo mkdir -p /data/repos
sudo chown $USER:$USER /data/repos
```

### Namespace-Pfad fehlt

Wenn `namespace_path` leer ist, wird Repository direkt unter `/data/repos/{repo_name}/` abgelegt.

## Logging

Alle Clone-Operationen werden geloggt:

```json
{
  "message": "Cloning repository 'ArvenDatenKurier' from ... to ...",
  "source": "/home/marc/git/archinspect/testdata/repos/arvendatenkurier",
  "target": "/data/repos/art-operations/krake/ArvenDatenKurier",
  "url": "https://gitlab.ruv.de/art-operations/krake/arvendatenkurier"
}
```

## Austausch gegen echten Git-Clone

Für Produktion kann `GitCloneService` durch echten Git-Clone ersetzt werden:

```python
class ProductionGitCloneService:
    def clone_repository(self, repo_name, namespace_path, target_root, source_url):
        import subprocess

        target_path = Path(target_root) / namespace_path / repo_name
        target_path.parent.mkdir(parents=True, exist_ok=True)

        # Echter Git-Clone
        subprocess.run([
            'git', 'clone', source_url, str(target_path)
        ], check=True)

        return target_path
```

Die View-Logik bleibt unverändert - vollständig transparent!

## Vorteile

✅ **Transparent**: System merkt nicht, dass GitLab gemockt ist
✅ **Strukturiert**: Repositories nach Namespace organisiert
✅ **Effizient**: Kopiert nur bei Bedarf
✅ **Status-Tracking**: `local_path` zeigt Clone-Status
✅ **Austauschbar**: Mock leicht gegen echten Git-Clone ersetzbar
✅ **Testbar**: Vollständig mit Testdaten testbar

## Testdaten

Aktuell verfügbare Test-Repositories in `testdata/repos/`:
- arvendatenkurier (77 Dateien, 0.14 MB)
- bka-bff
- zahlungen-service
- dokumente-service
- flowhub-azure-iac
- yepwebsvc
- agentcommunicationsvc
- abocomplete-bff
- contactmanagementsvc
- bpm-Dialogeinwilligung-v1

Diese wurden bereits aus HTML-Dateien extrahiert via `extract_repos.py`.
