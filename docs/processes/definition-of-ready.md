# Definition of Ready

Checkliste vor Start einer Aufgabe - stellt sicher, dass Task klar definiert und startbar ist.

## 🎯 Zweck

**Definition of Ready (DoR)** stellt sicher, dass:
- Aufgabe **klar verstanden** ist
- Alle **Informationen vorhanden** sind
- Task **geschätzt** werden kann
- **Keine Blocker** existieren

**Regel**: Wenn DoR nicht erfüllt → Task zurück in Refinement

## ✅ Checkliste

### 1. Ziel ist klar

- [ ] **Was soll erreicht werden?** (Feature, Bugfix, Refactoring)
- [ ] **Warum** ist das wichtig? (Business Value)
- [ ] **Wer** profitiert davon? (User Story: "Als ... möchte ich ... damit ...")

**Beispiel**:
```
✅ RICHTIG:
Titel: CSV-Export für Fahrten implementieren
Ziel: User können Fahrten eines Monats als CSV exportieren für Excel-Auswertung
User Story: Als Buchhalter möchte ich Fahrten als CSV exportieren,
            damit ich sie in Excel weiterverarbeiten kann

❌ FALSCH:
Titel: Export machen
Ziel: ?
```

### 2. Akzeptanzkriterien definiert

- [ ] **Eingaben** sind klar (Was geht rein?)
- [ ] **Ausgaben** sind klar (Was kommt raus?)
- [ ] **Verhalten** ist spezifiziert (Was soll passieren?)
- [ ] **Edge Cases** berücksichtigt (Was wenn...?)

**Beispiel**:
```
Akzeptanzkriterien CSV-Export:

Eingaben:
- Jahr und Monat (z.B. 2025, 11)
- Optional: Filter nach Person

Ausgaben:
- CSV-Datei mit Feldern: Datum, Person, Start, Ziel, KM, Spesen, Kosten
- Dateiname: fahrten_YYYY_MM.csv

Verhalten:
- Export-Button in Monatsübersicht
- Download startet direkt
- CSV mit korrekter UTF-8 Encoding

Edge Cases:
- Keine Fahrten im Monat → Leere CSV (nur Header)
- Sonderzeichen in Ziel → Escaped
```

### 3. Abhängigkeiten geklärt

- [ ] **Andere Tasks**: Gibt es Vorbedingungen?
- [ ] **APIs/Services**: Sind alle benötigten Services verfügbar?
- [ ] **Daten**: Sind Testdaten vorhanden?
- [ ] **Berechtigungen**: Haben wir Zugriff auf alles Nötige?

**Beispiel**:
```
Abhängigkeiten CSV-Export:

✅ Erledigt:
- MonthlyStatisticsUseCase existiert bereits
- Fahrt-Entity hat alle benötigten Felder

⚠️ Zu klären:
- Brauchen wir Berechtigungsprüfung? (nur eigene Fahrten?)
- Welches CSV-Format? (Komma vs Semikolon, deutsche Zahlen?)
```

### 4. Testdaten vorhanden

- [ ] **Testdaten** sind verfügbar oder können erstellt werden
- [ ] **Test-Szenarien** sind bekannt
- [ ] **Expected Results** sind klar

**Beispiel**:
```
Testdaten CSV-Export:

Vorhanden:
- 2025-11: 15 Fahrten (Marc: 10, Ingo: 5)
- 2025-10: 3 Fahrten

Zu erstellen:
- 2025-12: 0 Fahrten (für Empty-Case)
- Fahrt mit Sonderzeichen im Ziel ("Halle (Saale)")
```

### 5. BDD-Feature (falls Domain-Logik)

- [ ] **BDD-Feature** skizziert (Gherkin)
- [ ] **Szenarien** identifiziert
- [ ] **Examples** vorhanden

**Beispiel**:
```gherkin
Feature: CSV-Export für Fahrten

Scenario: Export eines Monats mit Fahrten
  Given es existieren Fahrten für November 2025:
    | Person | Datum      | Ziel    | KM  |
    | Marc   | 2025-11-01 | Leipzig | 500 |
    | Marc   | 2025-11-05 | Berlin  | 600 |
    | Ingo   | 2025-11-03 | Dresden | 450 |
  When ich den CSV-Export für November 2025 anfordere
  Then erhalte ich eine CSV-Datei "fahrten_2025_11.csv"
  And die CSV enthält 3 Zeilen (plus Header)
  And die erste Zeile enthält "Marc,2025-11-01,Leipzig,500"

Scenario: Export eines leeren Monats
  Given es existieren keine Fahrten für Dezember 2025
  When ich den CSV-Export für Dezember 2025 anfordere
  Then erhalte ich eine CSV-Datei mit nur dem Header
```

### 6. Keine Blocker

- [ ] **Keine technischen Blocker** (fehlende Tools, Libraries, etc.)
- [ ] **Keine organisatorischen Blocker** (Entscheidungen offen, etc.)
- [ ] **Team verfügbar** (keine Urlauber die benötigt werden)

**Beispiel**:
```
Blocker-Check CSV-Export:

✅ Kein Blocker:
- Python csv library verfügbar (Standard Library)
- Django Response-Klassen bekannt

❌ Blocker:
- Entscheidung CSV-Format offen (Komma vs Semikolon)
  → Muss mit Product Owner geklärt werden
```

### 7. Geschätzt

- [ ] **Aufwand geschätzt** (Story Points / Stunden / T-Shirt Size)
- [ ] **Passt in Sprint/Timebox**
- [ ] **Nicht zu groß** (max 1-3 Tage für eine Person)

**Beispiel**:
```
Schätzung CSV-Export:

Small (1-2 Tage):
- CSV-Generator: 0.5d
- View/Endpoint: 0.5d
- Tests: 0.5d
- Review/Fixes: 0.5d

→ Passt in Sprint, DoR erfüllt
```

## 🚫 Nicht Ready - Was tun?

**Wenn DoR nicht erfüllt**:

1. **Zurück zu Refinement** - Task nicht starten
2. **Blocker dokumentieren** - Was fehlt?
3. **Klärung organisieren** - Meeting, Slack, etc.
4. **Task aktualisieren** - DoR-Items abarbeiten

**Beispiel**:
```
Task: CSV-Export implementieren

DoR-Status: ❌ NOT READY

Offene Punkte:
- [ ] CSV-Format klären (Komma vs Semikolon)
- [ ] Berechtigungskonzept klären
- [ ] Testdaten für Edge Cases erstellen

Aktion:
→ Meeting mit Product Owner: Mo 10:00
→ Danach: Task aktualisieren und erneut DoR prüfen
```

## 📝 Template

```markdown
## Task: [Titel]

### Ziel
[Was soll erreicht werden? Warum?]

**User Story**: Als [Rolle] möchte ich [Aktion], damit [Nutzen].

### Akzeptanzkriterien

**Eingaben**:
- [Input 1]
- [Input 2]

**Ausgaben**:
- [Output 1]
- [Output 2]

**Verhalten**:
- [Erwartetes Verhalten 1]
- [Erwartetes Verhalten 2]

**Edge Cases**:
- [Edge Case 1]
- [Edge Case 2]

### Abhängigkeiten
- [ ] [Abhängigkeit 1]
- [ ] [Abhängigkeit 2]

### Testdaten
- Vorhanden: [Liste]
- Zu erstellen: [Liste]

### BDD-Feature (optional)
```gherkin
Feature: [Name]

Scenario: [Szenario 1]
  Given [Precondition]
  When [Action]
  Then [Expected Result]
```

### Blocker
- [ ] Keine Blocker | [Liste von Blockern]

### Schätzung
[S/M/L] - [Zeitschätzung]

### DoR-Check
- [ ] Ziel klar
- [ ] Akzeptanzkriterien definiert
- [ ] Abhängigkeiten geklärt
- [ ] Testdaten vorhanden
- [ ] BDD-Feature skizziert (falls Domain-Logik)
- [ ] Keine Blocker
- [ ] Geschätzt

**Status**: ✅ READY | ❌ NOT READY
```

## 🎓 Best Practices

### 1. Refinement-Meetings nutzen

**DoR wird im Refinement sichergestellt**:
- Backlog Items durchgehen
- DoR-Checkliste abarbeiten
- Unklare Items zurückstellen

### 2. DoR ist Team-Verantwortung

Nicht nur PO/Lead, sondern **ganzes Team** prüft DoR:
- Developer: Technische Machbarkeit
- Tester: Testbarkeit
- PO: Business Value

### 3. DoR ist iterativ

DoR kann sich entwickeln:
- Erste Version: Grobes Verständnis
- Nach Diskussion: Mehr Details
- Vor Sprint: Finale DoR

### 4. "Just enough" DoR

**Nicht zu viel** Details:
- ✅ Genug um zu starten
- ❌ Nicht jede Zeile Code spezifizieren

### 5. DoR dokumentieren

DoR-Items im Ticket festhalten:
- GitHub Issue
- Jira Story
- Linear Task

## 📚 Weiterführende Dokumente

- [Definition of Done](definition-of-done.md) - Quality Gate vor Abschluss
- [Testing Strategy](../development/testing-strategy.md) - BDD Features
- [Git Workflow](../development/git-workflow.md) - Branching

---

**Zuletzt aktualisiert:** 2025-11-03
