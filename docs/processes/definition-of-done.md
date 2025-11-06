# Definition of Done

Quality Gate vor Commit - stellt sicher, dass Task vollständig und in Production-Qualität ist.

## 🎯 Zweck

**Definition of Done (DoD)** stellt sicher, dass:
- Code **produktionsreif** ist
- Alle **Tests grün** sind
- **Dokumentation** aktuell ist
- **Review** durchgeführt wurde
- **Keine technischen Schulden** hinterlassen werden

**Regel**: Nur Code der DoD erfüllt darf in `main` gemerged werden.

## ✅ Checkliste

### 1. Funktionalität

- [ ] **Feature funktioniert** wie spezifiziert
- [ ] **Akzeptanzkriterien** erfüllt
- [ ] **Edge Cases** behandelt
- [ ] **Error Handling** implementiert
- [ ] **Happy Path** und **Fehlerfall** getestet

### 2. Tests

- [ ] **Domain Tests** geschrieben (für Business Logic)
  - Entities, Value Objects, Domain Services
  - Sehr schnell (< 1ms pro Test)
  - Keine I/O, keine DB

- [ ] **Service Tests** geschrieben (mit Fakes/In-Memory)
  - Domain Services mit In-Memory Repository
  - Use Cases mit Test-Dependencies

- [ ] **Adapter Tests** geschrieben (mit Mocks)
  - Repository Mapping-Tests
  - Provider Tests
  - Integration mit Framework (Django, etc.)

- [ ] **Integration Tests** geschrieben (wo nötig)
  - Kritische Workflows
  - DB-Integration
  - API-Integration

- [ ] **Alle Tests grün**
  ```bash
  pytest
  # Alle Tests müssen durchlaufen
  ```

- [ ] **Coverage ≥ 80%** für geänderte Module
  ```bash
  pytest --cov=bounded_context --cov-report=term
  ```

- [ ] **BDD Tests grün** (falls Domain-Feature)
  ```bash
  pytest --tags=bdd
  ```

### 3. Code-Qualität

- [ ] **Code formatiert** (Black)
  ```bash
  black . --line-length 100
  ```

- [ ] **Linting ohne Fehler**
  ```bash
  pylint bounded_context/
  ```

- [ ] **Type Hints** vollständig
  ```bash
  mypy bounded_context/ --strict
  ```

- [ ] **Dependency Rules** eingehalten
  ```bash
  lint-imports
  # Domain darf KEINE Framework-Imports haben!
  ```

- [ ] **Keine Code-Duplizierung**
  - DRY-Prinzip befolgt
  - Gemeinsamer Code extrahiert

- [ ] **SOLID-Prinzipien** befolgt
  - Single Responsibility
  - Open/Closed
  - Liskov Substitution
  - Interface Segregation
  - Dependency Inversion

- [ ] **Naming** ist aussagekräftig
  - Variablen: `fahrt_service` nicht `fs`
  - Funktionen: `berechne_kosten()` nicht `calc()`
  - Klassen: `FahrtService` nicht `FS`

### 4. Architektur

- [ ] **Layer-Trennung** eingehalten
  - Domain kennt KEINE Infrastructure
  - Domain kennt KEINE UI
  - Application kennt nur Domain
  - Infrastructure implementiert Ports

- [ ] **Ports & Adapters** korrekt verwendet
  - Ports (Interfaces) im Domain Layer
  - Adapters (Implementierungen) im Infrastructure Layer

- [ ] **Dependency Injection** verwendet
  - Services über Container injiziert
  - Keine `new` in Business Logic

- [ ] **Decimal für Geld** (niemals Float!)
  - Alle Geldbeträge als `Decimal`
  - Keine Float-Arithmetik

### 5. Security

- [ ] **Input Validierung** implementiert
  - Alle User-Inputs validiert
  - Type Checking
  - Range Checking
  - Business Rules geprüft

- [ ] **Keine SQL-Injection** möglich
  - Parametrisierte Queries (ORM)
  - Kein String-Concat für SQL

- [ ] **Keine Command-Injection** möglich
  - subprocess mit Liste (nicht shell=True)
  - Input validiert

- [ ] **Secrets nicht hardcoded**
  - Keine Passwords im Code
  - Keine API-Keys im Code
  - Environment Variables nutzen

- [ ] **Secrets nicht geloggt**
  - Keine Passwords in Logs
  - Keine Tokens in Logs

### 6. Performance

- [ ] **Keine N+1 Queries**
  - Eager Loading / Batch Queries
  - Query-Count geprüft

- [ ] **Caching** wo sinnvoll
  - Teure Operationen gecacht
  - Cache-Invalidierung implementiert

- [ ] **Performance akzeptabel**
  - Domain Logic < 1ms
  - API Endpoints < 500ms

### 7. Logging & Monitoring

- [ ] **Logging implementiert**
  - Info-Logs für wichtige Aktionen
  - Error-Logs für Exceptions
  - Mit Context (z.B. `fahrt.key`)

- [ ] **Exception Handling** implementiert
  - Try-Catch an richtigen Stellen
  - Exceptions werden geloggt
  - User-freundliche Error Messages

- [ ] **Monitoring-Ready**
  - Metriken können erfasst werden
  - Health Check funktioniert

### 8. Dokumentation

- [ ] **Code-Dokumentation**
  - Docstrings für Public Functions
  - Komplexe Logik kommentiert
  - Type Hints vorhanden

- [ ] **Enhancement-Datei** erstellt
  - `docs/enhancements/YYYY-MM-DD_HH-MM_beschreibung.md`
  - Beschreibung der Änderung
  - Durchgeführte Tasks
  - Lessons Learned

- [ ] **ADR** geschrieben (bei Architektur-Entscheidungen)
  - In `docs/architecture/adr/`
  - Context, Decision, Consequences

- [ ] **Bounded Context Canvas** aktualisiert (bei Domain-Änderungen)
  - In `bounded-context/docs/`
  - Neue Entities, Services dokumentiert

- [ ] **README** aktualisiert (bei neuen Features)
  - Hauptdokumente aktuell
  - Links funktionieren

- [ ] **API-Dokumentation** aktualisiert (bei API-Änderungen)
  - Endpoints dokumentiert
  - Request/Response Beispiele

### 9. Database

- [ ] **Migrations** erstellt und getestet
  ```bash
  python manage.py makemigrations
  python manage.py migrate
  ```

- [ ] **Migrations reversibel** (wo möglich)
  - Rollback-Migration existiert

- [ ] **Migration Performance** geprüft
  - Bei großen Tabellen: Performance-Test
  - Downtime geplant (falls nötig)

- [ ] **Backup vor Migration** (Production)
  - Automatisches Backup im Deployment

### 10. Environment & Configuration

- [ ] **Environment Variables** dokumentiert
  - Neue ENV Vars in `.env.example`
  - In Deployment-Doku erwähnt

- [ ] **.gitignore** aktualisiert
  - Keine Secrets committed
  - Keine `__pycache__/`
  - Keine `.env`

- [ ] **Dependencies** aktualisiert
  - `requirements.txt` aktuell
  - Keine veralteten Packages

### 11. Deployment-Readiness

- [ ] **Makefile-Target** vorhanden (falls nötig)
  - Neue Commands dokumentiert

- [ ] **Deployment funktioniert**
  - Lokal getestet
  - Docker-Build erfolgreich (falls Docker)

- [ ] **Rollback-Plan** vorhanden
  - Wie kann man zurückrollen?
  - Migrations reversibel?

### 12. Code Review

- [ ] **Self-Review** durchgeführt
  - Eigenen Code nochmal durchgegangen
  - Offensichtliche Fehler behoben

- [ ] **Peer Review** durchgeführt (falls Team)
  - Mindestens 1 Approval
  - Kommentare addressiert

- [ ] **Architectural Review** (bei größeren Changes)
  - Layer-Trennung geprüft
  - DDD-Prinzipien eingehalten

## 🎓 DoD-Levels

### Level 1: Minimal (Bugfixes, kleine Änderungen)

- Funktionalität ✅
- Tests ✅
- Code-Qualität (formatiert, linting) ✅
- Logging ✅

### Level 2: Standard (Features, Refactorings)

- Level 1 ✅
- Architektur ✅
- Security ✅
- Performance ✅
- Dokumentation (Enhancement-Datei) ✅
- Deployment-Readiness ✅

### Level 3: Comprehensive (große Features, Breaking Changes)

- Level 2 ✅
- BDD Tests ✅
- Integration Tests ✅
- ADR (bei Architektur-Entscheidungen) ✅
- Performance-Tests ✅
- Security-Review ✅
- Umfangreichere Dokumentation ✅

## 🚫 Nicht Done - Was tun?

**Wenn DoD nicht erfüllt**:

1. **Task auf "In Progress" lassen** - Nicht mergen!
2. **Fehlende Items** identifizieren
3. **Items nacharbeiten**
4. **Erneut DoD prüfen**

**Beispiel**:
```
Task: CSV-Export implementieren

DoD-Status: ❌ NOT DONE

Fehlende Items:
- [ ] Integration Tests fehlen
- [ ] Enhancement-Datei nicht erstellt
- [ ] Dependency-Check failed (Domain imports Django!)

Aktion:
→ Integration Tests schreiben
→ Django-Import aus Domain entfernen
→ Enhancement-Datei erstellen
→ Erneut DoD prüfen
```

## 🔧 Tools zur DoD-Prüfung

### Automatische Checks

```bash
#!/bin/bash
# scripts/check-dod.sh
# Automatische DoD-Checks

set -e

echo "🔍 Checking Definition of Done..."

# 1. Tests
echo "Running tests..."
pytest || { echo "❌ Tests failed"; exit 1; }

# 2. Coverage
echo "Checking coverage..."
pytest --cov=bounded_context --cov-report=term --cov-fail-under=80 || { echo "❌ Coverage < 80%"; exit 1; }

# 3. Formatting
echo "Checking code formatting..."
black . --check --line-length 100 || { echo "❌ Code not formatted"; exit 1; }

# 4. Linting
echo "Running linter..."
pylint bounded_context/ || { echo "❌ Linting failed"; exit 1; }

# 5. Type Checking
echo "Checking types..."
mypy bounded_context/ --strict || { echo "❌ Type errors"; exit 1; }

# 6. Dependency Check
echo "Checking dependencies..."
lint-imports || { echo "❌ Dependency rules violated"; exit 1; }

echo "✅ All automatic DoD checks passed!"
```

**In Git Pre-Commit Hook**:

```bash
# .git/hooks/pre-commit
#!/bin/bash
./scripts/check-dod.sh
```

### CI/CD Pipeline

```yaml
# .github/workflows/dod-check.yml
name: DoD Check

on: [push, pull_request]

jobs:
  dod-check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Install dependencies
        run: pip install -r requirements.txt
      - name: Run DoD Checks
        run: ./scripts/check-dod.sh
```

## 📋 DoD-Checkliste Template

```markdown
## Definition of Done Checklist

Task: [Task-Name]

### Funktionalität
- [ ] Feature funktioniert
- [ ] Akzeptanzkriterien erfüllt
- [ ] Edge Cases behandelt

### Tests
- [ ] Domain Tests geschrieben
- [ ] Service/Use Case Tests geschrieben
- [ ] Adapter Tests geschrieben (falls nötig)
- [ ] Alle Tests grün
- [ ] Coverage ≥ 80%

### Code-Qualität
- [ ] Code formatiert (black)
- [ ] Linting ohne Fehler (pylint)
- [ ] Type Hints (mypy)
- [ ] Dependency Rules (lint-imports)
- [ ] Naming aussagekräftig

### Architektur
- [ ] Layer-Trennung eingehalten
- [ ] Ports & Adapters korrekt
- [ ] Dependency Injection
- [ ] Decimal für Geld

### Security
- [ ] Input Validierung
- [ ] Keine SQL-Injection
- [ ] Secrets nicht hardcoded/geloggt

### Performance
- [ ] Keine N+1 Queries
- [ ] Caching implementiert (wo nötig)

### Logging
- [ ] Logging implementiert
- [ ] Exception Handling

### Dokumentation
- [ ] Code-Dokumentation (Docstrings)
- [ ] Enhancement-Datei erstellt
- [ ] ADR (bei Architektur-Entscheidung)
- [ ] README/API-Doku aktualisiert

### Deployment
- [ ] Migrations getestet
- [ ] ENV Vars dokumentiert
- [ ] Dependencies aktualisiert

### Review
- [ ] Self-Review
- [ ] Peer Review (falls Team)

**Status**: ✅ DONE | ❌ NOT DONE
```

## 📚 Weiterführende Dokumente

- [Definition of Ready](definition-of-ready.md) - Vor Task-Start
- [Coding Standards](../development/coding-standards.md) - Code-Qualität
- [Testing Strategy](../development/testing-strategy.md) - Test-Pyramide
- [Security Guidelines](../development/security-guidelines.md) - Security Checks
- [Git Workflow](../development/git-workflow.md) - Commit-Prozess

---

**Zuletzt aktualisiert:** 2025-11-03
