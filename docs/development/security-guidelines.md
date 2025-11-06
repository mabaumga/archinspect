# Security Guidelines

Sicherheits-Richtlinien für sichere Software-Entwicklung.

Diese Richtlinien sind framework-agnostisch und gelten für alle Projekte.

## 🎯 Grundprinzipien

1. **Defense in Depth** - Mehrere Sicherheitsebenen
2. **Least Privilege** - Minimale notwendige Rechte
3. **Secure by Default** - Sichere Standardkonfiguration
4. **Fail Securely** - Fehler dürfen keine Sicherheitslücken öffnen
5. **Never Trust User Input** - Alle Eingaben validieren

## 🔐 Input Validation

### Alle Eingaben validieren

```python
# ✅ RICHTIG: Strikte Validierung
from datetime import date
from decimal import Decimal, InvalidOperation

def create_fahrt(km: str, datum: str) -> Fahrt:
    """Validiert alle Eingaben"""
    # 1. Type Validation
    try:
        km_int = int(km)
    except ValueError:
        raise ValueError("KM muss eine Zahl sein")

    # 2. Range Validation
    if km_int < 0:
        raise ValueError("KM dürfen nicht negativ sein")
    if km_int > 10000:
        raise ValueError("KM zu hoch (max 10.000)")

    # 3. Date Validation
    try:
        fahrt_datum = date.fromisoformat(datum)
    except ValueError:
        raise ValueError("Ungültiges Datumsformat (erwarte YYYY-MM-DD)")

    # 4. Business Rules
    if fahrt_datum > date.today():
        raise ValueError("Datum darf nicht in der Zukunft liegen")

    return Fahrt(km=km_int, von=fahrt_datum, ...)

# ❌ FALSCH: Keine Validierung
def create_fahrt_unsafe(km, datum):
    return Fahrt(km=int(km), von=datum)  # Direkt verwendet!
```

### Whitelisting vs. Blacklisting

```python
# ✅ RICHTIG: Whitelist (nur erlaubte Werte)
ALLOWED_PERSONS = {"Marc", "Ingo", "Jan"}

def validate_person(person: str) -> str:
    if person not in ALLOWED_PERSONS:
        raise ValueError(f"Person nicht erlaubt: {person}")
    return person

# ❌ FALSCH: Blacklist (verbotene Zeichen entfernen)
def validate_person_unsafe(person: str) -> str:
    # Versucht gefährliche Zeichen zu entfernen
    return person.replace("'", "").replace(";", "")
    # Problem: Man kann nicht alle gefährlichen Kombinationen kennen
```

## 💉 Injection Prevention

### SQL Injection (wenn direkte SQL-Queries nötig)

```python
# ✅ RICHTIG: Parametrisierte Queries
def find_by_person(person: str):
    query = "SELECT * FROM fahrten WHERE person = ?"
    cursor.execute(query, (person,))  # Parameter-Binding
    return cursor.fetchall()

# ❌ FALSCH: String-Konkatenation
def find_by_person_unsafe(person: str):
    query = f"SELECT * FROM fahrten WHERE person = '{person}'"
    cursor.execute(query)  # SQL Injection möglich!
    # Angriff: person = "Marc'; DROP TABLE fahrten; --"
```

### Command Injection

```python
# ✅ RICHTIG: subprocess mit Liste
import subprocess

def backup_database(db_name: str):
    # Validiere Input
    if not db_name.isalnum():
        raise ValueError("DB-Name darf nur alphanumerisch sein")

    # Nutze Liste (keine Shell)
    subprocess.run(
        ["pg_dump", "-d", db_name, "-f", "backup.sql"],
        check=True,
        shell=False  # Wichtig!
    )

# ❌ FALSCH: Shell-String
def backup_database_unsafe(db_name: str):
    subprocess.run(
        f"pg_dump -d {db_name} -f backup.sql",
        shell=True  # Gefährlich!
    )
    # Angriff: db_name = "test; rm -rf /"
```

### Path Traversal

```python
# ✅ RICHTIG: Path Validation
from pathlib import Path

UPLOAD_DIR = Path("/var/uploads")

def save_file(filename: str, content: bytes):
    # Verhindere Directory Traversal
    safe_path = (UPLOAD_DIR / filename).resolve()

    # Prüfe, dass Pfad innerhalb UPLOAD_DIR liegt
    if not safe_path.is_relative_to(UPLOAD_DIR):
        raise ValueError("Ungültiger Pfad")

    # Weitere Validierung
    if not filename.replace("_", "").replace("-", "").replace(".", "").isalnum():
        raise ValueError("Ungültiger Dateiname")

    safe_path.write_bytes(content)

# ❌ FALSCH: Keine Validierung
def save_file_unsafe(filename: str, content: bytes):
    with open(f"/var/uploads/{filename}", "wb") as f:
        f.write(content)
    # Angriff: filename = "../../../etc/passwd"
```

## 🔑 Secrets Management

### Environment Variables

```python
# ✅ RICHTIG: Secrets aus Environment
import os
from typing import Optional

def get_secret(key: str) -> str:
    """Holt Secret aus Environment"""
    value = os.getenv(key)
    if value is None:
        raise ValueError(f"Secret nicht gesetzt: {key}")
    return value

# Verwendung
DB_PASSWORD = get_secret("DB_PASSWORD")
API_KEY = get_secret("API_KEY")

# ❌ FALSCH: Hardcoded Secrets
DB_PASSWORD = "geheim123"  # NIEMALS!
API_KEY = "sk-1234567890"  # NIEMALS!
```

### .env Files (nie committen!)

```bash
# .env (lokal, nicht in Git!)
DB_PASSWORD=geheim123
API_KEY=sk-1234567890
FINTS_PIN=12345
```

```python
# Laden mit python-dotenv
from dotenv import load_dotenv
import os

load_dotenv()  # Lädt .env
DB_PASSWORD = os.getenv("DB_PASSWORD")
```

**.gitignore**:
```gitignore
.env
.env.local
.env.*.local
secrets.yaml
credentials.json
```

### Secrets nicht loggen

```python
# ✅ RICHTIG: Secrets maskieren
logger.info(f"Connecting to DB user={user} host={host}")
# NICHT loggen: password

# ❌ FALSCH: Secrets in Logs
logger.debug(f"DB connection: {connection_string}")  # Enthält Password!
logger.error(f"API call failed: {api_request}")      # Enthält API Key!
```

## 🛡️ Authentication & Authorization

### Password Hashing

```python
# ✅ RICHTIG: bcrypt/argon2
import bcrypt

def hash_password(password: str) -> str:
    """Hash password mit bcrypt"""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode(), salt).decode()

def verify_password(password: str, hashed: str) -> bool:
    """Verifiziert Password"""
    return bcrypt.checkpw(password.encode(), hashed.encode())

# ❌ FALSCH: Plain-Text oder schwache Hashes
def hash_password_unsafe(password: str) -> str:
    import hashlib
    return hashlib.md5(password.encode()).hexdigest()  # MD5 ist unsicher!
```

### Session Management

```python
# ✅ RICHTIG: Sichere Session-Tokens
import secrets

def generate_session_token() -> str:
    """Generiert kryptographisch sicheren Token"""
    return secrets.token_urlsafe(32)

# ❌ FALSCH: Vorhersagbare Tokens
import random
def generate_session_token_unsafe() -> str:
    return str(random.randint(1000, 9999))  # Vorhersagbar!
```

## 🌐 Web Security

### Cross-Site Scripting (XSS)

```python
# ✅ RICHTIG: Template Engine mit Auto-Escaping
# (Jinja2, Django Templates, etc.)
# Template:
# <p>{{ user_input }}</p>  # Automatisch escaped

# ❌ FALSCH: Manuelles HTML-Building
def render_message_unsafe(message: str) -> str:
    return f"<p>{message}</p>"  # XSS möglich!
    # Angriff: message = "<script>alert('XSS')</script>"
```

### Cross-Site Request Forgery (CSRF)

```python
# ✅ RICHTIG: CSRF-Tokens bei State-Changing Requests
# (Framework-spezifisch - Django, Flask-WTF, etc.)

# In Form:
# <input type="hidden" name="csrf_token" value="{{ csrf_token() }}">

# In View: Framework validiert automatisch

# ❌ FALSCH: Keine CSRF-Protection bei POST/PUT/DELETE
```

### Clickjacking Prevention

```python
# ✅ RICHTIG: X-Frame-Options Header
# (Framework Middleware/Config)
response.headers['X-Frame-Options'] = 'DENY'
# Oder:
response.headers['X-Frame-Options'] = 'SAMEORIGIN'
```

## 📊 Sensitive Data

### Logging

```python
# ✅ RICHTIG: Keine sensitiven Daten in Logs
logger.info(f"User {user_id} logged in")  # OK
logger.debug(f"Processing transaction {transaction_id}")  # OK

# ❌ FALSCH: Sensitive Daten loggen
logger.debug(f"User password: {password}")  # NIEMALS!
logger.info(f"Credit card: {cc_number}")    # NIEMALS!
logger.debug(f"PIN: {pin}")                 # NIEMALS!
```

### Error Messages

```python
# ✅ RICHTIG: Generische Error Messages an User
try:
    authenticate(username, password)
except AuthenticationError as e:
    logger.error(f"Auth failed for {username}: {e}")  # Detailliert in Log
    return "Login fehlgeschlagen"  # Generisch an User

# ❌ FALSCH: Details an User
try:
    authenticate(username, password)
except AuthenticationError as e:
    return f"Fehler: {e}"  # Gibt Angreifer zu viel Information
    # z.B. "User existiert nicht" vs "Passwort falsch"
```

### Daten-Minimierung

```python
# ✅ RICHTIG: Nur notwendige Daten speichern
@dataclass
class User:
    id: str
    email: str
    # NICHT speichern: Passwort (nur Hash), Geburtsdatum (falls nicht nötig), etc.

# API Response: Nur notwendige Felder
def get_user_info(user_id: str) -> dict:
    user = repository.find(user_id)
    return {
        "id": user.id,
        "name": user.name
        # NICHT zurückgeben: password_hash, email, etc.
    }
```

## 🔒 Encryption

### Daten in Transit (HTTPS)

```python
# ✅ RICHTIG: Erzwinge HTTPS
# (Framework/Server Config)
# Redirect HTTP → HTTPS
# HSTS Header setzen

# ❌ FALSCH: Sensitive Daten über HTTP
# Credentials, Tokens, Personal Data nur über HTTPS!
```

### Daten at Rest

```python
# ✅ RICHTIG: Sensitive Daten verschlüsseln
from cryptography.fernet import Fernet

def encrypt_sensitive_data(data: str, key: bytes) -> bytes:
    """Verschlüsselt Daten"""
    f = Fernet(key)
    return f.encrypt(data.encode())

def decrypt_sensitive_data(encrypted: bytes, key: bytes) -> str:
    """Entschlüsselt Daten"""
    f = Fernet(key)
    return f.decrypt(encrypted).decode()

# Key Management: Key aus Environment/Secrets Manager
ENCRYPTION_KEY = get_secret("ENCRYPTION_KEY")
```

## 📦 Dependencies

### Dependency Scanning

```bash
# Prüfe auf bekannte Vulnerabilities
pip install safety
safety check

# Oder: pip-audit
pip install pip-audit
pip-audit
```

### Regelmäßige Updates

```bash
# Dependencies aktualisieren
pip list --outdated

# Update (nach Review!)
pip install --upgrade package-name
```

### Requirements Pinning

```
# requirements.txt
django==4.2.7  # Pinned auf sichere Version
requests>=2.31.0,<3.0  # Mit Mindestversion
```

## 🔍 Code Review Checkliste

Security Checks vor jedem Commit:

- [ ] **Input Validierung** für alle User-Inputs
- [ ] **Keine SQL-Injection** (Parametrisierte Queries)
- [ ] **Keine Command-Injection** (subprocess mit Liste)
- [ ] **Path Traversal** verhindert
- [ ] **Secrets nicht hardcoded** (Environment Variables)
- [ ] **Secrets nicht in Logs**
- [ ] **Error Messages** geben keine sensitiven Details preis
- [ ] **Dependencies** auf Vulnerabilities geprüft
- [ ] **HTTPS** erzwungen (bei Web-Apps)
- [ ] **CSRF-Protection** bei State-Changing Requests

## 🚨 Security Incidents

### Was tun bei Security-Problemen?

1. **Dokumentieren**: Was ist passiert?
2. **Isolieren**: Betroffene Komponente deaktivieren
3. **Fixen**: Patch entwickeln
4. **Testen**: Security-Test für das Problem
5. **Deployen**: Schnellstmöglich
6. **Kommunizieren**: User informieren (falls nötig)
7. **Post-Mortem**: Wie konnte das passieren? Wie verhindern wir das künftig?

## 🛠️ Tools

### Static Analysis

```bash
# Bandit - Python Security Linter
pip install bandit
bandit -r bounded_context/

# Beispiel-Findings:
# - Hardcoded passwords
# - SQL injection risks
# - Weak crypto
```

### Dependency Scanning

```bash
# Safety
pip install safety
safety check

# pip-audit
pip install pip-audit
pip-audit
```

## 📚 OWASP Top 10

Awareness für die häufigsten Web-Vulnerabilities:

1. **Broken Access Control** - Unzureichende Autorisierung
2. **Cryptographic Failures** - Schwache Verschlüsselung
3. **Injection** - SQL, Command, etc.
4. **Insecure Design** - Fehlende Security in Architektur
5. **Security Misconfiguration** - Default Passwords, etc.
6. **Vulnerable Components** - Veraltete Dependencies
7. **Authentication Failures** - Schwache Auth
8. **Data Integrity Failures** - Unsignierte/unverifizierte Daten
9. **Logging Failures** - Keine/unzureichende Logs
10. **Server-Side Request Forgery (SSRF)** - Unvalidierte URLs

**Ressource**: https://owasp.org/Top10/

## 📚 Weiterführende Dokumente

- [Coding Standards](coding-standards.md) - Code-Qualität
- [Definition of Done](../processes/definition-of-done.md) - Security Checkliste
- [Deployment Guide](../processes/deployment-guide.md) - Production Security

---

**Zuletzt aktualisiert:** 2025-11-03
