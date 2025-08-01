# 🏪 Tienda Loyalty System - Setup Instructions

## Quick Start Guide

Follow these steps to get your Tienda Loyalty System up and running:

### Prerequisites

Before you begin, ensure you have the following installed:

- **Python 3.9+** - [Download from python.org](https://www.python.org/downloads/)
- **Node.js 18+** - [Download from nodejs.org](https://nodejs.org/)
- **Git** - [Download from git-scm.com](https://git-scm.com/)
- **VS Code** (recommended) - [Download from code.visualstudio.com](https://code.visualstudio.com/)

### Installation

1. **Open the project in VS Code**
   ```bash
   code tienda-loyalty-system.code-workspace
   ```

2. **Install all dependencies automatically**
   - Press `Ctrl+Shift+P` (or `Cmd+Shift+P` on Mac)
   - Type "Tasks: Run Task"
   - Select "🏪 Install All Dependencies"
   
   Or run manually:
   ```powershell
   .\scripts\install-dependencies.ps1
   ```

3. **Start the development environment**
   - Press `Ctrl+Shift+P`
   - Type "Tasks: Run Task"
   - Select "🚀 Start Development Environment"
   
   Or run manually:
   ```bash
   npm run dev
   ```

### What Gets Started

When you run the development environment, the following services start automatically:

1. **Python Backend** - `http://localhost:8000`
   - FastAPI server with WebSocket support
   - Receipt monitoring and parsing
   - Database management

2. **Electron Cashier App** - Desktop application window
   - Cashier interface for POS operators
   - Customer registration controls
   - Barcode scanning interface

3. **Tablet Customer Interface** - `http://localhost:8000/tablet`
   - Customer-facing registration forms
   - Purchase confirmation screens
   - Animated idle screen

### Accessing the System

Once everything is running:

- 📊 **API Documentation**: http://localhost:8000/docs
- 📱 **Tablet Interface**: http://localhost:8000/tablet
- 🖥️ **Cashier Interface**: Electron app window
- ⚡ **API Health Check**: http://localhost:8000/health

### Testing the System

1. **Test Customer Registration**:
   - Click "Register New Customer" in the Electron app
   - Fill out the form on the tablet interface
   - Customer gets a unique barcode

2. **Test Customer Scanning**:
   - Click "Scan Customer Barcode" in Electron app
   - Enter or scan a customer's barcode
   - System identifies the customer

3. **Test Receipt Processing**:
   - Use the admin panel to test receipt parsing
   - POST to `/api/admin/test-receipt` with sample receipt text

### Development Workflow

#### VS Code Tasks
- `🏪 Install All Dependencies` - Install Python and Node.js dependencies
- `🚀 Start Development Environment` - Start all services
- `🐍 Start Backend Only` - Run just the Python backend
- `🖥️ Start Electron App Only` - Run just the Electron app
- `🧪 Test Receipt Parser` - Test receipt parsing functionality
- `📦 Build Electron App` - Build production Electron app

#### Debug Configurations
- `🐍 Debug Backend` - Debug the Python FastAPI backend
- `🖥️ Debug Electron Main Process` - Debug the Electron main process

### File Structure

```
tienda-software-project/
├── backend/                 # Python FastAPI backend
│   ├── app/
│   │   ├── models/         # Database models
│   │   ├── routes/         # API routes
│   │   ├── services/       # Business logic
│   │   └── utils/          # Utility functions
│   ├── main.py             # FastAPI application entry point
│   └── requirements.txt    # Python dependencies
├── electron-app/           # Electron desktop application
│   ├── src/
│   │   ├── main/          # Main process
│   │   └── renderer/      # Renderer process (UI)
│   └── package.json
├── tablet-ui/             # Browser-based tablet interface
│   ├── static/
│   └── index.html
├── docs/                  # Documentation
├── scripts/              # Utility scripts
└── README.md
```

### Configuration

#### Environment Variables
Copy `backend/.env.development` to `backend/.env` and modify as needed:

- `DATABASE_URL` - Database connection string
- `RECEIPT_FOLDER_PATH` - Path to monitor for receipt files
- `RECEIPT_MATCH_WINDOW_SECONDS` - Time window for matching receipts to customers

#### Receipt Monitoring
The system monitors the Windows print spool directory by default:
```
C:/Windows/System32/spool/PRINTERS
```

For different POS systems, you may need to:
1. Update the `RECEIPT_FOLDER_PATH` in `.env`
2. Modify receipt parsing patterns in `app/utils/receipt_parser.py`

### Deployment

#### For Production
1. Set up a PostgreSQL database
2. Update `DATABASE_URL` in `.env`
3. Set `DEBUG=false`
4. Use a proper web server (nginx + uvicorn)
5. Build the Electron app: `npm run build`

#### Security Considerations
- Change the `SECRET_KEY` in production
- Implement proper authentication
- Use HTTPS for all communications
- Secure the database connection

### Troubleshooting

#### Common Issues

**Python dependencies fail to install:**
- Ensure Python 3.9+ is installed and in PATH
- Try running: `python -m pip install --upgrade pip`

**Node.js dependencies fail to install:**
- Ensure Node.js 18+ is installed
- Clear npm cache: `npm cache clean --force`

**Electron app won't start:**
- Check that backend is running first
- Verify port 8000 is not in use by another service

**Tablet interface not loading:**
- Check browser console for errors
- Ensure WebSocket connection is working
- Verify backend WebSocket endpoint is accessible

**Receipt monitoring not working:**
- Check that `RECEIPT_FOLDER_PATH` exists and is accessible
- Verify Windows print spooler service is running
- Test with manual receipt files first

#### Getting Help

1. Check the logs in the terminal where services are running
2. Review the API documentation at `/docs`
3. Use VS Code debugger to step through code
4. Check WebSocket connections in browser developer tools

### Hardware Setup

#### Recommended Hardware
- **Main Computer**: Windows 10/11 PC with 8GB+ RAM
- **Receipt Printer**: Any Windows-compatible thermal printer
- **Barcode Scanner**: USB barcode scanner (plug-and-play)
- **Customer Tablet**: Android tablet or Windows tablet with Chrome browser
- **Network**: Local WiFi network for tablet connection

#### Physical Setup
1. Connect receipt printer to main computer via USB
2. Install printer drivers and test printing
3. Connect barcode scanner to main computer
4. Set up tablet on counter, connect to WiFi
5. Navigate tablet browser to `http://[main-computer-ip]:8000/tablet`
6. Enable kiosk mode on tablet for fullscreen experience

### Next Steps

Once your system is running:
1. Customize receipt parsing patterns for your POS system
2. Adjust loyalty points calculation rules
3. Brand the tablet interface with your store colors/logo
4. Set up customer rewards and promotional campaigns
5. Configure backup and data export procedures

Happy selling! 🛍️
