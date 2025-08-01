"""
Receipt monitoring service for detecting and parsing printed receipts
"""
import asyncio
import logging
import os
import time
from datetime import datetime, timedelta
from typing import Optional, Dict, List
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from app.utils.receipt_parser import ReceiptParser
from app.utils.config import settings

logger = logging.getLogger(__name__)

class ReceiptFileHandler(FileSystemEventHandler):
    """File system event handler for receipt monitoring"""
    
    def __init__(self, receipt_monitor):
        self.receipt_monitor = receipt_monitor
        
    def on_created(self, event):
        """Handle file creation events"""
        if not event.is_directory:
            asyncio.create_task(self.receipt_monitor.process_new_file(event.src_path))
    
    def on_modified(self, event):
        """Handle file modification events"""
        if not event.is_directory:
            asyncio.create_task(self.receipt_monitor.process_modified_file(event.src_path))

class ReceiptMonitor:
    """Monitors for new receipts and processes them for loyalty integration"""
    
    def __init__(self, websocket_manager):
        self.websocket_manager = websocket_manager
        self.receipt_parser = ReceiptParser()
        self.observer = None
        self.is_monitoring = False
        self.processed_files = set()
        self.pending_customer_scans: List[Dict] = []
        
    async def start_monitoring(self):
        """Start monitoring for receipt files"""
        if not settings.receipt_monitor_enabled:
            logger.info("Receipt monitoring disabled in settings")
            return
            
        try:
            # Create observer for file system events
            self.observer = Observer()
            event_handler = ReceiptFileHandler(self)
            
            # Monitor the print spool directory
            monitor_path = settings.receipt_folder_path
            if os.path.exists(monitor_path):
                self.observer.schedule(event_handler, monitor_path, recursive=False)
                self.observer.start()
                self.is_monitoring = True
                logger.info(f"Started receipt monitoring on: {monitor_path}")
            else:
                logger.warning(f"Receipt folder not found: {monitor_path}")
                
            # Start background processing task
            asyncio.create_task(self._process_pending_receipts())
            
        except Exception as e:
            logger.error(f"Error starting receipt monitor: {e}")
    
    async def stop_monitoring(self):
        """Stop receipt monitoring"""
        if self.observer:
            self.observer.stop()
            self.observer.join()
        self.is_monitoring = False
        logger.info("Receipt monitoring stopped")
    
    async def process_new_file(self, file_path: str):
        """Process a newly created file"""
        await self._process_file(file_path, "created")
    
    async def process_modified_file(self, file_path: str):
        """Process a modified file"""
        await self._process_file(file_path, "modified")
    
    async def _process_file(self, file_path: str, event_type: str):
        """Process a receipt file"""
        try:
            # Skip if already processed
            if file_path in self.processed_files:
                return
                
            # Wait a moment for file to be fully written
            await asyncio.sleep(0.5)
            
            # Check if file looks like a receipt
            if not self._is_receipt_file(file_path):
                return
                
            # Read file content
            receipt_content = await self._read_receipt_file(file_path)
            if not receipt_content:
                return
                
            # Parse receipt
            parsed_receipt = self.receipt_parser.parse_receipt(receipt_content)
            
            # Validate receipt
            if not self.receipt_parser.is_valid_receipt(receipt_content):
                logger.debug(f"File {file_path} doesn't appear to be a valid receipt")
                return
                
            # Mark as processed
            self.processed_files.add(file_path)
            
            # Try to match with recent customer scan
            customer_match = await self._match_customer_scan(parsed_receipt)
            
            if customer_match:
                await self._process_customer_purchase(customer_match, parsed_receipt)
            else:
                logger.info(f"No customer match found for receipt: {parsed_receipt.get('receipt_id', 'unknown')}")
                
        except Exception as e:
            logger.error(f"Error processing receipt file {file_path}: {e}")
    
    def _is_receipt_file(self, file_path: str) -> bool:
        """Check if file appears to be a receipt"""
        filename = os.path.basename(file_path).lower()
        
        # Check file extensions that might contain receipt data
        receipt_extensions = ['.txt', '.prn', '.spl', '.log']
        
        return any(filename.endswith(ext) for ext in receipt_extensions)
    
    async def _read_receipt_file(self, file_path: str) -> Optional[str]:
        """Read receipt file content"""
        try:
            # Try different encodings
            encodings = ['utf-8', 'cp1252', 'ascii']
            
            for encoding in encodings:
                try:
                    with open(file_path, 'r', encoding=encoding) as f:
                        content = f.read()
                        if content.strip():
                            return content
                except UnicodeDecodeError:
                    continue
                    
            # If text reading fails, try binary mode for special printer formats
            with open(file_path, 'rb') as f:
                binary_content = f.read()
                # Convert printable bytes to string
                content = ''.join(chr(b) if 32 <= b <= 126 else '\n' for b in binary_content)
                return content if content.strip() else None
                
        except Exception as e:
            logger.error(f"Error reading receipt file {file_path}: {e}")
            return None
    
    async def _match_customer_scan(self, receipt_data: Dict) -> Optional[Dict]:
        """Match receipt with recent customer scan"""
        if not self.websocket_manager.current_customer_scan:
            return None
            
        # Check if scan is within time window
        scan_time_str = self.websocket_manager.current_customer_scan.get('scanned_at')
        if not scan_time_str:
            return None
            
        try:
            scan_time = datetime.fromisoformat(scan_time_str.replace('Z', '+00:00'))
            current_time = datetime.utcnow()
            time_diff = (current_time - scan_time).total_seconds()
            
            # Check if within matching window
            if time_diff <= settings.receipt_match_window_seconds:
                return self.websocket_manager.current_customer_scan
                
        except Exception as e:
            logger.error(f"Error matching customer scan time: {e}")
            
        return None
    
    async def _process_customer_purchase(self, customer_scan: Dict, receipt_data: Dict):
        """Process a customer purchase"""
        try:
            # Notify Electron app about the purchase
            purchase_data = {
                "barcode": customer_scan.get("barcode"),
                "receipt_data": receipt_data,
                "scanned_at": customer_scan.get("scanned_at"),
                "processed_at": datetime.utcnow().isoformat()
            }
            
            await self.websocket_manager.send_to_electron({
                "action": "process_purchase",
                "purchase_data": purchase_data
            })
            
            logger.info(f"Processed purchase for customer {customer_scan.get('barcode')}: ${receipt_data.get('total', 0)}")
            
        except Exception as e:
            logger.error(f"Error processing customer purchase: {e}")
    
    async def _process_pending_receipts(self):
        """Background task to process any pending receipts"""
        while self.is_monitoring:
            try:
                # Clean up old processed files from memory
                if len(self.processed_files) > 1000:
                    # Keep only recent files
                    self.processed_files = set(list(self.processed_files)[-500:])
                
                # Sleep for a bit before next check
                await asyncio.sleep(5)
                
            except Exception as e:
                logger.error(f"Error in pending receipts processor: {e}")
                await asyncio.sleep(10)
    
    def add_test_receipt(self, receipt_content: str) -> Dict:
        """Add a test receipt for development/testing purposes"""
        parsed_receipt = self.receipt_parser.parse_receipt(receipt_content)
        
        # Try to match with current customer scan
        customer_match = self.websocket_manager.current_customer_scan
        
        if customer_match:
            asyncio.create_task(self._process_customer_purchase(customer_match, parsed_receipt))
        
        return parsed_receipt
    
    def get_monitoring_status(self) -> Dict:
        """Get current monitoring status"""
        return {
            "is_monitoring": self.is_monitoring,
            "monitor_path": settings.receipt_folder_path,
            "processed_files_count": len(self.processed_files),
            "pending_scans": len(self.pending_customer_scans)
        }
