.\.venv\Scripts\Activate.ps1
$env:USE_SQLITE_FOR_TESTS="1"
python manage.py check
python manage.py test
Remove-Item Env:USE_SQLITE_FOR_TESTS
