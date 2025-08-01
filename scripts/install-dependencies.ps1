# PowerShell script to install all dependencies for Tienda Loyalty System

Write-Host "🏪 Installing Tienda Loyalty System Dependencies" -ForegroundColor Cyan
Write-Host "=" * 50

# Check if Python is installed
Write-Host "Checking Python installation..." -ForegroundColor Yellow
try {
    $pythonVersion = python --version 2>&1
    Write-Host "✅ Found: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ Python not found. Please install Python 3.9+ first." -ForegroundColor Red
    exit 1
}

# Check if Node.js is installed
Write-Host "Checking Node.js installation..." -ForegroundColor Yellow
try {
    $nodeVersion = node --version 2>&1
    Write-Host "✅ Found Node.js: $nodeVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ Node.js not found. Please install Node.js 18+ first." -ForegroundColor Red
    exit 1
}

# Install Python dependencies
Write-Host "`n📦 Installing Python backend dependencies..." -ForegroundColor Yellow
Set-Location "backend"
python -m pip install --upgrade pip
pip install -r requirements.txt

if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Python dependencies installed successfully" -ForegroundColor Green
} else {
    Write-Host "❌ Failed to install Python dependencies" -ForegroundColor Red
    exit 1
}

# Copy environment file
if (-not (Test-Path ".env")) {
    Copy-Item ".env.example" ".env"
    Write-Host "✅ Created .env file from example" -ForegroundColor Green
}

Set-Location ".."

# Install Node.js dependencies for main project
Write-Host "`n📦 Installing main project dependencies..." -ForegroundColor Yellow
npm install

if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Main project dependencies installed successfully" -ForegroundColor Green
} else {
    Write-Host "❌ Failed to install main project dependencies" -ForegroundColor Red
    exit 1
}

# Install Electron app dependencies
Write-Host "`n🖥️  Installing Electron app dependencies..." -ForegroundColor Yellow
Set-Location "electron-app"
npm install

if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Electron app dependencies installed successfully" -ForegroundColor Green
} else {
    Write-Host "❌ Failed to install Electron app dependencies" -ForegroundColor Red
    exit 1
}

Set-Location ".."

Write-Host "`n🎉 Installation completed successfully!" -ForegroundColor Green
Write-Host "`nNext steps:" -ForegroundColor Cyan
Write-Host "1. Start the development environment: npm run dev" -ForegroundColor White
Write-Host "2. Access the cashier interface via the Electron app" -ForegroundColor White
Write-Host "3. Access the tablet interface at: http://localhost:8000/tablet" -ForegroundColor White
Write-Host "4. View API documentation at: http://localhost:8000/docs" -ForegroundColor White

Write-Host "`n📖 For more information, see README.md and docs/API.md" -ForegroundColor Yellow
