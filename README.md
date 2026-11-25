# DocuVault — Document Management System

A Django 4.2 + MySQL document repository for the PY-EN-005 internship task.

## Implemented
- User registration, login and logout
- Document upload with metadata, categories and comma-separated tags
- Version history and current-version replacement
- Owner-based access plus per-user view/edit/download/share permissions
- Expiring document shares and revocation
- Search by title, description, category and tags; category/status filters
- Audit log for upload, view, download, edit, version and access/share changes
- PDF/image/text preview; download tracking
- Comments, favorites, dashboard, Django admin
- Responsive Bootstrap 5 interface

## Windows setup
1. Install Python 3.10+ and MySQL 8.
2. Create a database and user in MySQL:
   ```sql
   CREATE DATABASE doc_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
   CREATE USER 'doc_user'@'localhost' IDENTIFIED BY 'Choose-A-Strong-Password';
   GRANT ALL PRIVILEGES ON doc_db.* TO 'doc_user'@'localhost';
   FLUSH PRIVILEGES;
   ```
3. Open this folder in PowerShell:
   ```powershell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   python -m pip install --upgrade pip
   pip install -r requirements.txt
   Copy-Item .env.example .env
   ```
4. Edit `.env` with the MySQL username/password and a unique `SECRET_KEY`.
5. Create and apply the database schema:
   ```powershell
   python manage.py makemigrations docs
   python manage.py migrate
   python manage.py createsuperuser
   ```
6. Run checks and tests:
   ```powershell
   python manage.py check
   python manage.py test
   ```
7. Start the site:
   ```powershell
   python manage.py runserver
   ```
   Open http://127.0.0.1:8000

## Test without MySQL (SQLite test mode)
Set `USE_SQLITE_FOR_TESTS=1` for the test process:
```powershell
$env:USE_SQLITE_FOR_TESTS="1"
python manage.py makemigrations docs
python manage.py test
Remove-Item Env:USE_SQLITE_FOR_TESTS
```
The normal application configuration uses MySQL. SQLite mode is only for isolated automated tests.

## Notes
- Uploaded files are stored under `media/`; back up this directory with the database.
- The document extension allow-list is in `docs/models.py`. For production, add malware scanning, content-signature validation, private object storage and HTTPS.
- `DEBUG=True` is for local development only. Set `DEBUG=False`, configure secure cookies/HTTPS and a strong secret before production.
- The provided test suite covers login protection, upload/versioning, search, permissions, sharing, favorites, comments, audit records, preview and download.
