# Installation and Setup Scripts

## install-dependencies.ps1
PowerShell script to install all project dependencies on Windows.

## start-all.js
Node.js script to start both backend and frontend services for development.

## test-receipt.py
Python script to test receipt parsing functionality.

## database-setup.py
Python script to initialize the database and create sample data.

## Usage

### Install Dependencies
```powershell
.\scripts\install-dependencies.ps1
```

### Start Development Environment
```bash
npm run dev
# or
node scripts/start-all.js
```

### Test Receipt Parsing
```bash
cd backend
python scripts/test-receipt.py
```

### Setup Database
```bash
cd backend
python scripts/database-setup.py
```
