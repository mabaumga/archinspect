# Repository Clone & Update Feature

## Überblick

Jedes Repository kann jetzt **erstmalig geklont** oder **aktualisiert** werden. Das System erkennt automatisch, ob ein Repository bereits lokal vorhanden ist und bietet die passende Aktion an.

## Funktionalität

### Automatische Erkennung

Das System unterscheidet automatisch zwischen:
- **Erstmaliges Klonen**: Repository existiert noch nicht lokal (`local_path` ist leer)
- **Aktualisieren**: Repository wurde bereits geklont (`local_path` ist gesetzt)

### UI-Integration

#### Repository-Detailseite

**Button-Zustand:**
- Noch nicht geklont: **"Klonen"** Button (blau, Download-Icon)
- Bereits geklont: **"Aktualisieren"** Button (grau, Refresh-Icon)

Der Button zeigt im Tooltip den aktuellen lokalen Pfad an (wenn geklont).

#### Repository-Liste

**Neue Spalte: "Clone-Status"**
- ✓ **Geklont** (grünes Badge) - Repository ist lokal vorhanden
- ✗ **Nicht geklont** (graues Badge) - Repository noch nicht geklont

**Aktionen:**
- Download-Icon (blau) - Erstmaliges Klonen
- Refresh-Icon (grau) - Aktualisieren eines vorhandenen Repositories
- Auge-Icon - Zur Detailansicht

## Implementierung

### GitCloneService

**Neue Methode:** `update_or_clone_repository()`

```python
def update_or_clone_repository(
    self,
    repo_name: str,
    namespace_path: str,
    target_root: str,
    source_url: Optional[str] = None,
    local_path: Optional[str] = None
) -> tuple[Path, bool]:
    """
    Update repository if it exists, otherwise clone it.

    Returns:
        Tuple of (Path to repository, was_updated: bool)
        was_updated is True if repository was updated, False if newly cloned
    """
```

**Funktionsweise:**
1. Prüft, ob `local_path` existiert und valide ist
2. Loggt entsprechend "Updating" oder "Cloning"
3. Führt Clone-Operation aus (überschreibt bei Update)
4. Gibt Pfad und Update-Status zurück

### View-Änderungen

**`repository_clone` View:**
- Nutzt jetzt `update_or_clone_repository()` statt `clone_repository()`
- Unterscheidet in der Success-Message zwischen "geklont" und "aktualisiert"
- Loggt `was_updated` Flag für Auswertungen

```python
cloned_path, was_updated = clone_service.update_or_clone_repository(
    repo_name=repository.name,
    namespace_path=repository.namespace_path,
    target_root=target_root,
    source_url=repository.url,
    local_path=repository.local_path  # Wichtig: übergebe existierenden Pfad
)

action = "aktualisiert" if was_updated else "geklont"
messages.success(request, f"Repository '{repository.name}' erfolgreich {action}...")
```

### Template-Änderungen

**`repositories/detail.html`:**

```django
<a href="{% url 'repository-clone' repository.pk %}"
   class="btn btn-{% if repository.local_path %}secondary{% else %}primary{% endif %}"
   title="{% if repository.local_path %}Repository aktualisieren ({{ repository.local_path }}){% else %}Repository von GitLab klonen{% endif %}">
    <i class="bi bi-{% if repository.local_path %}arrow-repeat{% else %}cloud-download{% endif %}"></i>
    {% if repository.local_path %}Aktualisieren{% else %}Klonen{% endif %}
</a>
```

**`repositories/list.html`:**

Neue Spalte mit Clone-Status:
```django
<td>
    {% if repo.local_path %}
        <span class="badge bg-success" title="Geklont nach {{ repo.local_path }}">
            <i class="bi bi-check-circle"></i> Geklont
        </span>
    {% else %}
        <span class="badge bg-secondary">
            <i class="bi bi-x-circle"></i> Nicht geklont
        </span>
    {% endif %}
</td>
```

Aktions-Buttons:
```django
<div class="btn-group btn-group-sm">
    <a href="{% url 'repository-clone' repo.pk %}"
       class="btn btn-{% if repo.local_path %}outline-secondary{% else %}outline-primary{% endif %}"
       title="{% if repo.local_path %}Aktualisieren{% else %}Klonen{% endif %}">
        <i class="bi bi-{% if repo.local_path %}arrow-repeat{% else %}cloud-download{% endif %}"></i>
    </a>
    <a href="{% url 'repository-detail' repo.pk %}" class="btn btn-outline-primary">
        <i class="bi bi-eye"></i>
    </a>
</div>
```

## Verwendung

### Via Web-UI

1. **Repository-Liste öffnen** (http://localhost:8000/repositories/)
2. Clone-Status in der Übersicht sehen
3. Auf Download-Icon (erstmaliges Klonen) oder Refresh-Icon (Aktualisieren) klicken
4. Erfolgsmeldung bestätigt die Aktion mit Dateianzahl und Größe

### Via Python

```python
from adapters.git_platform.clone_service import GitCloneService
from adapters.persistence.models import Repository

repo = Repository.objects.get(pk=1)
clone_service = GitCloneService()

# Klonen oder Aktualisieren
cloned_path, was_updated = clone_service.update_or_clone_repository(
    repo_name=repo.name,
    namespace_path=repo.namespace_path,
    target_root='/data/repos',
    source_url=repo.url,
    local_path=repo.local_path
)

repo.local_path = str(cloned_path)
repo.save()

print(f"Repository {'aktualisiert' if was_updated else 'geklont'}")
```

## Testing

```bash
cd /home/marc/git/archinspect/repo_analyst
.venv/bin/python -c "
from src.adapters.git_platform.clone_service import GitCloneService

service = GitCloneService()

# Test: Erstmaliges Klonen
path, was_updated = service.update_or_clone_repository(
    repo_name='ArvenDatenKurier',
    namespace_path='art-operations/krake',
    target_root='/tmp/test-repos',
    local_path=None
)
print(f'Neu geklont: {path}, Update: {was_updated}')  # Update: False

# Test: Aktualisieren
path, was_updated = service.update_or_clone_repository(
    repo_name='ArvenDatenKurier',
    namespace_path='art-operations/krake',
    target_root='/tmp/test-repos',
    local_path=str(path)
)
print(f'Aktualisiert: {path}, Update: {was_updated}')  # Update: True
"
```

## Vorteile

✅ **Benutzerfreundlich**: Klare visuelle Unterscheidung zwischen Clone und Update
✅ **Automatisch**: System erkennt selbst, welche Aktion nötig ist
✅ **Übersichtlich**: Clone-Status direkt in der Repository-Liste sichtbar
✅ **Transparent**: Mock-Implementierung bereitet echten Git-Clone vor
✅ **Skalierbar**: Beide Aktionen nutzen dieselbe View-Logik

## Mock vs. Produktion

### Aktuelles Verhalten (Mock)

- **Klonen**: Kopiert von `testdata/repos/` nach `/data/repos/{namespace}/{name}/`
- **Aktualisieren**: Löscht Zielverzeichnis und kopiert neu (simuliert `git clone`)

### Zukünftiges Verhalten (Produktion)

```python
class ProductionGitCloneService:
    def update_or_clone_repository(self, ...):
        if self.is_cloned(local_path):
            # Echtes Update via Git Pull
            subprocess.run(['git', '-C', local_path, 'pull'], check=True)
            return Path(local_path), True
        else:
            # Echtes Klonen via Git Clone
            subprocess.run(['git', 'clone', source_url, target_path], check=True)
            return target_path, False
```

## Änderungsübersicht

### Geänderte Dateien

1. **[src/adapters/git_platform/clone_service.py](src/adapters/git_platform/clone_service.py:137-180)**
   - Neue Methode `update_or_clone_repository()`
   - Gibt Tuple zurück: `(Path, was_updated: bool)`

2. **[src/adapters/web/views.py](src/adapters/web/views.py:143-169)**
   - Nutzt `update_or_clone_repository()` statt `clone_repository()`
   - Unterscheidet in Nachrichten zwischen "geklont" und "aktualisiert"

3. **[src/ui/templates/repositories/detail.html](src/ui/templates/repositories/detail.html:17-27)**
   - Button wechselt zwischen "Klonen" (blau) und "Aktualisieren" (grau)
   - Icons: Download vs. Refresh

4. **[src/ui/templates/repositories/list.html](src/ui/templates/repositories/list.html:58-125)**
   - Neue Spalte "Clone-Status" mit Badges
   - Aktions-Buttons mit Icon-Wechsel

5. **[CLONE_FEATURE.md](CLONE_FEATURE.md:38-105)**
   - Dokumentation aktualisiert mit Update-Funktionalität

## Zusammenfassung

Die Erweiterung ermöglicht es Benutzern, Repositories nicht nur erstmalig zu klonen, sondern auch zu aktualisieren. Das System erkennt automatisch den Status und bietet die passende Aktion an - sowohl in der Detailansicht als auch in der Repository-Liste. Die UI-Integration ist konsistent und intuitiv mit unterschiedlichen Icons und Farben für Clone vs. Update.

**Status**: ✅ Implementiert und getestet
**Getestet**: 2025-11-04
**Kompatibilität**: Django 5.0, Bootstrap 5, Bootstrap Icons
