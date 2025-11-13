# PowerShell script to start MongoDB locally (without Docker)

Write-Host "Checking MongoDB installation..." -ForegroundColor Cyan

# Common MongoDB installation paths
$mongoPaths = @(
    "C:\Program Files\MongoDB\Server\*\bin\mongod.exe",
    "C:\Program Files (x86)\MongoDB\Server\*\bin\mongod.exe",
    "$env:LOCALAPPDATA\Programs\MongoDB\*\bin\mongod.exe",
    "$env:ProgramFiles\MongoDB\*\bin\mongod.exe"
)

$mongodPath = $null
foreach ($path in $mongoPaths) {
    $found = Get-ChildItem -Path $path -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($found) {
        $mongodPath = $found.FullName
        Write-Host "[OK] Found MongoDB at: $mongodPath" -ForegroundColor Green
        break
    }
}

# Also check if mongod is in PATH
if (-not $mongodPath) {
    try {
        $mongodPath = (Get-Command mongod -ErrorAction Stop).Source
        Write-Host "[OK] Found MongoDB in PATH: $mongodPath" -ForegroundColor Green
    } catch {
        Write-Host "[ERROR] MongoDB not found!" -ForegroundColor Red
        Write-Host ""
        Write-Host "Please install MongoDB:" -ForegroundColor Yellow
        Write-Host "  1. Download from: https://www.mongodb.com/try/download/community" -ForegroundColor Cyan
        Write-Host "  2. Install MongoDB Community Edition" -ForegroundColor Cyan
        Write-Host "  3. During installation, select 'Install MongoDB as a Service'" -ForegroundColor Cyan
        Write-Host "  4. Or add MongoDB bin folder to PATH" -ForegroundColor Cyan
        Write-Host ""
        Write-Host "  OR use MongoDB Atlas (cloud - no installation needed):" -ForegroundColor Yellow
        Write-Host "  https://www.mongodb.com/cloud/atlas/register" -ForegroundColor Cyan
        exit 1
    }
}

# Create data directory if it doesn't exist
$dataDir = "C:\data\db"
if (-not (Test-Path $dataDir)) {
    Write-Host "Creating data directory: $dataDir" -ForegroundColor Yellow
    New-Item -ItemType Directory -Path $dataDir -Force | Out-Null
}

# Check if MongoDB is already running
$mongoProcess = Get-Process -Name mongod -ErrorAction SilentlyContinue
if ($mongoProcess) {
    Write-Host "[OK] MongoDB is already running (PID: $($mongoProcess.Id))" -ForegroundColor Green
    Write-Host "   MongoDB is ready on localhost:27017" -ForegroundColor Cyan
    exit 0
}

# Start MongoDB
Write-Host "Starting MongoDB..." -ForegroundColor Cyan
Write-Host "   Data directory: $dataDir" -ForegroundColor Gray
Write-Host "   Port: 27017" -ForegroundColor Gray
Write-Host ""

# Start MongoDB in background
$process = Start-Process -FilePath $mongodPath -ArgumentList "--dbpath", "`"$dataDir`"", "--port", "27017" -PassThru -WindowStyle Hidden

# Wait a moment for MongoDB to start
Start-Sleep -Seconds 3

# Check if MongoDB started successfully
if (Get-Process -Id $process.Id -ErrorAction SilentlyContinue) {
    Write-Host "[OK] MongoDB started successfully!" -ForegroundColor Green
    Write-Host "   Process ID: $($process.Id)" -ForegroundColor Gray
    Write-Host "   Running on: localhost:27017" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "To stop MongoDB, run:" -ForegroundColor Yellow
    Write-Host "   Stop-Process -Id $($process.Id)" -ForegroundColor Gray
} else {
    Write-Host "[ERROR] Failed to start MongoDB" -ForegroundColor Red
    Write-Host "   Check if port 27017 is already in use" -ForegroundColor Yellow
}
