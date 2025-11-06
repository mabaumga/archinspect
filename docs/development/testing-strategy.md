# Testing Strategy

Test-Strategie für Hexagonale Architektur und Domain-Driven Design.

Diese Strategie ist framework-agnostisch und gilt für alle Projekte nach diesem Architektur-Ansatz.

## 🎯 Test-Pyramide

```
                    ┌─────────┐
                    │   UI    │  Wenige, langsam
                    │  Tests  │  (E2E, Browser)
                    └─────────┘
                 ┌──────────────┐
                 │ Integration  │   Moderate Anzahl
                 │    Tests     │   (API, DB)
                 └──────────────┘
            ┌────────────────────────┐
            │    Adapter Tests       │   Viele, mit Mocks
            │   (Repository, etc.)   │
            └────────────────────────┘
       ┌──────────────────────────────────┐
       │         Domain Tests             │   Sehr viele, sehr schnell
       │  (Entities, Services, Use Cases) │   (Keine I/O, Pure Logic)
       └──────────────────────────────────┘
```

### Prinzipien

1. **Domain Tests** (80% der Tests)
   - Schnell (keine I/O, keine DB, keine externen Services)
   - Isoliert (Pure Business Logic)
   - Keine Mocks nötig (oder minimal)

2. **Adapter Tests** (15% der Tests)
   - Mit Mocks für externe Dependencies
   - Testen Mapping (Domain ↔ Infrastructure)

3. **Integration Tests** (4% der Tests)
   - Testen Zusammenspiel der Komponenten
   - Mit echter DB oder Test-Containern

4. **UI Tests** (1% der Tests)
   - End-to-End
   - Nur für kritische User Journeys

## 📂 Test-Organisation

### Verzeichnisstruktur

```
bounded-context/
├── domain/
│   ├── entities.py
│   └── services.py
├── application/
│   └── use_cases.py
├── adapters/
│   └── persistence/
│       └── orm_repository.py
└── tests/
    ├── test_entities.py        # Domain Tests (schnell)
    ├── test_services.py        # Domain Tests (schnell)
    ├── test_use_cases.py       # Application Tests (schnell)
    ├── test_repository.py      # Adapter Tests (mit Mocks)
    └── integration/
        ├── test_db_repository.py   # Integration Tests (mit echter DB)
        └── test_end_to_end.py      # E2E Tests
```

## 🧪 Test-Kategorien

### 1. Domain Tests

**Ziel**: Testen der Business Logic ohne externe Dependencies

**Charakteristik**:
- Sehr schnell (< 1ms pro Test)
- Keine Mocks nötig
- Keine I/O Operations
- Pure Functions / Domain Services

**Beispiel - Entity Tests**:

```python
# test_entities.py
import pytest
from datetime import date
from decimal import Decimal

from domain.entities import Fahrt

def test_fahrt_creation():
    """Test: Fahrt kann erstellt werden"""
    fahrt = Fahrt(
        key="2025-11-03-marc",
        von=date(2025, 11, 3),
        person="Marc",
        start="Hanau",
        ziel="Leipzig",
        km=500,
        spesen=12
    )

    assert fahrt.key == "2025-11-03-marc"
    assert fahrt.km == 500

def test_fahrt_validation_negative_km():
    """Test: Negative KM werden abgelehnt"""
    with pytest.raises(ValueError, match="Kilometer.*negativ"):
        Fahrt(
            key="test",
            von=date.today(),
            person="Marc",
            km=-100  # Ungültig
        )

def test_berechne_kosten():
    """Test: Kostenberechnung korrekt"""
    fahrt = Fahrt(
        key="test",
        von=date.today(),
        person="Marc",
        km=100,
        spesen=12
    )

    # (100 km * 0.30 €/km) + 12 € Pauschale + 12 € Verpflegung = 54.00 €
    assert fahrt.berechne_kosten(satz=Decimal('0.30')) == Decimal('54.00')
```

**Beispiel - Service Tests**:

```python
# test_services.py
from domain.services import FahrtService
from domain.ports import FahrtRepository
from tests.fakes import InMemoryFahrtRepository

def test_create_fahrt():
    """Test: Fahrt wird erstellt und gespeichert"""
    # Arrange
    repository = InMemoryFahrtRepository()
    service = FahrtService(repository)

    # Act
    fahrt = service.create_fahrt(
        key="test",
        von=date.today(),
        person="Marc",
        ziel="Leipzig",
        km=500
    )

    # Assert
    assert fahrt.key == "test"
    assert repository.count() == 1

def test_get_fahrten_by_month():
    """Test: Filtern nach Monat"""
    repository = InMemoryFahrtRepository()
    repository.save(Fahrt(..., von=date(2025, 11, 1)))
    repository.save(Fahrt(..., von=date(2025, 11, 15)))
    repository.save(Fahrt(..., von=date(2025, 10, 1)))  # Anderer Monat

    service = FahrtService(repository)

    fahrten = service.get_fahrten_by_month(2025, 11)

    assert len(fahrten) == 2
```

### 2. Application Layer Tests (Use Cases)

**Ziel**: Testen der Orchestrierung zwischen Services

**Charakteristik**:
- Schnell (mit Fakes/In-Memory Repos)
- Testen Use Case Logik
- Minimal Mocks

**Beispiel**:

```python
# test_use_cases.py
from application.use_cases import CreateFahrtUseCase, FahrtDTO
from tests.fakes import InMemoryFahrtRepository, MockRouteProvider

def test_create_fahrt_from_route():
    """Test: Fahrt wird aus Route erstellt"""
    # Arrange
    repository = InMemoryFahrtRepository()
    route_provider = MockRouteProvider()
    route_provider.add_route("Marc", "leipzig", km=500, verpflegung=12)

    fahrt_service = FahrtService(repository)
    route_service = RouteService(route_provider)
    use_case = CreateFahrtUseCase(fahrt_service, route_service)

    # Act
    fahrt = use_case.execute_from_route(
        person="Marc",
        ziel_key="leipzig",
        von=date.today(),
        key="test"
    )

    # Assert
    assert fahrt.ziel == "Leipzig"
    assert fahrt.km == 500
    assert fahrt.spesen == 12

def test_create_fahrt_route_not_found():
    """Test: Exception bei nicht gefundener Route"""
    repository = InMemoryFahrtRepository()
    route_provider = MockRouteProvider()  # Leer

    use_case = CreateFahrtUseCase(
        FahrtService(repository),
        RouteService(route_provider)
    )

    with pytest.raises(ValueError, match="Route nicht gefunden"):
        use_case.execute_from_route(
            person="Marc",
            ziel_key="unbekannt",
            von=date.today(),
            key="test"
        )
```

### 3. Adapter Tests

**Ziel**: Testen der Adapter-Implementierungen (Repository, Provider, etc.)

**Charakteristik**:
- Mit Mocks für externe Dependencies
- Testen Mapping (Domain ↔ Infrastructure)
- Testen Error Handling

**Beispiel - Repository Tests**:

```python
# test_repository.py
import pytest
from unittest.mock import Mock, MagicMock
from adapters.persistence.orm_repository import OrmFahrtRepository
from domain.entities import Fahrt

def test_save_creates_new_model():
    """Test: save() erstellt neues ORM Model"""
    # Arrange
    mock_model_class = Mock()
    mock_model_instance = MagicMock()
    mock_model_class.objects.get.side_effect = Exception("DoesNotExist")  # Kein existierendes

    repository = OrmFahrtRepository(model_class=mock_model_class)
    fahrt = Fahrt(key="test", von=date.today(), person="Marc", km=100)

    # Act
    repository.save(fahrt)

    # Assert
    mock_model_class.assert_called_once()  # Neues Model erstellt
    mock_model_instance.save.assert_called_once()

def test_mapping_domain_to_model():
    """Test: Mapping von Domain zu ORM Model"""
    repository = OrmFahrtRepository()
    fahrt = Fahrt(
        key="test",
        von=date(2025, 11, 3),  # Domain: "von"
        person="Marc",           # Domain: "person"
        spesen=12                # Domain: "spesen"
    )

    model = repository._domain_to_model(fahrt)

    # Mapping prüfen
    assert model.datum == date(2025, 11, 3)  # Model: "datum"
    assert model.fahrer == "Marc"             # Model: "fahrer"
    assert model.verpflegung == 12            # Model: "verpflegung"

def test_mapping_model_to_domain():
    """Test: Mapping von ORM Model zu Domain"""
    model = Mock()
    model.key = "test"
    model.datum = date(2025, 11, 3)
    model.fahrer = "Marc"
    model.verpflegung = Decimal('12.00')

    repository = OrmFahrtRepository()
    fahrt = repository._model_to_domain(model)

    assert fahrt.von == date(2025, 11, 3)
    assert fahrt.person == "Marc"
    assert fahrt.spesen == 12
```

**Beispiel - CSV Provider Tests**:

```python
# test_csv_provider.py
from unittest.mock import mock_open, patch
from adapters.infrastructure.csv_route_provider import CsvRouteProvider

def test_load_routes_from_csv():
    """Test: Routen werden aus CSV geladen"""
    csv_data = """person,ziel_key,ziel,km,verpflegung
Marc,leipzig,Leipzig,500,12.00
Ingo,berlin,Berlin,600,12.00"""

    with patch('builtins.open', mock_open(read_data=csv_data)):
        provider = CsvRouteProvider(csv_path="ziele.csv")
        routes = provider.get_routes_for_person("Marc")

    assert len(routes) == 1
    assert routes[0].ziel == "Leipzig"
    assert routes[0].km == 500
```

### 4. Integration Tests

**Ziel**: Testen des Zusammenspiels aller Komponenten

**Charakteristik**:
- Mit echter Datenbank (oder Test-Container)
- Langsamer
- Testen kritische Pfade

**Beispiel**:

```python
# integration/test_db_repository.py
import pytest
from adapters.persistence.orm_repository import OrmFahrtRepository
from domain.entities import Fahrt

@pytest.mark.integration
def test_save_and_retrieve_from_db(db_session):
    """Test: Fahrt wird in DB gespeichert und geladen"""
    repository = OrmFahrtRepository(session=db_session)

    # Save
    fahrt = Fahrt(
        key="integration-test",
        von=date.today(),
        person="Marc",
        km=500
    )
    saved = repository.save(fahrt)

    # Retrieve
    found = repository.find_by_key("integration-test")

    assert found is not None
    assert found.key == "integration-test"
    assert found.km == 500
```

### 5. UI Tests (End-to-End)

**Ziel**: Testen kritischer User Journeys

**Nur für kritische Flows** - z.B. "Fahrt erstellen und absenden"

```python
# integration/test_end_to_end.py
import pytest

@pytest.mark.e2e
def test_create_fahrt_journey(client):
    """E2E: Fahrt erstellen über UI"""
    # 1. Fahrt-Formular öffnen
    response = client.get('/reisekosten/fahrt/neu')
    assert response.status_code == 200

    # 2. Formular absenden
    response = client.post('/reisekosten/fahrt/neu', data={
        'datum': '2025-11-03',
        'person': 'Marc',
        'ziel': 'Leipzig'
    })
    assert response.status_code == 302  # Redirect nach Erfolg

    # 3. Fahrt in Übersicht sichtbar
    response = client.get('/reisekosten/2025/11')
    assert 'Leipzig' in response.text
```

## 🔧 Test Helpers

### Fakes (In-Memory Implementierungen)

```python
# tests/fakes.py
from typing import Optional
from domain.ports import FahrtRepository
from domain.entities import Fahrt

class InMemoryFahrtRepository:
    """Fake Repository für Tests (keine DB)"""

    def __init__(self):
        self._storage: dict[str, Fahrt] = {}

    def save(self, fahrt: Fahrt) -> Fahrt:
        self._storage[fahrt.key] = fahrt
        return fahrt

    def find_by_key(self, key: str) -> Optional[Fahrt]:
        return self._storage.get(key)

    def find_all(self) -> list[Fahrt]:
        return list(self._storage.values())

    def count(self) -> int:
        return len(self._storage)
```

### Fixtures

```python
# conftest.py
import pytest
from tests.fakes import InMemoryFahrtRepository

@pytest.fixture
def repository():
    """In-Memory Repository für Tests"""
    return InMemoryFahrtRepository()

@pytest.fixture
def fahrt_service(repository):
    """FahrtService mit Test-Repository"""
    return FahrtService(repository)

# Für Integration Tests
@pytest.fixture
def db_session():
    """DB Session für Integration Tests"""
    # Setup DB
    session = create_test_session()
    yield session
    # Teardown
    session.rollback()
    session.close()
```

## 📊 Coverage

### Ziele

- **Domain Layer**: ≥ 90% Coverage
- **Application Layer**: ≥ 85% Coverage
- **Adapter Layer**: ≥ 80% Coverage
- **Gesamt**: ≥ 80% Coverage

### Coverage messen

```bash
# pytest mit Coverage
pytest --cov=bounded_context --cov-report=html

# Nur Domain Tests (schnell)
pytest tests/test_entities.py tests/test_services.py --cov=domain/

# Report anzeigen
open htmlcov/index.html
```

## ✅ Test-Checkliste (DoD)

Vor jedem Commit:

- [ ] **Domain Tests** für neue Entities/Services geschrieben
- [ ] **Use Case Tests** für neue Use Cases geschrieben
- [ ] **Adapter Tests** für neue Repositories/Provider
- [ ] **Alle Tests grün** (`pytest`)
- [ ] **Coverage ≥ 80%** für geänderte Module
- [ ] **Keine langsamen Tests** in Domain Layer (< 1ms)
- [ ] **Integration Tests** nur wo nötig

## 🚀 Best Practices

### 1. Test-Namen sind aussagekräftig

```python
# ✅ RICHTIG
def test_berechne_kosten_mit_pauschale_und_verpflegung():
    pass

# ❌ FALSCH
def test_calculate():
    pass
```

### 2. AAA Pattern (Arrange, Act, Assert)

```python
def test_create_fahrt():
    # Arrange - Setup
    repository = InMemoryFahrtRepository()
    service = FahrtService(repository)

    # Act - Ausführen
    fahrt = service.create_fahrt(...)

    # Assert - Prüfen
    assert fahrt.key == "expected"
```

### 3. Ein Assert pro logischem Konzept

```python
# ✅ RICHTIG
def test_fahrt_creation():
    fahrt = create_fahrt()
    assert fahrt.key == "test"
    assert fahrt.km == 500

# ❌ FALSCH (zu viele unabhängige Asserts)
def test_everything():
    fahrt = create_fahrt()
    assert fahrt.key == "test"
    assert service.count() == 1
    assert calculate_something() == 42
```

### 4. Keine Logik in Tests

```python
# ❌ FALSCH
def test_with_logic():
    for person in ["Marc", "Ingo", "Jan"]:
        fahrt = create_fahrt(person)
        assert fahrt.person == person  # Logik im Test

# ✅ RICHTIG
@pytest.mark.parametrize("person", ["Marc", "Ingo", "Jan"])
def test_create_fahrt_for_person(person):
    fahrt = create_fahrt(person)
    assert fahrt.person == person
```

## 📚 Weiterführende Dokumente

- [Coding Standards](coding-standards.md) - Code-Qualität
- [Definition of Done](../processes/definition-of-done.md) - Quality Gates
- [Hexagonal Architecture](../architecture/hexagonal-architecture.md) - Layer-Trennung

---

**Zuletzt aktualisiert:** 2025-11-03
