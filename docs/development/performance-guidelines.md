# Performance Guidelines

Performance-Richtlinien für effiziente Software-Entwicklung.

Diese Richtlinien sind framework-agnostisch und gelten für alle Projekte.

## 🎯 Grundprinzipien

1. **Measure First** - Erst messen, dann optimieren
2. **Optimize Bottlenecks** - Fokus auf die 20% die 80% ausmachen
3. **Readability First** - Lesbarkeit vor Mikro-Optimierungen
4. **Lazy Loading** - Nur laden was gebraucht wird
5. **Cache Smart** - Häufige Operationen cachen

## 📊 Performance Budget

### Response Time Ziele

| Operation | Ziel | Maximum |
|-----------|------|---------|
| Domain Logic | < 1ms | 5ms |
| DB Query (einfach) | < 10ms | 50ms |
| DB Query (komplex) | < 50ms | 200ms |
| API Request (intern) | < 100ms | 500ms |
| API Request (extern) | < 500ms | 2s |
| Page Load | < 1s | 3s |

### Memory

- **Domain Objects**: Minimal (< 1KB pro Entity)
- **Cache**: Max 100MB für In-Memory Caches
- **Request**: Max 50MB pro Request

## 🏗️ Architecture Performance

### Layer-spezifische Regeln

#### Domain Layer

**Regel**: Domain Layer muss sehr schnell sein (< 1ms)

```python
# ✅ RICHTIG: Pure Business Logic, keine I/O
@dataclass
class Fahrt:
    key: str
    km: int
    spesen: int

    def berechne_kosten(self, satz: Decimal = Decimal('0.30')) -> Decimal:
        """Reine Berechnung - sehr schnell (< 1ms)"""
        return (self.km * satz) + self.spesen

# ❌ FALSCH: I/O im Domain Layer
def berechne_kosten_unsafe(self) -> Decimal:
    rate = load_from_database()  # Langsam!
    return self.km * rate
```

#### Repository Layer

**N+1 Problem vermeiden**:

```python
# ✅ RICHTIG: Eager Loading / Batch Query
def get_fahrten_with_person_details(year: int, month: int) -> list[Fahrt]:
    """Lädt Fahrten mit Personen-Details in einer Query"""
    # SQL: SELECT * FROM fahrten JOIN persons ON ... WHERE ...
    return repository.find_with_join(year, month)

# ❌ FALSCH: N+1 Queries
def get_fahrten_with_person_details_slow(year: int, month: int) -> list[Fahrt]:
    fahrten = repository.find_by_month(year, month)  # 1 Query
    for fahrt in fahrten:
        person = person_repository.find(fahrt.person)  # N Queries!
        fahrt.person_details = person
    return fahrten
```

**Select nur notwendige Felder**:

```python
# ✅ RICHTIG: Nur benötigte Felder
def get_fahrt_summary(key: str) -> dict:
    """Lädt nur id, datum, person"""
    return repository.find_fields(key, fields=["id", "datum", "person"])

# ❌ FALSCH: Alle Felder laden (wenn nicht nötig)
def get_fahrt_summary_slow(key: str) -> dict:
    fahrt = repository.find(key)  # Lädt alle Felder inkl. BLOB, etc.
    return {"id": fahrt.id, "datum": fahrt.datum}
```

## 💾 Caching

### Wann Cachen?

Cache Daten die:
- **Häufig gelesen** werden
- **Selten ändern**
- **Teuer zu berechnen/laden** sind

### Cache Strategien

#### 1. In-Memory Cache (Funktions-Level)

```python
from functools import lru_cache

# ✅ RICHTIG: Cache für teure Berechnungen
@lru_cache(maxsize=128)
def calculate_complex_statistics(year: int, month: int) -> Statistics:
    """Cacht Statistiken pro Jahr/Monat"""
    # Teure Berechnung...
    return Statistics(...)

# Cache invalidieren wenn nötig
calculate_complex_statistics.cache_clear()
```

#### 2. Instance-Level Cache

```python
class RouteService:
    """Service mit Cache für Routen"""

    def __init__(self, provider: RouteProvider):
        self._provider = provider
        self._cache: dict[str, list[Route]] = {}

    def get_routes_for_person(self, person: str) -> list[Route]:
        """Lädt Routen (mit Cache)"""
        if person not in self._cache:
            self._cache[person] = self._provider.load_routes(person)
        return self._cache[person]

    def invalidate_cache(self, person: str):
        """Invalidiert Cache für Person"""
        self._cache.pop(person, None)
```

#### 3. Singleton Pattern (für Services)

```python
# ✅ RICHTIG: Service als Singleton (eine Instanz pro App)
class ServiceContainer:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    @lru_cache(maxsize=1)
    def get_fahrt_service(self) -> FahrtService:
        """Singleton - nur eine Instanz"""
        return FahrtService(self.get_repository())

# ❌ FALSCH: Service bei jedem Request neu erstellen
def handle_request():
    service = FahrtService(Repository())  # Neue Instanz!
    return service.get_data()
```

### Cache Invalidierung

```python
# ✅ RICHTIG: Cache invalidieren bei Änderungen
class FahrtService:
    def __init__(self, repository):
        self.repository = repository
        self._stats_cache = {}

    def create_fahrt(self, data: FahrtDTO) -> Fahrt:
        fahrt = Fahrt(**data)
        self.repository.save(fahrt)

        # Cache invalidieren
        cache_key = (fahrt.von.year, fahrt.von.month)
        self._stats_cache.pop(cache_key, None)

        return fahrt

    @lru_cache
    def get_statistics(self, year: int, month: int) -> Statistics:
        # Wird gecacht
        return self._calculate_statistics(year, month)
```

## 🗄️ Database Performance

### Index richtig nutzen

```sql
-- ✅ RICHTIG: Index auf häufig gefilterte Felder
CREATE INDEX idx_fahrten_datum ON fahrten(datum);
CREATE INDEX idx_fahrten_person ON fahrten(person);
CREATE INDEX idx_fahrten_datum_person ON fahrten(datum, person);

-- Query nutzt Index
SELECT * FROM fahrten WHERE datum >= '2025-11-01' AND datum < '2025-12-01';
```

### Batch Operations

```python
# ✅ RICHTIG: Batch Insert
def import_fahrten(fahrten: list[Fahrt]):
    """Importiert viele Fahrten auf einmal"""
    repository.bulk_create(fahrten)  # Ein DB-Roundtrip

# ❌ FALSCH: Einzeln speichern
def import_fahrten_slow(fahrten: list[Fahrt]):
    for fahrt in fahrten:
        repository.save(fahrt)  # N DB-Roundtrips!
```

### Pagination

```python
# ✅ RICHTIG: Pagination für große Resultsets
def get_fahrten_paginated(page: int = 1, page_size: int = 50) -> list[Fahrt]:
    """Lädt nur eine Seite"""
    offset = (page - 1) * page_size
    return repository.find_all(limit=page_size, offset=offset)

# ❌ FALSCH: Alle Daten laden
def get_all_fahrten() -> list[Fahrt]:
    return repository.find_all()  # Kann Millionen Einträge sein!
```

## 📈 Algorithmic Performance

### Time Complexity

**Bevorzuge**:
- O(1) - Konstant: Dictionary/Set Lookup
- O(log n) - Logarithmisch: Binary Search
- O(n) - Linear: Single Loop

**Vermeide**:
- O(n²) - Quadratisch: Nested Loops
- O(2ⁿ) - Exponentiell: Rekursive Brute-Force

```python
# ✅ RICHTIG: O(1) Dictionary Lookup
person_map = {p.id: p for p in persons}  # O(n) einmalig
person = person_map.get("marc")  # O(1)

# ❌ FALSCH: O(n) bei jedem Lookup
person = next((p for p in persons if p.id == "marc"), None)  # O(n)
```

### Data Structures

```python
# ✅ RICHTIG: Set für Membership-Tests (O(1))
valid_persons = {"Marc", "Ingo", "Jan"}
if person in valid_persons:  # O(1)
    ...

# ❌ FALSCH: List für Membership-Tests (O(n))
valid_persons = ["Marc", "Ingo", "Jan"]
if person in valid_persons:  # O(n)
    ...

# ✅ RICHTIG: Dictionary für Gruppierung
fahrten_by_person = {}
for fahrt in fahrten:
    fahrten_by_person.setdefault(fahrt.person, []).append(fahrt)

# ❌ FALSCH: Nested Loop (O(n²))
persons = set(f.person for f in fahrten)
fahrten_by_person = {
    person: [f for f in fahrten if f.person == person]  # O(n) für jede Person!
    for person in persons
}
```

## 🔄 Lazy Loading

### Load on Demand

```python
# ✅ RICHTIG: Lazy Loading von Services
class ServiceContainer:
    def __init__(self):
        self._fahrt_service = None  # Noch nicht initialisiert

    def get_fahrt_service(self) -> FahrtService:
        """Lazy: Erstellt nur wenn gebraucht"""
        if self._fahrt_service is None:
            self._fahrt_service = FahrtService(self.get_repository())
        return self._fahrt_service

# ❌ FALSCH: Eager Loading aller Services
class ServiceContainer:
    def __init__(self):
        # Alle Services sofort erstellen (auch wenn nicht gebraucht)
        self.fahrt_service = FahrtService(...)
        self.route_service = RouteService(...)
        self.stats_service = StatisticsService(...)
```

### Property-based Lazy Loading

```python
# ✅ RICHTIG: Property für Lazy Loading
@dataclass
class FahrtAggregate:
    key: str
    _route: Optional[Route] = None

    @property
    def route(self) -> Route:
        """Lädt Route nur wenn abgerufen"""
        if self._route is None:
            self._route = route_service.find(self.key)
        return self._route
```

## 📦 File I/O

### CSV Reading

```python
# ✅ RICHTIG: Generator für große Files
def read_routes_lazy(csv_path: str):
    """Generator - lädt nur eine Zeile zur Zeit"""
    with open(csv_path, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            yield Route(**row)

# Verwendung
for route in read_routes_lazy("ziele.csv"):
    process(route)  # Nur eine Zeile im Memory

# ❌ FALSCH: Gesamtes File in Memory
def read_routes_eager(csv_path: str) -> list[Route]:
    with open(csv_path, 'r') as f:
        reader = csv.DictReader(f)
        return [Route(**row) for row in reader]  # Gesamtes File im Memory!
```

## 🧪 Performance Testing

### Profiling

```python
import cProfile
import pstats

# Profiling einer Funktion
def profile_function():
    profiler = cProfile.Profile()
    profiler.enable()

    # Code ausführen
    result = expensive_operation()

    profiler.disable()

    # Statistiken ausgeben
    stats = pstats.Stats(profiler)
    stats.sort_stats('cumulative')
    stats.print_stats(10)  # Top 10

# Oder: Decorator
from functools import wraps
import time

def timing_decorator(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        start = time.perf_counter()
        result = func(*args, **kwargs)
        end = time.perf_counter()
        print(f"{func.__name__} took {(end-start)*1000:.2f}ms")
        return result
    return wrapper

@timing_decorator
def slow_function():
    # ...
    pass
```

### Benchmarking

```python
import pytest

@pytest.mark.benchmark
def test_fahrt_creation_performance(benchmark):
    """Benchmark: Fahrt Creation"""
    def create_fahrt():
        return Fahrt(
            key="test",
            von=date.today(),
            person="Marc",
            km=500
        )

    result = benchmark(create_fahrt)
    assert result.key == "test"

# Ausführen: pytest --benchmark-only
```

### Load Testing

```python
# Für APIs: locust, ab, wrk
# Beispiel: locust

from locust import HttpUser, task, between

class FahrtenUser(HttpUser):
    wait_time = between(1, 3)

    @task
    def get_month_overview(self):
        self.client.get("/reisekosten/2025/11")

    @task(3)  # 3x häufiger
    def create_fahrt(self):
        self.client.post("/reisekosten/fahrt/neu", json={
            "datum": "2025-11-03",
            "person": "Marc",
            "km": 500
        })

# Run: locust -f locustfile.py
```

## 📋 Performance Checkliste

Vor jedem Commit:

- [ ] **Keine N+1 Queries**
- [ ] **Batch Operations** für Bulk-Daten
- [ ] **Caching** für teure Operationen
- [ ] **Lazy Loading** wo sinnvoll
- [ ] **Pagination** für große Listen
- [ ] **Indexes** auf gefilterte DB-Felder
- [ ] **Algorithmic Complexity** O(n) oder besser
- [ ] **Domain Tests** < 1ms
- [ ] **API Endpoints** < 500ms

## 🔍 Common Pitfalls

### 1. Premature Optimization

```python
# ❌ FALSCH: Mikro-Optimierung ohne Messung
# "String concat ist langsam, ich nutze Liste"
def build_string():
    parts = []
    for i in range(10):  # Nur 10 Iterationen!
        parts.append(str(i))
    return ''.join(parts)

# ✅ RICHTIG: Lesbarkeit bei kleinen Daten
def build_string():
    result = ""
    for i in range(10):
        result += str(i)  # Völlig OK für 10 Iterationen
    return result

# Optimierung nur bei VIELEN Iterationen (> 1000)
```

### 2. Over-Caching

```python
# ❌ FALSCH: Alles cachen
@lru_cache(maxsize=None)  # Unbegrenzt!
def get_fahrt(key: str) -> Fahrt:
    return repository.find(key)

# Problem: Memory wächst unbegrenzt

# ✅ RICHTIG: Sinnvolles Limit
@lru_cache(maxsize=100)  # Maximal 100 Einträge
def get_fahrt(key: str) -> Fahrt:
    return repository.find(key)
```

### 3. Synchronous statt Asynchronous

```python
# Für I/O-intensive Operations: async nutzen
# (Bei Bedarf - nicht immer nötig)

# ❌ LANGSAM: Sequenziell
def fetch_all_data():
    data1 = fetch_from_api_1()  # 500ms
    data2 = fetch_from_api_2()  # 500ms
    return data1, data2  # Total: 1000ms

# ✅ SCHNELL: Parallel
import asyncio

async def fetch_all_data():
    data1, data2 = await asyncio.gather(
        fetch_from_api_1_async(),  # 500ms
        fetch_from_api_2_async()   # 500ms (parallel)
    )
    return data1, data2  # Total: 500ms
```

## 🎯 Optimization Workflow

1. **Measure** - Profiling, Benchmarks
2. **Identify** - Bottlenecks finden (80/20 Regel)
3. **Optimize** - Nur die Bottlenecks
4. **Measure** - Verbesserung verifizieren
5. **Document** - Warum optimiert? (Kommentar/ADR)

## 📚 Weiterführende Dokumente

- [Coding Standards](coding-standards.md) - Code-Qualität
- [Testing Strategy](testing-strategy.md) - Performance Tests
- [Architecture](../architecture/hexagonal-architecture.md) - Layer Performance

---

**Zuletzt aktualisiert:** 2025-11-03
