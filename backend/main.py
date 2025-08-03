"""
Main FastAPI application entry point for the Loyalty System
"""
import asyncio
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import socketio
from app.models.database import init_db
from app.routes import customers, purchases, admin
from app.services.websocket_manager import WebSocketManager
from app.services.receipt_monitor import ReceiptMonitor
from app.utils.config import Settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize settings
settings = Settings()

# WebSocket manager
ws_manager = WebSocketManager()

# Receipt monitor
receipt_monitor = ReceiptMonitor(ws_manager)

# Create Socket.IO server
sio = socketio.AsyncServer(
    async_mode='asgi',
    cors_allowed_origins="*",
    logger=True,
    engineio_logger=True
)

# Set Socket.IO server in WebSocket manager
ws_manager.set_socketio_server(sio)

# Socket.IO event handlers
@sio.event
async def connect(sid, environ, auth):
    """Handle Socket.IO client connection"""
    logger.info(f"Socket.IO client connected: {sid}")
    await sio.emit('connected', {'status': 'connected'}, room=sid)

@sio.event
async def disconnect(sid):
    """Handle Socket.IO client disconnection"""
    logger.info(f"Socket.IO client disconnected: {sid}")
    # Clean up any stored client references
    if ws_manager.tablet_sid == sid:
        ws_manager.tablet_sid = None
    if ws_manager.electron_sid == sid:
        ws_manager.electron_sid = None

@sio.event
async def identify_client(sid, data):
    """Handle client identification"""
    client_type = data.get('type', 'unknown')
    logger.info(f"Client {sid} identified as: {client_type}")
    
    if client_type == 'tablet':
        ws_manager.tablet_sid = sid
        await ws_manager._reset_to_idle()
    elif client_type == 'electron':
        ws_manager.electron_sid = sid
        await sio.emit('electron_connected', {'status': 'connected'}, room=sid)

@sio.event
async def message(sid, data):
    """Handle generic message from Socket.IO clients"""
    logger.info(f"Received message from {sid}: {data}")
    
    # Handle different client types based on the path or data
    action = data.get('action', '')
    
    if action == 'start_registration':
        await ws_manager._start_customer_registration()
    elif action == 'customer_scanned':
        barcode = data.get('barcode', '')
        await ws_manager._handle_customer_scan(barcode)
    elif action == 'submit_customer_form':
        customer_data = data.get('data', {})
        await ws_manager._handle_customer_registration(customer_data)
    elif action == 'reset_to_idle':
        await ws_manager._reset_to_idle()
    elif action == 'heartbeat':
        await sio.emit('heartbeat_ack', room=sid)

@sio.on('tablet_message')
async def handle_tablet_message(sid, data):
    """Handle messages specifically from tablet"""
    logger.info(f"Tablet message from {sid}: {data}")
    await ws_manager.handle_tablet_message(data)

@sio.on('electron_message')
async def handle_electron_message(sid, data):
    """Handle messages specifically from Electron app"""
    logger.info(f"Electron message from {sid}: {data}")
    await ws_manager.handle_electron_message(data)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    # Startup
    logger.info("Starting Loyalty System Backend...")
    await init_db()
    
    # Start receipt monitoring in background
    asyncio.create_task(receipt_monitor.start_monitoring())
    
    yield
    
    # Shutdown
    logger.info("Shutting down Loyalty System Backend...")
    await receipt_monitor.stop_monitoring()

# Create FastAPI app
app = FastAPI(
    title="Tienda Loyalty System",
    description="Backend API for hybrid loyalty enrollment system",
    version="1.0.0",
    lifespan=lifespan
)

# Mount Socket.IO app
socket_app = socketio.ASGIApp(sio, app)

# Include routers
app.include_router(customers.router, prefix="/api/customers", tags=["customers"])
app.include_router(purchases.router, prefix="/api/purchases", tags=["purchases"])
app.include_router(admin.router, prefix="/api/admin", tags=["admin"])

# Serve tablet UI static files
app.mount("/static", StaticFiles(directory="../tablet-ui/static"), name="static")

@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "Tienda Loyalty System API", "version": "1.0.0"}

@app.get("/tablet")
async def tablet_interface():
    """Serve tablet interface"""
    return FileResponse("../tablet-ui/index.html")

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "loyalty-backend"}

# WebSocket endpoint for tablet communication
@app.websocket("/ws/tablet")
async def websocket_tablet_endpoint(websocket: WebSocket):
    """WebSocket endpoint for tablet interface"""
    await ws_manager.connect_tablet(websocket)
    try:
        while True:
            data = await websocket.receive_json()
            await ws_manager.handle_tablet_message(data)
    except WebSocketDisconnect:
        ws_manager.disconnect_tablet()
        logger.info("Tablet disconnected")

# WebSocket endpoint for electron app communication  
@app.websocket("/ws/electron")
async def websocket_electron_endpoint(websocket: WebSocket):
    """WebSocket endpoint for Electron app"""
    await ws_manager.connect_electron(websocket)
    try:
        while True:
            data = await websocket.receive_json()
            await ws_manager.handle_electron_message(data)
    except WebSocketDisconnect:
        ws_manager.disconnect_electron()
        logger.info("Electron app disconnected")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        socket_app,
        host=settings.host,
        port=settings.port,
        reload=False,  # Socket.IO doesn't work well with reload
        log_level="info"
    )
