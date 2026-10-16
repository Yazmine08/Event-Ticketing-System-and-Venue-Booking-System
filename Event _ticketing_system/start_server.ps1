# ======================================================================
#   EVENT TICKETING & VENUE BOOKING SYSTEM - RESTful WEB API
#   Course: SWC3633 / SWC4443 Web API Development
#   Universiti Poly-Tech Malaysia (UPTM)
# ======================================================================

Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host "   EVENT TICKETING & VENUE BOOKING SYSTEM - RESTful WEB API" -ForegroundColor Green
Write-Host "   Course: SWC3633 / SWC4443 Web API Development (UPTM)" -ForegroundColor Yellow
Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host ""

Set-Location $PSScriptRoot
$folderName = Split-Path -Leaf $PSScriptRoot
Write-Host "[INFO] Project Folder: $PSScriptRoot" -ForegroundColor Gray

# Check if port 8000 is already active
$portActive = Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue
if ($portActive) {
    Write-Host ""
    Write-Host "[SUCCESS] The Backend Server is ALREADY RUNNING on http://127.0.0.1:8000!" -ForegroundColor Green
    Write-Host "[INFO] XAMPP Hub:   http://localhost/$folderName/" -ForegroundColor Cyan
    Write-Host "[INFO] Direct App:  http://127.0.0.1:8000" -ForegroundColor Yellow
    Write-Host "[INFO] Swagger:     http://127.0.0.1:8000/docs" -ForegroundColor Yellow
    Write-Host ""
    return
}

Write-Host "[INFO] Starting RESTful API Server on http://127.0.0.1:8000 ..." -ForegroundColor Cyan
Write-Host "[INFO] XAMPP Hub:    http://localhost/$folderName/" -ForegroundColor Green
Write-Host "[INFO] Direct App:   http://127.0.0.1:8000" -ForegroundColor Green
Write-Host "[INFO] Swagger Docs: http://127.0.0.1:8000/docs" -ForegroundColor Yellow
Write-Host "[INFO] ReDoc Docs:   http://127.0.0.1:8000/redoc" -ForegroundColor Yellow
Write-Host ""

python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload
