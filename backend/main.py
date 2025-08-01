"""
Main FastAPI application entry point for the Loyalty System
"""
import asyncio
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
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
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level="info"
    )
