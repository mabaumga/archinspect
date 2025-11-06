# Hexagonale Architektur

Architektur-Prinzipien und Patterns für Domain-Driven Design.

## 🎯 Überblick

Die **Hexagonale Architektur** (auch "Ports and Adapters" genannt) trennt die **Business Logic** (Domain) von **technischen Details** (Infrastructure).

**Ziel**: Domain-Code ist unabhängig von Frameworks, Datenbanken, UI, etc.

```
┌──────────────────────────────────────────────────────────────────┐
│                          UI Layer                                 │
│                    (Web, CLI, API, etc.)                          │
└────────────────────────────────┬─────────────────────────────────┘
                                 │
┌────────────────────────────────▼─────────────────────────────────┐
│                      Application Layer                            │
│                      (Use Cases / DTOs)                           │
│                                                                    │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                    Domain Layer                           │   │
│  │              (Entities, Services, Ports)                  │   │
│  │                                                            │   │
│  │  Business Logic - Framework-Unabhängig                    │   │
│  │                                                            │   │
│  └────────┬───────────────────────────────────┬──────────────┘   │
└───────────┼───────────────────────────────────┼──────────────────┘
            │                                   │
            │ Ports (Interfaces)                │
            │                                   │
┌───────────▼───────────────┐       ┌──────────▼──────────────┐
│   Persistence Adapter     │       │  Infrastructure Adapter  │
│  (Repository: DB/ORM)     │       │  (CSV, API, Email, etc.) │
└───────────────────────────┘       └─────────────────────────┘
```

## 🏗️ Layer-Übersicht

### 1. Domain Layer (Kern)

**Was**: Business Logic, Domain Model

**Charakteristik**:
- **Keine Dependencies** zu Frameworks (Django, Flask, etc.)
- **Pure Python** - Dataclasses, Standard Library
- **Sehr testbar** - Keine I/O, sehr schnell
- **Ubiquitous Language** - Fachbegriffe aus der Domäne

**Bestandteile**:
- **Entities**: Geschäftsobjekte mit Identity
- **Value Objects**: Immutable Werte ohne Identity
- **Domain Services**: Business Logic die nicht zu einer Entity gehört
- **Ports**: Interfaces für externe Dependencies (Repository, Provider)
- **Domain Exceptions**: Fachliche Fehler

**Beispiel**:

```python
# domain/entities.py
from dataclasses import dataclass
from datetime import date
from decimal import Decimal

@dataclass
class Fahrt:
    """Domain Entity - Repräsentiert eine Dienstreise"""
    key: str
    von: date
    person: str
    start: str
    ziel: str
    km: int
    spesen: int = 0

    def berechne_kosten(self, satz: Decimal = Decimal('0.30')) -> Decimal:
        """Berechnet Gesamtkosten der Fahrt"""
        fahrtkosten = self.km * satz + Decimal('12.00')  # Pauschale
        return fahrtkosten + self.spesen

# domain/services.py
class FahrtService:
    """Domain Service - Business Logic für Fahrten"""

    def __init__(self, repository: FahrtRepository):
        self.repository = repository

    def create_fahrt(self, data: FahrtDTO) -> Fahrt:
        """Erstellt neue Fahrt mit Validierung"""
        # Business Rules
        if data.km < 0:
            raise ValueError("KM dürfen nicht negativ sein")

        fahrt = Fahrt(**data.__dict__)
        return self.repository.save(fahrt)

# domain/ports.py
from typing import Protocol, Optional

class FahrtRepository(Protocol):
    """Port - Interface für Persistierung"""

    def save(self, fahrt: Fahrt) -> Fahrt:
        """Speichert Fahrt"""
        ...

    def find_by_key(self, key: str) -> Optional[Fahrt]:
        """Findet Fahrt nach Key"""
        ...
```

### 2. Application Layer

**Was**: Use Cases, Orchestrierung

**Charakteristik**:
- **Orchestriert** Domain Services
- **DTOs** für Input/Output
- **Framework-unabhängig** (aber kennt Domain)
- **Transaction Boundaries**

**Bestandteile**:
- **Use Cases**: Anwendungsfälle (z.B. "Fahrt erstellen", "Statistik anzeigen")
- **DTOs**: Data Transfer Objects für Input/Output
- **Application Services**: Koordinieren Use Cases

**Beispiel**:

```python
# application/use_cases.py
from dataclasses import dataclass
from datetime import date

@dataclass
class FahrtDTO:
    """DTO - Datenstruktur für Input"""
    key: str
    von: date
    person: str
    ziel: str
    km: int
    spesen: int = 0

class CreateFahrtUseCase:
    """Use Case - Erstellt Fahrt"""

    def __init__(self, fahrt_service: FahrtService, route_service: RouteService):
        self.fahrt_service = fahrt_service
        self.route_service = route_service

    def execute(self, data: FahrtDTO) -> Fahrt:
        """Führt Use Case aus"""
        return self.fahrt_service.create_fahrt(data)

    def execute_from_route(self, person: str, ziel_key: str, von: date, key: str) -> Fahrt:
        """Alternative: Erstellt Fahrt aus Route"""
        # 1. Route laden
        route = self.route_service.find_route_for_person(person, ziel_key)
        if not route:
            raise ValueError(f"Route nicht gefunden: {ziel_key}")

        # 2. Fahrt aus Route erstellen
        fahrt = self.route_service.create_fahrt_from_route(route, key, von)

        # 3. Speichern
        return self.fahrt_service.repository.save(fahrt)
```

### 3. Infrastructure Layer (Adapter)

**Was**: Konkrete Implementierungen der Ports

**Charakteristik**:
- **Framework-spezifisch** (Django, SQLAlchemy, etc.)
- **Implementiert Ports** aus Domain
- **Mapping** zwischen Domain und Technical Model

**Bestandteile**:
- **Repository Adapter**: DB-Zugriff
- **Provider Adapter**: Externe Services (CSV, API, etc.)
- **DI Container**: Dependency Injection

**Beispiel**:

```python
# adapters/persistence/django_fahrt_repository.py
from kvb.reisekosten.django.models import FahrtkostenModel
from kvb.reisekosten.domain.entities import Fahrt
from kvb.reisekosten.domain.ports import FahrtRepository

class DjangoFahrtRepository:
    """Repository Adapter - Django ORM Implementierung"""

    def save(self, fahrt: Fahrt) -> Fahrt:
        """Speichert Fahrt in DB"""
        model = self._domain_to_model(fahrt)
        model.save()
        return self._model_to_domain(model)

    def find_by_key(self, key: str) -> Optional[Fahrt]:
        """Findet Fahrt in DB"""
        try:
            model = FahrtkostenModel.objects.get(key=key)
            return self._model_to_domain(model)
        except FahrtkostenModel.DoesNotExist:
            return None

    def _domain_to_model(self, fahrt: Fahrt) -> FahrtkostenModel:
        """Mapping: Domain → Django Model"""
        return FahrtkostenModel(
            key=fahrt.key,
            datum=fahrt.von,        # Domain: "von" → Model: "datum"
            fahrer=fahrt.person,    # Domain: "person" → Model: "fahrer"
            start=fahrt.start,
            ziel=fahrt.ziel,
            km=fahrt.km,
            verpflegung=fahrt.spesen  # Domain: "spesen" → Model: "verpflegung"
        )

    def _model_to_domain(self, model: FahrtkostenModel) -> Fahrt:
        """Mapping: Django Model → Domain"""
        return Fahrt(
            key=model.key,
            von=model.datum,
            person=model.fahrer,
            start=model.start,
            ziel=model.ziel,
            km=model.km,
            spesen=int(model.verpflegung or 0)
        )
```

```python
# adapters/infrastructure/csv_route_provider.py
import csv
from kvb.reisekosten.domain.ports import RouteProvider
from kvb.reisekosten.domain.entities import Route

class CsvRouteProvider:
    """Provider Adapter - CSV Implementierung"""

    def __init__(self, csv_path: str = "ziele.csv"):
        self.csv_path = csv_path
        self._cache: Optional[list[Route]] = None

    def get_routes_for_person(self, person: str) -> list[Route]:
        """Lädt Routen aus CSV"""
        if self._cache is None:
            self._load_from_csv()

        return [r for r in self._cache if r.person == person]

    def _load_from_csv(self):
        """Lädt CSV und parsed zu Domain-Objekten"""
        with open(self.csv_path, 'r') as f:
            reader = csv.DictReader(f)
            self._cache = [
                Route(
                    person=row['person'],
                    ziel_key=row['ziel_key'],
                    ziel=row['ziel'],
                    km=int(row['km']),
                    verpflegung=Decimal(row['verpflegung'])
                )
                for row in reader
            ]
```

### 4. UI Layer (Framework-spezifisch)

**Was**: User Interface, API Endpoints, CLI

**Charakteristik**:
- **Framework-spezifisch** (Django Views, Flask Routes, CLI Commands)
- **Nutzt Use Cases** (nicht direkt Domain Services)
- **Übersetzt** zwischen UI und Application Layer

**Beispiel**:

```python
# ui/views.py (Django Beispiel)
from django.http import JsonResponse
from kvb.reisekosten.infrastructure.view_helpers import with_container

@with_container
@require_http_methods(["POST"])
def create_fahrt_view(request, container):
    """View - Erstellt Fahrt über Use Case"""
    try:
        # 1. Request-Daten extrahieren
        data = FahrtDTO(
            key=request.POST.get('key'),
            von=date.fromisoformat(request.POST.get('date')),
            person=request.POST.get('person'),
            ziel=request.POST.get('ziel'),
            km=int(request.POST.get('km', 0)),
            spesen=int(request.POST.get('spesen', 0))
        )

        # 2. Use Case ausführen
        use_case = container.get_create_fahrt_use_case()
        fahrt = use_case.execute(data)

        # 3. Response
        return JsonResponse({
            "status": "success",
            "key": fahrt.key
        })

    except ValueError as e:
        return JsonResponse({"error": str(e)}, status=400)
```

## 🔌 Dependency Injection

**Prinzip**: Dependencies werden von außen injiziert (nicht im Code erzeugt)

### Service Container

```python
# infrastructure/container.py
class ServiceContainer:
    """DI Container - Zentralisiert Service-Erstellung"""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if not hasattr(self, '_initialized'):
            self._initialized = True
            self._fahrt_repository = None
            self._route_provider = None

    # Repositories
    def get_fahrt_repository(self) -> FahrtRepository:
        if self._fahrt_repository is None:
            self._fahrt_repository = DjangoFahrtRepository()
        return self._fahrt_repository

    def get_route_provider(self) -> RouteProvider:
        if self._route_provider is None:
            self._route_provider = CsvRouteProvider()
        return self._route_provider

    # Domain Services
    @lru_cache(maxsize=1)
    def get_fahrt_service(self) -> FahrtService:
        return FahrtService(self.get_fahrt_repository())

    @lru_cache(maxsize=1)
    def get_route_service(self) -> RouteService:
        return RouteService(self.get_route_provider())

    # Use Cases
    def get_create_fahrt_use_case(self) -> CreateFahrtUseCase:
        return CreateFahrtUseCase(
            self.get_fahrt_service(),
            self.get_route_service()
        )

# Globale Instanz
_container = ServiceContainer()

def get_container() -> ServiceContainer:
    return _container
```

### View Helpers

```python
# infrastructure/view_helpers.py
from functools import wraps

def with_container(view_func):
    """Decorator - Injiziert Container in View"""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        container = get_container()
        return view_func(request, container, *args, **kwargs)
    return wrapper
```

## 📏 Layer-Regeln

### Dependency Rule

**Regel**: Dependencies zeigen immer nach innen (zur Domain)

```
UI → Application → Domain ← Infrastructure
```

- ✅ **Application** darf **Domain** kennen
- ✅ **Infrastructure** darf **Domain** kennen (Ports implementieren)
- ✅ **UI** darf **Application** kennen
- ❌ **Domain** darf **NICHT** Infrastructure kennen
- ❌ **Domain** darf **NICHT** Application kennen

### Was darf wo importiert werden?

```python
# ✅ RICHTIG
# application/use_cases.py
from domain.entities import Fahrt  # Application kennt Domain
from domain.services import FahrtService

# infrastructure/container.py
from domain.services import FahrtService  # Infrastructure kennt Domain (Ports)
from adapters.persistence import DjangoFahrtRepository

# ui/views.py
from application.use_cases import CreateFahrtUseCase  # UI kennt Application

# ❌ FALSCH
# domain/services.py
from adapters.persistence import DjangoFahrtRepository  # Domain kennt NICHT Infrastructure!
from django.db import models  # Domain kennt NICHT Frameworks!
```

## 🧪 Testing

### Domain Tests (Sehr schnell)

```python
# tests/test_entities.py
def test_fahrt_berechne_kosten():
    """Test - Pure Business Logic"""
    fahrt = Fahrt(
        key="test",
        von=date.today(),
        person="Marc",
        km=100,
        spesen=12
    )

    kosten = fahrt.berechne_kosten(satz=Decimal('0.30'))

    # (100 * 0.30) + 12 (Pauschale) + 12 (Spesen) = 54.00
    assert kosten == Decimal('54.00')
```

### Service Tests (mit Fakes)

```python
# tests/test_services.py
from tests.fakes import InMemoryFahrtRepository

def test_create_fahrt():
    """Test - Service mit In-Memory Repository"""
    repository = InMemoryFahrtRepository()
    service = FahrtService(repository)

    fahrt = service.create_fahrt(FahrtDTO(...))

    assert repository.count() == 1
    assert fahrt.key == "expected"
```

### Adapter Tests (mit Mocks)

```python
# tests/test_django_repository.py
from unittest.mock import Mock

def test_save_creates_model():
    """Test - Repository Mapping"""
    mock_model_class = Mock()
    repository = DjangoFahrtRepository(model_class=mock_model_class)

    fahrt = Fahrt(key="test", von=date.today(), person="Marc", km=100)
    repository.save(fahrt)

    mock_model_class.assert_called_once()
```

## 📂 Verzeichnisstruktur

### Standard-Struktur (empfohlen)

```
bounded-context/
├── domain/                          # Domain Layer
│   ├── __init__.py
│   ├── entities.py                  # Fahrt, Route, ... (@dataclass)
│   ├── services.py                  # FahrtService, RouteService
│   └── ports/                       # Interfaces (Protocols)
│       ├── __init__.py
│       ├── repository.py            # FahrtRepository Protocol
│       └── provider.py              # RouteProvider Protocol
│
├── application/                     # Application Layer
│   ├── __init__.py
│   └── use_cases.py                # Use Cases, DTOs
│
├── adapters/                        # Infrastructure Adapters
│   └── persistence/                 # Alle Daten-Adapter
│       ├── django/                  # Django ORM Implementierung
│       │   ├── __init__.py
│       │   ├── models.py           # FahrtkostenModel (ORM)
│       │   └── repository.py       # DjangoFahrtRepository
│       ├── csv/                     # CSV Implementierung
│       │   ├── __init__.py
│       │   ├── provider.py         # CsvRouteProvider
│       │   └── data.csv            # Stammdaten
│       └── memory/                  # In-Memory (für Tests)
│           ├── __init__.py
│           └── repository.py       # InMemoryFahrtRepository
│
├── infrastructure/                  # DI & Cross-cutting
│   ├── __init__.py
│   ├── container.py                # ServiceContainer (DI)
│   └── ui_helpers.py               # View Helpers (@with_container)
│
├── ui/                             # UI Layer (auf Hauptebene - pragmatisch)
│   ├── __init__.py
│   ├── views.py                    # Views
│   ├── forms.py                    # Forms
│   └── admin.py                    # Admin
│
├── templates/                       # Django Templates (Hauptebene)
├── templatetags/                    # Django Template Tags (Hauptebene)
├── migrations/                      # Django Migrations (Hauptebene)
│
├── tests/
│   ├── __init__.py
│   ├── test_entities.py
│   ├── test_services.py
│   ├── test_use_cases.py
│   ├── test_django_repository.py
│   └── ...
│
├── docs/                           # Context-Dokumentation
│   ├── bounded-context-canvas.md
│   └── domain-model.md
│
├── apps.py                         # Django App Config
├── urls.py                         # Django URLs
└── Makefile
```

### Architektur-Entscheidungen

#### 1. ORM Models gehören zu Persistence, nicht UI

**Entscheidung**: Django Models in `adapters/persistence/django/models.py`

**Begründung**:
- ✅ Models sind **Persistence-Adapter**, nicht UI
- ✅ Klare Trennung: Business Logic (Domain) vs Datenzugriff (Persistence)
- ✅ Ermöglicht **mehrere Persistence-Implementierungen**:
  ```
  adapters/persistence/
  ├── django/          # Django ORM
  │   └── repository.py
  ├── sqlalchemy/      # SQLAlchemy (alternative)
  │   └── repository.py
  └── memory/          # In-Memory (Tests)
      └── repository.py
  ```
- ✅ Container entscheidet welche Implementierung verwendet wird

#### 2. UI auf Hauptebene (pragmatisch für Single-UI Projekte)

**Entscheidung**: `ui/` auf gleicher Ebene wie `domain/`, nicht unter `adapters/`

**Begründung**:
- ✅ **Pragmatisch** für Django-Projekte
- ✅ **Weniger Verschachtelung**
- ✅ UI ist der **Haupteinstiegspunkt**
- ✅ Django-Konventionen größtenteils erhalten

**Alternative** (bei mehreren UIs):
```
adapters/
└── ui/
    ├── django_web/
    ├── rest_api/
    └── cli/
```

#### 3. Alle Daten-Provider unter persistence/

**Entscheidung**: CSV-Provider in `adapters/persistence/csv/`, nicht `adapters/infrastructure/`

**Begründung**:
- ✅ **Konsistenz**: Routes sind Daten (wie Fahrten)
- ✅ Alle Daten-Adapter unter `persistence/`
- ✅ **Zukunftssicher**: Bei DB-Umstellung → `adapters/persistence/django/route_provider.py`
- ✅ Stammdaten liegen beim Provider: `adapters/persistence/csv/data.csv`

**Regel**:
- `persistence/` - Für Daten (DB, CSV, Memory)
- `infrastructure/` - Für externe Services (APIs, Email, Message Queues)

#### 4. Templates/Templatetags auf Hauptebene

**Entscheidung**: `templates/` und `templatetags/` auf Hauptebene

**Begründung**:
- ✅ **Django-Konvention** (Django sucht dort automatisch)
- ✅ **Weniger Konfiguration** nötig
- ✅ **Praktisch** - bekannte Struktur

### Beispiel: Zweite Persistence-Implementierung

```python
# Container entscheidet welche Implementierung:
class ServiceContainer:
    def get_fahrt_repository(self) -> FahrtRepository:
        # Option 1: Django (Production)
        from adapters.persistence.django.repository import DjangoFahrtRepository
        return DjangoFahrtRepository()

        # Option 2: SQLAlchemy (alternative DB)
        # from adapters.persistence.sqlalchemy.repository import SqlAlchemyRepository
        # return SqlAlchemyRepository()

        # Option 3: Memory (Tests)
        # from adapters.persistence.memory.repository import InMemoryRepository
        # return InMemoryRepository()
```

## 🎓 Best Practices

### 1. Ubiquitous Language

Domain-Code nutzt **Fachbegriffe**:

```python
# ✅ RICHTIG: Fachsprache
class Fahrt:
    von: date        # Fachbegriff
    person: str      # Fachbegriff
    spesen: int      # Fachbegriff

# ❌ FALSCH: Technische Begriffe
class Trip:
    start_date: date
    user_id: str
    allowance: int
```

### 2. Ein Entity pro Fachkonzept

```python
# ✅ RICHTIG: Fahrt nur in reisekosten/
# bounded-contexts/reisekosten/domain/entities.py
class Fahrt:
    pass

# ❌ FALSCH: Fahrt dupliziert in anderem Context
# bounded-contexts/urlaubsplanung/domain/entities.py
class Fahrt:  # Andere Bedeutung? → Anderen Namen nutzen!
    pass
```

### 3. Ports sind Interfaces

```python
# ✅ RICHTIG: Port als Protocol
from typing import Protocol

class FahrtRepository(Protocol):
    def save(self, fahrt: Fahrt) -> Fahrt: ...

# ❌ FALSCH: Port als konkrete Klasse
class FahrtRepository:
    def save(self, fahrt: Fahrt):
        # Konkrete Implementierung im Port!
        pass
```

### 4. DTOs für Boundaries

```python
# ✅ RICHTIG: DTO an Boundary (UI → Application)
@dataclass
class FahrtDTO:
    key: str
    von: date
    person: str

def create_fahrt_view(request):
    data = FahrtDTO(...)  # DTO
    use_case.execute(data)

# ❌ FALSCH: Domain Entity direkt von UI
def create_fahrt_view(request):
    fahrt = Fahrt(...)  # Domain Entity direkt erstellt
    use_case.execute(fahrt)
```

## 📚 Weiterführende Dokumente

- [Bounded Contexts](bounded-contexts.md) - Context-Übersicht
- [Coding Standards](../development/coding-standards.md) - Layer-spezifische Regeln
- [Testing Strategy](../development/testing-strategy.md) - Layer-spezifische Tests
- [ADR 0001](adr/0001-hexagonal-architecture.md) - Entscheidung für Hexagonal Architecture

---

**Zuletzt aktualisiert:** 2025-11-03
