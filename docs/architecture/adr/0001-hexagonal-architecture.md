# ADR-0001: Hexagonale Architektur für Bounded Contexts

**Status**: Accepted
**Datum**: 2025-11-03
**Entscheider**: Marc Baumgartner
**Ersetzt**: -
**Ersetzt durch**: -

## Context

Das KVB Admin System ist historisch gewachsen und nutzt Django direkt in der Business Logic. Dies führt zu:

- **Tight Coupling**: Business Logic ist fest an Django ORM gebunden
- **Schwer testbar**: Tests benötigen Django DB Setup
- **Keine Portabilität**: Wechsel des Frameworks sehr aufwendig
- **Vermischte Concerns**: Fachlogik und technische Details in gleichen Dateien

### Anforderungen

- Business Logic muss **framework-unabhängig** sein
- Domain Code muss **sehr schnell testbar** sein (< 1ms pro Test)
- System muss **erweiterbar** sein (neue Adapter einfach hinzufügbar)
- **Domain-Driven Design** Prinzipien sollen eingehalten werden
- **Schrittweise Migration** möglich (nicht Big Bang)

### Constraints

- Bestehende Django Datenbank-Schemas müssen weiterhin funktionieren
- Keine Breaking Changes für existierende Features
- Migration muss Bounded Context für Bounded Context erfolgen können

## Decision

Wir führen **Hexagonale Architektur** (Ports and Adapters) für alle Bounded Contexts ein.

### Gewählte Option

**Hexagonale Architektur** mit folgenden Layern:

1. **Domain Layer** - Pure Python, keine Framework-Dependencies
2. **Application Layer** - Use Cases, orchestriert Domain Services
3. **Infrastructure Layer** - Adapter (Repository, Provider, etc.)
4. **UI Layer** - Framework-spezifisch (Django, CLI, API)

### Begründung

- **Testbarkeit**: Domain Tests benötigen keine DB (sehr schnell)
- **Flexibilität**: Framework-Wechsel möglich ohne Domain-Code zu ändern
- **DDD-Kompatibel**: Natürliche Struktur für DDD
- **Bewährtes Pattern**: In der Industry etabliert
- **Schrittweise Migration**: Ein Context nach dem anderen

## Considered Options

### Option 1: Hexagonale Architektur (Ports and Adapters)

**Beschreibung**: Strikte Layer-Trennung mit Ports (Interfaces) und Adapters

**Vorteile**:
- Domain vollständig framework-unabhängig
- Sehr testbar (Domain Tests ohne I/O)
- Klare Dependency Rules
- Ermöglicht DDD
- Framework-Austausch möglich

**Nachteile**:
- Mehr Boilerplate (Interfaces, DTOs, Mapping)
- Initiale Lernkurve
- Migration-Aufwand

**Entscheidung**: ✅ Gewählt

---

### Option 2: Clean Architecture (Uncle Bob)

**Beschreibung**: Ähnlich zu Hexagonal, aber mit strengeren Regeln

**Vorteile**:
- Sehr strikte Dependency Rules
- Noch besser testbar
- Sehr gut dokumentiert (Bücher, Artikel)

**Nachteile**:
- Noch mehr Boilerplate als Hexagonal
- Overhead für kleine Contexts
- Steile Lernkurve

**Entscheidung**: ❌ Abgelehnt (zu strikt für unsere Anforderungen)

---

### Option 3: Service Layer (nur leichte Abstraktion)

**Beschreibung**: Services zwischen Views und Models, aber weiterhin Django-basiert

**Vorteile**:
- Einfacher zu implementieren
- Weniger Boilerplate
- Schnellere Migration

**Nachteile**:
- Weiterhin Django-abhängig
- Tests weiterhin langsam (DB benötigt)
- Kein echter Framework-Wechsel möglich
- Kein echtes DDD

**Entscheidung**: ❌ Abgelehnt (löst Kernprobleme nicht)

---

### Option 4: Status Quo (Django direkt)

**Beschreibung**: Keine Änderung, weiterhin direkter Django-Code

**Vorteile**:
- Kein Aufwand
- Alle kennen es bereits

**Nachteile**:
- Probleme bleiben bestehen
- Tests langsam
- Kein DDD möglich
- Framework Lock-in

**Entscheidung**: ❌ Abgelehnt (Probleme müssen gelöst werden)

## Consequences

### Positive

- **Testbarkeit**: Domain Tests < 1ms (keine DB)
- **Wartbarkeit**: Klare Layer-Trennung, einfacher zu verstehen
- **Flexibilität**: Framework-Wechsel theoretisch möglich
- **DDD**: Ermöglicht echtes Domain-Driven Design
- **Quality**: Erzwingt saubere Architektur

### Negative

- **Boilerplate**: Mehr Code (Ports, Adapters, DTOs, Mapping)
- **Lernkurve**: Team muss Pattern lernen
- **Migration-Aufwand**: Bestehender Code muss refactored werden
- **Komplexität**: Mehr Layers = mehr Komplexität (initial)

### Neutral

- **Code-Menge**: Mehr Code, aber strukturierter
- **Performance**: Mapping-Overhead minimal (< 1ms)

## Implementation

### Migration Path

**Phase 1**: Proof of Concept (Reisekosten)
- ✅ Domain Layer (Entities, Services, Ports)
- ✅ Domain Services (FahrtService, RouteService)
- ✅ Django Repository Adapter
- ✅ Application Layer (Use Cases)
- ✅ DI Container
- ✅ View Helpers
- ✅ Refactored Views (Beispiele)

**Phase 2**: Vollständige Migration Reisekosten
- Legacy Views durch hexagonale ersetzen
- Alle Use Cases implementieren
- Integration Tests

**Phase 3**: Weitere Contexts
- Liegenschaft
- Finanzen (falls sinnvoll)
- etc.

### Aufgaben

- [x] ADR schreiben
- [x] Proof of Concept (Reisekosten)
- [x] Dokumentation (Hexagonal Architecture, Coding Standards)
- [ ] Vollständige Migration Reisekosten
- [ ] Migration weiterer Contexts

## References

- [Hexagonal Architecture (Alistair Cockburn)](https://alistair.cockburn.us/hexagonal-architecture/)
- [docs/architecture/hexagonal-architecture.md](../hexagonal-architecture.md) - Interne Dokumentation
- [docs/development/coding-standards.md](../../development/coding-standards.md) - Layer-Regeln
- [kvb/reisekosten/docs/](../../../kvb/reisekosten/docs/) - Reisekosten Bounded Context

## Notes

### Lessons Learned (Phase 1)

**Was gut funktioniert hat**:
- Domain Tests sind extrem schnell (< 1ms)
- Mapping Repository funktioniert gut (Domain "von" ↔ Model "datum")
- DI Container vereinfacht Testing (inject_repository)
- Use Cases klar strukturiert

**Challenges**:
- Boilerplate initial hoch (Ports, Adapter, Container)
- Mapping kann Fehler enthalten (Tests wichtig!)
- Team-Onboarding benötigt Zeit

**Empfehlungen für weitere Contexts**:
- Template/Generator für Boilerplate nutzen
- Mapping-Tests immer schreiben
- Documentation as Code (Bounded Context Canvas)

---

**ADR Version**: 1.0
**Zuletzt aktualisiert**: 2025-11-03
