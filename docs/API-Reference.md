# API Documentation

## Tienda Loyalty System API

The Tienda Loyalty System provides a REST API for managing customers, purchases, and loyalty points. The API is built with FastAPI and includes real-time WebSocket communication for tablet and Electron app integration.

### Base URL
```
http://localhost:8000
```

### Authentication
Currently, the API does not require authentication for development. In production, implement proper authentication mechanisms.

## Endpoints

### Health Check
- **GET** `/health` - Check API health status
- **GET** `/` - Root endpoint with API information

### Customer Management

#### Create Customer
- **POST** `/api/customers/`
- **Body:**
```json
{
  "name": "John Doe",
  "email": "john@example.com",
  "phone": "(555) 123-4567",
  "notes": "VIP customer"
}
```

#### Get Customer
- **GET** `/api/customers/{customer_id}`
- **GET** `/api/customers/barcode/{barcode}`

#### List Customers
- **GET** `/api/customers/?skip=0&limit=100&search=john`

#### Update Customer
- **PUT** `/api/customers/{customer_id}`

#### Delete Customer
- **DELETE** `/api/customers/{customer_id}`

### Purchase Management

#### Create Purchase
- **POST** `/api/purchases/`
- **Body:**
```json
{
  "customer_id": "uuid-here",
  "receipt_id": "RCP123456",
  "amount": 29.99,
  "receipt_text": "Raw receipt content...",
  "items_count": 3
}
```

#### Process Barcode Purchase
- **POST** `/api/purchases/process-barcode-purchase`
- **Body:**
```json
{
  "barcode": "CUSTOMER123",
  "receipt_data": {
    "total": 29.99,
    "receipt_id": "RCP123456",
    "raw_text": "Receipt content...",
    "items_count": 3
  }
}
```

#### Get Purchase
- **GET** `/api/purchases/{purchase_id}`

#### Get Customer Purchases
- **GET** `/api/purchases/customer/{customer_id}?skip=0&limit=50`

#### Get Customer Purchase Statistics
- **GET** `/api/purchases/stats/{customer_id}`

#### List Purchases
- **GET** `/api/purchases/?skip=0&limit=100&customer_id=uuid&start_date=2024-01-01&end_date=2024-12-31`

### Admin & System

#### System Statistics
- **GET** `/api/admin/stats`

#### Recent Activity
- **GET** `/api/admin/recent-activity?limit=20`

#### Test Receipt Parsing
- **POST** `/api/admin/test-receipt`
- **Body:**
```json
{
  "receipt_text": "TOTAL: $29.99\nReceipt #123456"
}
```

#### Export Data
- **GET** `/api/admin/export-data?format=json&include_customers=true&include_purchases=true`

### WebSocket Endpoints

#### Tablet Communication
- **WebSocket** `/ws/tablet`
- Used for real-time communication with customer-facing tablet interface

#### Electron App Communication
- **WebSocket** `/ws/electron`
- Used for real-time communication with cashier Electron app

### WebSocket Message Format

#### From Tablet
```json
{
  "action": "submit_customer_form",
  "data": {
    "name": "John Doe",
    "email": "john@example.com",
    "phone": "(555) 123-4567"
  }
}
```

#### To Tablet
```json
{
  "action": "show_registration_form",
  "fields": ["name", "email", "phone"],
  "title": "New Customer Registration",
  "timeout": 120
}
```

#### From Electron
```json
{
  "action": "start_registration",
  "timestamp": "2024-01-01T12:00:00Z"
}
```

#### To Electron
```json
{
  "action": "customer_scanned",
  "barcode": "CUSTOMER123",
  "customer": {
    "id": "uuid-here",
    "name": "John Doe",
    "barcode_data": "CUSTOMER123"
  }
}
```

## Error Responses

All endpoints return standard HTTP status codes:

- `200` - Success
- `201` - Created
- `400` - Bad Request
- `404` - Not Found
- `422` - Validation Error
- `500` - Internal Server Error

Error response format:
```json
{
  "detail": "Error message here"
}
```

## Data Models

### Customer
```json
{
  "id": "uuid",
  "name": "string",
  "email": "string|null",
  "phone": "string|null",
  "barcode_data": "string",
  "barcode_image": "data:image/png;base64,...",
  "joined_at": "2024-01-01T12:00:00Z",
  "updated_at": "2024-01-01T12:00:00Z",
  "notes": "string|null"
}
```

### Purchase
```json
{
  "id": "uuid",
  "customer_id": "uuid",
  "receipt_id": "string|null",
  "timestamp": "2024-01-01T12:00:00Z",
  "amount": 29.99,
  "points_awarded": 30,
  "items_count": 3,
  "processed_at": "2024-01-01T12:00:00Z"
}
```

### System Stats
```json
{
  "total_customers": 150,
  "total_purchases": 500,
  "total_revenue": 15000.00,
  "total_points_awarded": 18500,
  "total_scan_events": 750,
  "avg_purchase_amount": 30.00
}
```

## Interactive Documentation

When the server is running, you can access interactive API documentation at:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`
