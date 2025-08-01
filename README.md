# Hybrid Loyalty Enrollment System

A modern customer loyalty and point tracking system that integrates non-invasively with existing legacy POS software for textile retail environments.

## 🏗️ Architecture

- **Backend**: Python FastAPI server with WebSocket support
- **Desktop App**: Electron.js application for cashier interface
- **Tablet UI**: Browser-based customer interface
- **Database**: PostgreSQL/SQLite for customer and transaction data
- **Receipt Monitoring**: Python daemon for print stream parsing

## 📁 Project Structure

```
tienda-software-project/
├── backend/                 # Python FastAPI backend server
│   ├── app/
│   ├── requirements.txt
│   └── main.py
├── electron-app/           # Electron desktop application
│   ├── src/
│   ├── package.json
│   └── main.js
├── tablet-ui/             # Browser-based tablet interface
│   ├── static/
│   ├── index.html
│   └── app.js
├── scripts/               # Utility and deployment scripts
└── docs/                  # Documentation
```

## 🚀 Quick Start

### Prerequisites
- Python 3.9+
- Node.js 18+
- PostgreSQL (optional, SQLite by default)

### Backend Setup
```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Electron App Setup
```bash
cd electron-app
npm install
npm run dev
```

### Tablet UI
Access via browser: `http://localhost:8000/tablet`

## 📋 Features

- ✅ Non-invasive POS integration
- ✅ Real-time receipt monitoring
- ✅ Customer barcode/QR scanning
- ✅ WebSocket-based UI synchronization
- ✅ Loyalty points calculation
- ✅ Customer registration interface
- ✅ Admin dashboard for cashiers

## 🔧 Development Phases

- **Phase 1**: Core framework setup ✅
- **Phase 2**: Integration and WebSocket syncing
- **Phase 3**: Polish, animations, and deployment

## 📖 Documentation

See the `docs/` folder for detailed technical specifications and API documentation.
