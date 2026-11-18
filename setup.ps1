# Book Studio setup for Windows (dm-1324). Run from D:\Projects\book-studio in PowerShell:
#   powershell -ExecutionPolicy Bypass -File .\setup.ps1
$ErrorActionPreference = "Stop"
Write-Host "Checking Python..."
python --version
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

Write-Host "Building the sample book to test everything..."
python tools\build_book.py books\cricket-word-search
python tools\build_cover.py books\cricket-word-search
python tools\check_book.py books\cricket-word-search

Write-Host ""
Write-Host "Done. Open books\cricket-word-search\dist\interior.pdf and cover.pdf to look at the sample."
Write-Host "Next (manual): install Kindle Previewer later for ebooks; puzzle paperbacks don't need it."
Write-Host "Weekly batch: add a Task Scheduler task that runs  python tools\batch.py  in this folder."
