$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $MyInvocation.MyCommand.Path

Write-Host "Starting KeenFox backend..." -ForegroundColor Cyan
Start-Process powershell -ArgumentList "-NoExit", "-Command", "Set-Location '$root\backend'; & '$root\backend\venv\Scripts\python.exe' app.py"

Write-Host "Starting KeenFox frontend..." -ForegroundColor Cyan
Start-Process powershell -ArgumentList "-NoExit", "-Command", "Set-Location '$root\frontend'; $env:PORT='3001'; npm start"

Write-Host "Opening app on http://localhost:3001" -ForegroundColor Green
Start-Process "http://localhost:3001"
