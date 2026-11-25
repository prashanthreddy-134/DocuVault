if (!(Test-Path ".env")) { Copy-Item ".env.example" ".env"; Write-Host "Edit .env with your MySQL credentials, then rerun." -ForegroundColor Yellow; exit 1 }
.\.venv\Scripts\Activate.ps1
python manage.py check
python manage.py runserver
