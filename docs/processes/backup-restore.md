# Backup & Restore

Backup-Strategie und Wiederherstellungs-Prozesse.

## 🎯 Backup-Strategie

### Grundprinzipien

1. **3-2-1 Regel**:
   - **3** Kopien der Daten
   - **2** verschiedene Medien/Technologien
   - **1** Kopie Off-Site

2. **Regelmäßigkeit**: Automatische tägliche Backups

3. **Testbarkeit**: Regelmäßige Restore-Tests

4. **Verschlüsselung**: Backups verschlüsselt speichern

5. **Retention**: Definierte Aufbewahrungsfristen

## 📋 Was wird gesichert?

### 1. Datenbank

**Kritisch**: Enthält alle Business-Daten

- Fahrten, Routen, Einheiten, Verträge, Buchungen, etc.
- Täglich: Full Backup
- Stündlich: Transaktions-Log (falls möglich)

### 2. Uploaded Files

**Wichtig**: User-Uploads, Dokumente

- Rechnungen, Verträge, Fotos, etc.
- Täglich: Incremental Backup
- Wöchentlich: Full Backup

### 3. Configuration

**Wichtig**: Environment-Config

- `.env` Files (ohne Secrets im Repo!)
- nginx/systemd Configs
- SSL Certificates

### 4. Code

**Nice-to-have**: Bereits in Git

- Git Repository (GitHub/GitLab)
- Backup via Git Clone

## 🔧 Backup-Implementation

### Datenbank Backup (PostgreSQL)

**Script**: `scripts/backup-db.sh`

```bash
#!/bin/bash
# scripts/backup-db.sh

set -e  # Exit on error

# Configuration
BACKUP_DIR="/var/backups/kvb-admin/db"
RETENTION_DAYS=30
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
DB_NAME="kvb_admin"

# Create backup directory
mkdir -p "$BACKUP_DIR"

# Backup filename
BACKUP_FILE="$BACKUP_DIR/${DB_NAME}_${TIMESTAMP}.sql.gz"

# Create backup (with compression)
pg_dump -U kvb_user -h localhost "$DB_NAME" | gzip > "$BACKUP_FILE"

# Verify backup
if [ -f "$BACKUP_FILE" ]; then
    echo "✅ Backup created: $BACKUP_FILE"
    echo "   Size: $(du -h "$BACKUP_FILE" | cut -f1)"
else
    echo "❌ Backup failed!"
    exit 1
fi

# Delete old backups (older than RETENTION_DAYS)
find "$BACKUP_DIR" -name "${DB_NAME}_*.sql.gz" -type f -mtime +$RETENTION_DAYS -delete
echo "🗑️  Old backups deleted (older than $RETENTION_DAYS days)"

# Optional: Upload to S3/Remote
# aws s3 cp "$BACKUP_FILE" s3://my-bucket/backups/db/
```

**Ausführbar machen**:

```bash
chmod +x scripts/backup-db.sh
```

**Cron Job** (täglich um 2 Uhr nachts):

```bash
# /etc/cron.d/kvb-admin-backup
0 2 * * * kvbadmin /app/scripts/backup-db.sh >> /var/log/kvb-admin/backup.log 2>&1
```

### File Backup (rsync)

**Script**: `scripts/backup-files.sh`

```bash
#!/bin/bash
# scripts/backup-files.sh

set -e

# Configuration
SOURCE_DIR="/app/media"
BACKUP_DIR="/var/backups/kvb-admin/files"
TIMESTAMP=$(date +%Y%m%d)
RETENTION_DAYS=30

# Create backup directory
mkdir -p "$BACKUP_DIR"

# Incremental backup using rsync
rsync -av --delete \
    "$SOURCE_DIR/" \
    "$BACKUP_DIR/current/"

# Create daily snapshot (hard links for efficiency)
cp -al "$BACKUP_DIR/current" "$BACKUP_DIR/${TIMESTAMP}"

echo "✅ File backup created: $BACKUP_DIR/${TIMESTAMP}"

# Delete old backups
find "$BACKUP_DIR" -maxdepth 1 -name "202*" -type d -mtime +$RETENTION_DAYS -exec rm -rf {} \;
echo "🗑️  Old file backups deleted"
```

### Full System Backup

**Script**: `scripts/backup-full.sh`

```bash
#!/bin/bash
# scripts/backup-full.sh
# Komplettes Backup: DB + Files + Config

set -e

echo "🔄 Starting full backup..."

# 1. Database Backup
./scripts/backup-db.sh

# 2. File Backup
./scripts/backup-files.sh

# 3. Configuration Backup
CONFIG_BACKUP="/var/backups/kvb-admin/config/$(date +%Y%m%d).tar.gz"
tar -czf "$CONFIG_BACKUP" \
    /etc/nginx/sites-available/kvb-admin \
    /etc/systemd/system/kvb-admin.service \
    /app/.env

echo "✅ Full backup completed"

# 4. Upload to remote (optional)
# rclone sync /var/backups/kvb-admin remote:kvb-backups
```

## 🔄 Restore-Prozesse

### Database Restore

**Script**: `scripts/restore-db.sh`

```bash
#!/bin/bash
# scripts/restore-db.sh

set -e

# Usage: ./restore-db.sh <backup-file>
if [ $# -eq 0 ]; then
    echo "Usage: $0 <backup-file.sql.gz>"
    echo ""
    echo "Available backups:"
    ls -lh /var/backups/kvb-admin/db/*.sql.gz | tail -5
    exit 1
fi

BACKUP_FILE="$1"
DB_NAME="kvb_admin"

# Confirmation
echo "⚠️  WARNING: This will restore database from backup!"
echo "   Backup: $BACKUP_FILE"
echo "   Database: $DB_NAME"
read -p "Continue? (yes/no): " CONFIRM

if [ "$CONFIRM" != "yes" ]; then
    echo "Aborted."
    exit 0
fi

# Stop application (avoid writes during restore)
echo "🛑 Stopping application..."
sudo systemctl stop kvb-admin

# Create safety backup of current state
echo "💾 Creating safety backup of current database..."
./scripts/backup-db.sh

# Restore
echo "🔄 Restoring database..."
gunzip -c "$BACKUP_FILE" | psql -U kvb_user -h localhost "$DB_NAME"

echo "✅ Database restored"

# Start application
echo "🚀 Starting application..."
sudo systemctl start kvb-admin

# Health check
sleep 5
curl -f http://localhost:8000/health/ && echo "✅ Application healthy" || echo "❌ Health check failed"
```

### File Restore

```bash
#!/bin/bash
# scripts/restore-files.sh

set -e

# Usage: ./restore-files.sh <backup-date>
if [ $# -eq 0 ]; then
    echo "Usage: $0 <YYYYMMDD>"
    echo ""
    echo "Available backups:"
    ls -d /var/backups/kvb-admin/files/202* | tail -5
    exit 1
fi

BACKUP_DATE="$1"
SOURCE="/var/backups/kvb-admin/files/${BACKUP_DATE}"
TARGET="/app/media"

# Confirmation
echo "⚠️  WARNING: This will restore files from backup!"
echo "   Backup: $SOURCE"
echo "   Target: $TARGET"
read -p "Continue? (yes/no): " CONFIRM

if [ "$CONFIRM" != "yes" ]; then
    echo "Aborted."
    exit 0
fi

# Restore using rsync
rsync -av --delete "$SOURCE/" "$TARGET/"

echo "✅ Files restored from $BACKUP_DATE"
```

### Point-in-Time Recovery

**Für kritische Systeme**: PostgreSQL Continuous Archiving

```bash
# postgresql.conf
wal_level = replica
archive_mode = on
archive_command = 'cp %p /var/lib/postgresql/wal_archive/%f'

# Restore zu bestimmter Zeit
pg_restore --target-time='2025-11-03 14:30:00' ...
```

## 🧪 Backup-Tests

### Regelmäßige Restore-Tests

**Monatlich**: Testweise Restore durchführen

```bash
#!/bin/bash
# scripts/test-restore.sh
# Testet Restore auf Staging-System

set -e

echo "🧪 Testing backup restore on staging..."

# 1. Latest Backup holen
LATEST_BACKUP=$(ls -t /var/backups/kvb-admin/db/*.sql.gz | head -1)
echo "Testing with: $LATEST_BACKUP"

# 2. Restore auf Staging
ssh staging-server << EOF
    # Stop staging app
    sudo systemctl stop kvb-admin-staging

    # Restore backup
    gunzip -c "$LATEST_BACKUP" | psql -U kvb_user kvb_admin_staging

    # Start app
    sudo systemctl start kvb-admin-staging

    # Health check
    curl -f http://localhost:8001/health/
EOF

echo "✅ Restore test successful"
```

## 📊 Backup-Monitoring

### Backup-Status prüfen

```bash
#!/bin/bash
# scripts/check-backups.sh

set -e

BACKUP_DIR="/var/backups/kvb-admin/db"
MAX_AGE_HOURS=25  # Warnung wenn > 25 Stunden alt

# Letztes Backup finden
LATEST_BACKUP=$(ls -t "$BACKUP_DIR"/*.sql.gz | head -1)

if [ -z "$LATEST_BACKUP" ]; then
    echo "❌ No backups found!"
    exit 1
fi

# Alter prüfen
BACKUP_AGE_SECONDS=$(( $(date +%s) - $(stat -c %Y "$LATEST_BACKUP") ))
BACKUP_AGE_HOURS=$(( $BACKUP_AGE_SECONDS / 3600 ))

echo "Latest backup: $LATEST_BACKUP"
echo "Age: $BACKUP_AGE_HOURS hours"

if [ $BACKUP_AGE_HOURS -gt $MAX_AGE_HOURS ]; then
    echo "⚠️  WARNING: Backup is older than $MAX_AGE_HOURS hours!"
    # Optional: Sende Alarm (E-Mail, Slack, etc.)
    exit 1
else
    echo "✅ Backup is recent"
fi
```

**Cron Job** (täglich prüfen):

```bash
# /etc/cron.d/kvb-admin-backup-check
0 10 * * * kvbadmin /app/scripts/check-backups.sh >> /var/log/kvb-admin/backup-check.log 2>&1
```

## 🔐 Backup-Verschlüsselung

### GPG-Verschlüsselung

```bash
#!/bin/bash
# Backup mit GPG-Verschlüsselung

# Backup erstellen und verschlüsseln
pg_dump -U kvb_user kvb_admin | gzip | gpg --encrypt --recipient admin@example.com > backup.sql.gz.gpg

# Entschlüsseln (für Restore)
gpg --decrypt backup.sql.gz.gpg | gunzip | psql -U kvb_user kvb_admin
```

### Encryption at Rest

**Wenn Backup auf Cloud gespeichert**:

```bash
# S3 mit Server-Side Encryption
aws s3 cp backup.sql.gz s3://my-bucket/backups/ --sse AES256

# Oder: Client-Side Encryption (rclone mit crypt)
rclone copy backup.sql.gz encrypted-remote:backups/
```

## 📅 Retention Policy

### Backup-Aufbewahrung

| Backup-Typ | Häufigkeit | Retention |
|------------|------------|-----------|
| **Database (Daily)** | Täglich | 30 Tage |
| **Database (Weekly)** | Sonntag | 12 Wochen |
| **Database (Monthly)** | 1. des Monats | 12 Monate |
| **Files (Daily)** | Täglich | 30 Tage |
| **Files (Weekly)** | Sonntag | 12 Wochen |
| **Config** | Bei Änderung | 12 Monate |

**Beispiel-Script**:

```bash
# Retention-Management
# Daily → 30 Tage
find /var/backups/db/daily -mtime +30 -delete

# Weekly → 12 Wochen (84 Tage)
find /var/backups/db/weekly -mtime +84 -delete

# Monthly → 12 Monate (365 Tage)
find /var/backups/db/monthly -mtime +365 -delete
```

## 🚨 Disaster Recovery

### Kompletter System-Wiederaufbau

**Scenario**: Server total verloren

**Prozess**:

1. **Neuer Server aufsetzen**
   ```bash
   # OS installieren (Ubuntu 22.04)
   # Python, PostgreSQL, nginx installieren
   ```

2. **Application Code wiederherstellen**
   ```bash
   git clone https://github.com/org/kvb-admin.git /app
   cd /app
   git checkout v1.2.3  # Letzte Production-Version
   pip install -r requirements.txt
   ```

3. **Database wiederherstellen**
   ```bash
   # DB erstellen
   createdb kvb_admin

   # Letztes Backup wiederherstellen
   gunzip -c /backups/db/latest.sql.gz | psql kvb_admin
   ```

4. **Files wiederherstellen**
   ```bash
   rsync -av /backups/files/latest/ /app/media/
   ```

5. **Configuration wiederherstellen**
   ```bash
   # .env file
   # nginx config
   # systemd service
   ```

6. **Services starten**
   ```bash
   sudo systemctl start kvb-admin
   sudo systemctl start nginx
   ```

7. **Verifizieren**
   ```bash
   curl http://localhost:8000/health/
   # Manuelle Tests durchführen
   ```

### Recovery Time Objective (RTO) & Recovery Point Objective (RPO)

**RTO** (Wiederherstellungszeit):
- Target: < 4 Stunden
- Komplett-Wiederaufbau: < 1 Tag

**RPO** (Datenverlust):
- Target: < 24 Stunden (tägliche Backups)
- Mit Transaktions-Logs: < 1 Stunde

## 📚 Weiterführende Dokumente

- [Deployment Guide](deployment-guide.md) - Deployment-Prozess
- [Definition of Done](definition-of-done.md) - Backup als Teil von DoD

---

**Zuletzt aktualisiert:** 2025-11-03
