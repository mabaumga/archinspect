# Git Workflow

Git-Workflow und Konventionen für saubere Versionshistorie.

Diese Konventionen sind framework-agnostisch und gelten für alle Projekte.

## 🌿 Branching Strategy

### Trunk-Based Development

Wir nutzen eine vereinfachte Trunk-Based Development Strategie:

```
main (production-ready)
  ├── feature/reisekosten-use-cases
  ├── fix/calculation-error
  └── refactor/hexagonal-architecture
```

**Prinzipien**:
- `main` ist **immer deploybar**
- Feature Branches sind **kurzlebig** (max. 1-3 Tage)
- **Kleine, häufige Commits** statt große Änderungen
- **Daily Integration** in main

### Branch-Typen

| Präfix | Verwendung | Beispiel |
|--------|------------|----------|
| `feature/` | Neue Features | `feature/fahrt-export` |
| `fix/` | Bugfixes | `fix/kosten-berechnung` |
| `refactor/` | Refactorings | `refactor/repository-pattern` |
| `docs/` | Nur Dokumentation | `docs/update-readme` |
| `test/` | Nur Tests | `test/add-use-case-tests` |

### Branch-Namen

**Format**: `typ/kurze-beschreibung`

```bash
# ✅ RICHTIG
git checkout -b feature/fahrt-statistik
git checkout -b fix/negative-km-validation
git checkout -b refactor/extract-route-service

# ❌ FALSCH
git checkout -b new-feature           # Kein Typ
git checkout -b feature-123           # Nicht aussagekräftig
git checkout -b fix_bug               # Underscore statt Dash
```

## 📝 Commit Messages

### Format (Conventional Commits)

```
<typ>: <kurze Beschreibung>

[Optionaler Body mit Details]

[Optional: Referenzen]
```

**Typen**:
- `feat`: Neues Feature
- `fix`: Bugfix
- `refactor`: Code-Refactoring (keine funktionale Änderung)
- `test`: Tests hinzugefügt/geändert
- `docs`: Dokumentation
- `chore`: Build, Dependencies, Tools
- `perf`: Performance-Verbesserung
- `style`: Code-Formatierung (kein funktionaler Change)

### Beispiele

```bash
# Feature
git commit -m "feat: Add CreateFahrtUseCase for trip creation"

# Bugfix
git commit -m "fix: Correct cost calculation for overnight trips

Previous calculation did not include overnight allowance.
Now adds 12€ per overnight stay.

Fixes calculation error in FahrtService.berechne_kosten()"

# Refactoring
git commit -m "refactor: Extract RouteService from FahrtService

Separated route lookup logic into dedicated service following
hexagonal architecture principles."

# Tests
git commit -m "test: Add integration tests for DjangoFahrtRepository"

# Dokumentation
git commit -m "docs: Update bounded-context-canvas for Reisekosten"
```

### Commit-Regeln

1. **Erste Zeile**: Max. 72 Zeichen, imperativ ("Add", nicht "Added")
2. **Body** (optional): Erklärt "Warum", nicht "Was"
3. **Sprache**: Englisch für Messages, Deutsch für Domain-Begriffe
4. **Atomic**: Ein Commit = Eine logische Änderung

```bash
# ✅ RICHTIG
git commit -m "feat: Add Fahrt entity with validation"

# ❌ FALSCH
git commit -m "changes"  # Nicht aussagekräftig
git commit -m "Added new feature and fixed bug and updated docs"  # Zu viel in einem Commit
git commit -m "WIP"  # Work in Progress sollte nicht committed werden
```

## 🔄 Workflow

### 1. Neues Feature starten

```bash
# Main aktualisieren
git checkout main
git pull origin main

# Feature Branch erstellen
git checkout -b feature/fahrt-export

# Entwickeln...
# (Kleine, häufige Commits)

git add .
git commit -m "feat: Add CSV export for Fahrt entities"
```

### 2. Während der Entwicklung

```bash
# Regelmäßig main mergen (bei länger laufenden Branches)
git checkout main
git pull origin main
git checkout feature/fahrt-export
git merge main

# Oder: Rebase (für saubere History)
git checkout feature/fahrt-export
git rebase main
```

### 3. Vor dem Merge

**Checkliste** (siehe auch [Definition of Done](../processes/definition-of-done.md)):

```bash
# 1. Tests laufen
pytest

# 2. Code formatiert
black . --line-length 100

# 3. Linting
pylint bounded_context/

# 4. Coverage prüfen
pytest --cov=bounded_context --cov-report=term

# 5. Main mergen
git checkout main
git pull
git checkout feature/fahrt-export
git merge main

# 6. Nochmal Tests
pytest
```

### 4. Merge in Main

```bash
# Nach main wechseln
git checkout main

# Feature mergen (fast-forward wenn möglich)
git merge feature/fahrt-export

# Pushen
git push origin main

# Branch löschen (lokal)
git branch -d feature/fahrt-export

# Branch löschen (remote, falls gepusht)
git push origin --delete feature/fahrt-export
```

## 🚫 Was NICHT committen

### .gitignore

```gitignore
# Python
__pycache__/
*.pyc
*.pyo
*.pyd
.Python
*.so
*.egg
*.egg-info/
dist/
build/
.pytest_cache/
.coverage
htmlcov/

# Virtual Environments
venv/
.venv/
env/
ENV/

# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# Environment Variables
.env
.env.local
*.env

# Secrets
secrets.yaml
credentials.json
*.pem
*.key

# OS
.DS_Store
Thumbs.db

# Databases
*.db
*.sqlite
*.sqlite3

# Logs
*.log
logs/

# Temporary
tmp/
temp/
*.tmp
```

### Vor Commit prüfen

```bash
# Was wird committed?
git status

# Diff anzeigen
git diff

# Staged Diff
git diff --staged

# Einzelne Files adden (statt "git add .")
git add domain/entities.py
git add tests/test_entities.py
```

## 🔀 Merge vs. Rebase

### Merge (Standard)

**Wann**: Für Feature Branches in main

```bash
git checkout main
git merge feature/fahrt-export
```

**Vorteil**: Bewahrt vollständige History

### Rebase (Für saubere History)

**Wann**: Feature Branch auf aktuellen Stand von main bringen

```bash
git checkout feature/fahrt-export
git rebase main
```

**Vorteil**: Lineare History, sauberer

**⚠️ Achtung**: Nie rebase auf gepushten Branches (außer eigener Feature Branch)

### Interactive Rebase (Commits aufräumen)

```bash
# Letzte 3 Commits bearbeiten
git rebase -i HEAD~3

# Im Editor:
pick abc1234 feat: Add Fahrt entity
squash def5678 fix typo  # Wird in vorherigen Commit gemerged
reword ghi9012 test: Add tests  # Commit message ändern
```

## 📋 Pull Request / Merge Request

### PR Beschreibung Template

```markdown
## Beschreibung

Kurze Beschreibung der Änderung.

## Änderungen

- Hinzugefügt: CreateFahrtUseCase
- Geändert: FahrtService nutzt jetzt Repository Pattern
- Entfernt: Direkter Model-Zugriff in Views

## Testing

- [ ] Unit Tests geschrieben
- [ ] Integration Tests geschrieben
- [ ] Alle Tests grün
- [ ] Coverage ≥ 80%

## Checkliste

- [ ] Code formatiert (Black)
- [ ] Linting ohne Fehler
- [ ] Dokumentation aktualisiert
- [ ] Enhancement-Datei erstellt

## Screenshots (falls UI-Änderungen)

...
```

## 🔍 Nützliche Git Befehle

### History ansehen

```bash
# Log mit Graph
git log --oneline --graph --decorate --all

# Kompakt
git log --oneline -10

# Mit Dateien
git log --stat

# Suchen in Commits
git log --grep="Fahrt"

# Änderungen an Datei
git log -p domain/entities.py
```

### Änderungen rückgängig machen

```bash
# Unstage (aus Staging Area entfernen)
git reset HEAD file.py

# Änderungen an Datei verwerfen
git checkout -- file.py

# Letzten Commit rückgängig (Änderungen behalten)
git reset --soft HEAD~1

# Letzten Commit rückgängig (Änderungen verwerfen)
git reset --hard HEAD~1

# Commit rückgängig (neuer Commit)
git revert abc1234
```

### Stashing (Änderungen temporär speichern)

```bash
# Änderungen speichern
git stash

# Mit Beschreibung
git stash save "WIP: Refactoring FahrtService"

# Liste anzeigen
git stash list

# Wiederherstellen
git stash pop

# Bestimmten Stash wiederherstellen
git stash apply stash@{1}
```

### Branches aufräumen

```bash
# Lokale Branches anzeigen
git branch

# Remote Branches anzeigen
git branch -r

# Gemergte Branches löschen
git branch --merged main | grep -v "main" | xargs git branch -d

# Remote Branches aufräumen
git fetch --prune
```

## 🏷️ Tags

### Releases taggen

```bash
# Annotated Tag (empfohlen)
git tag -a v1.0.0 -m "Release 1.0.0: Reisekosten Modul"

# Tag pushen
git push origin v1.0.0

# Alle Tags pushen
git push origin --tags

# Tags auflisten
git tag -l

# Tag löschen (lokal)
git tag -d v1.0.0

# Tag löschen (remote)
git push origin --delete v1.0.0
```

### Semantic Versioning

Format: `vMAJOR.MINOR.PATCH`

- **MAJOR**: Breaking Changes
- **MINOR**: Neue Features (backwards compatible)
- **PATCH**: Bugfixes

Beispiel:
- `v1.0.0` - Initial Release
- `v1.1.0` - Neues Feature (FahrtExport)
- `v1.1.1` - Bugfix (Kostenberechnung)
- `v2.0.0` - Breaking Change (API-Änderung)

## 📚 Weiterführende Dokumente

- [Definition of Done](../processes/definition-of-done.md) - Merge-Checkliste
- [Coding Standards](coding-standards.md) - Code-Qualität
- [Deployment Guide](../processes/deployment-guide.md) - Release-Prozess

---

**Zuletzt aktualisiert:** 2025-11-03
