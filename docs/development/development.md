# Entwicklungs-Guide

Anleitung zur Entwicklung und zum Setup von KVB-Admin2.

## Quick Start

```bash
# 1. Repository klonen
git clone <repo-url> kvb-admin2
cd kvb-admin2

# 2. Virtual Environment erstellen
python3 -m venv .venv
source .venv/bin/activate

# 3. Dependencies installieren
make install-dev
# oder manuell:
pip install -r requirements.txt -r dev-requirements.txt

# 4. Umgebungsvariablen setzen
cp .env.example .env
nano .env  # Anpassen

# 5. Datenbank initialisieren
make migrate
# oder:
python manage.py migrate

# 6. Superuser erstellen
python manage.py createsuperuser

# 7. Development Server starten
make run
# oder:
python manage.py runserver 0.0.0.0:8000
```

## Entwicklungs-Setup

### Voraussetzungen

- **Python**: >= 3.10
- **PostgreSQL**: >= 13
- **Node.js**: >= 18 (für Frontend-Tools)
- **Git**: >= 2.30

### Virtual Environment

```bash
# Erstellen
python3 -m venv .venv

# Aktivieren (Linux/Mac)
source .venv/bin/activate

# Aktivieren (Windows)
.venv\Scripts\activate

# Deaktivieren
deactivate
```

### Dependencies

```bash
# Production Dependencies
pip install -r requirements.txt

# Development Dependencies
pip install -r dev-requirements.txt

# Einzelne Pakete installieren
pip install django-debug-toolbar ipython
```

### Datenbank

**PostgreSQL Setup**:

```bash
# PostgreSQL starten
sudo systemctl start postgresql

# Datenbank und User erstellen
sudo -u postgres psql
CREATE DATABASE kvb_admin2;
CREATE USER kvb_user WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE kvb_admin2 TO kvb_user;
\q

# In .env konfigurieren
DATABASE_URL=postgresql://kvb_user:your_password@localhost:5432/kvb_admin2
```

**SQLite (für Entwicklung)**:

```python
# settings.py
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}
```

### Migrations

```bash
# Migrations erstellen
python manage.py makemigrations

# Migrations anwenden
python manage.py migrate

# Migration für spezifische App
python manage.py makemigrations finanzen
python manage.py migrate finanzen

# Migrations anzeigen
python manage.py showmigrations

# Migration zurücksetzen
python manage.py migrate finanzen 0005  # Zu Migration 0005 zurück
```

## Makefile-Befehle

Das Projekt verwendet ein umfassendes Makefile für häufige Operationen.

### Übersicht

```bash
# Hilfe anzeigen
make help
make help-all  # Alle Befehle

# Quick Start
make dev-setup      # Komplettes Development Setup
make run            # Development Server starten
make test           # Tests ausführen
```

### Setup-Befehle

```bash
make venv           # Virtual Environment erstellen
make install        # Production Dependencies
make install-dev    # Dev Dependencies
make migrate        # Datenbank migrieren
make superuser      # Admin-User erstellen
make dev-setup      # Komplettes Setup
```

### Development-Befehle

```bash
make run            # Django runserver
make shell          # Django shell
make dbshell        # Datenbank-Shell
make makemigrations # Migrations erstellen
make migrate        # Migrations anwenden
```

### Test-Befehle

```bash
make test           # Alle Tests
make test-coverage  # Tests mit Coverage
make test-app APP=finanzen  # Tests für eine App
make lint           # Code-Qualität prüfen
```

### Code-Qualität

```bash
make lint           # Ruff + Black
make format         # Code formatieren
make type-check     # mypy Type-Checking
make security       # Bandit Security Scan
```

### Datenbank-Befehle

```bash
make db-reset       # Datenbank zurücksetzen
make db-backup      # Backup erstellen
make db-restore     # Backup wiederherstellen
make db-shell       # PostgreSQL Shell
```

### Docker-Befehle

```bash
make docker-build   # Image bauen
make docker-up      # Container starten
make docker-down    # Container stoppen
make docker-logs    # Logs anzeigen
make docker-shell   # Shell im Container
```

### Frontend-Befehle

```bash
make collectstatic  # Static Files sammeln
make download-vendor # Vendor Assets laden (Bootstrap, etc.)
make frontend-setup  # Komplettes Frontend Setup
```

## Projekt-Struktur

```
kvb-admin2/
├── kvb/                      # Hauptprojekt
│   ├── app/                  # Django Settings
│   │   ├── settings.py
│   │   ├── urls.py
│   │   └── wsgi.py
│   ├── gesellschaft/         # Gesellschafts-App
│   │   └── finanzen/        # Finanzen Sub-App
│   ├── liegenschaft/         # Liegenschaften
│   ├── darlehen/            # Darlehen
│   ├── reisekosten/         # Reisekosten
│   ├── dokumente/           # Dokumentenverwaltung
│   ├── userauth/            # Authentifizierung
│   ├── shared/              # Gemeinsame Komponenten
│   └── log_config_optimized.py  # Logging
├── doc/                      # Dokumentation
│   ├── apps/                # App-Dokumentationen
│   │   ├── finanzen.md
│   │   ├── liegenschaft.md
│   │   └── ...
│   ├── development.md       # Diese Datei
│   └── deployment.md
├── static/                   # Static Files
│   ├── css/
│   ├── js/
│   └── vendor/
├── templates/               # Templates
├── requirements.txt         # Dependencies
├── dev-requirements.txt     # Dev Dependencies
├── Makefile                 # Make-Befehle
├── manage.py               # Django Management
└── README.md               # Projekt-Übersicht
```

## Code-Konventionen

### Python Style

Wir folgen **PEP 8** mit einigen Anpassungen:

```python
# Imports sortieren
import os
import sys
from datetime import date

from django.db import models
from django.contrib.auth import User

from kvb.shared.models import BaseModel

# Line Length: 100 Zeichen (nicht 79)

# Type Hints verwenden
def get_kontostand(iban: str) -> Optional[Decimal]:
    ...

# Docstrings verwenden
def complex_function(param: str) -> dict:
    """
    Kurze Beschreibung.

    Args:
        param: Parameter-Beschreibung

    Returns:
        Dictionary mit Ergebnis
    """
    ...
```

### Django Conventions

```python
# Models
class MyModel(models.Model):
    """Model Docstring."""

    class Meta:
        db_table = 'app_mymodel'
        verbose_name = 'My Model'
        verbose_name_plural = 'My Models'
        ordering = ['-created_at']

    # Fields zuerst
    name = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    # Dann Meta
    # Dann __str__
    def __str__(self):
        return self.name

    # Dann andere Methoden
    def get_absolute_url(self):
        return reverse('app:detail', kwargs={'pk': self.pk})
```

### JavaScript/CSS

- **Modern ES6+**: Keine jQuery mehr in neuem Code
- **BEM CSS**: Block-Element-Modifier Naming
- **CSS Custom Properties**: CSS-Variablen verwenden

Siehe: [CSS_MODERNIZATION.md](CSS_MODERNIZATION.md)

## Testing

### Unit Tests

```bash
# Alle Tests
python manage.py test

# Spezifische App
python manage.py test kvb.finanzen

# Spezifischer Test
python manage.py test kvb.finanzen.tests.test_models.TestKonto

# Mit Coverage
coverage run --source='.' manage.py test
coverage report
coverage html  # HTML-Report in htmlcov/
```

### Test-Struktur

```python
# tests/test_models.py
from django.test import TestCase
from kvb.finanzen.domain.models import Konto

class TestKonto(TestCase):
    def setUp(self):
        self.konto = Konto(
            iban="DE12505500200000190250",
            bezeichnung="Test-Konto"
        )

    def test_konto_creation(self):
        self.assertEqual(self.konto.iban, "DE12505500200000190250")

    def test_konto_str(self):
        self.assertEqual(str(self.konto), "Test-Konto (DE12...)")
```

### Integration Tests

```python
from django.test import TestCase, Client

class TestFinanzenViews(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user('test', password='test')

    def test_umsatz_list_view(self):
        self.client.login(username='test', password='test')
        response = self.client.get('/finanzen/umsaetze/')
        self.assertEqual(response.status_code, 200)
```

## Debugging

### Django Debug Toolbar

```python
# settings.py
if DEBUG:
    INSTALLED_APPS += ['debug_toolbar']
    MIDDLEWARE += ['debug_toolbar.middleware.DebugToolbarMiddleware']
    INTERNAL_IPS = ['127.0.0.1']
```

### Django Shell

```bash
# Standard Shell
python manage.py shell

# IPython (empfohlen)
pip install ipython
python manage.py shell

# Shell Plus (django-extensions)
pip install django-extensions
python manage.py shell_plus
```

### Logging

```python
# In Code
from kvb.log_config_optimized import get_logger

logger = get_logger(__name__)
logger.info("Info message")
logger.error("Error message", exc_info=True)

# Log-Level in settings.py
LOGGING = {
    'loggers': {
        'kvb': {
            'level': 'DEBUG',  # Für Entwicklung
        }
    }
}
```

## Git Workflow

### Branches

```bash
# Feature Branch
git checkout -b feature/neue-funktion
git add .
git commit -m "feat: Neue Funktion implementiert"
git push origin feature/neue-funktion

# Pull Request erstellen (GitHub/GitLab)
# Nach Review: Merge in main
```

### Commit Messages

Wir folgen **Conventional Commits**:

```bash
feat: Neue Funktion
fix: Bugfix
docs: Dokumentation
style: Formatierung
refactor: Code-Refactoring
test: Tests
chore: Build/Tools
```

Beispiele:
```bash
git commit -m "feat(finanzen): Multi-Bank-Support hinzugefügt"
git commit -m "fix(mietkonto): Drag & Drop bei Firefox"
git commit -m "docs: README und App-Dokumentation aktualisiert"
```

## Siehe auch

- **Deployment**: [deployment.md](deployment.md)
- **Makefile**: [MAKEFILE_DOCKER_GUIDE.md](MAKEFILE_DOCKER_GUIDE.md)
- **App-Dokumentationen**: [apps/](apps/)
