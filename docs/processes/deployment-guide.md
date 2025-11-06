# Deployment Guide

Deployment-Prozess und Best Practices.

Diese Anleitung ist framework-agnostisch wo möglich.

## 🎯 Deployment-Strategie

### Grundprinzipien

1. **Automatisierung** - Manuelle Schritte minimieren
2. **Reproduzierbarkeit** - Gleiches Deployment = Gleiches Ergebnis
3. **Rollback-Fähigkeit** - Schnell zurückrollen bei Problemen
4. **Zero-Downtime** - Keine Ausfallzeiten (wo möglich)
5. **Monitoring** - Deployment-Erfolg verifizieren

## 📋 Pre-Deployment Checkliste

Vor jedem Deployment prüfen:

- [ ] **Alle Tests grün** (`pytest`)
- [ ] **Code Review** durchgeführt
- [ ] **Definition of Done** erfüllt
- [ ] **Migrations** getestet (falls DB-Änderungen)
- [ ] **Backup** erstellt (vor DB-Migration)
- [ ] **Rollback-Plan** vorhanden
- [ ] **Monitoring** vorbereitet (Logs, Metrics)
- [ ] **Stakeholder** informiert (bei großen Changes)

## 🚀 Deployment-Prozess

### 1. Vorbereitung

```bash
# 1. Main Branch aktualisieren
git checkout main
git pull origin main

# 2. Tests lokal ausführen
pytest

# 3. Dependency-Check
lint-imports

# 4. Linting
black . --check
pylint kvb/
```

### 2. Versioning (Semantic Versioning)

```bash
# Version-Tag erstellen
git tag -a v1.2.3 -m "Release 1.2.3: CSV Export Feature"

# Tag pushen
git push origin v1.2.3
```

**Format**: `vMAJOR.MINOR.PATCH`
- **MAJOR**: Breaking Changes
- **MINOR**: Neue Features (backwards compatible)
- **PATCH**: Bugfixes

### 3. Environment-spezifisches Deployment

#### Development

```bash
# Entwicklungs-Environment (lokal)
# Automatisch bei git push (optional: pre-push hook)

# Migrations ausführen
python manage.py migrate

# Server neu starten
make restart-dev
```

#### Staging

```bash
# Staging-Environment
# CI/CD Pipeline deployed automatisch auf main-push

# Oder manuell:
ssh user@staging-server
cd /app
git pull origin main
source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py collectstatic --noinput
sudo systemctl restart kvb-admin
```

#### Production

```bash
# Production-Environment
# Nur auf Tagged Releases deployen

# 1. SSH in Production
ssh user@production-server

# 2. Backup erstellen
./scripts/backup.sh

# 3. Deployment
cd /app
git fetch origin
git checkout v1.2.3  # Spezifischer Tag!
source venv/bin/activate
pip install -r requirements.txt --no-cache-dir

# 4. Migrations (mit Backup!)
python manage.py migrate

# 5. Static Files
python manage.py collectstatic --noinput

# 6. Service neu starten
sudo systemctl restart kvb-admin

# 7. Health Check
curl http://localhost:8000/health/

# 8. Monitoring prüfen
# - Logs: tail -f /var/log/kvb-admin/app.log
# - Metrics: Check Grafana/Prometheus
```

## 🗄️ Database Migrations

### Migration-Strategie

**Zwei-Phasen-Deployment** für Breaking Changes:

#### Phase 1: Additive Changes

```python
# Migration 001: Neue Felder hinzufügen (nullable)
class Migration(migrations.Migration):
    operations = [
        migrations.AddField(
            model_name='fahrt',
            name='new_field',
            field=models.CharField(max_length=100, null=True, blank=True)
        ),
    ]
```

**Deploy**: Code + Migration deployen → Funktioniert mit alter und neuer Version

#### Phase 2: Data Migration + Enforcement

```python
# Migration 002: Daten migrieren
def migrate_data(apps, schema_editor):
    Fahrt = apps.get_model('reisekosten', 'Fahrt')
    for fahrt in Fahrt.objects.filter(new_field__isnull=True):
        fahrt.new_field = calculate_value(fahrt)
        fahrt.save()

class Migration(migrations.Migration):
    dependencies = [('reisekosten', '001_add_new_field')]
    operations = [
        migrations.RunPython(migrate_data),
    ]

# Migration 003: NOT NULL setzen
class Migration(migrations.Migration):
    operations = [
        migrations.AlterField(
            model_name='fahrt',
            name='new_field',
            field=models.CharField(max_length=100)  # Nicht mehr nullable
        ),
    ]
```

### Migration-Checklist

- [ ] **Backup vor Migration**
- [ ] **Lokal getestet** (mit Produktions-ähnlichen Daten)
- [ ] **Reversible** (Rollback-Migration vorhanden)
- [ ] **Performance** geprüft (bei großen Tabellen)
- [ ] **Downtime** geplant (falls nötig)

### Rollback einer Migration

```bash
# Letzte Migration rückgängig machen
python manage.py migrate reisekosten 0042  # Zurück zu 0042

# ODER: Komplettes Rollback
git checkout v1.2.2  # Vorherige Version
python manage.py migrate
sudo systemctl restart kvb-admin
```

## 🐳 Docker Deployment

### Docker-Build

```bash
# Image bauen
docker build -t kvb-admin:v1.2.3 .

# Tag für Registry
docker tag kvb-admin:v1.2.3 registry.example.com/kvb-admin:v1.2.3
docker tag kvb-admin:v1.2.3 registry.example.com/kvb-admin:latest

# Push to Registry
docker push registry.example.com/kvb-admin:v1.2.3
docker push registry.example.com/kvb-admin:latest
```

### Docker-Compose Deployment

```yaml
# docker-compose.prod.yml
version: '3.8'

services:
  web:
    image: registry.example.com/kvb-admin:v1.2.3
    environment:
      - DJANGO_SETTINGS_MODULE=kvb.app.settings_prod
      - DATABASE_URL=${DATABASE_URL}
    volumes:
      - static:/app/static
      - media:/app/media
    restart: unless-stopped

  db:
    image: postgres:15
    volumes:
      - postgres_data:/var/lib/postgresql/data
    environment:
      - POSTGRES_PASSWORD=${DB_PASSWORD}
    restart: unless-stopped

volumes:
  static:
  media:
  postgres_data:
```

```bash
# Deployment
docker-compose -f docker-compose.prod.yml pull
docker-compose -f docker-compose.prod.yml up -d

# Migrations
docker-compose -f docker-compose.prod.yml exec web python manage.py migrate

# Logs
docker-compose -f docker-compose.prod.yml logs -f web
```

## 🔄 Rollback-Strategie

### Schneller Rollback

**Voraussetzungen**:
- Previous Version als Git Tag
- Backup vorhanden
- Migrations sind reversible

**Prozess**:

```bash
# 1. Previous Version deployen
git checkout v1.2.2

# 2. Dependencies installieren
pip install -r requirements.txt

# 3. Migrations zurückrollen (falls nötig)
python manage.py migrate reisekosten 0042

# 4. Service neu starten
sudo systemctl restart kvb-admin

# 5. Verifizieren
curl http://localhost:8000/health/
```

### Rollback-Checklist

- [ ] **Backup vorhanden** (vor Rollback!)
- [ ] **DB-Migrations** rückgängig gemacht
- [ ] **Static Files** der alten Version
- [ ] **Dependencies** der alten Version installiert
- [ ] **Health Check** erfolgreich
- [ ] **Monitoring** zeigt normale Metriken

## 📊 Post-Deployment

### Health Checks

```bash
# Application Health
curl http://localhost:8000/health/
# Expected: {"status": "ok", "version": "1.2.3"}

# Database Connectivity
curl http://localhost:8000/health/db/
# Expected: {"status": "ok", "db": "connected"}

# Specific Feature
curl http://localhost:8000/api/reisekosten/2025/11/
# Expected: JSON response mit Fahrten
```

### Monitoring

**Logs prüfen**:

```bash
# Application Logs
tail -f /var/log/kvb-admin/app.log

# Error Logs
tail -f /var/log/kvb-admin/error.log

# Access Logs
tail -f /var/log/nginx/access.log
```

**Metriken prüfen**:
- Response Times (sollten stabil bleiben)
- Error Rate (sollte nicht steigen)
- Database Queries (Performance)

### Smoke Tests

Manuelle Tests nach Deployment:

- [ ] **Login** funktioniert
- [ ] **Hauptfeatures** funktionieren (z.B. Fahrt erstellen)
- [ ] **Neue Features** funktionieren
- [ ] **Kritische Workflows** durchspielen

## 🔐 Security

### Secrets Management

```bash
# Secrets NICHT im Code!
# Nutze Environment Variables oder Secrets Manager

# .env (nie in Git!)
DATABASE_URL=postgresql://user:pass@localhost/db
SECRET_KEY=very-secret-key
API_KEY=sk-1234567890

# In Production: Secrets Manager (AWS Secrets Manager, Vault, etc.)
# Oder: Environment Variables via systemd

# /etc/systemd/system/kvb-admin.service
[Service]
Environment="SECRET_KEY=..."
Environment="DATABASE_URL=..."
EnvironmentFile=/etc/kvb-admin/secrets.env
```

### SSL/TLS

```bash
# Zertifikate aktualisieren (Let's Encrypt)
sudo certbot renew

# Nginx Config prüfen
sudo nginx -t

# Nginx neu laden
sudo systemctl reload nginx
```

## 📚 CI/CD Integration

### GitHub Actions Beispiel

```yaml
# .github/workflows/deploy.yml
name: Deploy

on:
  push:
    tags:
      - 'v*'

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Run Tests
        run: |
          pip install -r requirements.txt
          pytest
          lint-imports

  deploy:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - name: Deploy to Production
        run: |
          ssh user@prod-server "cd /app && ./deploy.sh ${{ github.ref_name }}"

      - name: Health Check
        run: |
          sleep 10
          curl -f http://prod-server/health/ || exit 1
```

## 🎓 Best Practices

### 1. Feature Flags

Für große Features:

```python
# Feature Flag (über Environment oder DB)
ENABLE_CSV_EXPORT = os.getenv('ENABLE_CSV_EXPORT', 'false') == 'true'

def csv_export_view(request):
    if not ENABLE_CSV_EXPORT:
        return HttpResponse("Feature not enabled", status=404)
    # ...
```

**Vorteil**: Deploy Code, aktiviere Feature später

### 2. Blue-Green Deployment

Zwei identische Environments:
- **Blue**: Aktuelle Production
- **Green**: Neue Version

**Prozess**:
1. Deploy auf Green
2. Tests auf Green
3. Switch Traffic: Blue → Green
4. Bei Problemen: Switch zurück

### 3. Canary Deployment

Neue Version für **kleinen Teil** der User:
- 5% Traffic → Neue Version
- Bei Erfolg: 100% Traffic

### 4. Database Backups vor Migrations

```bash
# Automatisches Backup vor Migration
# In deploy-script:
./scripts/backup.sh
python manage.py migrate || {
    echo "Migration failed, restoring backup"
    ./scripts/restore.sh latest
    exit 1
}
```

## 📚 Weiterführende Dokumente

- [Backup & Restore](backup-restore.md) - Backup-Strategie
- [Definition of Done](definition-of-done.md) - Pre-Deployment Checks
- [Git Workflow](../development/git-workflow.md) - Versioning

---

**Zuletzt aktualisiert:** 2025-11-03
