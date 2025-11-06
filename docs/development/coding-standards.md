# Coding Standards

Standards und Konventionen für Code-Qualität nach Hexagonaler Architektur und DDD.

Diese Standards sind framework-agnostisch und gelten für alle Projekte nach diesem Architektur-Ansatz.

## 🎯 Grundprinzipien

1. **Clean Code** - Lesbarer, wartbarer Code
2. **SOLID Prinzipien** - Insbesondere Single Responsibility und Dependency Inversion
3. **DDD-Konventionen** - Ubiquitous Language im Code
4. **Hexagonale Architektur** - Klare Layer-Trennung
5. **Framework-Unabhängigkeit** - Domain kennt keine Frameworks

## 📂 Projektstruktur

### Bounded Context Layout

```
kvb/bounded-context/
├── domain/              # Domain Layer (keine externen Dependencies)
│   ├── entities/        # Geschäftsobjekte
│   ├── services/        # Domain Services
│   ├── ports/           # Interfaces (Repositories, Provider)
│   └── exceptions.py    # Domain Exceptions
│
├── application/         # Application Layer
│   └── use_cases.py     # Use Cases (Orchestrierung)
│
├── adapters/           # Infrastructure Adapter
│   ├── persistence/    # Repository-Implementierungen
│   └── infrastructure/ # Externe Services (CSV, API, etc.)
│
├── infrastructure/     # DI Container & Helpers
│   ├── container.py    # ServiceContainer
│   └── ui_helpers.py   # UI Framework Helpers
│
├── ui/                # UI Layer (Framework-Adapter)
│   ├── models.py      # ORM Models (Suffix: "Model")
│   ├── views.py       # Views / Controllers
│   ├── routes.py      # URL/Route Config
│   └── templates/     # Templates
│
├── tests/             # Tests
│   ├── test_entities.py
│   ├── test_services.py
│   ├── test_repositories.py
│   └── test_use_cases.py
│
└── docs/              # Context-Dokumentation
    ├── bounded-context-canvas.md
    ├── domain-model.md
    └── api-documentation.md
```

## 🐍 Python Code Style

### Allgemein

- **Python Version**: 3.11+
- **Style Guide**: PEP 8
- **Formatter**: Black (line-length 100)
- **Type Hints**: Pflicht für alle Public Functions
- **Docstrings**: Google Style

### Naming Conventions

```python
# Klassen: PascalCase
class FahrtService:
    pass

class DjangoFahrtRepository:  # Django Models: Suffix "Model"
    pass

# Funktionen/Methoden: snake_case
def create_fahrt(data: FahrtDTO) -> Fahrt:
    pass

def get_fahrten_by_month(year: int, month: int) -> list[Fahrt]:
    pass

# Konstanten: UPPER_SNAKE_CASE
MAX_FAHRTEN_PER_MONTH = 50
DEFAULT_START_ORT = "Hanau"

# Private Attribute: Prefix "_"
class Repository:
    def __init__(self):
        self._cache = {}
```

### Type Hints

```python
from typing import Optional, Protocol
from decimal import Decimal
from datetime import date

# Immer Type Hints verwenden
def calculate_kosten(km: int, satz: Decimal) -> Decimal:
    """
    Berechnet Fahrtkosten

    Args:
        km: Kilometer
        satz: Kilometersatz (z.B. Decimal('0.30'))

    Returns:
        Gesamtkosten

    Raises:
        ValueError: Bei negativen km
    """
    if km < 0:
        raise ValueError("Kilometer dürfen nicht negativ sein")
    return km * satz

# Optional für None-Werte
def find_fahrt(key: str) -> Optional[Fahrt]:
    pass

# Generics für Collections
def get_all_fahrten() -> list[Fahrt]:
    pass

def group_by_person(fahrten: list[Fahrt]) -> dict[str, list[Fahrt]]:
    pass
```

### Docstrings

```python
class FahrtService:
    """
    Domain Service für Fahrten-Verwaltung

    Verwaltet Geschäftslogik rund um Fahrten und Fahrtkostenberechnung.
    Nutzt Repository-Pattern für Persistierung.

    Attributes:
        repository: FahrtRepository für Persistierung
    """

    def __init__(self, repository: FahrtRepository):
        """
        Initialisiert FahrtService

        Args:
            repository: Repository-Implementierung
        """
        self.repository = repository

    def berechne_kosten(self, fahrt: Fahrt, satz: Decimal = Decimal('0.30')) -> Decimal:
        """
        Berechnet Gesamtkosten einer Fahrt

        Formel: (km * satz + pauschale) + verpflegung

        Args:
            fahrt: Fahrt-Entity
            satz: Kilometersatz (default: 0.30 €/km)

        Returns:
            Gesamtkosten inkl. Verpflegung

        Example:
            >>> fahrt = Fahrt(km=100, spesen=12)
            >>> service.berechne_kosten(fahrt)
            Decimal('42.00')
        """
        pass
```

## 🏗️ Architektur-Regeln

### Domain Layer

**Regel**: Domain Layer hat KEINE Dependencies zu Frameworks (Django, Flask, FastAPI, etc.)

```python
# ✅ RICHTIG: Domain kennt keine Infrastructure
from dataclasses import dataclass
from decimal import Decimal
from datetime import date

@dataclass
class Fahrt:
    """Domain Entity - Pure Python, keine Framework-Dependencies"""
    key: str
    von: date
    person: str
    start: str
    ziel: str
    km: int
    spesen: int = 0

# ❌ FALSCH: Domain darf NICHT von Frameworks abhängen
from django.db import models  # NIEMALS im domain/
from sqlalchemy import Column  # NIEMALS im domain/
from flask import request     # NIEMALS im domain/

class Fahrt(models.Model):  # ❌ Domain Entities sind KEINE ORM Models
    pass
```

### Repository Pattern

```python
# Port (Interface) im Domain Layer
from abc import ABC, abstractmethod
from typing import Protocol

class FahrtRepository(Protocol):
    """Repository Port - definiert Interface"""

    def save(self, fahrt: Fahrt) -> Fahrt:
        """Speichert Fahrt"""
        ...

    def find_by_key(self, key: str) -> Optional[Fahrt]:
        """Findet Fahrt nach Key"""
        ...

# Adapter im Infrastructure Layer
class OrmFahrtRepository:
    """Repository Adapter - implementiert Interface für ORM (Django/SQLAlchemy/etc.)"""

    def save(self, fahrt: Fahrt) -> Fahrt:
        # Mapping Domain ↔ ORM Model
        model = self._domain_to_model(fahrt)
        model.save()  # ORM-spezifisch
        return self._model_to_domain(model)
```

### Naming: Domain vs. Persistence Model

**Regel**: Domain nutzt **Ubiquitous Language** (Fachsprache), Persistence Models können abweichende (technische/Legacy-)Namen haben.

```python
# Domain Entity - Ubiquitous Language (Fachsprache)
@dataclass
class Fahrt:
    von: date      # "von" - Fachbegriff
    person: str    # "person" - Fachbegriff
    spesen: int    # "spesen" - Fachbegriff

# Persistence Model - Technische/Legacy Namen
class FahrtkostenModel:  # ORM Model (Django/SQLAlchemy)
    datum: date           # "datum" statt "von" (Legacy DB-Schema)
    fahrer: str           # "fahrer" statt "person" (Legacy)
    verpflegung: Decimal  # "verpflegung" statt "spesen" (Legacy)

    # Metadata (framework-spezifisch)
    __tablename__ = 'fahrtkosten'  # Bestehende DB-Tabelle
```

**Mapping im Repository** übersetzt zwischen Domain-Sprache und Persistence-Schema.

### Entity-Regeln

```python
# ✅ RICHTIG: Eine Entität pro Fachkonzept
class Fahrt:  # In reisekosten/domain/
    pass

class Fahrt:  # ❌ FALSCH: Nicht nochmal in anderem Context
    pass

# ✅ RICHTIG: Wenn andere Kontexte "Fahrt" brauchen → eigene Entity
class Reise:  # In urlaubsplanung/domain/
    """Andere Bedeutung, anderer Context"""
    pass
```

## 💰 Finanzberechnungen

### Niemals Float!

```python
# ❌ FALSCH
kosten = 100.5 * 0.3  # Float-Arithmetik = Rundungsfehler
total = 12.1 + 0.1 + 0.1  # != 12.3

# ✅ RICHTIG
from decimal import Decimal

kosten = Decimal('100.5') * Decimal('0.3')
total = Decimal('12.1') + Decimal('0.1') + Decimal('0.1')

# Django Models
class FahrtkostenModel(models.Model):
    verpflegung = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00')
    )
```

### Währung

```python
# Beträge immer in Cent-Genauigkeit
PAUSCHALE = Decimal('12.00')
KILOMETERSATZ = Decimal('0.30')

def format_currency(amount: Decimal) -> str:
    """Formatiert Betrag als EUR"""
    return f"{amount:.2f} €"
```

## 🧪 Code-Organisation

### Imports

```python
# Reihenfolge: Standard Library → Third Party → Local
import logging
from datetime import date
from decimal import Decimal
from typing import Optional

from django.db import models
from django.http import JsonResponse

from kvb.reisekosten.domain.entities import Fahrt
from kvb.reisekosten.domain.services import FahrtService
from kvb.reisekosten.infrastructure.container import get_container
```

### Exception Handling

```python
# Domain Exceptions (framework-unabhängig)
class FahrtNichtGefundenError(Exception):
    """Fahrt mit gegebenem Key existiert nicht"""
    pass

class UngueltigeFahrtDatenError(ValueError):
    """Fahrtdaten sind ungültig"""
    pass

# Verwendung in Domain/Use Cases
def get_fahrt(key: str) -> Fahrt:
    fahrt = repository.find_by_key(key)
    if not fahrt:
        raise FahrtNichtGefundenError(f"Fahrt nicht gefunden: {key}")
    return fahrt

# In UI Layer: Exceptions catchen und in HTTP-Response übersetzen
# (Beispiel für Web-Framework - analog für CLI, API, etc.)
@with_container
def create_fahrt_handler(request, container):
    try:
        use_case = container.get_create_fahrt_use_case()
        fahrt = use_case.execute(data)
        return success_response({"status": "success"})
    except UngueltigeFahrtDatenError as e:
        logger.warning(f"Validation error: {e}")
        return error_response(str(e), status=400)
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        return error_response("Internal error", status=500)
```

### Logging

```python
import kvb.log_config
logger = kvb.log_config.get_logger(__name__)

# Log-Levels
logger.debug("Detaillierte Informationen für Debugging")
logger.info("Allgemeine Informationen (z.B. Service gestartet)")
logger.warning("Warnung - z.B. Validation-Fehler")
logger.error("Fehler - Exception aufgetreten", exc_info=True)
logger.critical("Kritischer Fehler - System nicht funktionsfähig")

# Best Practices
logger.info(f"Fahrt erstellt: {fahrt.key}")  # Context mitgeben
logger.error(f"Fehler beim Speichern von {fahrt.key}: {e}", exc_info=True)
```

## 📋 Code Review Checkliste

Vor jedem Commit prüfen:

- [ ] **Type Hints** für alle Public Functions
- [ ] **Docstrings** für Klassen und Public Methods
- [ ] **Tests** geschrieben und grün
- [ ] **Keine `float`** für Geldbeträge (nur `Decimal`)
- [ ] **Layer-Trennung** eingehalten (Domain ↔ Infrastructure)
- [ ] **Logging** an wichtigen Stellen
- [ ] **Exception Handling** implementiert
- [ ] **Code formatiert** (Black)
- [ ] **Imports sortiert**
- [ ] **Namen** folgen Konventionen

## 🔧 Tools

### Black (Formatter)

```bash
# Formatieren
black kvb/ --line-length 100

# Check (ohne Änderungen)
black kvb/ --check --line-length 100
```

### Pylint / Flake8

```bash
# Linting
pylint kvb/reisekosten/

# Oder
flake8 kvb/reisekosten/ --max-line-length 100
```

### MyPy (Type Checking)

```bash
mypy kvb/reisekosten/ --strict
```

### Import Linter (Dependency Rules)

**Tool**: `import-linter` - Prüft dass Layer-Regeln eingehalten werden

```bash
# Installation
pip install import-linter

# .import-linter.ini erstellen
```

**Konfiguration** (`.import-linter.ini`):

```ini
[importlinter]
root_package = kvb.reisekosten

[importlinter:contract:domain-independence]
name = Domain Layer darf keine Infrastructure-Dependencies haben
type = forbidden
source_modules =
    kvb.reisekosten.domain
forbidden_modules =
    django
    sqlalchemy
    flask
    kvb.reisekosten.adapters
    kvb.reisekosten.infrastructure
    kvb.reisekosten.ui

[importlinter:contract:application-dependencies]
name = Application Layer darf nur Domain kennen
type = layers
layers =
    kvb.reisekosten.ui
    kvb.reisekosten.application
    kvb.reisekosten.domain
```

**Ausführen**:

```bash
# Dependency-Check
lint-imports

# Beispiel-Output bei Verstoß:
# ❌ kvb.reisekosten.domain.services imports django.db.models
#    → Verstoß gegen domain-independence
```

**In CI/CD integrieren**:

```bash
# In pre-commit hook oder CI
lint-imports || exit 1
```

## 🔒 Type Safety

**Regel**: Type Safety ist Pflicht - alle öffentlichen Funktionen und Methoden MÜSSEN Type Hints haben.

### Warum Type Safety?

✅ **Vorteile:**
- Fehler werden **vor der Laufzeit** gefunden (mypy, pyright)
- **IDE-Support** wird massiv besser (Autocomplete, Refactoring)
- **Dokumentation im Code** - Typen sind selbsterklärend
- **Refactoring ist sicherer** - Type Checker findet alle betroffenen Stellen
- **Bessere Wartbarkeit** - besonders in größeren Teams

### Pflicht-Regeln

```python
# ✅ RICHTIG: Type Hints für alle öffentlichen Funktionen/Methoden
from typing import List, Optional, Protocol
from decimal import Decimal

def calculate_total(items: List[Fahrt]) -> Decimal:
    """Berechnet Gesamtkosten"""
    return sum((item.berechne_kosten() for item in items), Decimal('0'))

def find_fahrt(key: str) -> Optional[Fahrt]:
    """Findet Fahrt oder gibt None zurück"""
    return repository.get(key)

# ✅ RICHTIG: Protocol statt ABC für Interfaces
class Repository(Protocol):
    """Repository Interface"""

    def save(self, entity: Fahrt) -> Fahrt: ...
    def get(self, key: str) -> Optional[Fahrt]: ...

# ❌ FALSCH: Keine Type Hints
def calculate_total(items):  # ❌ Welcher Typ?
    return sum(...)

def find_fahrt(key):  # ❌ Was kommt zurück?
    return repository.get(key)
```

### TypedDict für komplexe Datenstrukturen

```python
from typing import TypedDict

class FahrtDTO(TypedDict):
    """DTO für Fahrt-Daten (Type-Safe)"""
    key: str
    von: date
    person: str
    km: int
    spesen: int

# Verwendung
def create_from_dict(data: FahrtDTO) -> Fahrt:
    return Fahrt(**data)  # IDE prüft alle Keys!
```

### Tools für Type Checking

**mypy** - Standard Python Type Checker:

```bash
# Installation
pip install mypy

# Ausführen
mypy kvb/reisekosten/

# In pyproject.toml konfigurieren:
[tool.mypy]
python_version = "3.11"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true  # Pflicht: Alle Funktionen typisiert
```

**pyright** - Schneller Type Checker (von Microsoft):

```bash
# Installation
pip install pyright

# Ausführen
pyright kvb/reisekosten/

# In pyrightconfig.json:
{
  "typeCheckingMode": "strict",
  "reportMissingTypeStubs": true
}
```

### Pragmatische Ausnahmen

```python
# Tests dürfen lockerer sein (aber Fixture-Returns typen!)
@pytest.fixture
def sample_fahrt() -> Fahrt:  # ✅ Return-Typ angeben!
    return Fahrt(key="test", ...)

def test_something(sample_fahrt):  # ✅ Fixture-Parameter ok ohne Type
    assert sample_fahrt.km > 0

# Legacy-Code: Schrittweise migrieren
def old_function(data):  # TODO: Type Hints hinzufügen
    # type: ignore  # Temporär erlaubt, aber MUSS dokumentiert werden
    pass

# Any nur als letzter Ausweg
from typing import Any

def handle_unknown(data: Any) -> dict:  # ⚠️ Any vermeiden, nur wenn nötig
    """WARUM Any nötig ist, dokumentieren!"""
    pass
```

### CI/CD Integration

```bash
# In .github/workflows/ci.yml oder pre-commit
- name: Type Check
  run: |
    mypy kvb/ --strict
    pyright kvb/
```

## 📦 Semantic Versioning (SemVer)

**Regel**: Alle Projekte nutzen [Semantic Versioning 2.0.0](https://semver.org/lang/de/).

### Format: `MAJOR.MINOR.PATCH`

```
1.0.0 → Initial Release
1.0.1 → Bugfix
1.1.0 → Neue Features (abwärtskompatibel)
2.0.0 → Breaking Changes
```

### Versionsnummern-Regeln

1. **MAJOR** (Breaking Changes):
   - Nicht-abwärtskompatible API-Änderungen
   - Beispiele:
     - Entfernen eines öffentlichen Endpoints
     - Ändern von Function Signatures
     - Umbenennen von Klassen/Methoden
     - Ändern des Verhaltens bestehender Features

   ```python
   # Version 1.x.x
   def calculate_kosten(km: int) -> Decimal:
       pass

   # Version 2.0.0 - Breaking Change!
   def calculate_kosten(km: int, satz: Decimal) -> Decimal:  # Neuer Parameter
       pass
   ```

2. **MINOR** (Neue Features):
   - Neue Funktionalität (abwärtskompatibel)
   - Beispiele:
     - Neue Endpoints/Use Cases
     - Neue optionale Parameter
     - Neue Klassen/Module

   ```python
   # Version 1.0.0
   def calculate_kosten(km: int) -> Decimal:
       pass

   # Version 1.1.0 - Neues Feature (abwärtskompatibel)
   def calculate_kosten(km: int, satz: Decimal = Decimal('0.30')) -> Decimal:
       pass  # Optional parameter - alte Calls funktionieren noch!
   ```

3. **PATCH** (Bugfixes):
   - Bugfixes (abwärtskompatibel)
   - Performance-Verbesserungen
   - Refactorings ohne Verhaltensänderung
   - Dokumentations-Updates

   ```python
   # Version 1.0.0 - Bug
   def calculate_kosten(km: int) -> Decimal:
       return km * Decimal('0.3')  # ❌ Falsch gerundet

   # Version 1.0.1 - Bugfix
   def calculate_kosten(km: int) -> Decimal:
       return Decimal(km) * Decimal('0.30')  # ✅ Korrekt
   ```

### Pre-Release Versionen

```
1.0.0-alpha.1    → Alpha-Version
1.0.0-beta.2     → Beta-Version
1.0.0-rc.1       → Release Candidate
1.0.0            → Stable Release
```

### Version Management

**In `pyproject.toml`:**

```toml
[tool.poetry]
name = "kvb-admin"
version = "1.2.3"
```

**Git Tags:**

```bash
# Release erstellen
git tag -a v1.2.3 -m "Release 1.2.3: Add Fahrt export feature"
git push origin v1.2.3

# Changelog automatisch generieren (z.B. mit commitizen)
cz changelog
```

### Changelog Format

```markdown
# Changelog

## [2.0.0] - 2025-11-03

### 🔥 Breaking Changes
- Removed deprecated `oldFunction()` method
- Renamed `FahrtModel` to `Fahrt` entity

### ✨ Features
- Added Reisekosten PDF export
- Implemented Hexagonal Architecture refactoring

### 🐛 Bugfixes
- Fixed decimal rounding in cost calculation
- Corrected date filtering in monthly view

### 📚 Documentation
- Added Architecture Decision Records
- Updated API documentation

## [1.5.2] - 2025-10-15

### 🐛 Bugfixes
- Fixed CSV import encoding issue
```

### Dependency Versioning

```toml
# In pyproject.toml

[tool.poetry.dependencies]
python = "^3.11"           # Caret: >=3.11.0, <4.0.0
django = "~5.0"            # Tilde: >=5.0, <5.1
pydantic = ">=2.0,<3.0"    # Range
pytest = "^7.4"            # Für Tests
```

### Version Bumping

```bash
# Automatisch mit poetry
poetry version patch   # 1.0.0 → 1.0.1
poetry version minor   # 1.0.1 → 1.1.0
poetry version major   # 1.1.0 → 2.0.0

# Oder mit commitizen
cz bump              # Automatisch basierend auf Commits
cz bump --major      # Force major bump
```

## 📚 Weiterführende Dokumente

- [Testing Strategy](testing-strategy.md) - Test-Pyramide und Ansatz
- [Hexagonal Architecture](../architecture/hexagonal-architecture.md) - Architektur-Prinzipien
- [Definition of Done](../processes/definition-of-done.md) - Quality Gates

---

**Zuletzt aktualisiert:** 2025-11-03
