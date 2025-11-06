# ArchInspect - KI Projekt-Kontext

> **WICHTIG**: Diese Datei ist die zentrale Referenz für KI-Assistenten.
> Bei Änderungen an Coding Standards oder Architektur MUSS diese Datei aktualisiert werden!
>
> **Dokumentations-Aufteilung**:
> - `.claude/project-context.md` (diese Datei) → Kompakte KI-Referenz
> - `docs/**/*.md` → Ausführliche Dokumentation für Menschen

## Architektur

### Hexagonal Architecture (Ports & Adapters)

### Standard-Struktur
```
├── domain/          # Pure Business Logic (keine Framework-Dependencies!)
├── application/     # Use Cases + DTOs
├── adapters/        # Persistence, API, CSV, etc.
│   └── persistence/django/  # ORM Models HIER (nicht im Root!)
├── infrastructure/  # DI Container
├── ui/             # Views, Forms (auf Hauptebene, NICHT unter adapters!)
│   ├── views.py
│   ├── forms.py
│   └── urls.py     # Detail-URLs
├── tests/          # Unit, Integration, BDD
│   ├── fixtures/   # Testdaten
│   └── bdd/        # Gherkin Features
├── templates/      # Django Templates
├── urls.py         # Weiterleitung zu ui/urls.py
└── apps.py         # Django App Config
```

**Kritische Regeln**:
- `ui/` liegt im **Root** des Contexts (NICHT in `adapters/ui/`)
- `models.py` liegt in `adapters/persistence/django/` (ORM = Persistence Detail)
- Domain-Layer hat **KEINE** Framework-Dependencies
- Container in `infrastructure/container.py` (Singleton Pattern)

## Coding Standards

### Repository Pattern
- **Naming**: `Django*Repository` (z.B. `DjangoLiegenschaftRepository`)
- **NICHT**: `*RepositoryDjango` oder `*DjangoRepository`
- **Port** (Interface) in `domain/ports/`
- **Adapter** in `adapters/persistence/django/`

### Import-Konventionen
- `adapters` (Plural!) - NICHT `adapter`
- Container-Imports: `from {context}.infrastructure.container import {context}_container`
- NICHT: `from {context}.domain.{context}_container` (Container gehören in infrastructure!)

### Tools
- **Type Checker**: pyright (Config: `pyrightconfig.json`)
  - Nur kritische Fehler: undefined/unbound variables
  - Ziel: 0 Errors, 0 Warnings
- **Linter**: ruff (Config: `ruff.toml`)
- **Formatter**: ruff format
- **Import Checker**: flake8 (Config: `.flake8`)
  - Respektiert `# noqa: F401` für intentionale Imports

### Finanzbeträge
- **IMMER** `Decimal` verwenden, **NIEMALS** `float`
- Beispiel: `Decimal('100.50')` statt `100.5`

## Quality Checks: `make check-all`

**Vor jedem Commit MUSS `make check-all` bestehen!**

Führt 6 Checks durch:
1. **Repository-Naming** - Django*Repository Pattern
2. **Import-Checks** - flake8 (F-Kategorie)
3. **Django-Startup** - Lädt 14 kritische Module mit Django-Kontext
4. **Linting** - ruff
5. **Formatierung** - ruff format
6. **Type-Checking** - pyright

### Wichtige Befehle
- `make check-all` - Alle Checks (erforderlich vor Commit)
- `make lint-fix` - Auto-Fix Linting + Formatierung
- `make check-django-startup` - Testet Django-Startup
- `make type-check` - Nur Type-Checking

### Django-Startup-Check (WICHTIG!)
- **Script**: `scripts/check_django_startup.py`
- **Findet**: Fehler die flake8 nicht erkennt (z.B. falsche Container-Imports)
- **Testet**: 7 Views + 7 URLs Module mit echtem Django-Kontext

### Bei Makefile-Verlust
Check-Logik in:
- `scripts/check_django_startup.py`
- `pyrightconfig.json`
- `ruff.toml`
- `.flake8`

## Wichtige Dateien

### Konfiguration
- `pyrightconfig.json` - Type Checker (0 errors, 0 warnings)
- `ruff.toml` - Linter & Formatter
- `.flake8` - Import Checker
- `.dev/config/log_config.json` - Logging (KEIN JSON-Formatter!)

## App-Initialisierung

### Verzögerte Background-Threads
Django-Apps starten Background-Threads **verzögert**, um DB-Zugriffe während App-Init zu vermeiden:

**Grund**: Vermeidung der RuntimeWarning "Accessing the database during app initialization"

## Meta-Regel: Dokumentations-Synchronisation

**Bei Änderungen an Coding Standards oder Architektur**:
1. Aktualisiere `docs/development/coding-standards.md` (für Menschen)
2. Aktualisiere `.claude/project-context.md` (diese Datei, für KI)
3. Prüfe ob weitere Docs betroffen sind (architecture/, processes/)
