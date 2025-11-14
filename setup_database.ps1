# Health AI - PostgreSQL Setup Script
# Run this script to set up your database

Write-Host "============================================" -ForegroundColor Cyan
Write-Host "   Health AI - PostgreSQL Setup" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

# Add PostgreSQL to PATH
$env:Path += ";C:\Program Files\PostgreSQL\18\bin"

# Get PostgreSQL password
Write-Host "Enter your PostgreSQL password (set during installation):" -ForegroundColor Yellow
$password = Read-Host -AsSecureString
$passwordPlain = [Runtime.InteropServices.Marshal]::PtrToStringAuto([Runtime.InteropServices.Marshal]::SecureStringToBSTR($password))

Write-Host ""
Write-Host "Step 1: Testing PostgreSQL connection..." -ForegroundColor Green

# Test connection
$env:PGPASSWORD = $passwordPlain
$testResult = psql -U postgres -c "SELECT version();" 2>&1

if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ PostgreSQL connection successful!" -ForegroundColor Green
} else {
    Write-Host "❌ Connection failed. Please check your password." -ForegroundColor Red
    Write-Host "Error: $testResult" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "Step 2: Creating database 'healthai'..." -ForegroundColor Green

# Check if database exists
$dbExists = psql -U postgres -tAc "SELECT 1 FROM pg_database WHERE datname='healthai'" 2>&1

if ($dbExists -eq "1") {
    Write-Host "⚠️  Database 'healthai' already exists" -ForegroundColor Yellow
} else {
    # Create database
    psql -U postgres -c "CREATE DATABASE healthai;" 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Database 'healthai' created successfully!" -ForegroundColor Green
    } else {
        Write-Host "❌ Failed to create database" -ForegroundColor Red
        exit 1
    }
}

Write-Host ""
Write-Host "Step 3: Updating .env file..." -ForegroundColor Green

# Update .env file
$envPath = ".env"
$envContent = Get-Content $envPath -Raw

# Create new DATABASE_URL
$newDatabaseUrl = "DATABASE_URL=postgresql://postgres:$passwordPlain@localhost:5432/healthai"

# Check if DATABASE_URL exists
if ($envContent -match "DATABASE_URL=") {
    $envContent = $envContent -replace "DATABASE_URL=.*", $newDatabaseUrl
} else {
    $envContent += "`n`n# PostgreSQL Database Configuration`n"
    $envContent += "# Format: postgresql://username:password@localhost:5432/database_name`n"
    $envContent += $newDatabaseUrl
}

Set-Content -Path $envPath -Value $envContent
Write-Host "✅ .env file updated with DATABASE_URL" -ForegroundColor Green

Write-Host ""
Write-Host "Step 4: Installing Python SQL packages..." -ForegroundColor Green

# Activate virtual environment and install packages
& .\.venv\Scripts\Activate.ps1
pip install psycopg2-binary==2.9.9 SQLAlchemy==2.0.23 --quiet

if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Python packages installed" -ForegroundColor Green
} else {
    Write-Host "⚠️  Package installation had issues, but continuing..." -ForegroundColor Yellow
}

Write-Host ""
Write-Host "Step 5: Testing database connection from Python..." -ForegroundColor Green

# Test Python connection
python backend/app/database.py

Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "   Setup Complete!" -ForegroundColor Green
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "  1. Run migration: python backend/migrate_to_sql.py" -ForegroundColor White
Write-Host "  2. This will transfer all data from JSON/CSV to SQL" -ForegroundColor White
Write-Host "  3. Test the SQL versions of your code" -ForegroundColor White
Write-Host ""
Write-Host "Need help? Check SQL_SETUP_GUIDE.md" -ForegroundColor Cyan
