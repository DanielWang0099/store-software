"""
WebSocket connection manager for tablet and electron communication
"""
import asyncio
import json
import logging
from datetime import datetime
from typing import Optional, Dict, Any
from fastapi import WebSocket

logger = logging.getLogger(__name__)

class WebSocketManager:
    """Manages WebSocket connections between tablet, electron app, and backend"""
    
    def __init__(self):
        self.tablet_connection: Optional[WebSocket] = None
        self.electron_connection: Optional[WebSocket] = None
        self.current_customer_scan: Optional[Dict] = None
        self.tablet_state = "idle"  # idle, registration, confirmation
        
    async def connect_tablet(self, websocket: WebSocket):
        """Connect tablet interface"""
        await websocket.accept()
        self.tablet_connection = websocket
        logger.info("Tablet connected")
        
        # Send initial idle state
        await self.send_to_tablet({
            "action": "set_state",
            "state": "idle",
            "timestamp": datetime.utcnow().isoformat()
        })
    
    async def connect_electron(self, websocket: WebSocket):
        """Connect Electron app"""
        await websocket.accept()
        self.electron_connection = websocket
        logger.info("Electron app connected")
        
        # Send connection confirmation
        await self.send_to_electron({
            "action": "connected",
            "timestamp": datetime.utcnow().isoformat()
        })
    
    def disconnect_tablet(self):
        """Disconnect tablet"""
        self.tablet_connection = None
        self.tablet_state = "idle"
        logger.info("Tablet disconnected")
    
    def disconnect_electron(self):
        """Disconnect Electron app"""
        self.electron_connection = None
        logger.info("Electron app disconnected")
    
    async def send_to_tablet(self, message: Dict[str, Any]):
        """Send message to tablet"""
        if self.tablet_connection:
            try:
                await self.tablet_connection.send_json(message)
                logger.debug(f"Sent to tablet: {message}")
            except Exception as e:
                logger.error(f"Error sending to tablet: {e}")
                self.tablet_connection = None
    
    async def send_to_electron(self, message: Dict[str, Any]):
        """Send message to Electron app"""
        if self.electron_connection:
            try:
                await self.electron_connection.send_json(message)
                logger.debug(f"Sent to Electron: {message}")
            except Exception as e:
                logger.error(f"Error sending to Electron: {e}")
                self.electron_connection = None
    
    async def handle_tablet_message(self, data: Dict[str, Any]):
        """Handle message from tablet"""
        action = data.get("action")
        logger.info(f"Received from tablet: {action}")
        
        if action == "submit_customer_form":
            await self._handle_customer_registration(data.get("data", {}))
        elif action == "reset_to_idle":
            await self._reset_to_idle()
        elif action == "heartbeat":
            await self.send_to_tablet({"action": "heartbeat_ack"})
    
    async def handle_electron_message(self, data: Dict[str, Any]):
        """Handle message from Electron app"""
        action = data.get("action")
        logger.info(f"Received from Electron: {action}")
        
        if action == "start_registration":
            await self._start_customer_registration()
        elif action == "customer_scanned":
            await self._handle_customer_scan(data.get("barcode", ""))
        elif action == "receipt_processed":
            await self._handle_receipt_processed(data.get("receipt_data", {}))
        elif action == "reset_tablet":
            await self._reset_to_idle()
    
    async def _start_customer_registration(self):
        """Start customer registration process"""
        self.tablet_state = "registration"
        await self.send_to_tablet({
            "action": "show_registration_form",
            "fields": ["name", "email", "phone"],
            "title": "New Customer Registration",
            "timeout": 120
        })
        
        await self.send_to_electron({
            "action": "registration_started",
            "tablet_state": self.tablet_state
        })
    
    async def _handle_customer_registration(self, customer_data: Dict):
        """Handle customer registration from tablet"""
        try:
            # Forward to Electron for processing
            await self.send_to_electron({
                "action": "process_customer_registration",
                "customer_data": customer_data,
                "timestamp": datetime.utcnow().isoformat()
            })
            
            # Show confirmation on tablet
            await self.send_to_tablet({
                "action": "show_confirmation",
                "message": f"Welcome, {customer_data.get('name', 'Customer')}!",
                "type": "success",
                "auto_reset": 5
            })
            
            # Reset to idle after confirmation
            await asyncio.sleep(5)
            await self._reset_to_idle()
            
        except Exception as e:
            logger.error(f"Error handling customer registration: {e}")
            await self.send_to_tablet({
                "action": "show_error",
                "message": "Registration failed. Please try again.",
                "auto_reset": 3
            })
    
    async def _handle_customer_scan(self, barcode: str):
        """Handle customer barcode scan"""
        self.current_customer_scan = {
            "barcode": barcode,
            "scanned_at": datetime.utcnow().isoformat()
        }
        
        # Show customer info on tablet
        await self.send_to_tablet({
            "action": "show_customer_info",
            "barcode": barcode,
            "message": "Customer scanned - processing...",
            "auto_reset": 10
        })
        
        logger.info(f"Customer scan recorded: {barcode}")
    
    async def _handle_receipt_processed(self, receipt_data: Dict):
        """Handle receipt processing completion"""
        await self.send_to_tablet({
            "action": "show_purchase_complete",
            "receipt_data": receipt_data,
            "points_awarded": receipt_data.get("points_awarded", 0),
            "auto_reset": 8
        })
        
        # Clear current customer scan
        self.current_customer_scan = None
    
    async def _reset_to_idle(self):
        """Reset tablet to idle state"""
        self.tablet_state = "idle"
        self.current_customer_scan = None
        
        await self.send_to_tablet({
            "action": "set_state",
            "state": "idle"
        })
        
        await self.send_to_electron({
            "action": "tablet_reset",
            "tablet_state": self.tablet_state
        })
    
    async def broadcast_system_status(self, status: Dict):
        """Broadcast system status to all connected clients"""
        message = {
            "action": "system_status",
            "status": status,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        await self.send_to_tablet(message)
        await self.send_to_electron(message)
    
    def get_connection_status(self) -> Dict:
        """Get current connection status"""
        return {
            "tablet_connected": self.tablet_connection is not None,
            "electron_connected": self.electron_connection is not None,
            "tablet_state": self.tablet_state,
            "current_customer_scan": self.current_customer_scan
        }
