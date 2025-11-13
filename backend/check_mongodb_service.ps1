# Check if MongoDB service exists and start it

Write-Host "Checking MongoDB service..." -ForegroundColor Cyan

# Check for MongoDB service
$service = Get-Service -Name "MongoDB" -ErrorAction SilentlyContinue

if ($service) {
    Write-Host "[OK] MongoDB service found!" -ForegroundColor Green
    Write-Host "   Status: $($service.Status)" -ForegroundColor Gray
    
    if ($service.Status -eq "Running") {
        Write-Host "[OK] MongoDB is already running!" -ForegroundColor Green
        Write-Host "   MongoDB is ready on localhost:27017" -ForegroundColor Cyan
    } else {
        Write-Host "Starting MongoDB service..." -ForegroundColor Yellow
        try {
            Start-Service -Name "MongoDB"
            Start-Sleep -Seconds 3
            $service.Refresh()
            if ($service.Status -eq "Running") {
                Write-Host "[OK] MongoDB service started successfully!" -ForegroundColor Green
                Write-Host "   MongoDB is ready on localhost:27017" -ForegroundColor Cyan
            } else {
                Write-Host "[ERROR] Failed to start MongoDB service" -ForegroundColor Red
                Write-Host "   Try running PowerShell as Administrator" -ForegroundColor Yellow
            }
        } catch {
            Write-Host "[ERROR] Cannot start service: $_" -ForegroundColor Red
            Write-Host "   Try running PowerShell as Administrator" -ForegroundColor Yellow
        }
    }
} else {
    Write-Host "[ERROR] MongoDB service not found" -ForegroundColor Red
    Write-Host ""
    Write-Host "MongoDB is not installed as a Windows service." -ForegroundColor Yellow
    Write-Host "Please install MongoDB:" -ForegroundColor Yellow
    Write-Host "  1. Download: https://www.mongodb.com/try/download/community" -ForegroundColor Cyan
    Write-Host "  2. During installation, select 'Install MongoDB as a Service'" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "OR use MongoDB Atlas (cloud - easier):" -ForegroundColor Yellow
    Write-Host "  https://www.mongodb.com/cloud/atlas/register" -ForegroundColor Cyan
}

