# Tienda Loyalty System - Technical Documentation

## API Documentation

### Base URL
```
http://localhost:8000
```

### Endpoints

#### Customers

**GET /api/customers**
- List all customers
- Query parameters:
  - `skip`: Number of records to skip (default: 0)
  - `limit`: Maximum number of records (default: 100)
  - `search`: Search term for name, email, or phone

**POST /api/customers**
- Create a new customer
- Body:
```json
{
  "name": "John Doe",
  "email": "john@example.com",
  "phone": "555-1234",
  "notes": "VIP customer"
}
```

**GET /api/customers/{customer_id}**
- Get customer by ID

**GET /api/customers/barcode/{barcode}**
- Get customer by barcode

**PUT /api/customers/{customer_id}**
- Update customer information

**DELETE /api/customers/{customer_id}**
- Delete customer

#### Purchases

**GET /api/purchases**
- List all purchases
- Query parameters:
  - `skip`, `limit`: Pagination
  - `customer_id`: Filter by customer
  - `start_date`, `end_date`: Date range filter

**POST /api/purchases**
- Create a new purchase
- Body:
```json
{
  "customer_id": "uuid",
  "receipt_id": "REC123",
  "amount": 45.99,
  "receipt_text": "Raw receipt content",
  "items_count": 3
}
```

**GET /api/purchases/{purchase_id}**
- Get purchase by ID

**GET /api/purchases/customer/{customer_id}**
- Get all purchases for a customer

**GET /api/purchases/stats/{customer_id}**
- Get purchase statistics for a customer

**POST /api/purchases/process-barcode-purchase**
- Process purchase from barcode scan and receipt data

#### Admin

**GET /api/admin/stats**
- Get system-wide statistics

**GET /api/admin/health**
- Health check endpoint

**GET /api/admin/recent-activity**
- Get recent system activity

**POST /api/admin/test-receipt**
- Test receipt parsing
- Body:
```json
{
  "receipt_text": "Raw receipt content to parse"
}
```

### WebSocket Events

#### Tablet WebSocket (`/ws/tablet`)

**Client to Server:**
- `submit_customer_form`: Submit customer registration data
- `reset_to_idle`: Reset tablet to idle state
- `heartbeat`: Keep connection alive

**Server to Client:**
- `show_registration_form`: Display registration form
- `show_confirmation`: Show confirmation message
- `show_error`: Display error message
- `show_customer_info`: Display customer information
- `show_purchase_complete`: Show purchase completion
- `set_state`: Change tablet state

#### Electron WebSocket (`/ws/electron`)

**Client to Server:**
- `start_registration`: Start customer registration
- `customer_scanned`: Customer barcode scanned
- `receipt_processed`: Receipt processing complete
- `reset_tablet`: Reset tablet to idle

**Server to Client:**
- `process_customer_registration`: Process new customer
- `process_purchase`: Process customer purchase
- `registration_started`: Registration initiated
- `tablet_reset`: Tablet state reset

## Database Schema

### customers
- `id`: UUID primary key
- `name`: Customer full name
- `email`: Email address (optional)
- `phone`: Phone number (optional)
- `barcode_data`: Unique barcode string
- `joined_at`: Registration timestamp
- `updated_at`: Last update timestamp
- `notes`: Additional notes

### purchases
- `id`: UUID primary key
- `customer_id`: Foreign key to customers
- `receipt_id`: POS receipt number
- `timestamp`: Purchase timestamp
- `amount`: Purchase amount (decimal)
- `points_awarded`: Loyalty points earned
- `receipt_text`: Raw receipt content
- `items_count`: Number of items purchased
- `processed_at`: Processing timestamp

### scan_events
- `id`: UUID primary key
- `customer_id`: Foreign key to customers (optional)
- `barcode_data`: Scanned barcode
- `scanned_at`: Scan timestamp
- `is_matched`: Whether matched to purchase
- `cashier_station`: Station identifier

## Configuration

### Environment Variables

Create a `.env` file in the backend directory:

```env
# Database
DATABASE_URL=sqlite+aiosqlite:///./loyalty_system.db

# Receipt monitoring
RECEIPT_MONITOR_ENABLED=true
RECEIPT_FOLDER_PATH=C:/Windows/System32/spool/PRINTERS
RECEIPT_MATCH_WINDOW_SECONDS=30

# Security
SECRET_KEY=your-secret-key-change-in-production

# Loyalty points
POINTS_PER_DOLLAR=1
BONUS_THRESHOLD_100=10
BONUS_THRESHOLD_250=25
BONUS_THRESHOLD_500=50

# Tablet UI
TABLET_IDLE_TIMEOUT_SECONDS=30
TABLET_FORM_TIMEOUT_SECONDS=120
```

## Receipt Parsing

The system monitors receipt files and parses them using configurable patterns:

### Supported Patterns
- **Total Amount**: `TOTAL: $45.99`, `Total: 45.99`
- **Receipt ID**: `Receipt #: ABC123`, `Transaction #: 456789`
- **Date/Time**: `01/15/2024 14:30:25`

### File Monitoring
- Monitors: `.txt`, `.prn`, `.spl`, `.log` files
- Location: Configurable print spool directory
- Encoding: Auto-detects UTF-8, CP1252, ASCII

### Matching Logic
- Customer scan must occur within 30 seconds of receipt
- Uses timestamp anchoring for reliable matching
- Supports multiple receipt formats

## Development

### Prerequisites
- Python 3.9+
- Node.js 18+
- PostgreSQL (optional)

### Setup
1. Install dependencies: `npm run install:all`
2. Start development: `npm run dev`
3. Access interfaces:
   - Cashier: Electron app opens automatically
   - Tablet: http://localhost:8000/tablet
   - API: http://localhost:8000/docs

### Testing
- Backend: `cd backend && python -m pytest`
- Receipt parsing: `python scripts/test-receipt.py`
- WebSocket: Use browser dev tools on tablet interface

## Deployment

### Production Setup
1. Set up PostgreSQL database
2. Configure environment variables
3. Build Electron app: `cd electron-app && npm run build`
4. Run backend with production WSGI server
5. Set up reverse proxy for tablet interface

### Hardware Requirements
- Main PC: Windows 10+, 4GB RAM, receipt printer
- Tablet: Any device with modern web browser
- Network: Local network connecting main PC and tablet

## Troubleshooting

### Common Issues

**Backend won't start:**
- Check Python version: `python --version`
- Install dependencies: `pip install -r requirements.txt`
- Check port 8000 availability

**Electron app connection failed:**
- Verify backend is running on port 8000
- Check firewall settings
- Ensure WebSocket connections allowed

**Receipt parsing not working:**
- Verify receipt folder path in settings
- Check file permissions
- Test with sample receipt using test endpoint

**Tablet interface blank:**
- Check browser console for errors
- Verify WebSocket connection
- Clear browser cache

### Logs
- Backend: Console output and app logs
- Electron: Dev tools console
- Tablet: Browser dev tools

## Security Considerations

### Data Protection
- Customer data encrypted at rest
- No sensitive data in WebSocket messages
- Barcode data is anonymized

### Network Security
- Use HTTPS in production
- Secure WebSocket connections (WSS)
- Firewall rules for tablet access

### Access Control
- Admin interface requires authentication
- Tablet interface is read-only for customers
- Audit logging for all transactions
